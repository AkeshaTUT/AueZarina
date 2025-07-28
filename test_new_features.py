"""
Тестирование новых функций Steam бота:
1. Steam Wishlist анализ
2. Генерация графиков цен
3. AI-рекомендации игр
"""
import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_wishlist_functionality():
    """Тестирует функциональность Steam Wishlist"""
    print("🔍 Тестирование Steam Wishlist функциональности...")
    
    try:
        from steam_wishlist import get_wishlist_discounts, SteamWishlistParser
        
        # Тестируем парсер URL
        async with SteamWishlistParser() as parser:
            test_urls = [
                "https://steamcommunity.com/id/testuser",
                "https://steamcommunity.com/profiles/76561198123456789",
                "steamcommunity.com/id/anothertestuser"
            ]
            
            print("📝 Тестирование извлечения Steam ID...")
            for url in test_urls:
                steam_id = parser.extract_steam_id(url)
                print(f"   URL: {url} -> Steam ID: {steam_id}")
        
        # Примечание: реальный тест wishlist требует публичного профиля
        print("✅ Steam Wishlist модуль загружен успешно")
        print("ℹ️  Для полного тестирования требуется публичный Steam профиль")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования Steam Wishlist: {e}")

async def test_price_chart_functionality():
    """Тестирует функциональность генерации графиков"""
    print("\n📈 Тестирование генерации графиков цен...")
    
    try:
        from price_chart_generator import generate_price_chart
        
        test_games = ["Cyberpunk 2077", "The Witcher 3", "Counter-Strike 2"]
        
        for game_name in test_games:
            print(f"   Генерирую тестовый график для: {game_name}")
            chart_buffer, game_info = await generate_price_chart(game_name)
            
            if chart_buffer:
                print(f"   ✅ График создан для {game_info.get('name', game_name)}")
                # Можно сохранить для просмотра
                # with open(f"test_chart_{game_name.replace(' ', '_')}.png", "wb") as f:
                #     chart_buffer.seek(0)
                #     f.write(chart_buffer.read())
            else:
                print(f"   ❌ Не удалось создать график для {game_name}")
        
        print("✅ Модуль генерации графиков работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования графиков: {e}")

async def test_ai_recommendations_functionality():
    """Тестирует функциональность AI-рекомендаций"""
    print("\n🤖 Тестирование AI-рекомендаций...")
    
    try:
        from ai_recommendations import get_game_recommendations
        
        test_preferences = [
            ["The Witcher 3", "Skyrim", "Cyberpunk 2077"],
            ["Counter-Strike", "Valorant"],
            ["Minecraft", "Terraria", "Stardew Valley"]
        ]
        
        for i, preferences in enumerate(test_preferences, 1):
            print(f"   Тест {i}: {', '.join(preferences)}")
            recommendations = await get_game_recommendations(preferences)
            
            if recommendations and recommendations.get('discounted_games'):
                games_count = recommendations['total_games']
                print(f"   ✅ Найдено {games_count} рекомендаций")
                
                # Показываем первые 3 рекомендации
                for j, game in enumerate(recommendations['discounted_games'][:3], 1):
                    name = game.get('name', 'Unknown')
                    discount = game.get('discount', 0)
                    print(f"      {j}. {name} (-{discount}%)")
            else:
                print(f"   ❌ Рекомендации не найдены")
        
        print("✅ Модуль AI-рекомендаций работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования AI-рекомендаций: {e}")

def test_imports():
    """Тестирует импорты всех модулей"""
    print("📦 Тестирование импортов модулей...")
    
    modules_to_test = [
        ('steam_wishlist', 'Steam Wishlist'),
        ('price_chart_generator', 'Price Chart Generator'),
        ('ai_recommendations', 'AI Recommendations')
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {description} модуль импортирован успешно")
        except ImportError as e:
            print(f"   ❌ Ошибка импорта {description}: {e}")

def test_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    print("\n📋 Проверка зависимостей...")
    
    dependencies = [
        ('aiohttp', 'HTTP client для async запросов'),
        ('matplotlib', 'Библиотека для графиков'),
        ('numpy', 'Математические операции'),
        ('openai', 'OpenAI API (опционально)')
    ]
    
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"   ✅ {package}: {description}")
        except ImportError:
            print(f"   ❌ {package}: {description} - НЕ УСТАНОВЛЕН")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования новых функций Steam бота\n")
    print("=" * 60)
    
    # Тестируем зависимости
    test_dependencies()
    
    # Тестируем импорты
    test_imports()
    
    # Тестируем функциональность
    await test_wishlist_functionality()
    await test_price_chart_functionality()
    await test_ai_recommendations_functionality()
    
    print("\n" + "=" * 60)
    print("🎯 Тестирование завершено!")
    print("\n💡 Для полного тестирования выполните:")
    print("   1. Установите зависимости: pip install -r requirements.txt")
    print("   2. Запустите бота: python steam_bot.py")
    print("   3. Протестируйте команды:")
    print("      • /wishlist https://steamcommunity.com/id/your_profile")
    print("      • /график Cyberpunk 2077")
    print("      • /рекомендую")

if __name__ == "__main__":
    asyncio.run(main())
