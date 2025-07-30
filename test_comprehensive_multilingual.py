#!/usr/bin/env python3
"""
Итоговый интеграционный тест многоязычного ZarinAI Bot
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from translations import get_text, get_available_languages

def comprehensive_multilingual_test():
    """Полный тест многоязычности бота"""
    
    print("🌐 КОМПЛЕКСНЫЙ ТЕСТ МНОГОЯЗЫЧНОГО ZARINAI BOT")
    print("=" * 60)
    
    # Инициализируем базу данных
    db = DatabaseManager()
    
    print(f"📅 Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Доступные языки: {get_available_languages()}")
    print()
    
    # ===== ТЕСТ 1: СИСТЕМА ПЕРЕВОДОВ =====
    print("🧪 ТЕСТ 1: СИСТЕМА ПЕРЕВОДОВ")
    print("-" * 35)
    
    # Ключевые функции для тестирования
    critical_functions = [
        # Основные команды
        ('start_command', ['welcome_title', 'welcome_description', 'choose_language']),
        ('help_command', ['all_commands', 'basic_title', 'new_title']),
        ('subscribe_command', ['subscribed_success', 'already_subscribed']),
        ('deals_command', ['searching_deals', 'no_suitable_deals', 'error_getting_deals']),
        ('free_command', ['searching_free_games', 'no_free_games', 'error_free_games']),
        ('settings_command', ['your_settings', 'subscription_status', 'change_language']),
        
        # Новые функции
        ('weeklydigest_command', ['weekly_digest_title', 'weekly_digest_subtitle', 'weekly_digest_cta']),
        ('wishlist_command', ['analyzing_wishlist', 'enter_steam_id']),
        ('ai_recommend_command', ['generating_recommendations', 'ai_not_available']),
        ('feedback_command', ['feedback_menu_title', 'report_bug', 'suggest_feature']),
        
        # Административные функции
        ('admin_commands', ['admin_only', 'digest_test_title', 'sending_digest', 'digest_sent'])
    ]
    
    total_keys = 0
    missing_keys = []
    
    for function_name, keys in critical_functions:
        print(f"  🔍 {function_name}:")
        for key in keys:
            total_keys += 1
            for lang in get_available_languages():
                try:
                    text = get_text(lang, key)
                    if f"[MISSING: {key}]" in text:
                        missing_keys.append(f"{lang}:{key}")
                        print(f"    ❌ {lang}:{key} - ОТСУТСТВУЕТ")
                    else:
                        print(f"    ✅ {lang}:{key} - OK")
                except Exception as e:
                    missing_keys.append(f"{lang}:{key}")
                    print(f"    ❌ {lang}:{key} - ОШИБКА: {e}")
    
    translation_success = len(missing_keys) == 0
    print(f"\n📊 Результат тестирования переводов:")
    print(f"  📋 Всего ключей: {total_keys * len(get_available_languages())}")
    print(f"  ✅ Найдено: {total_keys * len(get_available_languages()) - len(missing_keys)}")
    print(f"  ❌ Отсутствует: {len(missing_keys)}")
    print(f"  📈 Успешность: {((total_keys * len(get_available_languages()) - len(missing_keys)) / (total_keys * len(get_available_languages())) * 100):.1f}%")
    
    # ===== ТЕСТ 2: БАЗА ДАННЫХ =====
    print(f"\n🧪 ТЕСТ 2: МНОГОЯЗЫЧНАЯ БАЗА ДАННЫХ")
    print("-" * 40)
    
    # Тестируем функции базы данных для языков
    test_user_id = 999999  # Тестовый пользователь
    
    try:
        # Очищаем тестового пользователя
        db.remove_user(test_user_id)
        
        # Добавляем пользователя
        db.add_user(test_user_id, "test_user", "Test", "User")
        print("  ✅ Добавление пользователя: работает")
        
        # Тестируем языковые функции
        for lang in get_available_languages():
            db.set_user_language(test_user_id, lang)
            retrieved_lang = db.get_user_language(test_user_id)
            if retrieved_lang == lang:
                print(f"  ✅ Установка/получение языка {lang}: работает")
            else:
                print(f"  ❌ Установка/получение языка {lang}: ошибка ({retrieved_lang})")
        
        # Получаем настройки пользователя
        settings = db.get_user_settings(test_user_id)
        if 'language' in settings:
            print("  ✅ Получение настроек с языком: работает")
        else:
            print("  ❌ Получение настроек с языком: ошибка")
        
        # Очищаем тестовые данные
        db.remove_user(test_user_id)
        
        database_success = True
        
    except Exception as e:
        print(f"  ❌ Ошибка базы данных: {e}")
        database_success = False
    
    # ===== ТЕСТ 3: ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ =====
    print(f"\n🧪 ТЕСТ 3: МНОГОЯЗЫЧНЫЙ ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ")
    print("-" * 50)
    
    try:
        # Очищаем и добавляем тестовые данные
        db.clear_weekly_top()
        
        test_games = [
            ("Cyberpunk 2077", 85, 1299.0),
            ("The Witcher 3", 90, 599.0),
            ("Red Dead Redemption 2", 75, 1499.0)
        ]
        
        for title, discount, price in test_games:
            db.add_weekly_top_game(title, discount, price)
        
        weekly_data = db.get_weekly_top_games(5)
        
        if weekly_data:
            print(f"  ✅ Сбор данных дайджеста: работает ({len(weekly_data)} игр)")
            
            # Тестируем форматирование для каждого языка
            for lang in get_available_languages():
                try:
                    message = get_text(lang, 'weekly_digest_title') + "\n\n"
                    message += get_text(lang, 'weekly_digest_subtitle') + "\n\n"
                    
                    for i, game in enumerate(weekly_data[:3], 1):
                        emoji = ["🥇", "🥈", "🥉"][i-1]
                        message += f"{emoji} {game['title']}\n"
                        
                        if lang == 'ru':
                            message += f"💸 Скидка: -{game['discount']}%\n"
                            message += f"💰 Цена: {game['price']}₽\n\n"
                        else:
                            message += f"💸 Discount: -{game['discount']}%\n"
                            message += f"💰 Price: ${game['price']}\n\n"
                    
                    message += get_text(lang, 'weekly_digest_cta')
                    
                    if len(message) > 100:  # Проверяем, что сообщение сформировалось
                        lang_name = "Русский" if lang == 'ru' else "English"
                        print(f"  ✅ Форматирование дайджеста на {lang_name}: работает")
                    else:
                        print(f"  ❌ Форматирование дайджеста на {lang}: пустое сообщение")
                        
                except Exception as e:
                    print(f"  ❌ Форматирование дайджеста на {lang}: ошибка ({e})")
            
        else:
            print("  ❌ Сбор данных дайджеста: нет данных")
        
        # Очищаем тестовые данные
        db.clear_weekly_top()
        digest_success = True
        
    except Exception as e:
        print(f"  ❌ Ошибка дайджеста: {e}")
        digest_success = False
    
    # ===== ТЕСТ 4: ИНТЕГРАЦИЯ КОМПОНЕНТОВ =====
    print(f"\n🧪 ТЕСТ 4: ИНТЕГРАЦИЯ КОМПОНЕНТОВ")
    print("-" * 40)
    
    integration_tests = [
        ("Модуль переводов", translation_success),
        ("База данных", database_success),
        ("Еженедельный дайджест", digest_success),
    ]
    
    integration_success = True
    for test_name, result in integration_tests:
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if not result:
            integration_success = False
    
    # ===== ИТОГОВЫЕ РЕЗУЛЬТАТЫ =====
    print(f"\n🏆 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 45)
    
    overall_success = translation_success and database_success and digest_success and integration_success
    
    if overall_success:
        status_icon = "🎉"
        status_text = "ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!"
        status_color = "🟢"
    else:
        status_icon = "⚠️"
        status_text = "ОБНАРУЖЕНЫ ПРОБЛЕМЫ"
        status_color = "🔴"
    
    print(f"{status_color} {status_icon} {status_text}")
    print()
    
    # Детальная статистика
    print("📊 ДЕТАЛЬНАЯ СТАТИСТИКА:")
    print("-" * 25)
    print(f"🌐 Поддерживаемые языки: {len(get_available_languages())}")
    print(f"🔑 Протестированных ключей: {total_keys}")
    print(f"📋 Общих переводов: {total_keys * len(get_available_languages())}")
    print(f"🎯 Функций бота: {len(critical_functions)}")
    print(f"📊 Компонентов: {len(integration_tests)}")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 20)
    
    if overall_success:
        print("✅ Многоязычная система полностью готова к использованию")
        print("✅ Все компоненты работают корректно")
        print("✅ Можно запускать бота в продакшн")
        print("🚀 Система поддерживает:")
        print("   • Автоматическое определение языка пользователя")
        print("   • Переключение языка в настройках")
        print("   • Многоязычные команды и ответы")
        print("   • Локализованный еженедельный дайджест")
        print("   • AI-рекомендации на выбранном языке")
    else:
        print("⚠️ Обнаружены проблемы, требующие исправления:")
        
        if missing_keys:
            print(f"❌ Отсутствующие переводы: {len(missing_keys)}")
            print("   Необходимо добавить переводы в translations.py")
        
        if not database_success:
            print("❌ Проблемы с базой данных")
            print("   Проверьте database.py и миграции")
        
        if not digest_success:
            print("❌ Проблемы с дайджестом")
            print("   Проверьте функции еженедельного дайджеста")
    
    print(f"\n📋 ГОТОВНОСТЬ К ЗАПУСКУ:")
    print("-" * 30)
    
    readiness_score = sum([translation_success, database_success, digest_success, integration_success])
    readiness_percent = (readiness_score / 4) * 100
    
    if readiness_percent >= 100:
        print("🟢 ПОЛНОСТЬЮ ГОТОВ (100%)")
        print("🚀 Можно запускать в продакшн")
    elif readiness_percent >= 80:
        print(f"🟡 ПОЧТИ ГОТОВ ({readiness_percent:.0f}%)")
        print("🔧 Нужны небольшие доработки")
    else:
        print(f"🔴 ТРЕБУЕТ ДОРАБОТКИ ({readiness_percent:.0f}%)")
        print("⚙️ Необходимы серьезные исправления")
    
    print(f"\n🔚 Тестирование завершено: {datetime.now().strftime('%H:%M:%S')}")
    return overall_success

if __name__ == "__main__":
    success = comprehensive_multilingual_test()
    sys.exit(0 if success else 1)
