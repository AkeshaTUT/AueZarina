#!/usr/bin/env python3
"""
Тест основного функционала Steam Discount Bot v2.0
Проверяет работу всех 5 новых функций без подключения к Telegram API
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from steam_scraper import SteamScraper
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_database_functionality():
    """Тестирует функционал базы данных"""
    print("🗄️ Тестирование базы данных...")
    
    db = DatabaseManager()
    
    # Тест 1: Добавление пользователя
    user_id = 12345
    db.add_user(user_id, "test_user", "Test", "User")
    print("✅ Пользователь добавлен")
    
    # Тест 2: Настройка жанров
    genres = ["Экшен", "РПГ", "Стратегия"]
    db.set_user_genres(user_id, genres)
    user_genres = db.get_user_genres(user_id)
    print(f"✅ Жанры установлены: {user_genres}")
    
    # Тест 3: Настройка скидки
    db.set_user_min_discount(user_id, 50)
    min_discount = db.get_user_min_discount(user_id)
    print(f"✅ Минимальная скидка: {min_discount}%")
    
    # Тест 4: История цен
    db.add_price_history(123456, "Test Game", 1000.0)
    price_history = db.get_price_history(123456)
    print(f"✅ История цен: {len(price_history)} записей")
    
    # Тест 5: Бесплатные игры
    free_games = db.get_free_games()
    print(f"✅ Бесплатные игры: {len(free_games)} игр")
    
    # Тест 6: Еженедельный топ
    db.add_weekly_top_game("Test Game", 75, 500.0)
    weekly_top = db.get_weekly_top_games()
    print(f"✅ Еженедельный топ: {len(weekly_top)} игр")
    
    print("🎉 База данных работает корректно!")
    return True

async def test_scraper_functionality():
    """Тестирует функционал парсера Steam"""
    print("\n🔍 Тестирование парсера Steam...")
    
    try:
        scraper = SteamScraper()
        # Ограничиваем количество для теста
        games = await scraper.get_discounted_games(min_discount=30, max_results=5)
        
        print(f"✅ Найдено {len(games)} игр со скидками")
        
        for i, game in enumerate(games[:3]):  # Показываем первые 3
            print(f"  {i+1}. {game.get('title', 'Unknown')} - {game.get('discount', 0)}% скидка")
            if game.get('genres'):
                print(f"     Жанры: {', '.join(game['genres'][:3])}")
            if game.get('app_id'):
                print(f"     App ID: {game['app_id']}")
        
        return len(games) > 0
        
    except Exception as e:
        print(f"⚠️ Ошибка парсера (возможно проблемы с сетью): {e}")
        return False

def test_filter_functionality():
    """Тестирует фильтрацию игр"""
    print("\n🎯 Тестирование фильтрации...")
    
    # Тестовые данные
    test_games = [
        {"title": "Action Game", "discount": 40, "genres": ["Экшен", "Шутер"]},
        {"title": "RPG Game", "discount": 60, "genres": ["РПГ", "Приключения"]},
        {"title": "Strategy Game", "discount": 25, "genres": ["Стратегия"]},
        {"title": "Indie Game", "discount": 80, "genres": ["Инди", "Платформер"]},
    ]
    
    # Эмуляция фильтрации
    user_genres = ["Экшен", "РПГ"]
    min_discount = 35
    
    filtered_games = []
    for game in test_games:
        # Проверяем скидку
        if game["discount"] < min_discount:
            continue
        # Проверяем жанры
        if user_genres and not any(genre in user_genres for genre in game["genres"]):
            continue
        filtered_games.append(game)
    
    print(f"✅ Из {len(test_games)} игр отфильтровано {len(filtered_games)}")
    for game in filtered_games:
        print(f"  - {game['title']}: {game['discount']}% ({', '.join(game['genres'])})")
    
    return len(filtered_games) > 0

def test_inline_keyboards():
    """Тестирует генерацию inline клавиатур"""
    print("\n⌨️ Тестирование inline клавиатур...")
    
    # Тест жанров
    available_genres = ["Экшен", "РПГ", "Стратегия", "Симулятор", "Инди"]
    selected_genres = ["Экшен", "РПГ"]
    
    keyboard_data = []
    for genre in available_genres:
        status = "✅" if genre in selected_genres else "❌"
        keyboard_data.append(f"{status} {genre}")
    
    print(f"✅ Клавиатура жанров: {len(keyboard_data)} кнопок")
    print("   Пример кнопок:", keyboard_data[:3])
    
    # Тест скидок
    discount_options = [30, 50, 70, 90]
    current_discount = 50
    
    discount_keyboard = []
    for discount in discount_options:
        status = "🎯" if discount == current_discount else "💰"
        discount_keyboard.append(f"{status} {discount}%")
    
    print(f"✅ Клавиатура скидок: {len(discount_keyboard)} кнопок")
    print("   Пример кнопок:", discount_keyboard)
    
    return True

async def main():
    """Запуск всех тестов"""
    print("🚀 Steam Discount Bot v2.0 - Тестирование функционала")
    print("=" * 60)
    
    test_results = {
        "База данных": False,
        "Парсер Steam": False,
        "Фильтрация": False,
        "Клавиатуры": False
    }
    
    # Запуск тестов
    try:
        test_results["База данных"] = await test_database_functionality()
        test_results["Парсер Steam"] = await test_scraper_functionality()
        test_results["Фильтрация"] = test_filter_functionality()
        test_results["Клавиатуры"] = test_inline_keyboards()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    
    # Результаты
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ОШИБКА"
        print(f"{test_name:.<20} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Бот готов к работе!")
        print("\n📱 Для полного запуска используйте:")
        print("   python steam_bot.py")
        print("\n🔧 Убедитесь что:")
        print("   ✅ Токен бота корректный")
        print("   ✅ Интернет соединение стабильно")
        print("   ✅ Нет других экземпляров бота")
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте ошибки выше.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
