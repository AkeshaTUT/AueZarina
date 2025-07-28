"""
Test script for the specific Steam Wishlist case that was failing
"""
import asyncio
import logging
from steam_wishlist import get_wishlist_discounts

# Setup logging to match the bot's logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_specific_case():
    """Test the specific case that was failing"""
    
    # The URL that was failing
    test_url = "https://steamcommunity.com/id/Bolshiresiski/"
    
    print(f"🧪 Testing specific failing case: {test_url}")
    print("=" * 60)
    
    try:
        # Test the full wishlist functionality
        discounted_games = await get_wishlist_discounts(test_url)
        
        print(f"✅ Function completed without errors")
        print(f"📊 Results: {len(discounted_games)} games with discounts found")
        
        if discounted_games:
            print("\n🎮 Games with discounts:")
            for i, game in enumerate(discounted_games[:5], 1):  # Show first 5
                name = game.get('name', 'Unknown Game')
                discount = game.get('discount_percent', 0)
                price = game.get('final_formatted', 'N/A')
                print(f"  {i}. {name} - {discount}% off - {price}")
        else:
            print("\n📝 No games with discounts found - this could be:")
            print("   • Wishlist is private/inaccessible")
            print("   • Wishlist is empty")
            print("   • No current discounts on wishlist games")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_specific_case())
