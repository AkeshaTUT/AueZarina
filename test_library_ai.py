#!/usr/bin/env python3
"""
Тест для новой функциональности ИИ-рекомендаций с анализом библиотеки игр
"""
import asyncio
import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from steam_library import get_steam_library, get_recently_played_games
from ai_game_recommendations import get_ai_game_recommendations
from steam_wishlist import SteamWishlistParser
from config import OPENROUTER_API_KEY

async def test_library_parser():
    """Тестирует парсер библиотеки игр"""
    print("🔧 Тестирование парсера библиотеки игр Steam...")
    
    # Используем примеры публичных профилей Steam
    test_profiles = [
        "https://steamcommunity.com/id/gabelogannewell",  # Основатель Steam
        "https://steamcommunity.com/profiles/76561197960287930",  # Другой пример
    ]
    
    for profile_url in test_profiles:
        print(f"\n📋 Тестирование профиля: {profile_url}")
        
        try:
            # Получаем библиотеку игр
            library = await get_steam_library(profile_url, limit=10)
            
            if library:
                print(f"✅ Найдено {len(library)} игр в библиотеке:")
                
                for i, game in enumerate(library[:5], 1):
                    name = game.get('name', 'Unknown')
                    playtime = game.get('playtime_forever', 0)
                    hours = playtime / 60 if playtime > 0 else 0
                    
                    print(f"   {i}. {name} ({hours:.1f} часов)")
                
                if len(library) > 5:
                    print(f"   ... и еще {len(library) - 5} игр")
                    
            else:
                print("❌ Не удалось получить библиотеку (профиль может быть приватным)")
                
        except Exception as e:
            print(f"❌ Ошибка при тестировании {profile_url}: {e}")

async def test_comprehensive_ai_recommendations():
    """Тестирует комплексные ИИ-рекомендации"""
    print("\n🤖 Тестирование комплексных ИИ-рекомендаций...")
    
    # Создаем тестовые данные
    test_wishlist = [
        {'name': 'The Witcher 3: Wild Hunt'},
        {'name': 'Cyberpunk 2077'},
        {'name': 'Red Dead Redemption 2'},
        {'name': 'Baldur\'s Gate 3'},
        {'name': 'Disco Elysium'},
    ]
    
    test_library = [
        {'name': 'Skyrim', 'playtime_forever': 12000},  # 200 часов
        {'name': 'Fallout 4', 'playtime_forever': 6000},  # 100 часов
        {'name': 'Mass Effect 2', 'playtime_forever': 3600},  # 60 часов
        {'name': 'Dragon Age: Origins', 'playtime_forever': 1800},  # 30 часов
        {'name': 'Divinity: Original Sin 2', 'playtime_forever': 4800},  # 80 часов
    ]
    
    print(f"📊 Тестовые данные:")
    print(f"   💝 Wishlist: {len(test_wishlist)} игр")
    print(f"   📚 Библиотека: {len(test_library)} игр")
    
    try:
        # Получаем рекомендации
        ai_result = await get_ai_game_recommendations(
            test_wishlist, 
            test_library, 
            OPENROUTER_API_KEY, 
            6
        )
        
        if ai_result['success']:
            print(f"\n✅ ИИ-анализ успешно выполнен!")
            
            # Показываем анализ
            analysis = ai_result.get('analysis', {})
            if analysis:
                print(f"\n🧠 Анализ предпочтений:")
                
                if 'top_genres' in analysis:
                    print(f"   🎮 Жанры: {', '.join(analysis['top_genres'][:3])}")
                
                if 'preferred_mechanics' in analysis:
                    print(f"   ⚙️ Механики: {', '.join(analysis['preferred_mechanics'][:3])}")
                
                if 'gaming_style' in analysis:
                    print(f"   🎯 Стиль: {analysis['gaming_style']}")
            
            # Показываем рекомендации
            recommendations = ai_result.get('recommendations', [])
            if recommendations:
                print(f"\n🎯 Рекомендации ({len(recommendations)}):")
                
                for i, rec in enumerate(recommendations[:4], 1):
                    name = rec.get('name', 'Unknown')
                    reason = rec.get('reason', 'No reason')[:80]
                    similarity = rec.get('similarity_score', 0)
                    
                    print(f"   {i}. {name} ({similarity}%)")
                    print(f"      💡 {reason}")
                    
            else:
                print("❌ Рекомендации не сгенерированы")
                
        else:
            error = ai_result.get('error', 'Unknown error')
            print(f"❌ ИИ-анализ не удался: {error}")
            
    except Exception as e:
        print(f"❌ Ошибка в тестировании ИИ: {e}")

async def test_real_profile():
    """Тестирует реальный профиль (если доступен)"""
    print("\n🔍 Тест с реальным профилем Steam...")
    
    # Примеры профилей для тестирования (замените на свой если хотите)
    test_profiles = [
        "https://steamcommunity.com/id/gabelogannewell",  # Основатель Steam
    ]
    
    for profile_url in test_profiles:
        print(f"\n🔗 Тестирую: {profile_url}")
        
        try:
            # Получаем wishlist
            wishlist_games = []
            try:
                async with SteamWishlistParser() as parser:
                    steam_id = parser.extract_steam_id(profile_url)
                    if steam_id:
                        steam_id64 = await parser.resolve_steam_id(steam_id)
                        if steam_id64:
                            wishlist_games = await parser.get_wishlist_data(steam_id64)
                            
                print(f"💝 Wishlist: {len(wishlist_games)} игр")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить wishlist: {e}")
            
            # Получаем библиотеку
            owned_games = []
            try:
                owned_games = await get_steam_library(profile_url, limit=20)
                print(f"📚 Библиотека: {len(owned_games)} игр")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить библиотеку: {e}")
            
            # Проверяем, есть ли достаточно данных
            total_games = len(wishlist_games) + len(owned_games)
            if total_games >= 3:
                print(f"📊 Всего игр для анализа: {total_games}")
                
                # Получаем ИИ-рекомендации
                ai_result = await get_ai_game_recommendations(
                    wishlist_games[:10],  # Ограничиваем для теста
                    owned_games[:15], 
                    OPENROUTER_API_KEY, 
                    4
                )
                
                if ai_result['success']:
                    print("✅ ИИ-анализ выполнен успешно!")
                    
                    recommendations = ai_result.get('recommendations', [])
                    if recommendations:
                        print(f"🎯 Получено {len(recommendations)} рекомендаций:")
                        for i, rec in enumerate(recommendations[:3], 1):
                            print(f"   {i}. {rec.get('name', 'Unknown')}")
                else:
                    print(f"❌ ИИ-анализ не удался: {ai_result.get('error', 'Unknown')}")
            else:
                print(f"❌ Недостаточно данных для анализа ({total_games} игр)")
                
        except Exception as e:
            print(f"❌ Ошибка при тестировании реального профиля: {e}")

async def main():
    """Главная функция тестирования"""
    print("🚀 Тестирование новой функциональности ИИ-рекомендаций с библиотекой игр")
    print("=" * 80)
    
    # Проверяем API ключ
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your-api-key-here":
        print("❌ API ключ OpenRouter не настроен!")
        print("Настройте OPENROUTER_API_KEY в config.py")
        return
    
    print(f"✅ API ключ настроен: {OPENROUTER_API_KEY[:10]}...")
    
    # Тест 1: Парсер библиотеки игр
    await test_library_parser()
    
    # Тест 2: Комплексные ИИ-рекомендации
    await test_comprehensive_ai_recommendations()
    
    # Тест 3: Реальный профиль (опционально)
    await test_real_profile()
    
    print("\n" + "=" * 80)
    print("🎯 Тестирование завершено!")
    print("\n💡 Новые возможности:")
    print("   ✅ Анализ библиотеки игр Steam")
    print("   ✅ Учет времени игры в рекомендациях")
    print("   ✅ Комплексный анализ предпочтений")
    print("   ✅ Более точные персональные советы")

if __name__ == "__main__":
    asyncio.run(main())
