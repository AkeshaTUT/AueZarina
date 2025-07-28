#!/usr/bin/env python3
"""
Тест упрощенного парсера бесплатных игр
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_free_games_parser import get_current_free_games, SimpleFreeGamesParser
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_simple_parser():
    """Тест упрощенного парсера"""
    print("🆓 Тестирование упрощенного парсера бесплатных игр...")
    
    try:
        # Тест главной функции
        all_games = await get_current_free_games()
        
        print(f"✅ Найдено {len(all_games)} бесплатных игр")
        print()
        
        # Группировка по платформам
        platforms = {}
        for game in all_games:
            platform = game.get('platform', 'Unknown')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(game)
        
        # Вывод по платформам
        for platform, games in platforms.items():
            print(f"📱 {platform}: {len(games)} игр")
            for game in games[:3]:  # Показываем первые 3
                title = game.get('title', 'Unknown')
                description = game.get('description', 'No description')
                end_date = game.get('end_date', 'Unknown')
                
                print(f"  🎮 {title}")
                print(f"     {description}")
                print(f"     До: {end_date}")
                print()
        
        # Тест Epic Games отдельно
        print("🔍 Тестируем Epic Games API...")
        parser = SimpleFreeGamesParser()
        epic_games = await parser._get_epic_free_games_simple()
        print(f"✅ Epic Games: {len(epic_games)} игр с акциями")
        
        for game in epic_games:
            print(f"  🎁 {game.get('title', 'Unknown')}")
            print(f"     {game.get('description', 'No description')}")
            print()
        
        return len(all_games) > 0
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Запуск теста"""
    print("🚀 Тест упрощенного парсера бесплатных игр")
    print("=" * 60)
    
    success = await test_simple_parser()
    
    print("=" * 60)
    if success:
        print("🎉 Тест пройден! Упрощенный парсер работает корректно.")
        print("📱 Готов к использованию в Telegram боте.")
    else:
        print("❌ Тест не пройден. Проверьте ошибки выше.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
