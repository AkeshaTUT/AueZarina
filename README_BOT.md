# Steam Discount Telegram Bot

🎮 Telegram бот для получения уведомлений о скидках на игры в Steam от 30% до 100%.

## ✨ Возможности

- � Автоматический поиск скидок от 30% до 100%
- 📱 Уведомления в Telegram каждые 6 часов
- 🎯 Умная фильтрация (только игры, без DLC)
- 💰 Отображение оригинальной и новой цены
- 🖥️ Информация о поддерживаемых платформах
- 📊 Сортировка по размеру скидки

## �🚀 Быстрый старт

### 1. Создание бота в Telegram

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Придумайте имя для бота (например: "Steam Discounts Bot")
4. Придумайте username для бота (должен заканчиваться на "bot", например: "steam_discounts_bot")
5. Скопируйте токен, который выдаст BotFather

### 2. Установка зависимостей

```bash
py -m pip install -r requirements.txt
```

### 3. Настройка токена

**Способ 1 (простой):** Запустите `set_token.bat` и введите токен

**Способ 2 (командная строка):**
```cmd
set TELEGRAM_BOT_TOKEN=ваш_токен_здесь
```

### 4. Запуск бота

**Способ 1:** Запустите `start_bot.bat`

**Способ 2 (командная строка):**
```bash
py run_bot.py
```

## 📋 Команды бота

- `/start` - Приветственное сообщение
- `/subscribe` - Подписаться на уведомления о скидках
- `/unsubscribe` - Отписаться от уведомлений
- `/deals` - Получить текущие скидки (30-100%)
- `/help` - Справка

## 🛠️ Структура проекта

```
Steam_Bot/NeedFree/
├── steam_bot.py          # Основной код бота
├── steam_scraper.py      # Модуль для парсинга Steam
├── config.py             # Настройки бота
├── run_bot.py           # Скрипт запуска
├── test_scraper.py      # Тест парсера
├── start_bot.bat        # Запуск бота (Windows)
├── set_token.bat        # Установка токена (Windows)
├── requirements.txt      # Зависимости Python
├── NeedFree.py          # Оригинальный скрипт (100% скидки)
└── README_BOT.md        # Этот файл
```

## ⚙️ Настройки

Все основные настройки находятся в файле `config.py`:

- `MIN_DISCOUNT` - Минимальная скидка (по умолчанию 30%)
- `MAX_RESULTS` - Максимальное количество игр в сообщении
- `NOTIFICATION_INTERVAL` - Интервал отправки уведомлений (в часах)

## 🎮 Как работает бот

1. **Автоматические уведомления**: Каждые 6 часов бот ищет новые скидки и отправляет их всем подписчикам
2. **Поиск скидок**: Бот ищет игры со скидками от 30% до 100% в Steam Store
3. **Умная фильтрация**: Исключает DLC, сортирует по размеру скидки
4. **Разбивка сообщений**: Если скидок много, бот разбивает их на несколько сообщений

## � Тестирование

Перед запуском бота можно протестировать парсер Steam:

```bash
py test_scraper.py
```

Это покажет, правильно ли работает поиск скидок.

## 📱 Пример использования

После запуска бота:

1. Найдите вашего бота в Telegram по username
2. Нажмите `/start`
3. Нажмите `/subscribe` для подписки на уведомления
4. Используйте `/deals` для получения актуальных скидок

## 🔍 Отладка

Если бот не работает:

1. **Проверьте токен**: Убедитесь, что токен правильно установлен
2. **Проверьте зависимости**: `py -m pip install -r requirements.txt`
3. **Проверьте логи**: Логи сохраняются в файл `bot.log`
4. **Протестируйте парсер**: Запустите `py test_scraper.py`

## 🌐 Фоновый запуск

### Windows (как служба)

Создайте задачу в Планировщике заданий Windows:
1. Откройте "Планировщик заданий"
2. Создайте простую задачу
3. Укажите путь к `start_bot.bat`
4. Настройте автозапуск при старте системы

### Linux/Mac

```bash
nohup python3 run_bot.py &
```

## 📊 Статистика

Бот автоматически:
- Удаляет неактивных подписчиков
- Ведет логи операций
- Кэширует результаты поиска
- Соблюдает лимиты Steam API

## 🤝 Вклад в проект

Хотите улучшить бота? Отлично!

1. Форкните репозиторий
2. Создайте новую ветку для функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Основано на

Этот проект создан на основе [NeedFree](https://github.com/InJeCTrL/NeedFree) и расширен функциональностью Telegram бота для поиска скидок от 30% до 100%.

## 🎯 Основные отличия от оригинала

- ✅ Поиск скидок от 30% до 100% (не только бесплатные игры)
- ✅ Telegram бот с командами и подписками
- ✅ Автоматические уведомления каждые 6 часов
- ✅ Улучшенный парсер с обработкой ошибок
- ✅ Простая установка и настройка
- ✅ Подробная документация и тесты
