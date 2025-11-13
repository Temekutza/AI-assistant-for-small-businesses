import os
import logging
import chromadb
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()
logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        self.db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        os.makedirs(self.db_path, exist_ok=True)
        
        # Используем встроенную функцию эмбеддингов
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="business_docs",
            metadata={"description": "Business documents for small business assistant"},
            embedding_function=self.embedding_function
        )
    
    def is_collection_empty(self):
        """Проверка, пустая ли коллекция"""
        try:
            # Получаем количество документов в коллекции
            count = self.collection.count()
            logger.info(f"[DB] Количество документов в коллекции: {count}")
            return count == 0
        except Exception as e:
            logger.error(f"[DB] Ошибка при проверке коллекции: {str(e)}")
            # В случае ошибки считаем, что коллекция пустая и нуждается в загрузке данных
            return True
    
    async def add_documents(self, documents, metadatas, ids):
        """Добавление документов в векторную БД"""
        logger.info(f"[DB] Добавление {len(documents)} документов в векторную БД")
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("[DB] Документы успешно добавлены в векторную БД")
        except Exception as e:
            logger.error(f"[DB] Ошибка при добавлении документов: {str(e)}")
            raise
    
    async def search_with_metadata(self, query, n_results=3):
        """Поиск релевантных документов с возвратом метаданных"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Проверяем структуру результатов
            if not results["documents"] or len(results["documents"]) == 0 or len(results["documents"][0]) == 0:
                logger.warning(f"[DB] Не найдено документов для запроса: '{query}'")
                return []
            
            # Форматируем результаты для удобства использования
            formatted_results = []
            for i in range(len(results["documents"][0])):
                document = results["documents"][0][i] if i < len(results["documents"][0]) else None
                metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                distance = results["distances"][0][i] if "distances" in results and results["distances"] and i < len(results["distances"][0]) else None
                
                if document is not None:
                    formatted_results.append({
                        "document": document,
                        "metadata": metadata,
                        "distance": distance
                    })
            
            logger.info(f"[DB] Запрос: '{query}'")
            logger.info(f"[DB] Найдено результатов: {len(formatted_results)}")
            for res in formatted_results:
                source = res['metadata'].get('source', 'неизвестно')
                distance = res['distance'] if res['distance'] is not None else 'неизвестно'
                logger.info(f"[DB] - Источник: {source}, Расстояние: {distance}")
                logger.info(f"[DB] - Содержимое: \"{res['document'][:100]}...\"")
            
            return formatted_results
        except Exception as e:
            logger.error(f"[DB] Ошибка при поиске: {str(e)}")
            return []