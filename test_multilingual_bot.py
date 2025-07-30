#!/usr/bin/env python3
"""
Тестовый запуск бота с многоязычностью
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def test_multilingual_bot():
    """Тестовый запуск бота"""
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("❌ BOT_TOKEN не найден в .env файле!")
        print("\n💡 Создайте .env файл с содержимым:")
        print("BOT_TOKEN=your_telegram_bot_token_here")
        print("OPENROUTER_API_KEY=your_openrouter_api_key_here")
        return
    
    try:
        # Импортируем и запускаем бот
        from steam_bot import SteamDiscountBot
        from translations import get_text
        
        # Тестируем переводы
        print("🧪 Тестирование переводов:")
        print(f"RU: {get_text('ru', 'welcome_title')}")
        print(f"EN: {get_text('en', 'welcome_title')}")
        print()
        
        # Создаем и запускаем бот
        bot = SteamDiscountBot(bot_token)
        logger.info("🚀 Запуск многоязычного ZarinAI бота...")
        logger.info("🌍 Поддерживаемые языки: русский, английский")
        logger.info("📱 Используйте /start для выбора языка")
        
        bot.run()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("💡 Установите зависимости: pip install -r requirements.txt")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        logger.exception("Детали ошибки:")

if __name__ == "__main__":
    test_multilingual_bot()
