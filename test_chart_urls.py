"""
Тест новой функциональности команды /chart с поддержкой Steam URL
"""
import asyncio
from price_chart_generator import generate_price_chart, extract_game_id_from_url

async def test_chart_with_urls():
    """Тестирует генерацию графиков по разным типам ввода"""
    
    test_cases = [
        # Steam Store URL
        "https://store.steampowered.com/app/1091500/Cyberpunk_2077/",
        
        # Короткий Community URL
        "steamcommunity.com/app/730",
        
        # Просто ID
        "1091500",
        
        # Название игры (старый способ)
        "Counter-Strike 2"
    ]
    
    print("🧪 Тестирование новой функциональности команды /chart")
    print("=" * 60)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📋 Тест {i}: {test_input}")
        
        # Проверяем извлечение ID
        game_id = extract_game_id_from_url(test_input)
        if game_id:
            print(f"   ✅ Извлечен game_id: {game_id}")
        else:
            print(f"   ❌ ID не извлечен, будет поиск по названию")
        
        # Попробуем сгенерировать график
        try:
            chart_buffer, game_info = await generate_price_chart(test_input)
            
            if chart_buffer and game_info:
                print(f"   ✅ График создан для: {game_info.get('name', 'Unknown')}")
                if game_info.get('id'):
                    print(f"   🆔 Steam ID: {game_info['id']}")
            else:
                print(f"   ❌ Не удалось создать график")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_chart_with_urls())
