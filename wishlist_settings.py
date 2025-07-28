#!/usr/bin/env python3
"""
Скрипт для переключения режима проверки wishlist
"""

import os
import re

def toggle_full_check_mode(enable=True):
    """Переключает режим полной проверки wishlist"""
    config_file = "config.py"
    
    if not os.path.exists(config_file):
        print(f"❌ Файл конфигурации {config_file} не найден")
        return False
        
    try:
        # Читаем текущий файл
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Меняем настройку WISHLIST_ENABLE_FULL_CHECK
        if enable:
            new_content = re.sub(
                r'WISHLIST_ENABLE_FULL_CHECK = False',
                'WISHLIST_ENABLE_FULL_CHECK = True',
                content
            )
            print("🌟 Включен режим полной проверки - будут проверены ВСЕ игры из wishlist!")
        else:
            new_content = re.sub(
                r'WISHLIST_ENABLE_FULL_CHECK = True',
                'WISHLIST_ENABLE_FULL_CHECK = False',
                content
            )
            print(f"⚡ Включен режим ограниченной проверки - будут проверены только первые игры")
        
        # Сохраняем изменения
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ Настройки сохранены в {config_file}")
        print("🔄 Перезапустите бота для применения изменений")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при изменении настроек: {e}")
        return False

def show_current_settings():
    """Показывает текущие настройки"""
    try:
        from config import WISHLIST_MAX_GAMES_CHECK, WISHLIST_CHECK_DELAY, WISHLIST_ENABLE_FULL_CHECK
        
        print("📋 Текущие настройки Wishlist:")
        print(f"   Максимальное количество игр: {WISHLIST_MAX_GAMES_CHECK}")
        print(f"   Задержка между проверками: {WISHLIST_CHECK_DELAY} сек")
        print(f"   Полная проверка: {'✅ Включена' if WISHLIST_ENABLE_FULL_CHECK else '❌ Выключена'}")
        
        if WISHLIST_ENABLE_FULL_CHECK:
            print("🌟 Режим: Проверять ВСЕ игры из wishlist")
        else:
            print(f"⚡ Режим: Проверять максимум {WISHLIST_MAX_GAMES_CHECK} игр")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта настроек: {e}")

if __name__ == "__main__":
    print("🎮 Steam Wishlist Settings Manager")
    print("=" * 40)
    
    show_current_settings()
    
    print("\nВыберите действие:")
    print("1. Включить ПОЛНУЮ проверку (ВСЕ игры)")
    print("2. Включить ОГРАНИЧЕННУЮ проверку")
    print("3. Показать текущие настройки")
    print("4. Выход")
    
    try:
        choice = input("\nВведите номер действия (1-4): ").strip()
        
        if choice == "1":
            toggle_full_check_mode(True)
        elif choice == "2":
            toggle_full_check_mode(False)
        elif choice == "3":
            show_current_settings()
        elif choice == "4":
            print("👋 До свидания!")
        else:
            print("❌ Неверный выбор")
            
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
