#!/bin/bash

# 🚀 ZarinAI - Быстрая установка на Google Cloud VM
# Выполните: curl -sL https://raw.githubusercontent.com/AkeshaTUT/AueZarina/main/quick_install.sh | bash

set -e

echo "🤖 Быстрая установка ZarinAI на Google Cloud VM"
echo "================================================"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функция вывода с цветом
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав sudo
if ! sudo -n true 2>/dev/null; then
    print_error "Требуются права sudo для установки"
    exit 1
fi

print_status "Обновление системных пакетов..."
sudo apt update && sudo apt upgrade -y

print_status "Установка Python 3.11 и зависимостей..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev
sudo apt install -y git curl wget nano htop screen supervisor nginx

print_status "Создание пользователя zarinai..."
sudo useradd -m -s /bin/bash zarinai || print_warning "Пользователь уже существует"

print_status "Клонирование репозитория..."
cd /home/zarinai
if [ -d "AueZarina" ]; then
    print_warning "Директория AueZarina уже существует, обновляем..."
    cd AueZarina
    sudo -u zarinai git pull origin main
else
    sudo -u zarinai git clone https://github.com/AkeshaTUT/AueZarina.git
    cd AueZarina
fi

print_status "Создание виртуального окружения..."
sudo -u zarinai python3.11 -m venv venv
sudo -u zarinai ./venv/bin/pip install --upgrade pip

print_status "Установка Python зависимостей..."
sudo -u zarinai ./venv/bin/pip install -r requirements.txt

print_status "Создание конфигурационного файла..."
sudo -u zarinai cp .env.example .env

print_status "Создание systemd сервиса..."
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

print_status "Настройка Nginx..."
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
    
    location /status {
        return 200 "ZarinAI is running\n";
        add_header Content-Type text/plain;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/zarinai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

print_status "Настройка файрвола..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

print_status "Создание скрипта управления..."
sudo cp manage_bot.sh /usr/local/bin/zarinai-manage
sudo chmod +x /usr/local/bin/zarinai-manage

print_status "Активация сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable zarinai
sudo systemctl enable nginx

print_success "Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте токены: sudo nano /home/zarinai/AueZarina/.env"
echo "2. Запустите бота: sudo systemctl start zarinai"
echo "3. Проверьте статус: sudo systemctl status zarinai"
echo "4. Управление ботом: zarinai-manage"
echo ""
print_success "ZarinAI готов к работе! 🎉"
