import logging
import time
from ollama import AsyncClient
import asyncio

logger = logging.getLogger(__name__)

async def llm_start():
    prompt = f"""     """

    start = time.time()
    try:
        client = AsyncClient()
        response = await client.chat(
            model='mistral',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.7}
        )
    except Exception as e:
        logger.exception("Ошибка LLM")
        return "Не удалось сработать. Попробуйте позже."
