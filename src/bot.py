# src/bot.py
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
from dotenv import load_dotenv
import glob

from .rag import RAGSystem
from .llm import LLMService
from .logging_config import setup_logging

load_dotenv("config.env")
setup_logging()

logger = __import__("logging").getLogger(__name__)

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()
rag = RAGSystem()
llm_service = LLMService()

# === УМНАЯ АВТОЗАГРУЗКА ===
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
csv_pattern = os.path.join(data_dir, "*.csv")
csv_files = glob.glob(csv_pattern)

if rag.db and rag.db._collection.count() > 0:
    logger.info(f"RAG уже содержит {rag.db._collection.count()} документов. Пропускаем загрузку.")
else:
    logger.info(f"RAG пуст. Загружаю ВСЕ CSV из data/ ({len(csv_files)} файлов)...")
    
    if not csv_files:
        logger.critical("ПАПКА data/ ПУСТА! Добавьте CSV-файлы и перезапустите.")
        exit(1)
    
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        try:
            logger.info(f"Загружаю: {filename}...")
            rag.add_csv(csv_path, batch_size=4000)
            logger.info(f"УСПЕШНО: {filename}")
        except Exception as e:
            logger.critical(f"ОШИБКА при загрузке {filename}: {e}")
            exit(1)
# === ХЭНДЛЕРЫ ===
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я — ИИ-помощник для малого бизнеса.\n"
        "Задайте любой вопрос — я помогу!"
    )

@dp.message()
async def handle_text(message: types.Message):
    user_query = message.text.strip()
    if not user_query:
        await message.answer("Напишите вопрос!")
        return

    logger.info(f"Вопрос: {user_query}")
    context = rag.search(user_query, k=5)

    prompt = f"""
Ты — ИИ-помощник для малого бизнеса.
Отвечай кратко, по делу, на русском.
Анализируй CSV с колонками.
Дата в формате ГГГГ-ММ-ДД.

Контекст:
{context}

Вопрос: {user_query}

Ответ:
"""

    try:
        response = await llm_service.generate(prompt)
        await message.answer(response)
        logger.info(f"ОТПРАВЛЕНО пользователю: {response}")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Извините, не смог ответить.")