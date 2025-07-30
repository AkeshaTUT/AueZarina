#!/usr/bin/env python3
"""
Тест многоязычности основных команд бота
"""

import sys
import os

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translations import get_text, get_available_languages

def test_all_commands():
    """Тестирование всех переводов команд"""
    
    print("🧪 Тестирование многоязычности команд ZarinAI Bot")
    print("=" * 55)
    
    # Список всех ключей для тестирования
    test_keys = [
        # Основные команды
        'welcome_title', 'welcome_description',
        'cmd_subscribe', 'cmd_deals', 'cmd_free', 'cmd_settings',
        'cmd_wishlist', 'cmd_recommend', 'cmd_help',
        
        # Сообщения состояния
        'subscribed_success', 'already_subscribed',
        'unsubscribed_success', 'not_subscribed',
        'language_changed',
        
        # Поиск и ошибки
        'searching_deals', 'searching_free_games',
        'no_suitable_deals', 'error_getting_deals',
        'no_free_games', 'error_free_games',
        'analyzing_wishlist', 'generating_weekly_digest',
        
        # Настройки
        'your_settings', 'subscription_status',
        'min_discount_setting', 'selected_genres',
        'change_language',
        
        # AI функции
        'ai_not_available', 'generating_recommendations',
        'wishlist_check', 'enter_steam_id'
    ]
    
    languages = get_available_languages()
    
    print(f"📋 Доступные языки: {languages}")
    print(f"🔑 Тестируем {len(test_keys)} ключей переводов")
    print()
    
    # Результаты тестирования
    results = {}
    missing_keys = []
    
    for lang in languages:
        lang_name = "Русский" if lang == 'ru' else "English"
        flag = "🇷🇺" if lang == 'ru' else "🇺🇸"
        
        print(f"{flag} {lang_name} ({lang.upper()})")
        print("-" * 30)
        
        lang_missing = []
        for key in test_keys:
            try:
                text = get_text(lang, key)
                if f"[MISSING: {key}]" in text:
                    lang_missing.append(key)
                    print(f"  ❌ {key}: ОТСУТСТВУЕТ")
                else:
                    # Показываем только первые несколько символов для краткости
                    short_text = text[:50] + "..." if len(text) > 50 else text
                    print(f"  ✅ {key}: {short_text}")
            except Exception as e:
                lang_missing.append(key)
                print(f"  ❌ {key}: ОШИБКА - {e}")
        
        if lang_missing:
            missing_keys.extend([(lang, key) for key in lang_missing])
        
        results[lang] = {
            'total': len(test_keys),
            'present': len(test_keys) - len(lang_missing),
            'missing': len(lang_missing)
        }
        
        print(f"\n📊 Статистика {lang_name}:")
        print(f"   ✅ Переведено: {results[lang]['present']}/{results[lang]['total']}")
        print(f"   ❌ Отсутствует: {results[lang]['missing']}")
        print()
    
    # Тестирование форматирования
    print("📝 Тестирование форматирования:")
    print("-" * 35)
    
    format_tests = [
        ('no_suitable_deals', {'min_discount': 70}),
        ('current_deals', {'min_discount': 50}),
        ('discount_updated', {'discount': 60})
    ]
    
    for key, params in format_tests:
        print(f"🔑 {key}:")
        for lang in languages:
            try:
                formatted_text = get_text(lang, key, **params)
                short_text = formatted_text[:80] + "..." if len(formatted_text) > 80 else formatted_text
                lang_flag = "🇷🇺" if lang == 'ru' else "🇺🇸"
                print(f"  {lang_flag} {short_text}")
            except Exception as e:
                print(f"  ❌ {lang}: ОШИБКА - {e}")
        print()
    
    # Итоговая статистика
    print("🎯 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 25)
    
    total_keys = len(test_keys)
    for lang in languages:
        lang_name = "Русский" if lang == 'ru' else "English"
        coverage = (results[lang]['present'] / total_keys) * 100
        status = "✅ ОТЛИЧНО" if coverage >= 95 else "⚠️ ТРЕБУЕТ ВНИМАНИЯ" if coverage >= 80 else "❌ КРИТИЧНО"
        
        print(f"{lang_name}: {coverage:.1f}% покрытие - {status}")
    
    if missing_keys:
        print(f"\n⚠️ Найдено {len(missing_keys)} отсутствующих переводов:")
        for lang, key in missing_keys[:10]:  # Показываем первые 10
            print(f"   {lang}: {key}")
        if len(missing_keys) > 10:
            print(f"   ... и еще {len(missing_keys) - 10}")
    else:
        print("\n🎉 ВСЕ ПЕРЕВОДЫ НАЙДЕНЫ!")
    
    print("\n✅ Тестирование завершено!")
    return len(missing_keys) == 0

if __name__ == "__main__":
    success = test_all_commands()
    sys.exit(0 if success else 1)
