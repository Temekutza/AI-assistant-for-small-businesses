# src/logging_config.py
# Настройка логов: куда писать, что писать, как форматировать.

import logging
import os
from pathlib import Path

def setup_logging():
    # Папка с проектом
    log_dir = Path(__file__).parent.parent
    log_file = log_dir / "bot.log"  # Файл логов

    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,  # Уровень: INFO и выше
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',  # Формат строки
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),  # В файл
            logging.StreamHandler()  # В консоль
        ]
    )

    # Снижаем "шум" от библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    logging.info("Логирование инициализировано")