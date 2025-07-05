FROM python:3.11

WORKDIR /app

# Установка зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron nano && \
    pip install --upgrade pip setuptools wheel && \
    rm -rf /var/lib/apt/lists/*

# Установка зависимостей проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект и .env
COPY . .

# Создаём и настраиваем cron-задачу
RUN echo "0 21 * * * root cd /app && /usr/local/bin/python /app/cron.py >> /app/cron_tasks.log 2>&1" > /etc/cron.d/mycron && \
    chmod 0644 /etc/cron.d/mycron

# Запускаем cron в foreground и uvicorn
CMD cron -f & uvicorn main:app --host 0.0.0.0 --port 8000 --reload
