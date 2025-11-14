# src/main.py
# Точка входа. Запускает бота и проверяет, всё ли готово.

import asyncio
import os
from dotenv import load_dotenv
from .bot import dp, bot, rag  # Импортируем бота и RAG
from .logging_config import setup_logging

# === ЗАГРУЗКА НАСТРОЕК ===
load_dotenv("config.env")  # Читаем config.env
setup_logging()            # Включаем логи

logger = __import__("logging").getLogger(__name__)

async def main():
    # Проверяем: есть ли токен бота?
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в config.env")
        return

    # Проверяем: инициализирована ли база RAG?
    if not rag.db:
        logger.critical("ChromaDB не инициализирована! Проверьте data/ и Ollama.")
        return

    # Проверяем: есть ли данные в базе?
    if rag.db._collection.count() == 0:
        logger.warning("ChromaDB пуста! Загружаются CSV из data/...")
        # Загрузка уже произошла в bot.py
    else:
        logger.info(f"ChromaDB загружена: {rag.db._collection.count()} документов")

    logger.info("Бот запущен...")
    try:
        # Запускаем бота — он будет ждать сообщения
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        
# Запуск, если файл запускается напрямую
if __name__ == "__main__":
    asyncio.run(main())