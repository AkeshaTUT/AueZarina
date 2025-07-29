# Конфигурация Telegram бота для Steam скидок
import os

# Токен бота (получите от @BotFather в Telegram)
# В Replit добавьте в Secrets: TELEGRAM_BOT_TOKEN
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Настройки скидок
MIN_DISCOUNT = 30  # Минимальная скидка в процентах
MAX_RESULTS = 100   # Максимальное количество игр для поиска
SHOW_PLATFORMS = True  # Показывать поддерживаемые платформы

# Интервал отправки уведомлений (в часах)
NOTIFICATION_INTERVAL = 6

# Настройки логирования
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "bot.log"

# Файлы для хранения данных
SUBSCRIBERS_FILE = "subscribers.json"
DEALS_CACHE_FILE = "deals_cache.json"

# Настройки Steam API
STEAM_SEARCH_DELAY = 1  # Задержка между запросами к Steam (в секундах)
MAX_SEARCH_PAGES = 8    # Максимальное количество страниц для поиска
STEAM_WEB_API_KEY = os.getenv("STEAM_WEB_API_KEY")  # Steam Web API ключ из Replit Secrets

# Настройки Wishlist
WISHLIST_MAX_GAMES_CHECK = 100  # Максимальное количество игр для проверки скидок
WISHLIST_CHECK_DELAY = 0.15     # Задержка между проверками игр (в секундах)
WISHLIST_ENABLE_FULL_CHECK = True  # Проверять все игры из wishlist (если False - только первые N)

# Настройки ИИ-рекомендаций
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")
AI_RECOMMENDATIONS_ENABLED = True  # Включить ИИ-рекомендации
AI_MAX_RECOMMENDATIONS = 8         # Максимальное количество рекомендаций от ИИ

# Сообщения бота
WELCOME_MESSAGE = """
🎮 Добро пожаловать в ZarinAI! 

Этот бот поможет вам находить лучшие скидки на игры в Steam от 30% до 100%!

Доступные команды:
/subscribe - Подписаться на уведомления о скидках
/unsubscribe - Отписаться от уведомлений
/deals - Получить текущие скидки
/help - Показать это сообщение

Бот автоматически присылает новые скидки каждые 6 часов.
"""

HELP_MESSAGE = """
🔧 Команды бота:

/start - Приветственное сообщение
/subscribe - Подписаться на автоматические уведомления о скидках
/unsubscribe - Отписаться от уведомлений
/deals - Получить список текущих скидок (30-100%)
/feedback - Отправить отзыв, сообщить о баге или предложить идею
/help - Показать эту справку

📊 Бот ищет скидки от 30% до 100% в Steam Store и присылает их подписчикам каждые 6 часов.
"""
