#!/usr/bin/env python3
"""
Тест парсера бесплатных игр
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from free_games_parser import FreeGamesParser, FreeGamesScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_free_games_parser():
    """Тест парсера бесплатных игр"""
    print("🆓 Тестирование парсера бесплатных игр...")
    
    try:
        parser = FreeGamesParser()
        scraper = FreeGamesScraper()
        
        print("🔍 Получаем данные с Epic Games Store...")
        epic_games = await parser._get_epic_free_games()
        print(f"✅ Epic Games: найдено {len(epic_games)} игр")
        
        for game in epic_games[:3]:
            print(f"  - {game.get('title', 'Unknown')}")
            print(f"    Платформа: {game.get('platform', 'Unknown')}")
            print(f"    До: {game.get('end_date', 'Unknown')}")
            print()
        
        print("🔍 Получаем данные со Steam...")
        steam_games = await parser._get_steam_free_games()
        print(f"✅ Steam: найдено {len(steam_games)} игр")
        
        for game in steam_games[:3]:
            print(f"  - {game.get('title', 'Unknown')}")
            print(f"    Статус: {game.get('description', 'Unknown')}")
            print()
        
        print("🔍 Получаем данные с GOG...")
        gog_games = await parser._get_gog_free_games()
        print(f"✅ GOG: найдено {len(gog_games)} игр")
        
        for game in gog_games[:3]:
            print(f"  - {game.get('title', 'Unknown')}")
            print()
        
        print("🔍 Получаем дополнительную информацию...")
        additional_games = await scraper.get_freebies_info()
        print(f"✅ Дополнительно: {len(additional_games)} игр")
        
        # Общая статистика
        total_games = len(epic_games) + len(steam_games) + len(gog_games) + len(additional_games)
        print(f"\n📊 Общая статистика:")
        print(f"Epic Games Store: {len(epic_games)}")
        print(f"Steam: {len(steam_games)}")
        print(f"GOG: {len(gog_games)}")
        print(f"Дополнительно: {len(additional_games)}")
        print(f"Всего найдено: {total_games} бесплатных игр")
        
        # Тест полного метода
        print("\n🔍 Тестируем полный метод get_all_free_games...")
        all_games = await parser.get_all_free_games()
        print(f"✅ Всего получено: {len(all_games)} игр")
        
        return len(all_games) > 0
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

async def main():
    """Запуск теста"""
    print("🚀 Тест парсера бесплатных игр")
    print("=" * 50)
    
    success = await test_free_games_parser()
    
    print("=" * 50)
    if success:
        print("🎉 Тест пройден! Парсер бесплатных игр работает.")
    else:
        print("❌ Тест не пройден. Проверьте ошибки выше.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
