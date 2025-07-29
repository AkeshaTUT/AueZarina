#!/usr/bin/env python3
"""
ZarinAI Production Entry Point for Google Cloud VM
Optimized for 24/7 operation with proper error handling
"""

import os
import sys
import logging
import signal
import time
from datetime import datetime

# Настройка логирования для production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/zarinai.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Graceful shutdown handler"""
    logger.info("🛑 Получен сигнал завершения. Остановка ZarinAI...")
    sys.exit(0)

def main():
    """Main entry point for production deployment"""
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Запуск ZarinAI на Google Cloud VM...")
    logger.info(f"📅 Время запуска: {datetime.now()}")
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Проверка переменных окружения
    required_env_vars = ['BOT_TOKEN']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        logger.error("💡 Убедитесь, что файл .env настроен правильно")
        sys.exit(1)
    
    # Попытка импорта и запуска основного бота
    try:
        # Импорт основных модулей
        from steam_bot import SteamDiscountBot
        from keep_alive import keep_alive
        import threading
        
        logger.info("📦 Модули успешно импортированы")
        
        # Запуск веб-сервера в отдельном потоке
        web_thread = threading.Thread(target=keep_alive, daemon=True)
        web_thread.start()
        logger.info("🌐 Веб-сервер запущен в фоновом режиме")
        
        # Создание и запуск бота
        bot = SteamDiscountBot()
        logger.info("🤖 ZarinAI инициализирован")
        
        # Запуск бота
        bot.run()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта модулей: {e}")
        logger.error("💡 Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        logger.error("🔄 Перезапуск через 30 секунд...")
        time.sleep(30)
        
        # Попытка перезапуска
        try:
            main()
        except Exception as restart_error:
            logger.error(f"❌ Ошибка при перезапуске: {restart_error}")
            sys.exit(1)

if __name__ == "__main__":
    main()
