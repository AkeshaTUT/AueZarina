"""
Диагностический скрипт для проверки доступности Steam Wishlist
Поможет определить точную причину, по которой wishlist недоступен
"""
import asyncio
import logging
from steam_wishlist import SteamWishlistParser

# Настройка логирования для детальной диагностики
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def diagnose_wishlist_access(profile_url: str):
    """Диагностика доступности wishlist"""
    
    print(f"🔍 Диагностика доступности Steam Wishlist")
    print(f"Профиль: {profile_url}")
    print("=" * 60)
    
    async with SteamWishlistParser() as parser:
        # Шаг 1: Извлечение Steam ID
        print("\n📋 Шаг 1: Извлечение Steam ID из URL")
        steam_id = parser.extract_steam_id(profile_url)
        if steam_id:
            print(f"✅ Steam ID извлечен: {steam_id}")
        else:
            print(f"❌ Не удалось извлечь Steam ID из URL")
            return
        
        # Шаг 2: Разрешение Steam ID64
        print(f"\n🔄 Шаг 2: Разрешение Steam ID64")
        steam_id64 = await parser.resolve_steam_id(steam_id)
        if steam_id64:
            print(f"✅ Steam ID64: {steam_id64}")
        else:
            print(f"❌ Не удалось получить Steam ID64")
            return
        
        # Шаг 3: Проверка доступности wishlist страницы
        print(f"\n🌐 Шаг 3: Проверка доступности wishlist страницы")
        is_accessible = await parser.check_wishlist_accessibility(steam_id64)
        if is_accessible:
            print(f"✅ Wishlist страница доступна")
        else:
            print(f"⚠️ Wishlist страница недоступна (но попробуем API)")
        
        # Шаг 4: Попытка получить данные wishlist
        print(f"\n📊 Шаг 4: Получение данных wishlist")
        wishlist_data = await parser.get_wishlist_data(steam_id)
        
        if wishlist_data:
            print(f"✅ Успешно получены данные wishlist!")
            print(f"📋 Найдено игр в wishlist: {len(wishlist_data)}")
            
            # Показываем первые 5 игр
            print(f"\n🎮 Первые игры в wishlist:")
            for i, game in enumerate(wishlist_data[:5], 1):
                print(f"  {i}. {game.get('name', 'Неизвестная игра')} (ID: {game.get('app_id', 'N/A')})")
        else:
            print(f"❌ Не удалось получить данные wishlist")
        
        # Шаг 5: Проверка скидок (если есть игры)
        if wishlist_data:
            print(f"\n💰 Шаг 5: Проверка скидок на игры")
            discounted_games = await parser.check_wishlist_discounts(steam_id)
            
            if discounted_games:
                print(f"🎉 Найдено игр со скидками: {len(discounted_games)}")
                for game in discounted_games:
                    name = game.get('name', 'Неизвестная игра')
                    discount = game.get('discount_percent', 0)
                    price = game.get('final_formatted', 'N/A')
                    print(f"  🔥 {name}: -{discount}% → {price}")
            else:
                print(f"😔 Игры со скидками не найдены")
    
    print("\n" + "=" * 60)
    print("✅ Диагностика завершена!")

async def main():
    """Основная функция для диагностики"""
    
    # Здесь введите ваш Steam профиль URL
    # Замените на ваш реальный URL профиля
    profile_url = input("Введите URL вашего Steam профиля: ").strip()
    
    if not profile_url:
        print("❌ URL профиля не указан!")
        return
    
    if 'steamcommunity.com' not in profile_url:
        print("❌ Неверный формат URL. Используйте ссылки вида:")
        print("  https://steamcommunity.com/id/ваш_ник")
        print("  https://steamcommunity.com/profiles/76561198XXXXXXXXX")
        return
    
    try:
        await diagnose_wishlist_access(profile_url)
    except Exception as e:
        print(f"❌ Ошибка во время диагностики: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
