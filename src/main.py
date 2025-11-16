import asyncio
import os
import uvicorn
from dotenv import load_dotenv
from src.bot import dp, bot, rag  # Импортируем бота и RAG
from src.logging_config import setup_logging

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

    logger.info("Запуск бота и API...")

    # Создаём задачу для Telegram-бота (асинхронно, без блокировки)
    bot_task = asyncio.create_task(dp.start_polling(bot))

    # Запускаем FastAPI в отдельном потоке (Uvicorn не asyncio-native)
    api_task = asyncio.to_thread(uvicorn.run, "src.api:app", host="0.0.0.0", port=8000, log_level="info")

    try:
        await asyncio.gather(bot_task, api_task)
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)

# Запуск, если файл запускается напрямую
if __name__ == "__main__":
    asyncio.run(main())