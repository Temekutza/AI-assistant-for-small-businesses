# src/bot.py
# Этот файл — мозг Telegram-бота. Здесь он слушает сообщения и отвечает.

from aiogram import Bot, Dispatcher, types  # Библиотека для работы с Telegram
from aiogram.filters import Command     # Фильтр для команды /start
import os                               # Работа с файлами и путями
from dotenv import load_dotenv          # Загрузка настроек из файла config.env
import glob                             # Поиск файлов по шаблону (*.csv)

from .rag import RAGSystem              # Наш RAG — ищет ответы в CSV
from .llm import LLMService             # Наш ИИ — генерирует ответы
from .logging_config import setup_logging  # Настройка логов

# === ЗАГРУЗКА НАСТРОЕК ===
load_dotenv("config.env")  # Читаем файл config.env (токен бота, модели и т.д.)
setup_logging()            # Включаем логирование (в консоль и bot.log)

logger = __import__("logging").getLogger(__name__)  # Логгер для этого файла

# === СОЗДАЁМ БОТА ===
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))  # Бот с токеном из config.env
dp = Dispatcher()                                 # Диспетчер — управляет сообщениями
rag = RAGSystem()                                 # RAG — база знаний из CSV
llm_service = LLMService()                        # ИИ — отвечает на вопросы

# === АВТОЗАГРУЗКА ВСЕХ CSV ИЗ ПАПКИ data/ ===
# Если база пуста — загрузим все CSV, чтобы бот знал, о чём говорить
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")  # Путь к папке data/
csv_pattern = os.path.join(data_dir, "*.csv")  # Шаблон: все файлы .csv
csv_files = glob.glob(csv_pattern)             # Находим все CSV-файлы

# Проверяем: есть ли уже данные в базе?
if rag.db and rag.db._collection.count() > 0:
    # Если база не пуста — пропускаем загрузку (экономим время)
    logger.info(f"RAG уже содержит {rag.db._collection.count()} документов. Пропускаем загрузку.")
else:
    # Если база пуста — загружаем ВСЁ из data/
    logger.info(f"RAG пуст. Загружаю ВСЕ CSV из data/ ({len(csv_files)} файлов)...")
    
    if not csv_files:
        # Если папка data/ пуста — ругаемся и выходим
        logger.critical("ПАПКА data/ ПУСТА! Добавьте CSV-файлы и перезапустите.")
        exit(1)  # Останавливаем бота
    
    # Перебираем каждый CSV-файл
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)  # Имя файла (например, questions_clean.csv)
        try:
            logger.info(f"Загружаю: {filename}...")
            rag.add_csv(csv_path, batch_size=4000)  # Загружаем в RAG
            logger.info(f"УСПЕШНО: {filename}")
        except Exception as e:
            # Если ошибка (например, битый файл) — ругаемся и останавливаем
            logger.critical(f"ОШИБКА при загрузке {filename}: {e}")
            exit(1)

# === ОБРАБОТКА СООБЩЕНИЙ ===

@dp.message(Command("start"))
async def start(message: types.Message):
    # Пользователь написал /start
    await message.answer(
        "Привет! Я — ИИ-помощник для малого бизнеса.\n"
        "Задайте любой вопрос — я помогу!"
    )

@dp.message()
async def handle_text(message: types.Message):
    # Пользователь написал любой текст (не команду)
    user_query = message.text.strip()  # Убираем пробелы
    if not user_query:
        await message.answer("Напишите вопрос!")
        return

    logger.info(f"Вопрос: {user_query}")  # Записываем в лог

    # ШАГ 1: Ищем в CSV релевантные строки (RAG)
    context = rag.search(user_query, k=5)  # Находим 5 самых похожих строк

    # ШАГ 2: Формируем запрос для ИИ
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
        # ШАГ 3: Отправляем запрос в ИИ (Ollama)
        response = await llm_service.generate(prompt)
        # ШАГ 4: Отправляем ответ пользователю
        await message.answer(response)
        logger.info(f"ОТПРАВЛЕНО пользователю: {response}")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Извините, не смог ответить.")