# src/cache.py
import asyncio
import sqlite3
import json
import logging
from cachetools import TTLCache
from functools import wraps

logger = logging.getLogger(__name__)

# L1: в памяти, быстро
memory_cache = TTLCache(maxsize=128, ttl=300)  # 5 минут

# L2: на диске, персистентно
DB_PATH = "rag_cache.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.execute("DELETE FROM cache WHERE timestamp < datetime('now', '-24 hours')")
conn.commit()

def _get_from_db(key):
    cursor = conn.execute("SELECT value FROM cache WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None

def _save_to_db(key, value):
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()

def cached_search(func):
    @wraps(func)
    async def wrapper(self, query, k=5):
        key = f"rag:{query}:{k}"

        # 1. L1: память
        if key in memory_cache:
            logger.info(f"[L1 HIT] {query}")
            return memory_cache[key]

        # 2. L2: SQLite
        db_value = _get_from_db(key)
        if db_value:
            logger.info(f"[L2 HIT] {query}")
            memory_cache[key] = db_value  # подогрев L1
            return db_value

        # 3. Промах: выполняем поиск
        logger.info(f"[MISS] {query} → RAG")
        result = await func(self, query, k)

        # Сохраняем в оба уровня
        memory_cache[key] = result
        _save_to_db(key, result)
        logger.info(f"[SAVED] {query} → L1 + L2")

        return result
    return wrapper