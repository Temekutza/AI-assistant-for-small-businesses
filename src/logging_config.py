
import logging
import os
from pathlib import Path

def setup_logging():
    log_dir = Path(__file__).parent.parent
    log_file = log_dir / "bot.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Понижаем уровень для громких библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    logging.info("Логирование инициализировано")