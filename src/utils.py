import os
import logging
from src.vector_db import VectorDB

async def load_initial_data(vector_db=None):
    """Загрузка тестовых данных из файлов в папке data"""
    if vector_db is None:
        vector_db = VectorDB()
    
    # Правильный путь к папке с данными
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    
    logging.info(f"Поиск данных в директории: {data_dir}")
    
    if not os.path.exists(data_dir):
        logging.error(f"Директория с данными не найдена: {data_dir}")
        logging.error(f"Доступные директории в проекте: {os.listdir(project_root)}")
        return False
    
    documents = []
    metadatas = []
    ids = []
    
    # Счетчики для логирования
    total_files = 0
    total_docs = 0
    
    # Обработка всех .csv файлов в папке data
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            total_files += 1
            category = os.path.splitext(filename)[0]
            file_path = os.path.join(data_dir, filename)
            
            logging.info(f"Обработка файла: {filename} (категория: {category})")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    # Разделяем содержимое по двойным переносам строк или по точкам
                    if "\n\n" in content:
                        chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]
                    elif ". " in content:
                        chunks = [chunk.strip() for chunk in content.split(". ") if chunk.strip()]
                    else:
                        chunks = [content]
                    
                    logging.info(f"Разделено на {len(chunks)} частей")
                    
                    for i, chunk in enumerate(chunks):
                        if len(chunk) > 20:  # Игнорируем слишком короткие фрагменты
                            total_docs += 1
                            documents.append(chunk)
                            metadatas.append({
                                "source": category,
                                "category": category,
                                "filename": filename
                            })
                            ids.append(f"{category}_{i}")
                            logging.debug(f"Добавлен документ: {chunk[:30]}...")
            except Exception as e:
                logging.error(f"Ошибка при чтении {filename}: {str(e)}")
    
    logging.info(f"Всего обработано файлов: {total_files}")
    logging.info(f"Всего подготовлено документов для индексации: {len(documents)}")
    
    if not documents:
        logging.error("Не найдено ни одного документа для загрузки. Проверьте содержимое папки data.")
        return False
    
    try:
        logging.info("Начало индексации документов в векторную БД...")
        await vector_db.add_documents(documents, metadatas, ids)
        logging.info(f"Успешно загружено {len(documents)} документов в векторную БД")
        return True
    except Exception as e:
        logging.error(f"Ошибка при добавлении данных в векторную БД: {str(e)}")
        return False