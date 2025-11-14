import asyncio
import os
from dotenv import load_dotenv
from .bot import dp, bot, rag
from .logging_config import setup_logging

load_dotenv("config.env")
setup_logging()

logger = __import__("logging").getLogger(__name__)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в config.env")
        return

    # Проверка RAG
    if not rag.db:
        logger.critical("ChromaDB не инициализирована! Проверьте data/ и Ollama.")
        return

    if rag.db._collection.count() == 0:
        logger.warning("ChromaDB пуста! Загружаются CSV из data/...")
        # Автозагрузка уже в bot.py
    else:
        logger.info(f"ChromaDB загружена: {rag.db._collection.count()} документов")

    logger.info("Бот запущен...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        
if __name__ == "__main__":
    asyncio.run(main())