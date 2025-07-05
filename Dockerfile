FROM python:3.11

WORKDIR /app

# Установка зависимостей, включая cron и инструменты
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    pip install --upgrade pip setuptools wheel && \
    rm -rf /var/lib/apt/lists/*

# Установка зависимостей проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Установка cron-задачи
RUN echo "* * * * * root /usr/local/bin/python /app/cron.py >> /app/cron_output.log 2>&1" > /etc/cron.d/mycron && \
    chmod 0644 /etc/cron.d/mycron

# Запуск cron и uvicorn
CMD cron -f & uvicorn main:app --host 0.0.0.0 --port 8000 --reload
