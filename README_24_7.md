# 🤖 ZarinAI Bot - 24/7 Production Setup

Полная инструкция по настройке ZarinAI бота для непрерывной работы на Google Cloud VM.

## 🚀 Быстрая установка

### 1. Установка сервиса
```bash
# Сделайте скрипт исполняемым
chmod +x manage_service.sh
chmod +x monitor_bot.sh

# Установите бота как системный сервис
sudo ./manage_service.sh install
```

### 2. Установка мониторинга
```bash
# Установите автоматический мониторинг
sudo ./monitor_bot.sh install
```

## ✅ Готово!
Теперь ваш бот:
- ✅ Работает 24/7
- ✅ Автоматически запускается при перезагрузке
- ✅ Автоматически перезапускается при сбоях
- ✅ Отправляет уведомления о проблемах в Telegram

---

## 📋 Управление ботом

### Основные команды
```bash
# Проверить статус
sudo ./manage_service.sh status

# Перезапустить бота
sudo ./manage_service.sh restart

# Остановить бота
sudo ./manage_service.sh stop

# Запустить бота
sudo ./manage_service.sh start

# Обновить бота из GitHub
sudo ./manage_service.sh update
```

### Просмотр логов
```bash
# Логи в реальном времени
sudo ./manage_service.sh logs tail

# Последние 100 строк
sudo ./manage_service.sh logs last 100

# Логи за сегодня
sudo ./manage_service.sh logs today

# Только ошибки
sudo ./manage_service.sh logs errors
```

### Мониторинг
```bash
# Проверить здоровье бота
./monitor_bot.sh monitor

# Посмотреть логи мониторинга
./monitor_bot.sh logs

# Тест уведомлений
./monitor_bot.sh test
```

---

## 🔧 Подробная настройка

### Создание systemd сервиса вручную

Если автоматическая установка не работает, создайте сервис вручную:

```bash
sudo nano /etc/systemd/system/zarinai-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=ZarinAI Steam Bot - Multilingual Steam Deals Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=akezhanseytqasym
Group=akezhanseytqasym
WorkingDirectory=/home/akezhanseytqasym/AueZarina
Environment=PATH=/home/akezhanseytqasym/AueZarina/venv/bin:/usr/bin:/usr/local/bin
Environment=PYTHONPATH=/home/akezhanseytqasym/AueZarina
ExecStart=/home/akezhanseytqasym/AueZarina/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10
TimeoutStopSec=30

# Ограничения ресурсов
MemoryMax=512M
CPUQuota=50%

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=zarinai-bot

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/akezhanseytqasym/AueZarina

[Install]
WantedBy=multi-user.target
```

Активация сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable zarinai-bot
sudo systemctl start zarinai-bot
sudo systemctl status zarinai-bot
```

### Настройка мониторинга вручную

Добавьте в crontab задачу для мониторинга:
```bash
crontab -e
```

Добавьте строку:
```
*/5 * * * * /home/akezhanseytqasym/AueZarina/monitor_bot.sh monitor > /dev/null 2>&1
```

---

## 🔍 Диагностика проблем

### Проверка статуса
```bash
# Статус сервиса
sudo systemctl status zarinai-bot

# Активен ли сервис
sudo systemctl is-active zarinai-bot

# Включен ли автозапуск
sudo systemctl is-enabled zarinai-bot
```

### Просмотр логов
```bash
# Логи systemd
sudo journalctl -u zarinai-bot -f

# Последние 50 строк
sudo journalctl -u zarinai-bot -n 50

# Логи с ошибками
sudo journalctl -u zarinai-bot -p err
```

### Ресурсы системы
```bash
# Использование памяти и CPU
top -p $(pgrep -f "main.py")

# Место на диске
df -h

# Системная информация
./manage_service.sh info
```

### Сетевые проблемы
```bash
# Проверка подключения к Telegram
curl -s "https://api.telegram.org/bot8255737143:AAHMEy6kmHIee4H9__bSp0LEbaBQBlWt_Q0/getMe"

# Проверка портов
sudo netstat -tlpn | grep python
```

---

## 🛠️ Обслуживание

### Обновление бота
```bash
# Автоматическое обновление
sudo ./manage_service.sh update

# Ручное обновление
sudo systemctl stop zarinai-bot
cd /home/akezhanseytqasym/AueZarina
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl start zarinai-bot
```

### Очистка логов
```bash
# Очистка старых логов systemd
sudo journalctl --vacuum-time=7d

# Очистка логов мониторинга
sudo truncate -s 0 /var/log/zarinai-monitor.log
```

### Резервное копирование
```bash
# Создание бэкапа базы данных
cp steam_bot.db steam_bot.db.backup.$(date +%Y%m%d)

# Бэкап конфигурации
tar -czf zarinai-backup-$(date +%Y%m%d).tar.gz .env steam_bot.db subscribers.json
```

---

## 🚨 Аварийное восстановление

### Если бот не запускается
1. Проверьте логи: `sudo journalctl -u zarinai-bot -n 50`
2. Проверьте права доступа: `ls -la /home/akezhanseytqasym/AueZarina/`
3. Проверьте .env файл: `cat .env`
4. Проверьте виртуальное окружение: `ls -la venv/bin/`

### Если бот падает
1. Увеличьте лимиты памяти в сервисе
2. Проверьте ошибки в логах
3. Перезапустите с debug режимом: `LOG_LEVEL=DEBUG`

### Если не работают уведомления
1. Проверьте токен бота: `echo $BOT_TOKEN`
2. Проверьте подключение к Telegram API
3. Проверьте ID администратора в monitor_bot.sh

---

## 📊 Мониторинг производительности

### Метрики системы
```bash
# CPU и память
htop

# Диск
iotop

# Сеть
iftop

# Логи в реальном времени
tail -f /var/log/zarinai-monitor.log
```

### Настройка алертов
Мониторинг автоматически отправляет уведомления в Telegram при:
- Остановке бота
- Высоком использовании ресурсов
- Критических ошибках
- Нехватке места на диске

---

## 🔐 Безопасность

### Настройки файрвола
```bash
# Разрешить только необходимые порты
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow out 443  # HTTPS для Telegram API
sudo ufw allow out 80   # HTTP
```

### Обновления безопасности
```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте статус:** `sudo ./manage_service.sh status`
2. **Посмотрите логи:** `sudo ./manage_service.sh logs tail`
3. **Проверьте мониторинг:** `./monitor_bot.sh logs`
4. **Перезапустите бота:** `sudo ./manage_service.sh restart`

### Полезные файлы
- Сервис: `/etc/systemd/system/zarinai-bot.service`
- Логи systemd: `journalctl -u zarinai-bot`
- Логи мониторинга: `/var/log/zarinai-monitor.log`
- Конфигурация: `/home/akezhanseytqasym/AueZarina/.env`
- База данных: `/home/akezhanseytqasym/AueZarina/steam_bot.db`

---

**🎉 Поздравляем! Ваш ZarinAI бот теперь работает 24/7 с полным мониторингом и автоматическим восстановлением!**
