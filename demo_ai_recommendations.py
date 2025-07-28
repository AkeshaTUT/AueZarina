#!/usr/bin/env python3
"""
Демонстрация ИИ-рекомендаций с реальным wishlist
"""

import asyncio
import logging
from steam_wishlist import SteamWishlistParser
from ai_game_recommendations import get_ai_game_recommendations
from config import OPENROUTER_API_KEY

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def demo_ai_recommendations():
    """Демо ИИ-рекомендаций с реальным wishlist"""
    print("🎮 Steam Bot AI Recommendations Demo")
    print("=" * 50)
    
    # Тестовый профиль
    profile_url = "https://steamcommunity.com/profiles/76561199362644959"
    
    print(f"🔍 Analyzing wishlist from: {profile_url}")
    print("📋 Getting real wishlist data...")
    
    try:
        # Получаем реальные данные wishlist
        async with SteamWishlistParser() as parser:
            steam_id = parser.extract_steam_id(profile_url)
            if not steam_id:
                print("❌ Could not extract Steam ID")
                return
            
            wishlist_games = await parser.get_wishlist_data(steam_id)
            
            if not wishlist_games:
                print("❌ Could not get wishlist data")
                return
            
            print(f"✅ Found {len(wishlist_games)} games in wishlist")
            
            # Показываем первые 10 игр
            print(f"\n📋 Sample games from wishlist:")
            for i, game in enumerate(wishlist_games[:10], 1):
                print(f"  {i}. {game.get('name', 'Unknown Game')}")
            
            if len(wishlist_games) > 10:
                print(f"  ... and {len(wishlist_games) - 10} more games")
        
        print(f"\n🤖 Requesting AI analysis and recommendations...")
        print("⏱️ This will take 1-2 minutes...")
        
        # Получаем ИИ-рекомендации
        ai_result = await get_ai_game_recommendations(
            wishlist_games,
            OPENROUTER_API_KEY,
            6  # Максимум 6 рекомендаций для демо
        )
        
        print(f"\n🎯 AI ANALYSIS RESULTS:")
        print(f"✅ Success: {ai_result['success']}")
        
        # Анализ предпочтений
        analysis = ai_result.get('analysis', {})
        if analysis:
            print(f"\n🎮 YOUR GAMING PREFERENCES:")
            
            if 'top_genres' in analysis and analysis['top_genres']:
                genres = ', '.join(analysis['top_genres'][:4])
                print(f"  🎯 Favorite Genres: {genres}")
            
            if 'preferred_mechanics' in analysis and analysis['preferred_mechanics']:
                mechanics = ', '.join(analysis['preferred_mechanics'][:3])
                print(f"  ⚙️ Preferred Mechanics: {mechanics}")
            
            if 'game_types' in analysis and analysis['game_types']:
                types = ', '.join(analysis['game_types'][:3])
                print(f"  🏷️ Game Types: {types}")
            
            if 'analysis_summary' in analysis:
                summary = analysis['analysis_summary']
                print(f"  🧠 AI Summary: {summary}")
        
        # Рекомендации
        recommendations = ai_result.get('recommendations', [])
        if recommendations:
            print(f"\n🎁 PERSONALIZED GAME RECOMMENDATIONS:")
            
            for i, rec in enumerate(recommendations, 1):
                name = rec.get('name', 'Unknown Game')
                description = rec.get('description', '')
                reason = rec.get('reason', '')
                price = rec.get('estimated_price', 'Unknown')
                similarity = rec.get('similarity_score', 0)
                
                print(f"\n{i}. 🎮 {name}")
                if similarity:
                    print(f"   🎯 Match: {similarity}%")
                if description:
                    print(f"   📝 {description}")
                if reason:
                    print(f"   ✨ Why for you: {reason}")
                if price and price != 'Unknown':
                    print(f"   💰 Price: {price}")
        else:
            print("\n😞 No recommendations generated")
        
        print(f"\n🚀 Demo completed! Try the bot command:")
        print(f"   /recommend {profile_url}")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_ai_recommendations())
