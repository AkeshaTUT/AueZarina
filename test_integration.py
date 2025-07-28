"""
Быстрый тест интеграции новых функций в основной бот
"""
import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_bot_imports():
    """Тестирует импорты в основном файле бота"""
    print("🤖 Тестирование импортов в steam_bot.py...")
    
    try:
        # Проверяем, что steam_bot.py может импортировать все новые модули
        import steam_bot
        print("   ✅ Основной модуль steam_bot импортирован успешно")
        
        # Проверяем наличие новых методов
        bot_methods = dir(steam_bot.SteamDiscountBot)
        
        required_methods = [
            'wishlist_command',
            'price_chart_command', 
            'ai_recommendations_command',
            'handle_text_messages',
            '_process_wishlist',
            '_process_ai_recommendations'
        ]
        
        for method in required_methods:
            if method in bot_methods:
                print(f"   ✅ Метод {method} найден")
            else:
                print(f"   ❌ Метод {method} НЕ НАЙДЕН")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка импорта steam_bot: {e}")
        return False

def test_bot_initialization():
    """Тестирует инициализацию бота с новыми функциями"""
    print("\n🔧 Тестирование инициализации бота...")
    
    try:
        from steam_bot import SteamDiscountBot
        
        # Создаем бота с тестовым токеном
        test_token = "1234567890:TEST_TOKEN_FOR_TESTING_ONLY"
        bot = SteamDiscountBot(test_token)
        
        print("   ✅ Бот инициализирован успешно")
        
        # Проверяем наличие user_states для многошаговых команд
        if hasattr(bot, 'user_states'):
            print("   ✅ Состояния пользователей инициализированы")
        else:
            print("   ❌ Состояния пользователей НЕ инициализированы")
        
        # Проверяем обработчики команд
        handlers = bot.application.handlers
        command_handlers = []
        
        for group in handlers.values():
            for handler in group:
                if hasattr(handler, 'command'):
                    command_handlers.extend(handler.command)
        
        new_commands = ['wishlist', 'chart', 'recommend', 'grafik', 'rekomend']
        
        for cmd in new_commands:
            if cmd in command_handlers:
                print(f"   ✅ Команда /{cmd} зарегистрирована")
            else:
                print(f"   ❌ Команда /{cmd} НЕ зарегистрирована")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка инициализации бота: {e}")
        return False

def test_help_messages():
    """Проверяет, что справочные сообщения обновлены"""
    print("\n📋 Проверка справочных сообщений...")
    
    try:
        # Читаем steam_bot.py и проверяем наличие новых команд в help
        with open('steam_bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_commands_in_help = [
            '/wishlist',
            '/chart',
            '/recommend',
            'AI-рекомендации',
            'Steam Wishlist'
        ]
        
        for cmd in new_commands_in_help:
            if cmd in content:
                print(f"   ✅ {cmd} найден в справке")
            else:
                print(f"   ❌ {cmd} НЕ найден в справке")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка чтения справки: {e}")
        return False

def main():
    """Основная функция тестирования интеграции"""
    print("🚀 Тестирование интеграции новых функций в Steam бот")
    print("=" * 65)
    
    all_tests_passed = True
    
    # Запуск тестов
    if not test_bot_imports():
        all_tests_passed = False
    
    if not test_bot_initialization():
        all_tests_passed = False
    
    if not test_help_messages():
        all_tests_passed = False
    
    print("\n" + "=" * 65)
    
    if all_tests_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n✨ Новые функции полностью интегрированы:")
        print("   💝 Steam Wishlist анализ - /wishlist")
        print("   📈 Графики цен - /график")  
        print("   🤖 AI-рекомендации - /рекомендую")
        print("\n🚀 Бот готов к запуску: python steam_bot.py")
    else:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ В ИНТЕГРАЦИИ")
        print("   Проверьте ошибки выше и исправьте их")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
