"""
Скрипт для запуска Steam Discount Telegram Bot
"""
import os
import sys
import logging
from steam_bot import SteamDiscountBot
from config import BOT_TOKEN, LOG_LEVEL, LOG_FILE
from keep_alive import keep_alive

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Основная функция"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Запускаем keep-alive сервер для Replit
    keep_alive()
    
    # Получаем токен из переменной окружения или конфига
    token = os.getenv("TELEGRAM_BOT_TOKEN") or BOT_TOKEN
    
    if not token:
        logger.error("❌ Ошибка: Не установлен токен бота!")
        logger.error("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        logger.error("Или укажите токен в файле config.py")
        print("\n🔧 Как получить токен бота:")
        print("1. Напишите @BotFather в Telegram")
        print("2. Отправьте команду /newbot")
        print("3. Следуйте инструкциям для создания бота")
        print("4. Скопируйте токен и установите переменную окружения:")
        print("   export TELEGRAM_BOT_TOKEN=your_token_here")
        return 1
    
    try:
        logger.info("🚀 Запуск ZarinAI на Replit...")
        bot = SteamDiscountBot(token)
        bot.run()
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
        return 0
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
