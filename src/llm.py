# src/llm.py
import time
from ollama import AsyncClient
from dotenv import load_dotenv
import os
from .logging_config import setup_logging

load_dotenv("config.env")
setup_logging()

logger = __import__("logging").getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "qwen3:30b")
        logger.info(f"LLM модель: {self.model}")

    async def generate(self, prompt):
        start = time.time()
        logger.debug(f"Генерация для промпта длиной {len(prompt)} символов")
        try:
            client = AsyncClient()
            response = await client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'num_ctx': 4096
                }
            )
            elapsed = time.time() - start
            answer = response['response'].strip()

            # ДОБАВЛЕНО: ЛОГИРУЕМ ПОЛНЫЙ ОТВЕТ
            logger.info(f"LLM ОТВЕТ: {answer}")
            logger.info(f"LLM ответил за {elapsed:.2f}с")

            return answer
        except Exception as e:
            logger.error(f"LLM ошибка: {e}", exc_info=True)
            return "Извините, произошла ошибка при обработке запроса."