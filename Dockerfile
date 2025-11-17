FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Устанавливаем необходимые зависимости для сборки chromadb и других библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    cargo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements.txt, чтобы ускорить сборку
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Настройки Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запуск бота
CMD ["python", "src/main.py"]
