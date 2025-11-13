import os
import logging
import chromadb
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()

class VectorDB:
    def __init__(self):
        self.db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        os.makedirs(self.db_path, exist_ok=True)
        
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="business_data",
            metadata={"description": "Business documents for small business assistant"},
            embedding_function=self.embedding_function
        )
    
    async def add_documents(self, documents, metadatas, ids):
        """Добавление документов в векторную БД"""
        logging.info(f"Добавление {len(documents)} документов в векторную БД")
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logging.info("Документы успешно добавлены в векторную БД")
    
    async def search(self, query, n_results=3):
        """Поиск релевантных документов"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["documents"][0]
    
    def is_collection_empty(self):
        """Проверка, пустая ли коллекция"""
        try:
            # Пытаемся получить первый документ
            peek_result = self.collection.peek(limit=1)
            return len(peek_result.get('documents', [])) == 0
        except Exception as e:
            logging.error(f"Ошибка при проверке коллекции: {str(e)}")
            return True