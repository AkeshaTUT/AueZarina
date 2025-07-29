#!/usr/bin/env python3
"""
ZarinAI - Главный файл для запуска на Google Cloud VM
Поддерживает как локальную разработку, так и production на сервере
"""

import os
import sys
import logging
from datetime import datetime

# Настройка логирования
log_handlers = [logging.StreamHandler()]

# В production добавляем файловое логирование
if os.getenv('ENVIRONMENT') == 'production':
    log_handlers.append(logging.FileHandler('/var/log/zarinai.log'))
else:
    log_handlers.append(logging.FileHandler('bot.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

def main():
    """Главная функция запуска ZarinAI"""
    
    logger.info("🚀 Запуск ZarinAI...")
    logger.info(f"📅 Время запуска: {datetime.now()}")
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Проверка переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        if os.path.exists('.env'):
            # Загрузка из .env файла
            from dotenv import load_dotenv
            load_dotenv()
            bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ BOT_TOKEN не найден!")
        logger.error("💡 Настройте переменные окружения или создайте .env файл")
        sys.exit(1)
    
    try:
        # Определение среды выполнения
        environment = os.getenv('ENVIRONMENT', 'development')
        logger.info(f"🌍 Среда: {environment}")
        
        # Импорт модулей
        from steam_bot import SteamDiscountBot
        
        # Запуск веб-сервера keep-alive если нужно
        if environment == 'production' or os.getenv('REPLIT_DB_URL'):
            from keep_alive import keep_alive
            import threading
            
            web_thread = threading.Thread(target=keep_alive, daemon=True)
            web_thread.start()
            logger.info("🌐 Веб-сервер запущен на порту 8080")
        
        # Создание и запуск бота
        bot = SteamDiscountBot(bot_token)
        logger.info("🤖 ZarinAI готов к работе!")
        bot.run()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("💡 Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.exception("Детали ошибки:")
        sys.exit(1)

if __name__ == "__main__":
    main()
