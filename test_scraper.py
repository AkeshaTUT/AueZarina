"""
Тестовый скрипт для проверки работы Steam парсера
"""
import asyncio
import sys
from steam_scraper import SteamScraper

async def test_steam_scraper():
    """Тестирует функциональность парсера Steam"""
    print("🔍 Тестирование Steam парсера...")
    
    try:
        scraper = SteamScraper()
        
        # Тест 1: Получение игр со скидками от 30%
        print("\n📋 Тест 1: Получение скидок от 30%")
        deals_30 = await scraper.get_discounted_games(min_discount=30, max_results=5)
        
        if deals_30:
            print(f"✅ Найдено {len(deals_30)} игр со скидками от 30%:")
            for i, deal in enumerate(deals_30, 1):
                print(f"{i}. {deal['title']} (-{deal['discount']}%)")
                if deal['original_price'] and deal['discounted_price']:
                    print(f"   💰 {deal['original_price']} → {deal['discounted_price']}")
                print(f"   🔗 {deal['url']}")
                print()
        else:
            print("❌ Не удалось найти скидки от 30%")
        
        # Тест 2: Получение бесплатных игр (100% скидка)
        print("\n📋 Тест 2: Получение бесплатных игр")
        free_games = await scraper.get_free_games()
        
        if free_games:
            print(f"✅ Найдено {len(free_games)} бесплатных игр:")
            for i, game in enumerate(free_games, 1):
                print(f"{i}. {game['title']}")
                print(f"   🔗 {game['url']}")
        else:
            print("ℹ️ Бесплатных игр сейчас нет")
        
        # Тест 3: Получение крупных скидок (70%+)
        print("\n📋 Тест 3: Получение крупных скидок (70%+)")
        big_deals = await scraper.get_discounted_games(min_discount=70, max_results=3)
        
        if big_deals:
            print(f"✅ Найдено {len(big_deals)} игр со скидками 70%+:")
            for i, deal in enumerate(big_deals, 1):
                print(f"{i}. {deal['title']} (-{deal['discount']}%)")
                if deal['platforms']:
                    print(f"   🖥️ Платформы: {', '.join(deal['platforms'])}")
                print()
        else:
            print("ℹ️ Крупных скидок (70%+) сейчас нет")
        
        print("✅ Тестирование завершено успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def main():
    """Главная функция"""
    print("🎮 Steam Discount Bot - Тестирование парсера")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_steam_scraper())
        if success:
            print("\n🎉 Все тесты прошли успешно!")
            print("Теперь можно запускать бота: python run_bot.py")
        else:
            print("\n💥 Тесты завершились с ошибками")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
