#!/bin/bash

# 🚀 ZarinAI - Мануальная установка для Google Cloud VM (Debian)
# Пошаговая установка с проверками

echo "🤖 Мануальная установка ZarinAI"
echo "=============================="

# Обновление системы
echo "1. Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
echo "2. Установка системных пакетов..."
sudo apt install -y git curl wget nano python3 python3-pip python3-venv nginx

# Создание пользователя
echo "3. Создание пользователя zarinai..."
sudo useradd -m -s /bin/bash zarinai 2>/dev/null || echo "Пользователь уже существует"

# Переход в домашнюю директорию
echo "4. Клонирование репозитория..."
cd /home/zarinai
sudo -u zarinai git clone https://github.com/AkeshaTUT/AueZarina.git 2>/dev/null || {
    echo "Репозиторий уже существует, обновляем..."
    cd AueZarina
    sudo -u zarinai git pull origin main
}

cd /home/zarinai/AueZarina

# Создание виртуального окружения
echo "5. Создание виртуального окружения..."
sudo -u zarinai python3 -m venv venv
sudo -u zarinai ./venv/bin/pip install --upgrade pip

# Установка зависимостей Python
echo "6. Установка Python зависимостей..."
sudo -u zarinai ./venv/bin/pip install -r requirements.txt

# Создание конфигурации
echo "7. Создание файла конфигурации..."
sudo -u zarinai cp .env.example .env

echo ""
echo "⚙️ Теперь настройте токены:"
echo "sudo nano /home/zarinai/AueZarina/.env"
echo ""
echo "Добавьте ваши токены:"
echo "BOT_TOKEN=ваш_telegram_bot_token"
echo "OPENROUTER_API_KEY=ваш_openrouter_key"
echo ""
read -p "Нажмите Enter после настройки токенов..."

# Создание systemd сервиса
echo "8. Создание systemd сервиса..."
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

[Install]
WantedBy=multi-user.target
EOF

# Настройка Nginx
echo "9. Настройка Nginx..."
sudo tee /etc/nginx/sites-available/zarinai > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /status {
        return 200 "ZarinAI is running\n";
        add_header Content-Type text/plain;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/zarinai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Запуск сервисов
echo "10. Запуск сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable zarinai
sudo systemctl start zarinai

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📊 Команды для управления:"
echo "sudo systemctl status zarinai    # Проверить статус"
echo "sudo systemctl restart zarinai   # Перезапустить"
echo "sudo journalctl -u zarinai -f    # Просмотр логов"
echo ""

# Проверка статуса
sleep 3
echo "🔍 Проверка статуса бота..."
if systemctl is-active --quiet zarinai; then
    echo "✅ ZarinAI успешно запущен!"
    echo "🌐 Веб-интерфейс: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')/"
else
    echo "❌ Ошибка запуска. Проверьте логи: sudo journalctl -u zarinai"
fi
