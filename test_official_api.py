#!/usr/bin/env python3
"""
Тест нового функционала с официальным Steam API
"""
import asyncio
import logging
from steam_wishlist import SteamWishlistParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_official_api():
    """Тестирует новый функционал с официальным Steam API"""
    
    print("🧪 Testing Official Steam API Integration")
    print("=" * 50)
    
    # Тестовые Steam профили (публичные)
    test_profiles = [
        "https://steamcommunity.com/id/gabelogannewell/",  # Gabe Newell
        "https://steamcommunity.com/profiles/76561197960266962/"  # Steam ID
    ]
    
    for profile_url in test_profiles:
        print(f"\n🔍 Testing profile: {profile_url}")
        print("-" * 40)
        
        try:
            async with SteamWishlistParser() as parser:
                # Извлекаем Steam ID
                steam_id = parser.extract_steam_id(profile_url)
                print(f"📋 Extracted Steam ID: {steam_id}")
                
                if not steam_id:
                    print("❌ Could not extract Steam ID")
                    continue
                
                # Резолвим в Steam ID64
                steam_id64 = await parser.resolve_steam_id(steam_id)
                print(f"🔢 Resolved Steam ID64: {steam_id64}")
                
                if not steam_id64:
                    print("❌ Could not resolve Steam ID64")
                    continue
                
                # Пробуем официальный API для wishlist
                print(f"\n🌐 Testing official API for wishlist...")
                api_wishlist = await parser.get_wishlist_via_api(steam_id64)
                if api_wishlist:
                    print(f"✅ Official API returned {len(api_wishlist)} games")
                    for i, game in enumerate(api_wishlist[:3]):  # Показываем первые 3
                        print(f"  {i+1}. {game.get('name', 'Unknown')} (ID: {game.get('app_id', 'N/A')})")
                else:
                    print(f"⚠️ Official API returned no games or failed")
                
                # Пробуем официальный API для скидок
                print(f"\n💰 Testing official API for discounts...")
                api_discounts = await parser.get_wishlist_discounts_via_api(steam_id64)
                if api_discounts:
                    print(f"✅ Official discounts API returned {len(api_discounts)} games on sale")
                    for i, game in enumerate(api_discounts[:3]):  # Показываем первые 3
                        discount = game.get('discount_percent', 0)
                        price = game.get('final_formatted', 'N/A')
                        print(f"  {i+1}. {game.get('name', 'Unknown')} - {discount}% off, {price}")
                else:
                    print(f"⚠️ Official discounts API returned no games or failed")
                
                # Тестируем fallback метод
                print(f"\n🔄 Testing fallback method...")
                legacy_wishlist = await parser.get_wishlist_legacy(steam_id64)
                if legacy_wishlist:
                    print(f"✅ Legacy method returned {len(legacy_wishlist)} games")
                else:
                    print(f"⚠️ Legacy method returned no games or failed")
                
                # Общий тест через основной метод
                print(f"\n🎯 Testing main method (with API priority)...")
                main_result = await parser.check_wishlist_discounts(steam_id)
                if main_result:
                    print(f"✅ Main method found {len(main_result)} games with discounts")
                    for i, game in enumerate(main_result[:3]):  # Показываем первые 3
                        discount = game.get('discount_percent', 0)
                        price = game.get('final_formatted', 'N/A')
                        print(f"  {i+1}. {game.get('name', 'Unknown')} - {discount}% off, {price}")
                else:
                    print(f"📭 Main method found no games with discounts")
                
        except Exception as e:
            print(f"❌ Error testing profile {profile_url}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_official_api())
