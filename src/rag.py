import logging
import time
from src.vector_db import VectorDB
from src.llm import LLMService

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        self.vector_db = VectorDB()
        self.llm = LLMService()
    
    async def process_query(self, query):
        """Обработка запроса с детальным логированием"""
        logger.info(f"\n{'='*50}")
        logger.info(f"НОВЫЙ ЗАПРОС: {query}")
        logger.info(f"{'='*50}")
        
        # 1. Поиск релевантных документов
        start_time = time.time()
        raw_relevant_docs = await self.vector_db.search_with_metadata(query, n_results=3)
        search_time = time.time() - start_time
        
        # 2. Фильтрация документов по релевантности (только положительная релевантность)
        relevant_docs = sorted(raw_relevant_docs, key=lambda x: x['distance'])
        
        logger.info(f"[RAG] Поиск завершен за {search_time:.2f} секунд")
        logger.info(f"[RAG] Найдено документов до фильтрации: {len(raw_relevant_docs)}")
        logger.info(f"[RAG] Найдено релевантных документов после фильтрации: {len(relevant_docs)}")
            
        # Детальное логирование найденных документов
        for i, doc in enumerate(relevant_docs):
            logger.info(f"[RAG] Документ #{i+1}:")
            logger.info(f"[RAG] - Источник: {doc['metadata'].get('source', 'неизвестно')}")
            logger.info(f"[RAG] - Файл: {doc['metadata'].get('filename', 'неизвестно')}")
            logger.info(f"[RAG] - Содержимое: \"{doc['document'][:100]}...\"")
        
        # 2. Формирование промпта с контекстом
        context_docs = [doc['document'] for doc in relevant_docs]
        context = "\n".join([f"Источник [{i+1}]: {doc}" for i, doc in enumerate(context_docs)])
        
        prompt = self._build_prompt(query, context)
        logger.info(f"[RAG] Сформирован промпт:\n{prompt}")
        
        # 3. Генерация ответа
        start_time = time.time()
        response = await self.llm.generate(prompt)
        gen_time = time.time() - start_time
        
        logger.info(f"[RAG] Ответ сгенерирован за {gen_time:.2f} секунд")
        logger.info(f"[RAG] Сырой ответ от LLM: \"{response[:100]}...\"")
        
        # 4. Формирование финального ответа с указанием источников
        final_response = self._format_response_with_sources(response, relevant_docs)
        
        logger.info(f"[RAG] Финальный ответ с источниками:\n{final_response}")
        logger.info(f"{'='*50}\n")
        
        return final_response
    
    def _build_prompt(self, query, context):
        """Формирование промпта для LLM"""
        return f"""
    Вы - полезный виртуальный помощник для владельцев малого бизнеса в России.
    У вас есть доступ к следующему контексту из базы знаний:
    {context}
    
    ПРАВИЛА ОТВЕТА:
    1. Если контекст содержит релевантную информацию по вопросу - ИСПОЛЬЗУЙТЕ ЕЕ и укажите источник
    2. Если контекст не содержит точного ответа, но вопрос общий (бизнес, финансы, юриспруденция) - ИСПОЛЬЗУЙТЕ СВОИ ЗНАНИЯ
    3. Если вопрос содержит опечатку или неточность - ВЕЖЛИВО УТОЧНИТЕ или попробуйте понять суть
    4. Отвечайте КРАТКО, ПОЛЕЗНО и ПРАКТИЧНО
    5. Если вопрос выходит за рамки бизнеса или этики - ВЕЖЛИВО ОТКАЖИТЕСЬ
    
    ВОПРОС ПОЛЬЗОВАТЕЛЯ:
    {query}
    
    ТВЕТ:
    """
    
    def _format_response_with_sources(self, response, relevant_docs):
        """Добавление информации об источниках к ответу"""
        clean_response = response.strip()
        
        # Формируем список источников с полной информацией
        sources_section = "\n\n📚 Использованные источники информации:\n"
        source_markers = []
        
        for i, doc in enumerate(relevant_docs):
            source = doc['metadata'].get('source', 'другой источник')
            filename = doc['metadata'].get('filename', '')
            relevance = f"(релевантность: {1-doc['distance']:.2f})" if doc.get('distance') is not None else ""
            
            # Добавляем маркер источника для использования в тексте [1], [2] и т.д.
            source_markers.append(f"[{i+1}]")
            
            # Формируем информацию об источнике
            source_info = f"{i+1}. {source.title()} | {filename} {relevance}"
            content_sample = f"   Содержимое: \"{doc['document'][:150]}...\""
            sources_section += f"{source_info}\n{content_sample}\n\n"
        
        # Добавляем предупреждение о точности ответа
        disclaimer = "\nℹ️ Примечание: Ответ сгенерирован ИИ на основе указанных источников. " \
                    "Рекомендуется проверить важную информацию перед использованием."
        
        # Собираем финальный ответ
        final_response = f"{clean_response}{sources_section}{disclaimer}"
        
        return final_response