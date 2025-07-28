#!/usr/bin/env python3
"""
Тест улучшенной проверки скидок
"""
import asyncio
import logging
from steam_wishlist import get_wishlist_discounts

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_discount_improvements():
    """Тестирует улучшения в проверке скидок"""
    
    print("🛍️ Testing Improved Discount Detection")
    print("=" * 45)
    
    # Тестовый профиль с большим wishlist
    profile_url = "https://steamcommunity.com/profiles/76561199362644959"
    
    print(f"🔍 Testing improved discount detection for profile: {profile_url}")
    print(f"📋 Expecting to check up to 50 games instead of just 10...")
    print(f"⚡ Using faster processing with better logging...")
    print("-" * 45)
    
    try:
        # Получаем скидки
        discounts = await get_wishlist_discounts(profile_url)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"✅ Found {len(discounts)} games with discounts!")
        
        if discounts:
            print(f"\n🎁 GAMES ON SALE:")
            for i, game in enumerate(discounts[:10]):  # Показываем первые 10
                discount = game.get('discount_percent', 0)
                price = game.get('final_formatted', 'N/A')
                original_price = game.get('initial_formatted', 'N/A')
                print(f"  {i+1}. {game.get('name', 'Unknown')}")
                print(f"     💰 {discount}% OFF: {original_price} → {price}")
                print(f"     🔗 {game.get('url', 'N/A')}")
                print()
        else:
            print(f"😞 No games from wishlist are currently on sale")
            print(f"💡 This could mean:")
            print(f"   - No games are actually discounted right now")
            print(f"   - Steam is rate limiting our requests")
            print(f"   - Some games don't have price information available")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_discount_improvements())
