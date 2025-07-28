#!/usr/bin/env python3
"""
Быстрый тест ИИ-рекомендаций с библиотекой
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_game_recommendations import get_ai_game_recommendations
from config import OPENROUTER_API_KEY

async def main():
    print("🤖 Быстрый тест ИИ с библиотекой игр...")
    
    # Тестовые данные
    wishlist = [
        {'name': 'The Witcher 3: Wild Hunt'},
        {'name': 'Cyberpunk 2077'},
        {'name': 'Baldur\'s Gate 3'},
    ]
    
    library = [
        {'name': 'Skyrim', 'playtime_forever': 12000},
        {'name': 'Mass Effect 2', 'playtime_forever': 3600},
        {'name': 'Dragon Age: Origins', 'playtime_forever': 1800},
    ]
    
    try:
        result = await get_ai_game_recommendations(wishlist, library, OPENROUTER_API_KEY, 3)
        
        if result['success']:
            print("✅ Успех!")
            print(f"📊 Проанализировано: wishlist {len(wishlist)}, библиотека {len(library)}")
            
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"🎯 Рекомендации ({len(recommendations)}):")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec.get('name', 'Unknown')}")
            
            analysis = result.get('analysis', {})
            if analysis.get('top_genres'):
                print(f"🎮 Жанры: {', '.join(analysis['top_genres'][:3])}")
                
        else:
            print(f"❌ Ошибка: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(main())
