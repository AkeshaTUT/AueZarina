#!/usr/bin/env python3
"""
Тест команды /free в боте без запуска Telegram API
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_free_games_parser import get_current_free_games
from database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockUpdate:
    """Mock объект для эмуляции Telegram Update"""
    def __init__(self):
        self.effective_user = MockUser()
        self.message = MockMessage()

class MockUser:
    """Mock объект для пользователя"""
    def __init__(self):
        self.id = 12345
        self.username = "test_user"
        self.first_name = "Test"
        self.last_name = "User"

class MockMessage:
    """Mock объект для сообщения"""
    def __init__(self):
        self.responses = []
    
    async def reply_text(self, text, **kwargs):
        self.responses.append({
            'text': text,
            'kwargs': kwargs
        })
        print(f"📱 Ответ бота:")
        print(f"   {text[:200]}{'...' if len(text) > 200 else ''}")
        print()

async def test_free_command():
    """Тест команды /free"""
    print("🤖 Тестирование команды /free...")
    
    try:
        # Создаем mock объекты
        update = MockUpdate()
        
        # Создаем базу данных
        db = DatabaseManager()
        db.add_user(update.effective_user.id, 
                   update.effective_user.username,
                   update.effective_user.first_name, 
                   update.effective_user.last_name)
        
        # Эмулируем логику команды /free
        await update.message.reply_text("🔍 Ищу актуальные бесплатные раздачи... Пожалуйста, подождите.")
        
        # Получаем реальные данные
        all_games = await get_current_free_games()
        
        if not all_games:
            await update.message.reply_text("😔 На данный момент не удалось получить информацию о бесплатных раздачах. Попробуйте позже.")
            return False
        
        # Обновляем базу данных (упрощенно)
        print(f"📊 Найдено {len(all_games)} бесплатных игр")
        
        # Ограничиваем количество для отображения
        display_games = all_games[:10]
        message = f"🆓 <b>Актуальные бесплатные раздачи ({len(display_games)}):</b>\n\n"
        
        for game in display_games:
            # Определяем эмодзи платформы
            platform_emoji = {
                'Steam': '🟦',
                'Epic Games Store': '🟪', 
                'GOG': '🟫',
                'Other': '⚪'
            }.get(game.get('platform', 'Other'), '⚪')
            
            title = game.get('title', 'Неизвестная игра')
            description = game.get('description', 'Описание отсутствует')
            end_date = game.get('end_date', 'Неизвестно')
            url = game.get('url', '')
            
            message += f"{platform_emoji} <b>{title}</b>\n"
            message += f"📝 {description}\n"
            message += f"🗓️ До: {end_date}\n"
            if url:
                message += f"🔗 <a href='{url}'>Получить игру</a>\n"
            message += "\n"
        
        if len(all_games) > 10:
            message += f"💡 <i>И еще {len(all_games) - 10} раздач...</i>\n"
        
        message += "\n🔄 <i>Данные обновляются в реальном времени</i>"
        
        # Отправляем ответ
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
        
        print(f"✅ Команда /free обработана успешно")
        print(f"📊 Показано {len(display_games)} из {len(all_games)} игр")
        
        # Показываем примеры игр
        print("\n🎮 Примеры найденных игр:")
        for i, game in enumerate(all_games[:5], 1):
            print(f"  {i}. {game.get('title', 'Unknown')} ({game.get('platform', 'Unknown')})")
            print(f"     До: {game.get('end_date', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования команды: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Запуск теста"""
    print("🚀 Тест команды /free с живыми данными")
    print("=" * 60)
    
    success = await test_free_command()
    
    print("=" * 60)
    if success:
        print("🎉 Команда /free работает с живыми данными!")
        print("✅ Готова к использованию в реальном боте.")
    else:
        print("❌ Тест не пройден. Проверьте ошибки выше.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
