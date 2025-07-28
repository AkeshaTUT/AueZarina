"""
Простой тест для price_chart_generator
"""
import asyncio

try:
    from price_chart_generator import extract_game_id_from_url, PriceChartGenerator, generate_price_chart
    print("✅ Все импорты успешны")
    
    # Тестируем функцию извлечения ID
    test_url = "https://store.steampowered.com/app/730/CounterStrike_2/"
    game_id = extract_game_id_from_url(test_url)
    print(f"🎮 Извлечен ID: {game_id}")
    
    print("🚀 Тестирование завершено успешно!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("📋 Модуль загружен!")
