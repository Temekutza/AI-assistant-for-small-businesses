# src/api.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from src.rag import RAGSystem
from src.llm import LLMService
from src.logging_config import setup_logging
from dotenv import load_dotenv

load_dotenv("config.env")
setup_logging()
logger = __import__("logging").getLogger(__name__)

app = FastAPI(title="Alfa-Pomoshnik API")

# ---------- static ----------
# Папка: src/frontend (рядом с api.py)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "frontend", "static")

# Монтируем статику на /static (чтобы не конфликтовать с API)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Главная страница — index.html
@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# Переадресация без .html
@app.get("/{page}")
async def serve_page(page: str):
    mapping = {
        "features": "features.html",
        "examples": "examples.html",
        "assistant": "assistant.html",
    }
    filename = mapping.get(page)
    if filename:
        return FileResponse(os.path.join(STATIC_DIR, filename))
    raise HTTPException(status_code=404, detail="Page not found")

# ---------- API ----------
rag = RAGSystem()
llm = LLMService()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        query = request.message
        logger.info(f"API запрос: {query}")
        context = await rag.search(query, k=5)
        prompt = f"""
        Ты — бизнес‑помощник Альфа‑Банка. Отвечай кратко и по делу.
        Контекст из базы: {context}
        Вопрос пользователя: {query}
        """
        response = await llm.generate(prompt)
        return {"response": response}
    except Exception as e:
        logger.error(f"API ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки запроса")

@app.get("/health")
async def health():
    return {"status": "ok", "db_count": rag.db._collection.count() if rag.db else 0}