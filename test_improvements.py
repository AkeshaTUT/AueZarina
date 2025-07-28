"""
Быстрая проверка улучшений в Steam Wishlist
"""
import asyncio
import logging
from steam_wishlist import get_wishlist_discounts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_improvements():
    print("🧪 Тестирование улучшений Steam Wishlist...")
    
    # Тестируем с тем же URL, что был в логах
    test_url = "https://steamcommunity.com/id/Bolshiresiski/"
    
    try:
        discounted_games = await get_wishlist_discounts(test_url)
        
        print(f"✅ Тест завершен успешно")
        print(f"📊 Найдено игр со скидками: {len(discounted_games)}")
        
        if discounted_games:
            for game in discounted_games[:3]:
                name = game.get('name', 'Unknown')
                discount = game.get('discount_percent', 0)
                print(f"  🎮 {name}: -{discount}%")
        else:
            print("ℹ️ Скидки не найдены (это нормально, если wishlist приватный или пустой)")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improvements())
