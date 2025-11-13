from src.vector_db import VectorDB
from src.llm import LLMService

class RAGSystem:
    def __init__(self):
        self.vector_db = VectorDB()
        self.llm = LLMService()
    
    async def process_query(self, query, business_type="general"):
        """Основной метод обработки запроса"""
        # 1. Поиск релевантных документов
        relevant_docs = await self.vector_db.search(query)
        
        # 2. Формирование промпта с контекстом
        context = "\n".join(relevant_docs)
        prompt = self._build_prompt(query, context, business_type)
        
        # 3. Генерация ответа
        response = await self.llm.generate(prompt)
        return response
    
    def _build_prompt(self, query, context, business_type):
        """Формирование промпта для LLM"""
        return f"""
        Вы - виртуальный помощник для малого бизнеса. Помогите владельцу бизнеса, отвечая на его вопрос.
        Сфера бизнеса: {business_type}
        
        Контекст для ответа:
        {context}
        
        Вопрос пользователя:
        {query}
        
        Инструкции:
        1. Дайте четкий, краткий и полезный ответ на русском языке
        2. Опираетесь только на предоставленный контекст
        3. Если информации недостаточно, скажите об этом
        4. Предложите конкретные шаги для решения проблемы
        
        Ответ:
        """