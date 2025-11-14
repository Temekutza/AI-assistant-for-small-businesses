# src/rag.py
from langchain_community.document_loaders import CSVLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
from .logging_config import setup_logging

load_dotenv("config.env")
setup_logging()

logger = __import__("logging").getLogger(__name__)

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

class RAGSystem:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.db_path = os.path.join(os.path.dirname(__file__), "..", CHROMA_DB_PATH.lstrip("./"))
        os.makedirs(self.db_path, exist_ok=True)
        self.db = None
        self.load_or_create_db()
        logger.info(f"RAG инициализирован: {self.db_path}")

    def load_or_create_db(self):
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            self.db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
            logger.info("Загружена существующая БД")
        else:
            self.db = Chroma(embedding_function=self.embeddings, persist_directory=self.db_path)
            logger.info("Создана новая БД")

    def add_csv(self, csv_path: str, batch_size: int = 5000):
        loader = CSVLoader(csv_path)
        docs = loader.load()
        
        logger.info(f"Загружаю {len(docs)} документов из {csv_path} батчами по {batch_size}")

        for i in range(0, len(docs), batch_size):
            
            batch = docs[i:i + batch_size]
            try:
                self.db.add_documents(batch)
                logger.debug(f"Добавлен батч {i//batch_size + 1}: {len(batch)} документов")
            except Exception as e:
                logger.error(f"Ошибка при добавлении батча: {e}")
        
        
        logger.info(f"Успешно загружено {len(docs)} документов из {csv_path}")

    def search(self, query: str, k: int = 5):
        if not self.db:
            logger.warning("Поиск: БД пуста")
            return "БД пуста. Загрузите CSV."
        results = self.db.similarity_search(query, k=k)
        logger.debug(f"Найдено {len(results)} релевантных фрагментов")
        return "\n".join([doc.page_content for doc in results])