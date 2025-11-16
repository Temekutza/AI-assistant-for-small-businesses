from aiogram import Bot, Dispatcher, types  # Основные классы Telegram-бота
from aiogram.filters import Command     # Фильтр для команд (/start, /help и т.д.)
import os                               # Работа с путями и окружением
from dotenv import load_dotenv          # Загрузка переменных из .env-файла
import glob                             # Поиск CSV-файлов по шаблону

# Наши модули
from src.rag import RAGSystem              # RAG-система: поиск по CSV
from src.llm import LLMService             # LLM-обёртка: генерация ответов
from src.logging_config import setup_logging  # Настройка логов (консоль + bot.log)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # Клавиатура

# === ЗАГРУЗКА КОНФИГУРАЦИИ =====================================================
# Читаем config.env: токен бота, модели, пути и т.д.
load_dotenv("config.env")
setup_logging()  # Инициализируем логирование
logger = __import__("logging").getLogger(__name__)  # Логгер для этого модуля

# === ИНИЦИАЛИЗАЦИЯ БОТА =========================================================
# Создаём экземпляры бота и диспетчера
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))  # Токен из config.env
dp = Dispatcher()                                 # Управляет маршрутизацией сообщений
rag = RAGSystem()                                 # RAG: векторная БД + поиск
llm_service = LLMService()                        # LLM: генерация ответов

# === АВТОЗАГРУЗКА CSV ИЗ ПАПКИ data/ ===========================================
# Путь к папке с данными (относительно текущего файла)
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
csv_pattern = os.path.join(data_dir, "*.csv")     # Шаблон: все .csv файлы
csv_files = glob.glob(csv_pattern)                # Находим все CSV

# Проверяем, есть ли уже данные в векторной БД
if rag.db and rag.db._collection.count() > 0:
    # База не пуста — пропускаем загрузку (экономим время при перезапуске)
    logger.info(f"RAG содержит {rag.db._collection.count()} документов. Пропускаем загрузку.")
else:
    # База пуста — загружаем все CSV
    logger.info(f"RAG пуст. Загружаю {len(csv_files)} CSV-файлов из data/...")
    if not csv_files:
        # Критическая ошибка: нет данных для работы
        logger.critical("Папка data/ пуста! Добавьте CSV-файлы и перезапустите.")
        exit(1)  # Останавливаем бота

    # Перебираем каждый CSV-файл
    for csv_path in csv_files:
        fn = os.path.basename(csv_path)  # Имя файла для логов
        try:
            logger.info(f"Загружаю файл: {fn}")
            # Добавляем CSV в векторную БД (батчами по 4000 строк)
            rag.add_csv(csv_path, batch_size=4000)
            logger.info(f"УСПЕШНО загружено: {fn}")
        except Exception as e:
            # Любая ошибка при загрузке — критическая
            logger.critical(f"ОШИБКА при загрузке {fn}: {e}")
            exit(1)

# === КЛАВИАТУРА С КОМАНДАМИ =====================================================
# Одна кнопка в строке — удобно для мобильных устройств
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")],
        [KeyboardButton(text="/help")],
        [KeyboardButton(text="/info")]
    ],
    resize_keyboard=True  # Автоматически подгоняем размер
)

# === ОБРАБОТЧИКИ КОМАНД =========================================================
@dp.message(Command("start"))
async def start(message: types.Message):
    """
    Команда /start — приветственное сообщение и запуск бота.
    """
    await message.answer(
        "Привет! Я — ИИ-помощник для малого бизнеса.\n"
        "Задайте любой вопрос — я помогу!",
        reply_markup=keyboard
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    """
    Команда /help — список доступных команд.
    """
    await message.answer(
        "Доступные команды:\n"
        "/start — Начать работу\n"
        "/help  — Показать помощь\n"
        "/info  — Информация о боте",
        reply_markup=keyboard
    )

@dp.message(Command("info"))
async def info_cmd(message: types.Message):
    """
    Команда /info — техническая информация о боте.
    """
    await message.answer(
        "Я — ИИ-помощник на базе qwen3:30b + RAG.\n"
        "Анализирую CSV-файлы, отвечаю на вопросы бизнеса.",
        reply_markup=keyboard
    )

# === ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ ==============================================
@dp.message()
async def handle_text(message: types.Message):
    """
    Обрабатывает любой текст (не команду).
    1. Показывает "печатает..."
    2. Ищет релевантный контекст в RAG (асинхронно, с кэшем)
    3. Формирует промпт и отправляет в LLM
    4. Возвращает ответ пользователю
    """
    query = message.text.strip()  # Убираем лишние пробелы
    if not query:
        await message.answer("Напишите вопрос!", reply_markup=keyboard)
        return

    # Уведомляем пользователя, что идёт обработка
    typing_msg = await message.answer("Ищу ответ...")
    await bot.send_chat_action(message.chat.id, "typing")

    # Логируем входящий запрос
    logger.info(f"Вопрос от пользователя: {query}")

    # === ШАГ 1: Поиск контекста в RAG (асинхронный + кэшированный) ===
    context = await rag.search(query, k=5)  # 5 самых релевантных фрагментов

    # === ШАГ 2: Формируем промпт для LLM ===
    prompt = f"""
Ты — ИИ-помощник для малого бизнеса.
Отвечай по делу, на русском языке.
Анализируй CSV-данные. Даты в формате ГГГГ-ММ-ДД.

Контекст:
{context}

Вопрос: {query}

Ответ:
"""

    try:
        # === ШАГ 3: Генерация ответа через Ollama ===
        response = await llm_service.generate(prompt)

        # Удаляем сообщение "Ищу ответ..." и отправляем результат
        await typing_msg.delete()
        await message.answer(response, reply_markup=keyboard)
        logger.info(f"ОТПРАВЛЕНО пользователю: {response}")

    except Exception as e:
        # Обработка ошибок (Ollama недоступен, таймаут и т.д.)
        logger.error(f"Ошибка при генерации ответа: {e}")
        await typing_msg.delete()
        await message.answer("Извините, произошла ошибка. Попробуйте позже.", reply_markup=keyboard)