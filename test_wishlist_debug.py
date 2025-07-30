#!/usr/bin/env python3
"""
Отладочный тест команды /wishlist
"""

import asyncio
import sys
import os

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from steam_wishlist import get_wishlist_discounts

async def test_wishlist_debug():
    """Тестируем команду wishlist с дебагом"""
    
    print("🧪 ТЕСТ КОМАНДЫ /WISHLIST - ОТЛАДКА")
    print("=" * 50)
    
    # Тестовые профили с публичными wishlist'ами
    test_profiles = [
        "https://steamcommunity.com/id/gaben",  # Профиль основателя Steam
        "https://steamcommunity.com/profiles/76561197960287930",  # Тот же профиль в другом формате
    ]
    
    for i, profile_url in enumerate(test_profiles, 1):
        print(f"\n🔍 Тест {i}: {profile_url}")
        print("-" * 30)
        
        try:
            # Получаем скидки
            discounted_games = await get_wishlist_discounts(profile_url)
            
            print(f"📊 Результат: найдено {len(discounted_games)} игр со скидками")
            
            if discounted_games:
                print(f"\n🎮 Первые 5 игр:")
                for j, game in enumerate(discounted_games[:5], 1):
                    name = game.get('name', 'Unknown')
                    discount = game.get('discount_percent', 0)
                    price = game.get('final_formatted', 'N/A')
                    print(f"  {j}. {name} (-{discount}%) - {price}")
                
                if len(discounted_games) > 5:
                    print(f"  ... и еще {len(discounted_games) - 5} игр")
            else:
                print("❌ Игры со скидками не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Тест с несуществующим профилем
    print(f"\n🔍 Тест 3: Несуществующий профиль")
    print("-" * 30)
    
    try:
        discounted_games = await get_wishlist_discounts("https://steamcommunity.com/id/nonexistentuser12345")
        print(f"📊 Результат: {len(discounted_games)} игр (ожидается 0)")
    except Exception as e:
        print(f"❌ Ошибка (ожидается): {e}")
    
    print(f"\n✅ Тестирование завершено!")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print("1. Если находится мало игр - проверьте публичность wishlist")
    print("2. Если находится 0 игр - проверьте настройки приватности профиля")  
    print("3. Если ошибка API - подождите и попробуйте позже")
    print("4. В боте должно показываться до 15 игр из найденных")

if __name__ == "__main__":
    asyncio.run(test_wishlist_debug())
