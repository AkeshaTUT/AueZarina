#!/usr/bin/env python3
"""
Пример использования многоязычной системы ZarinAI Bot
"""

from translations import get_text, get_available_languages

def demo_multilingual():
    """Демонстрация многоязычной функциональности"""
    
    print("🌍 ZarinAI Bot - Multilingual Demo")
    print("=" * 40)
    
    # Показываем доступные языки
    languages = get_available_languages()
    print(f"📋 Available languages: {languages}")
    print()
    
    # Демонстрируем основные сообщения
    demo_keys = [
        'welcome_title',
        'cmd_subscribe',
        'cmd_deals', 
        'cmd_free',
        'subscribed_success',
        'language_changed'
    ]
    
    for lang in languages:
        lang_name = "Русский" if lang == 'ru' else "English"
        flag = "🇷🇺" if lang == 'ru' else "🇺🇸"
        
        print(f"{flag} {lang_name} ({lang.upper()})")
        print("-" * 25)
        
        for key in demo_keys:
            text = get_text(lang, key)
            print(f"  {key}: {text}")
        print()
    
    # Демонстрируем форматирование
    print("📝 Formatting Examples:")
    print("-" * 25)
    
    for lang in languages:
        # Пример с параметрами
        deals_text = get_text(lang, 'current_deals', min_discount=70)
        no_deals_text = get_text(lang, 'no_deals_found', min_discount=50)
        
        lang_name = "RU" if lang == 'ru' else "EN"
        print(f"{lang_name}: {deals_text}")
        print(f"{lang_name}: {no_deals_text}")
        print()
    
    print("✅ Demo completed! Ready to use multilingual bot!")
    print("\n💡 Usage in bot:")
    print("   language = db.get_user_language(user_id)")
    print("   message = get_text(language, 'welcome_title')")
    print("   await update.message.reply_text(message)")

if __name__ == "__main__":
    demo_multilingual()
