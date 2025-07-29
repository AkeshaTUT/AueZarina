# 🚀 Инструкция по деплою Steam Bot на Digital Ocean

## Метод 1: Быстрый деплой с Docker (Рекомендуется)

### 1. Создание дроплета на Digital Ocean

1. Зайдите в панель управления Digital Ocean
2. Создайте новый дроплет:
   - **Образ**: Ubuntu 22.04 LTS
   - **Размер**: Basic - $6/месяц (1 vCPU, 1GB RAM)
   - **Регион**: выберите ближайший к вам
   - **SSH ключи**: добавьте свой SSH ключ

### 2. Подключение к серверу

```bash
ssh root@your_server_ip
```

### 3. Подготовка сервера

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Устанавливаем Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создаем пользователя для бота
useradd -m -s /bin/bash steambot
usermod -aG docker steambot
```

### 4. Загрузка кода бота

```bash
# Переходим к пользователю steambot
su - steambot

# Клонируем репозиторий или загружаем файлы
# Если у вас Git репозиторий:
git clone https://your-repo-url.git steam-bot
cd steam-bot

# Или создаем директорию и загружаем файлы вручную:
mkdir steam-bot && cd steam-bot
# Загрузите все файлы бота в эту директорию
```

### 5. Настройка переменных окружения

```bash
# Копируем пример конфигурации
cp env.example .env

# Редактируем файл .env
nano .env
```

Заполните в файле `.env`:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
OPENROUTER_API_KEY=ваш_ключ_от_OpenRouter
STEAM_WEB_API_KEY=ваш_ключ_Steam_API
```

### 6. Запуск бота

```bash
# Делаем скрипт исполняемым
chmod +x deploy.sh

# Запускаем деплой
./deploy.sh
```

### 7. Проверка работы

```bash
# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps

# Проверка healthcheck
curl http://localhost:8000/health
```

## Метод 2: Деплой через systemd (альтернативный)

### 1. Подготовка окружения

```bash
# Устанавливаем Python и зависимости
apt install python3 python3-pip python3-venv -y

# Создаем пользователя
useradd -m -s /bin/bash steambot
su - steambot

# Создаем виртуальное окружение
python3 -m venv steam-bot-env
source steam-bot-env/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Настройка systemd сервиса

```bash
# Возвращаемся к root
exit

# Копируем файл сервиса
cp /home/steambot/steam-bot/steam-bot.service /etc/systemd/system/

# Редактируем файл сервиса
nano /etc/systemd/system/steam-bot.service
```

Отредактируйте переменные окружения в файле сервиса.

### 3. Запуск сервиса

```bash
# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable steam-bot

# Запускаем сервис
systemctl start steam-bot

# Проверяем статус
systemctl status steam-bot

# Просматриваем логи
journalctl -u steam-bot -f
```

## 🔧 Управление ботом

### Docker команды:
```bash
# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление (пересборка)
docker-compose down
docker-compose up -d --build
```

### Systemd команды:
```bash
# Статус
systemctl status steam-bot

# Перезапуск
systemctl restart steam-bot

# Остановка
systemctl stop steam-bot

# Логи
journalctl -u steam-bot -f
```

## 📊 Мониторинг

### Проверка работоспособности:
```bash
# HealthCheck endpoint
curl http://localhost:8000/health

# Проверка использования ресурсов
docker stats steam-discord-bot

# Или для systemd:
htop
```

### Настройка автоматических уведомлений:
Можно настроить мониторинг через:
- Digital Ocean Monitoring
- UptimeRobot
- Grafana + Prometheus

## 🔒 Безопасность

1. **Firewall**:
```bash
ufw enable
ufw allow ssh
ufw allow 80
ufw allow 443
```

2. **Обновления**:
```bash
# Автоматические обновления безопасности
apt install unattended-upgrades -y
dpkg-reconfigure unattended-upgrades
```

3. **Бэкапы**:
```bash
# Создайте скрипт для бэкапа базы данных и конфигов
mkdir -p /home/steambot/backups
# Настройте cron для регулярных бэкапов
```

## 🎯 Оптимизация производительности

1. **Логирование**:
   - Настройте ротацию логов
   - Используйте соответствующий уровень логирования

2. **Ресурсы**:
   - Мониторьте использование RAM и CPU
   - При необходимости увеличьте размер дроплета

3. **База данных**:
   - Регулярно очищайте старые данные
   - Создавайте индексы для часто используемых запросов

## ❓ Устранение проблем

### Бот не запускается:
1. Проверьте токен бота
2. Проверьте логи: `docker-compose logs` или `journalctl -u steam-bot`
3. Убедитесь, что все зависимости установлены

### Высокое потребление ресурсов:
1. Уменьшите частоту проверок в конфиге
2. Ограничьте количество одновременных запросов
3. Оптимизируйте базу данных

### Проблемы с сетью:
1. Проверьте настройки firewall
2. Убедитесь, что порты открыты
3. Проверьте DNS настройки

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи
2. Убедитесь, что все конфигурации корректны
3. Проверьте статус всех сервисов

Удачного деплоя! 🚀
