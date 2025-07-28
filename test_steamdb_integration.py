"""
Тест интеграции с SteamDB для получения реальных данных о ценах
"""
import asyncio
from price_chart_generator import generate_price_chart, extract_game_id_from_url, PriceChartGenerator

async def test_steamdb_integration():
    """Тестирует получение данных с SteamDB"""
    
    test_cases = [
        # Популярные игры с известными ID
        ("Counter-Strike 2", "730"),
        ("Cyberpunk 2077", "1091500"),
        ("The Witcher 3", "292030"),
        ("Dota 2", "570"),
    ]
    
    print("🧪 Тестирование интеграции с SteamDB")
    print("=" * 60)
    
    generator = PriceChartGenerator()
    
    for game_name, app_id in test_cases:
        print(f"\n🎮 Тестируем: {game_name} (ID: {app_id})")
        
        try:
            # Тестируем получение реальных данных
            real_data = await generator.get_real_price_data(app_id)
            
            if real_data:
                print(f"   ✅ Получено {len(real_data)} точек с SteamDB")
                print(f"   📅 Период: {real_data[0]['date'].strftime('%d.%m.%Y')} - {real_data[-1]['date'].strftime('%d.%m.%Y')}")
                
                # Показываем несколько цен
                recent_prices = real_data[-3:]
                print(f"   💰 Последние цены:")
                for price_point in recent_prices:
                    price_rub = price_point['price'] / 100
                    print(f"      {price_point['date'].strftime('%d.%m.%Y')}: {price_rub:.0f}₽")
                
            else:
                print(f"   ❌ Не удалось получить данные с SteamDB")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("🔗 Тестирование полной генерации графика с URL")
    
    # Тест с полным URL
    test_url = "https://store.steampowered.com/app/730/CounterStrike_2/"
    print(f"\n📋 Тестируем URL: {test_url}")
    
    try:
        chart_buffer, game_info = await generate_price_chart(test_url)
        
        if chart_buffer and game_info:
            print(f"   ✅ График создан для: {game_info.get('name', 'Unknown')}")
            print(f"   🆔 Steam ID: {game_info.get('id', 'Unknown')}")
            print(f"   📊 Источник данных: {game_info.get('data_source', 'Unknown')}")
            print(f"   📈 Количество точек: {game_info.get('data_points', 0)}")
        else:
            print(f"   ❌ Не удалось создать график")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("\n💡 Примечания:")
    print("- Если SteamDB недоступен, будут использованы демо-данные")
    print("- Реальные цены показываются в российских рублях")
    print("- График автоматически помечает источник данных")

if __name__ == "__main__":
    asyncio.run(test_steamdb_integration())
