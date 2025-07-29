# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Создаем пользователя для запуска приложения (безопасность)
RUN useradd -m -u 1000 steambot && chown -R steambot:steambot /app
USER steambot

# Открываем порт для healthcheck (если понадобится)
EXPOSE 8000

# Команда для запуска бота
CMD ["python", "run_bot.py"]
