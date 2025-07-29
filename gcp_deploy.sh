#!/bin/bash

# 🚀 ZarinAI - Google Cloud VM Deploy Script

set -e

echo "🤖 Настройка ZarinAI на Google Cloud VM..."

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11
echo "🐍 Установка Python 3.11..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev

# Установка дополнительных пакетов
echo "📚 Установка системных зависимостей..."
sudo apt install -y git curl wget nano htop screen supervisor nginx

# Создание пользователя для бота
echo "👤 Создание пользователя zarinai..."
sudo useradd -m -s /bin/bash zarinai || echo "Пользователь уже существует"

# Переход в домашнюю директорию
cd /home/zarinai

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
sudo -u zarinai git clone https://github.com/AkeshaTUT/AueZarina.git
cd AueZarina

# Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
sudo -u zarinai python3.11 -m venv venv
sudo -u zarinai ./venv/bin/pip install --upgrade pip

# Установка зависимостей
echo "📦 Установка Python зависимостей..."
sudo -u zarinai ./venv/bin/pip install -r requirements.txt

# Создание конфигурационного файла окружения
echo "⚙️ Создание .env файла..."
sudo -u zarinai cat > .env << 'EOF'
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY_HERE
ENVIRONMENT=production
EOF

echo "📝 ВАЖНО: Отредактируйте файл .env с вашими токенами:"
echo "sudo nano /home/zarinai/AueZarina/.env"

# Создание systemd сервиса
echo "🔧 Создание systemd сервиса..."
sudo tee /etc/systemd/system/zarinai.service > /dev/null << 'EOF'
[Unit]
Description=ZarinAI Telegram Bot
After=network.target

[Service]
Type=simple
User=zarinai
WorkingDirectory=/home/zarinai/AueZarina
Environment=PATH=/home/zarinai/AueZarina/venv/bin
ExecStart=/home/zarinai/AueZarina/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создание конфигурации Nginx (опционально для веб-интерфейса)
echo "🌐 Настройка Nginx..."
sudo tee /etc/nginx/sites-available/zarinai > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/zarinai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Настройка файрвола
echo "🔒 Настройка UFW файрвола..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Перезагрузка и запуск сервисов
echo "🔄 Настройка автозапуска сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable zarinai
sudo systemctl enable nginx

echo ""
echo "✅ Базовая настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте токены: sudo nano /home/zarinai/AueZarina/.env"
echo "2. Запустите бота: sudo systemctl start zarinai"
echo "3. Проверьте статус: sudo systemctl status zarinai"
echo "4. Просмотр логов: sudo journalctl -u zarinai -f"
echo ""
echo "🚀 ZarinAI готов к работе на Google Cloud VM!"
