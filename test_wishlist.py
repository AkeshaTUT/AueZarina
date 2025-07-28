"""
Test script for Steam Wishlist functionality
"""
import asyncio
import logging
from steam_wishlist import get_wishlist_discounts, SteamWishlistParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_wishlist_functionality():
    """Test the wishlist functionality with better error handling"""
    
    # Test URLs (you can replace with real ones for testing)
    test_urls = [
        "https://steamcommunity.com/id/testuser",  # Non-existent user
        "https://steamcommunity.com/profiles/76561198000000000",  # Invalid ID
        "invalid_url",  # Invalid format
    ]
    
    print("🧪 Testing Steam Wishlist functionality...")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: {url}")
        print("-" * 30)
        
        try:
            # Test Steam ID extraction
            async with SteamWishlistParser() as parser:
                steam_id = parser.extract_steam_id(url)
                print(f"Extracted Steam ID: {steam_id}")
                
                if steam_id:
                    # Test Steam ID resolution
                    resolved_id = await parser.resolve_steam_id(steam_id)
                    print(f"Resolved Steam ID64: {resolved_id}")
                    
                    if resolved_id:
                        # Test wishlist data retrieval
                        wishlist_data = await parser.get_wishlist_data(steam_id)
                        print(f"Wishlist games found: {len(wishlist_data)}")
                        
                        if wishlist_data:
                            # Test discount checking
                            discounted_games = await parser.check_wishlist_discounts(steam_id)
                            print(f"Games with discounts: {len(discounted_games)}")
                            
                            for game in discounted_games[:3]:  # Show first 3
                                print(f"  - {game.get('name', 'Unknown')}: {game.get('discount_percent', 0)}% off")
                else:
                    print("❌ Could not extract Steam ID from URL")
                    
        except Exception as e:
            print(f"❌ Error testing {url}: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_wishlist_functionality())
