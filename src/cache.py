import functools
from cachetools import TTLCache
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройка кэша: максимальный размер 120 записей, время жизни 200 секунд
cache = TTLCache(maxsize=120, ttl=200)

def cached_search(func):
    @functools.wraps(func)
    async def wrapper(self, query, k=5):
        # Проверяем, есть ли результат в кэше
        if query in cache:
            logger.info(f"Результат для запроса '{query}' найден в кэше.")
            return cache[query]  # Возвращаем кэшированный результат

        # Если нет, выполняем поиск
        logger.info(f"Запрос '{query}' не найден в кэше, выполняем поиск.")
        result = await func(self, query, k)
        
        # Сохраняем результат в кэш
        cache[query] = result
        logger.info(f"Результат для запроса '{query}' сохранен в кэше.")
        
        return result
    return wrapper
