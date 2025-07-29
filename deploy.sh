#!/bin/bash

# Скрипт для деплоя Steam Bot на Digital Ocean

echo "🚀 Начинаем деплой Steam Bot на Digital Ocean..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "Скопируйте env.example в .env и заполните переменные:"
    echo "cp env.example .env"
    echo "nano .env"
    exit 1
fi

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Устанавливаем Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker установлен. Перезайдите в систему или выполните: newgrp docker"
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Устанавливаем Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p data logs

# Останавливаем предыдущий контейнер (если есть)
echo "⏹️ Останавливаем предыдущий контейнер..."
docker-compose down

# Строим и запускаем контейнер
echo "🔨 Строим и запускаем контейнер..."
docker-compose up -d --build

# Проверяем статус
echo "📊 Проверяем статус контейнера..."
docker-compose ps

echo "✅ Деплой завершен!"
echo ""
echo "🔍 Полезные команды:"
echo "docker-compose logs -f          # Просмотр логов"
echo "docker-compose restart          # Перезапуск бота"
echo "docker-compose down             # Остановка бота"
echo "docker-compose up -d --build    # Пересборка и запуск"
echo ""
echo "📝 Логи сохраняются в директории ./logs/"
