# src/rag.py
# RAG — это "база знаний". Загружает CSV и ищет в них нужные строки.

from langchain_community.document_loaders import CSVLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
from .logging_config import setup_logging

load_dotenv("config.env")
setup_logging()

logger = __import__("logging").getLogger(__name__)

# === НАСТРОЙКИ ===
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")  # Папка с базой
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")  # Модель для поиска

class RAGSystem:
    def __init__(self):
        # Создаём модель для преобразования текста в числа (векторы)
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        # Путь к папке с базой
        self.db_path = os.path.join(os.path.dirname(__file__), "..", CHROMA_DB_PATH.lstrip("./"))
        os.makedirs(self.db_path, exist_ok=True)  # Создаём папку, если нет
        self.db = None
        self.load_or_create_db()  # Загружаем или создаём базу
        logger.info(f"RAG инициализирован: {self.db_path}")

    def load_or_create_db(self):
        # Если база уже есть — загружаем
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            self.db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
            logger.info("Загружена существующая БД")
        else:
            # Если нет — создаём новую
            self.db = Chroma(embedding_function=self.embeddings, persist_directory=self.db_path)
            logger.info("Создана новая БД")

    def add_csv(self, csv_path: str, batch_size: int = 5000):
        # Загружаем CSV-файл
        loader = CSVLoader(csv_path)
        docs = loader.load()  # Каждая строка — отдельный документ
        
        logger.info(f"Загружаю {len(docs)} документов из {csv_path} батчами по {batch_size}")

        # Добавляем по частям (батчам), чтобы не зависнуть
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]  # Отрезаем кусочек
            try:
                self.db.add_documents(batch)  # Добавляем в векторную базу
                logger.debug(f"Добавлен батч {i//batch_size + 1}: {len(batch)} документов")
            except Exception as e:
                logger.error(f"Ошибка при добавлении батча: {e}")
        
        logger.info(f"Успешно загружено {len(docs)} документов из {csv_path}")

    def search(self, query: str, k: int = 5):
        # Ищем в базе k самых похожих строк
        if not self.db:
            logger.warning("Поиск: БД пуста")
            return "БД пуста. Загрузите CSV."
        results = self.db.similarity_search(query, k=k)
        logger.debug(f"Найдено {len(results)} релевантных фрагментов")
        # Возвращаем текст всех найденных строк
        return "\n".join([doc.page_content for doc in results])