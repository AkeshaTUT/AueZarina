#!/usr/bin/env python3
"""
Тест ИИ-рекомендаций игр на основе Steam Wishlist
"""

import asyncio
import logging
from ai_game_recommendations import get_ai_game_recommendations

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Тестовые данные wishlist (примерные)
test_wishlist = [
    {
        'app_id': '292030',
        'name': 'The Witcher 3: Wild Hunt',
        'tags': [{'name': 'RPG'}, {'name': 'Open World'}, {'name': 'Fantasy'}]
    },
    {
        'app_id': '377160',
        'name': 'Fallout 4',
        'tags': [{'name': 'RPG'}, {'name': 'Post-apocalyptic'}, {'name': 'Shooter'}]
    },
    {
        'app_id': '72850',
        'name': 'The Elder Scrolls V: Skyrim',
        'tags': [{'name': 'RPG'}, {'name': 'Fantasy'}, {'name': 'Open World'}]
    },
    {
        'app_id': '413150',
        'name': 'Stardew Valley',
        'tags': [{'name': 'Simulation'}, {'name': 'Farming'}, {'name': 'Indie'}]
    },
    {
        'app_id': '207690',
        'name': 'Botanicula',
        'tags': [{'name': 'Adventure'}, {'name': 'Indie'}, {'name': 'Point & Click'}]
    },
    {
        'app_id': '381210',
        'name': 'Dead by Daylight',
        'tags': [{'name': 'Horror'}, {'name': 'Multiplayer'}, {'name': 'Survival'}]
    },
    {
        'app_id': '105600',
        'name': 'Terraria',
        'tags': [{'name': 'Sandbox'}, {'name': 'Adventure'}, {'name': '2D'}]
    },
    {
        'app_id': '578080',
        'name': 'PUBG: BATTLEGROUNDS',
        'tags': [{'name': 'Battle Royale'}, {'name': 'Shooter'}, {'name': 'Multiplayer'}]
    }
]

async def test_ai_recommendations():
    """Тестирует ИИ-рекомендации"""
    print("🤖 Testing AI Game Recommendations")
    print("=" * 50)
    
    # API ключ из конфигурации
    from config import OPENROUTER_API_KEY
    
    print(f"📋 Testing with {len(test_wishlist)} games from sample wishlist:")
    for game in test_wishlist:
        print(f"  • {game['name']}")
    
    print("\n🧠 Requesting AI analysis and recommendations...")
    print("⏱️ This may take 30-60 seconds...")
    
    try:
        result = await get_ai_game_recommendations(
            wishlist_games=test_wishlist,
            api_key=OPENROUTER_API_KEY,
            limit=6
        )
        
        print(f"\n🎯 RESULTS:")
        print(f"✅ Success: {result['success']}")
        print(f"📊 Total wishlist games analyzed: {result['total_wishlist_games']}")
        
        # Анализ предпочтений
        analysis = result.get('analysis', {})
        if analysis:
            print(f"\n🎮 PREFERENCE ANALYSIS:")
            
            if 'top_genres' in analysis:
                genres = ', '.join(analysis['top_genres'][:5])
                print(f"  Top Genres: {genres}")
            
            if 'preferred_mechanics' in analysis:
                mechanics = ', '.join(analysis['preferred_mechanics'][:3])
                print(f"  Preferred Mechanics: {mechanics}")
            
            if 'analysis_summary' in analysis:
                summary = analysis['analysis_summary'][:200]
                print(f"  AI Summary: {summary}")
        
        # Рекомендации
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"\n🎁 AI RECOMMENDATIONS ({len(recommendations)}):")
            
            for i, rec in enumerate(recommendations, 1):
                name = rec.get('name', 'Unknown Game')
                description = rec.get('description', '')[:100]
                reason = rec.get('reason', '')[:100]
                price = rec.get('estimated_price', 'Unknown')
                similarity = rec.get('similarity_score', 0)
                
                print(f"\n{i}. {name}")
                if description:
                    print(f"   📝 {description}")
                if reason:
                    print(f"   ✨ Why: {reason}")
                if price != 'Unknown':
                    print(f"   💰 Price: {price}")
                if similarity:
                    print(f"   🎯 Similarity: {similarity}%")
        else:
            print("\n😞 No recommendations generated")
        
        # Обработка ошибок
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_quick_ai():
    """Быстрый тест ИИ подключения"""
    print("\n🔧 Testing AI Connection...")
    
    try:
        from ai_game_recommendations import GameRecommendationAI
        from config import OPENROUTER_API_KEY
        
        ai = GameRecommendationAI(OPENROUTER_API_KEY)
        
        # Простой тест
        result = await ai.get_genre_analysis([
            {'name': 'The Witcher 3', 'tags': []},
            {'name': 'Skyrim', 'tags': []},
            {'name': 'Cyberpunk 2077', 'tags': []}
        ])
        
        if result:
            print("✅ AI connection successful!")
            print(f"📊 Response: {result}")
        else:
            print("❌ AI connection failed - empty response")
            
    except Exception as e:
        print(f"❌ AI connection error: {e}")

if __name__ == "__main__":
    print("🚀 Starting AI Recommendations Test")
    
    # Запускаем тесты
    asyncio.run(test_quick_ai())
    asyncio.run(test_ai_recommendations())
