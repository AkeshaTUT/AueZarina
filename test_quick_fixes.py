#!/usr/bin/env python3
"""
Быстрый тест исправлений в steam_wishlist.py
"""
import asyncio
import logging
from steam_wishlist import SteamWishlistParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def quick_test():
    """Быстрый тест исправлений"""
    
    print("🔧 Quick Test of Fixes")
    print("=" * 30)
    
    # Тестируем с одним публичным профилем
    profile_url = "https://steamcommunity.com/profiles/76561197960266962/"
    
    print(f"🔍 Testing profile: {profile_url}")
    
    try:
        async with SteamWishlistParser() as parser:
            steam_id = parser.extract_steam_id(profile_url)
            print(f"📋 Steam ID: {steam_id}")
            
            if not steam_id:
                print("❌ Could not extract Steam ID")
                return
            
            # Получаем wishlist через официальный API
            print(f"\n🌐 Testing official API...")
            steam_id64 = await parser.resolve_steam_id(steam_id)
            
            if steam_id64:
                print(f"🔢 Steam ID64: {steam_id64}")
                
                # Получаем wishlist
                wishlist_items = await parser.get_wishlist_via_api(steam_id64)
                print(f"📋 Wishlist items: {len(wishlist_items)}")
                
                if wishlist_items:
                    print(f"\n📝 First 3 games:")
                    for i, game in enumerate(wishlist_items[:3]):
                        print(f"  {i+1}. {game.get('name', 'Unknown')} (ID: {game.get('app_id', 'N/A')})")
                    
                    # Тестируем получение скидок
                    print(f"\n💰 Testing discounts...")
                    discounts = await parser.get_wishlist_discounts_via_api(steam_id64)
                    print(f"🛍️ Discounted games: {len(discounts)}")
                    
                    if discounts:
                        print(f"\n💸 Games on sale:")
                        for i, game in enumerate(discounts):
                            discount = game.get('discount_percent', 0)
                            price = game.get('final_formatted', 'N/A')
                            print(f"  {i+1}. {game.get('name', 'Unknown')} - {discount}% off, {price}")
                    else:
                        print("📭 No games on sale found")
                else:
                    print("📭 No wishlist items found")
            else:
                print("❌ Could not resolve Steam ID64")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
