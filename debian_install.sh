#!/bin/bash

# 🚀 ZarinAI - Установка на Debian/Google Cloud VM
# Оптимизированная версия для Debian систем

set -e

echo "🤖 Установка ZarinAI на Debian (Google Cloud VM)"
echo "==============================================="

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка прав sudo
if ! sudo -n true 2>/dev/null; then
    print_error "Требуются права sudo для установки"
    exit 1
fi

print_status "Обновление системы..."
sudo apt update && sudo apt upgrade -y

print_status "Установка системных зависимостей..."
sudo apt install -y git curl wget nano htop screen nginx build-essential

# Установка Python и зависимостей для компиляции
print_status "Установка Python и зависимостей..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y libffi-dev libssl-dev zlib1g-dev libbz2-dev
sudo apt install -y libreadline-dev libsqlite3-dev libncurses5-dev
sudo apt install -y libncursesw5-dev xz-utils tk-dev libxml2-dev
sudo apt install -y libxmlsec1-dev liblzma-dev

# Проверка версии Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_status "Установленная версия Python: $PYTHON_VERSION"

# Если Python меньше 3.9, устанавливаем более новую версию
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    print_success "Python версия подходит для ZarinAI"
else
    print_warning "Требуется Python 3.9+. Установка pyenv для управления версиями..."
    
    # Установка pyenv
    curl https://pyenv.run | bash
    
    # Добавление pyenv в PATH
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    
    # Перезагрузка bashrc
    source ~/.bashrc
    
    # Установка Python 3.11
    ~/.pyenv/bin/pyenv install 3.11.0
    ~/.pyenv/bin/pyenv global 3.11.0
fi

print_status "Создание пользователя zarinai..."
sudo useradd -m -s /bin/bash zarinai || print_warning "Пользователь уже существует"

print_status "Клонирование репозитория..."
cd /home/zarinai
if [ -d "AueZarina" ]; then
    print_warning "Обновление существующего репозитория..."
    cd AueZarina
    sudo -u zarinai git pull origin main
else
    sudo -u zarinai git clone https://github.com/AkeshaTUT/AueZarina.git
    cd AueZarina
fi

print_status "Создание виртуального окружения..."
# Используем доступную версию Python
PYTHON_CMD=$(which python3)
sudo -u zarinai $PYTHON_CMD -m venv venv
sudo -u zarinai ./venv/bin/pip install --upgrade pip

print_status "Установка Python зависимостей..."
sudo -u zarinai ./venv/bin/pip install -r requirements.txt

print_status "Создание конфигурации..."
sudo -u zarinai cp .env.example .env

print_status "Создание systemd сервиса..."
sudo tee /etc/systemd/system/zarinai.service > /dev/null << EOF
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
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
    
    location /status {
        return 200 "ZarinAI is running on Debian\n";
        add_header Content-Type text/plain;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/zarinai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

print_status "Настройка файрвола (если установлен ufw)..."
if command -v ufw &> /dev/null; then
    sudo ufw allow ssh
    sudo ufw allow 80
    sudo ufw allow 443
fi

print_status "Создание скрипта управления..."
sudo cp manage_bot.sh /usr/local/bin/zarinai-manage
sudo chmod +x /usr/local/bin/zarinai-manage

print_status "Активация сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable zarinai
sudo systemctl enable nginx

print_success "Установка ZarinAI завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте токены:"
echo "   sudo nano /home/zarinai/AueZarina/.env"
echo ""
echo "2. Запустите бота:"
echo "   sudo systemctl start zarinai"
echo ""
echo "3. Проверьте статус:"
echo "   sudo systemctl status zarinai"
echo ""
echo "4. Просмотр логов:"
echo "   sudo journalctl -u zarinai -f"
echo ""
echo "5. Управление ботом:"
echo "   zarinai-manage"
echo ""
echo "🌐 Веб-интерфейс будет доступен по адресу: http://$(curl -s ifconfig.me)/"
echo ""
print_success "ZarinAI готов к работе! 🎉"
