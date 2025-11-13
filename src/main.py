import os
import logging
import asyncio
import signal
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from src.rag import RAGSystem
from src.utils import load_initial_data
from src.vector_db import VectorDB

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(current_dir, 'config.env')
vector_db = None
rag_system = None

# Загрузка переменных окружения с отладкой
logger.info(f"Попытка загрузить переменные окружения из: {env_path}")

if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info("Файл config.env успешно найден и загружен")
else:
    logger.error(f"Файл config.env не найден по пути: {env_path}")
    load_dotenv()

# Проверка токена
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    logger.error("Ошибка: TELEGRAM_BOT_TOKEN не установлен")
    logger.error("Пожалуйста, получите токен у @BotFather в Telegram и обновите файл config.env")
    exit(1)

logger.info("TELEGRAM_BOT_TOKEN успешно загружен")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я виртуальный помощник для малого бизнеса.\n"
        "Напишите свой вопрос, и я постараюсь помочь.\n"
        "Доступные темы: юридические вопросы, маркетинг, финансы"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Как я могу помочь?\n"
        "1. Напишите свой вопрос по бизнесу\n"
        "2. Укажите сферу (юридические, маркетинг, финансы)\n"
        "3. Получите рекомендации"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    logger.info(f"Получен запрос от пользователя: {user_message}")
    
    # Показываем, что бот думает
    await update.message.reply_chat_action(action="typing")
    
    # Обрабатываем запрос через RAG
    response = await rag_system.process_query(user_message)
    
    # Отправляем ответ
    await update.message.reply_text(response)

async def initialize_system():
    """Инициализация системы перед запуском бота"""
    global vector_db, rag_system
    
    # Инициализация векторной БД
    vector_db = VectorDB()
    
    # Проверяем, нужно ли загружать данные
    db_needs_data = vector_db.is_collection_empty()
    db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    full_db_path = os.path.join(current_dir, db_path)
    
    logger.info(f"Проверка состояния векторной БД: {'пустая' if db_needs_data else 'содержит данные'}")
    logger.info(f"Путь к векторной БД: {full_db_path}")
    
    if db_needs_data:
        logger.info("Векторная БД пустая. Загрузка тестовых данных...")
        success = await load_initial_data(vector_db)
        if not success:
            logger.warning("Не удалось загрузить данные. Бот будет работать без контекста.")
    else:
        logger.info("Векторная БД уже содержит данные. Пропускаем загрузку.")
    
    # Инициализация RAG системы
    rag_system = RAGSystem()

async def main():
    """Основная асинхронная функция"""
    # Инициализация системы
    await initialize_system()
    
    # Создаем приложение
    logger.info("Создание приложения Telegram бота...")
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Настраиваем graceful shutdown
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Получен сигнал завершения. Остановка приложения...")
        application.stop()
        stop_event.set()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, signal_handler)
    
    # Запускаем бота
    logger.info("Запуск бота...")
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Бот успешно запущен и работает")
        
        # Ждем сигнала остановки
        await stop_event.wait()
    finally:
        logger.info("Завершение работы бота...")
        await application.stop()
        await application.shutdown()
        logger.info("Бот успешно остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Принудительная остановка приложения. Завершение работы...")