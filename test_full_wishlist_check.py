#!/usr/bin/env python3
"""
Тест полной проверки wishlist - проверяет ВСЕ игры из списка желаемого
"""

import asyncio
import logging
from steam_wishlist import get_wishlist_discounts
from config import WISHLIST_MAX_GAMES_CHECK, WISHLIST_CHECK_DELAY, WISHLIST_ENABLE_FULL_CHECK

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_full_wishlist_check():
    """Тестирует полную проверку всех игр из wishlist"""
    print("🌟 Testing FULL Wishlist Check")
    print("=" * 50)
    
    # Проверяем текущие настройки
    print(f"📋 Current Settings:")
    print(f"   WISHLIST_MAX_GAMES_CHECK: {WISHLIST_MAX_GAMES_CHECK}")
    print(f"   WISHLIST_CHECK_DELAY: {WISHLIST_CHECK_DELAY}")
    print(f"   WISHLIST_ENABLE_FULL_CHECK: {WISHLIST_ENABLE_FULL_CHECK}")
    
    if WISHLIST_ENABLE_FULL_CHECK:
        print("🌟 FULL CHECK MODE is ENABLED - will check ALL games!")
    else:
        print(f"⚠️ LIMITED CHECK MODE - will check only {WISHLIST_MAX_GAMES_CHECK} games")
    
    print("-" * 50)
    
    # Тестовый профиль
    profile_url = "https://steamcommunity.com/profiles/76561199362644959"
    
    print(f"🔍 Testing full wishlist check for profile: {profile_url}")
    print("⏱️ This will check ALL games from wishlist...")
    print("🕐 Estimated time: ~4-5 minutes for 180 games")
    print("-" * 50)
    
    try:
        discounted_games = await get_wishlist_discounts(profile_url)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"✅ Found {len(discounted_games)} games with discounts!")
        
        if discounted_games:
            print(f"\n🎁 GAMES ON SALE:")
            for i, game in enumerate(discounted_games):
                name = game.get('name', 'Unknown Game')
                discount = game.get('discount_percent', 0)
                original_price = game.get('initial_formatted', 'N/A')
                final_price = game.get('final_formatted', 'N/A')
                app_id = game.get('app_id', '')
                
                print(f"  {i+1}. {name}")
                print(f"     💰 {discount}% OFF: {original_price} → {final_price}")
                print(f"     🔗 https://store.steampowered.com/app/{app_id}/")
                print()
        else:
            print("😞 No games from wishlist are currently on sale")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_wishlist_check())
