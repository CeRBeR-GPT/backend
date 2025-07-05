FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Обновляем и устанавливаем необходимые инструменты сборки, cron и редактор
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev cron nano && \
    pip install --upgrade pip setuptools wheel && \
    rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем файл crontab
RUN echo "* * * * * /usr/local/bin/python /app/cron.py >> /app/cron_output.log 2>&1" > mycron

# Копируем crontab и устанавливаем права
RUN mv mycron /etc/cron.d/mycron && chmod 0644 /etc/cron.d/mycron

# Создаем каталог для логов cron
RUN mkdir -p /var/log/cron

# Запускаем cron и uvicorn (ВНИМАНИЕ: запуск в фоне)
CMD cron && uvicorn main:app --host 0.0.0.0 --port 8000 --reload