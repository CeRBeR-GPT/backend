FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Обновляем pip и устанавливаем необходимые инструменты сборки
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    pip install --upgrade pip setuptools wheel && \
    rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Копируем весь проект
COPY . .

# Команда по умолчанию (для FastAPI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]