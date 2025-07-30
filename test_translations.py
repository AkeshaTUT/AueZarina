#!/usr/bin/env python3
"""
Тест многоязычности для ZarinAI Bot
"""

import sys
import os
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translations import get_text, get_available_languages

def test_translations():
    """Тестирование системы переводов"""
    print("🧪 Тестирование системы переводов ZarinAI Bot")
    print("=" * 50)
    
    # Проверяем доступные языки
    languages = get_available_languages()
    print(f"📋 Доступные языки: {languages}")
    print()
    
    # Тестируем основные ключи
    test_keys = [
        'welcome_title',
        'welcome_description', 
        'cmd_subscribe',
        'cmd_deals',
        'subscribed_success',
        'already_subscribed',
        'your_settings',
        'language_changed'
    ]
    
    for lang in languages:
        print(f"🌍 Язык: {lang}")
        print("-" * 30)
        
        for key in test_keys:
            text = get_text(lang, key)
            print(f"  {key}: {text}")
        
        print()
    
    # Тестируем форматирование
    print("📝 Тестирование форматирования:")
    print("-" * 30)
    
    for lang in languages:
        formatted_text = get_text(lang, 'no_deals_found', min_discount=50)
        print(f"  {lang}: {formatted_text}")
    
    print()
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    test_translations()
