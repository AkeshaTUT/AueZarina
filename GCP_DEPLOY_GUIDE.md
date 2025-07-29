# 🚀 ZarinAI - Google Cloud VM Deploy Guide

## 📋 Предварительные требования

1. **Google Cloud Account** с активным проектом
2. **VM Instance** (рекомендуется: e2-micro или e2-small)
3. **Открытые порты**: 22 (SSH), 80 (HTTP), 443 (HTTPS)

## 🖥️ Создание VM Instance

### В Google Cloud Console:

1. **Compute Engine** → **VM instances** → **Create Instance**
2. **Настройки VM:**
   ```
   Name: zarinai-bot
   Region: us-central1 (или ближайший к вам)
   Machine type: e2-micro (1 vCPU, 1GB RAM) - БЕСПЛАТНО
   Boot disk: Ubuntu 22.04 LTS (10GB)
   Firewall: Allow HTTP, HTTPS traffic
   ```

3. **Создать SSH ключи** (если нужно)

## 🚀 Автоматический деплой

### Подключитесь к VM и выполните:

```bash
# Скачивание и запуск скрипта деплоя
wget https://raw.githubusercontent.com/AkeshaTUT/AueZarina/main/gcp_deploy.sh
chmod +x gcp_deploy.sh
sudo ./gcp_deploy.sh
```

## ⚙️ Настройка токенов

После выполнения скрипта:

```bash
# Откройте файл конфигурации
sudo nano /home/zarinai/AueZarina/.env

# Добавьте ваши токены:
BOT_TOKEN=1234567890:ВАНШBOTTOKEN
OPENROUTER_API_KEY=sk-or-v1-ВАША_OPENROUTER_KEY
ENVIRONMENT=production
```

## 🔄 Управление ботом

### Запуск бота:
```bash
sudo systemctl start zarinai
```

### Остановка бота:
```bash
sudo systemctl stop zarinai
```

### Перезапуск бота:
```bash
sudo systemctl restart zarinai
```

### Проверка статуса:
```bash
sudo systemctl status zarinai
```

### Просмотр логов:
```bash
# Последние логи
sudo journalctl -u zarinai -n 50

# Логи в реальном времени
sudo journalctl -u zarinai -f
```

## 🔧 Обновление бота

```bash
cd /home/zarinai/AueZarina
sudo -u zarinai git pull origin main
sudo systemctl restart zarinai
```

## 📊 Мониторинг

### Использование ресурсов:
```bash
htop
```

### Дисковое пространство:
```bash
df -h
```

### Логи системы:
```bash
sudo journalctl -f
```

## 🌐 Веб-интерфейс (опционально)

Бот также запускает веб-сервер на порту 8080, доступный через:
```
http://YOUR_VM_EXTERNAL_IP/
```

## 🔒 Безопасность

### UFW Firewall уже настроен:
- SSH (22) - разрешен
- HTTP (80) - разрешен  
- HTTPS (443) - разрешен

### Дополнительные настройки безопасности:

```bash
# Изменить SSH порт (опционально)
sudo nano /etc/ssh/sshd_config
# Найти: #Port 22
# Изменить на: Port 2222
sudo systemctl restart ssh

# Настроить автоматические обновления
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 💰 Стоимость Google Cloud

- **e2-micro**: БЕСПЛАТНО (Always Free Tier)
- **e2-small**: ~$13/месяц
- **e2-medium**: ~$27/месяц

## 🆘 Устранение неполадок

### Бот не запускается:
```bash
# Проверить логи
sudo journalctl -u zarinai -n 100

# Проверить конфигурацию
sudo nano /home/zarinai/AueZarina/.env

# Ручной запуск для отладки
cd /home/zarinai/AueZarina
sudo -u zarinai ./venv/bin/python main.py
```

### Проблемы с зависимостями:
```bash
cd /home/zarinai/AueZarina
sudo -u zarinai ./venv/bin/pip install -r requirements.txt --upgrade
```

### Нет интернета на VM:
```bash
# Проверить DNS
nslookup google.com

# Перезапуск сети
sudo systemctl restart networking
```

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `sudo journalctl -u zarinai -f`
2. Убедитесь, что токены правильно настроены
3. Проверьте статус сервиса: `sudo systemctl status zarinai`

---

🎉 **ZarinAI успешно развернут на Google Cloud VM!**
