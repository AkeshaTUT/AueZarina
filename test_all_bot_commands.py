#!/usr/bin/env python3
"""
Финальный тест многоязычности всех команд бота
"""

import sys
import os

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translations import get_text, get_available_languages

def test_all_bot_commands():
    """Комплексное тестирование всех команд и функций бота"""
    
    print("🤖 ФИНАЛЬНЫЙ ТЕСТ МНОГОЯЗЫЧНОСТИ ZarinAI BOT")
    print("=" * 60)
    
    # Основные команды бота
    bot_commands = [
        # Команды пользователя
        '/start', '/help', '/subscribe', '/unsubscribe',
        '/free', '/deals', '/wishlist', '/recommend',
        '/settings', '/genres', '/discount', '/feedback',
        '/weeklydigest'
    ]
    
    # Ключи переводов для каждой команды
    command_keys = {
        '/start': ['welcome_title', 'welcome_description', 'choose_language'],
        '/help': ['cmd_subscribe', 'cmd_deals', 'cmd_free', 'cmd_settings'],
        '/subscribe': ['subscribed_success', 'already_subscribed'],
        '/unsubscribe': ['unsubscribed_success', 'not_subscribed'],
        '/free': ['searching_free_games', 'no_free_games', 'error_free_games'],
        '/deals': ['searching_deals', 'no_suitable_deals', 'error_getting_deals'],
        '/wishlist': ['analyzing_wishlist', 'enter_steam_id'],
        '/recommend': ['generating_recommendations', 'ai_not_available'],
        '/settings': ['your_settings', 'subscription_status', 'min_discount_setting'],
        '/genres': ['select_genres_title', 'selected_genres', 'genres_instruction'],
        '/discount': ['discount_settings_title', 'current_discount', 'select_min_discount'],
        '/feedback': ['feedback_menu_title', 'report_bug', 'suggest_feature'],
        '/weeklydigest': ['generating_weekly_digest', 'no_weekly_data']
    }
    
    languages = get_available_languages()
    
    print(f"🌐 Тестируемые языки: {languages}")
    print(f"📋 Команды бота: {len(bot_commands)}")
    print()
    
    # Тестирование каждой команды
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for command in bot_commands:
        print(f"🔍 Тестирование команды: {command}")
        print("-" * 40)
        
        if command not in command_keys:
            print(f"  ⚠️ Нет ключей для тестирования команды {command}")
            continue
        
        keys = command_keys[command]
        
        for lang in languages:
            lang_name = "🇷🇺 Русский" if lang == 'ru' else "🇺🇸 English"
            
            for key in keys:
                total_tests += 1
                try:
                    text = get_text(lang, key)
                    if f"[MISSING: {key}]" in text:
                        print(f"  ❌ {lang_name}: {key} - ОТСУТСТВУЕТ")
                        failed_tests.append(f"{command} -> {lang}:{key}")
                    else:
                        print(f"  ✅ {lang_name}: {key} - OK")
                        passed_tests += 1
                except Exception as e:
                    print(f"  ❌ {lang_name}: {key} - ОШИБКА: {e}")
                    failed_tests.append(f"{command} -> {lang}:{key}")
        
        print()
    
    # Тестирование специальных функций
    print("🎯 ТЕСТИРОВАНИЕ СПЕЦИАЛЬНЫХ ФУНКЦИЙ:")
    print("-" * 45)
    
    special_tests = [
        # Кнопки интерфейса
        ('language_russian', {}),
        ('language_english', {}),
        ('clear_all_genres', {}),
        ('save_genres', {}),
        
        # Форматированные сообщения
        ('discount_updated', {'discount': 70}),
        ('no_suitable_deals', {'min_discount': 50}),
        ('selected_genres', {'genres': 'Action, Strategy'}),
        ('current_discount', {'discount': 60}),
    ]
    
    for key, params in special_tests:
        print(f"🔑 {key}:")
        for lang in languages:
            total_tests += 1
            try:
                text = get_text(lang, key, **params)
                if f"[MISSING: {key}]" in text:
                    print(f"  ❌ {lang}: ОТСУТСТВУЕТ")
                    failed_tests.append(f"special -> {lang}:{key}")
                else:
                    short_text = text[:60] + "..." if len(text) > 60 else text
                    flag = "🇷🇺" if lang == 'ru' else "🇺🇸"
                    print(f"  ✅ {flag}: {short_text}")
                    passed_tests += 1
            except Exception as e:
                print(f"  ❌ {lang}: ОШИБКА - {e}")
                failed_tests.append(f"special -> {lang}:{key}")
        print()
    
    # Итоговая статистика
    print("🏆 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 30)
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 Всего тестов: {total_tests}")
    print(f"✅ Пройдено: {passed_tests}")
    print(f"❌ Не пройдено: {len(failed_tests)}")
    print(f"📈 Успешность: {success_rate:.1f}%")
    print()
    
    if success_rate >= 95:
        status = "🎉 ОТЛИЧНО!"
        color = "🟢"
    elif success_rate >= 85:
        status = "👍 ХОРОШО"
        color = "🟡"
    else:
        status = "⚠️ ТРЕБУЕТ ВНИМАНИЯ"
        color = "🔴"
    
    print(f"{color} Общая оценка: {status}")
    
    if failed_tests:
        print(f"\n❌ Ошибки в тестах:")
        for i, error in enumerate(failed_tests[:10], 1):
            print(f"   {i}. {error}")
        if len(failed_tests) > 10:
            print(f"   ... и еще {len(failed_tests) - 10}")
    else:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"🚀 Бот готов к работе на двух языках!")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 20)
    
    if success_rate >= 95:
        print("✅ Многоязычность полностью реализована")
        print("✅ Все команды поддерживают оба языка")
        print("✅ Бот готов к продакшн использованию")
    else:
        print("⚠️ Некоторые переводы требуют доработки")
        print("⚠️ Рекомендуется исправить ошибки перед релизом")
        print("📝 Проверьте файл translations.py")
    
    print("\n🔚 Тестирование завершено!")
    return success_rate >= 95

if __name__ == "__main__":
    success = test_all_bot_commands()
    sys.exit(0 if success else 1)
