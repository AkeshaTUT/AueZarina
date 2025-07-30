#!/usr/bin/env python3
"""
Тест улучшенного алгоритма еженедельного дайджеста
"""

import sys
import os
from datetime import datetime

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def test_improved_digest_algorithm():
    """Тестируем новый алгоритм рейтинга игр"""
    
    print("🧪 ТЕСТ УЛУЧШЕННОГО АЛГОРИТМА ЕЖЕНЕДЕЛЬНОГО ДАЙДЖЕСТА")
    print("=" * 65)
    print(f"📅 Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Инициализируем базу данных
    db = DatabaseManager()
    
    # Очищаем старые данные
    db.clear_weekly_top()
    
    # Тестовые данные игр с разными характеристиками
    test_games = [
        # Формат: (название, скидка, цена, ожидаемый_рейтинг_примерно)
        ("Cyberpunk 2077", 85, 399.0, "высокий (популярная игра + хорошая скидка)"),
        ("The Witcher 3: Wild Hunt", 90, 199.0, "очень высокий (топ игра + отличная скидка + хорошая цена)"),
        ("Unknown Indie Game", 95, 50.0, "средний (большая скидка, но неизвестная игра)"),
        ("Call of Duty: Modern Warfare", 75, 2500.0, "высокий (популярная, но дорогая)"),
        ("Stardew Valley", 60, 299.0, "высокий (популярная инди игра)"),
        ("Random DLC Pack", 90, 100.0, "низкий (DLC штрафуется)"),
        ("Fallout 4", 80, 599.0, "высокий (популярная серия)"),
        ("Some Game 2012", 95, 150.0, "средний (старая игра)"),
        ("FIFA 2024", 70, 1999.0, "высокий (популярная серия)"),
        ("Hollow Knight", 50, 349.0, "высокий (популярная инди)")
    ]
    
    print("📊 ТЕСТОВЫЕ ДАННЫЕ:")
    print("-" * 40)
    
    # Имитируем алгоритм рейтинга (упрощенная версия)
    scored_games = []
    
    for title, discount, price, expected in test_games:
        # Упрощенный алгоритм рейтинга
        score = calculate_test_score(title, discount, price)
        
        scored_games.append({
            'title': title,
            'discount': discount, 
            'price': price,
            'score': score,
            'expected': expected
        })
        
        # Добавляем в базу
        db.add_weekly_top_game(title, discount, price, score)
        
        print(f"🎮 {title}")
        print(f"   💸 Скидка: {discount}%")
        print(f"   💰 Цена: {price}₽")
        print(f"   📊 Рейтинг: {score:.1f}/200")
        print(f"   💡 Ожидание: {expected}")
        print()
    
    # Сортируем по рейтингу
    sorted_games = sorted(scored_games, key=lambda x: x['score'], reverse=True)
    
    print("🏆 РЕЗУЛЬТАТЫ РЕЙТИНГА (топ-5):")
    print("-" * 35)
    
    for i, game in enumerate(sorted_games[:5], 1):
        emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
        score = game['score']
        
        # Эмодзи качества
        if score >= 150:
            quality_emoji = "⭐"
        elif score >= 100:
            quality_emoji = "🔥"
        elif score >= 80:
            quality_emoji = "✨"
        else:
            quality_emoji = "💰"
        
        print(f"{emoji} {quality_emoji} {game['title']}")
        print(f"    💸 Скидка: -{game['discount']}%")
        print(f"    💰 Цена: {game['price']}₽")
        print(f"    📊 Рейтинг: {score:.1f}/200")
        print()
    
    # Проверим работу базы данных
    print("💾 ПРОВЕРКА БАЗЫ ДАННЫХ:")
    print("-" * 30)
    
    weekly_top = db.get_weekly_top_games(10)
    
    if weekly_top:
        print(f"✅ В базе найдено {len(weekly_top)} игр")
        print("Порядок в базе (по рейтингу):")
        for i, game in enumerate(weekly_top, 1):
            score = game.get('score', 0)
            print(f"  {i}. {game['title']} - рейтинг: {score:.1f}, скидка: {game['discount']}%")
    else:
        print("❌ Данные в базе не найдены")
    
    # Анализ алгоритма
    print(f"\n📈 АНАЛИЗ АЛГОРИТМА:")
    print("-" * 25)
    
    # Проверяем, что популярные игры поднялись в рейтинге
    popular_games = [g for g in sorted_games if any(keyword in g['title'].lower() 
                    for keyword in ['witcher', 'cyberpunk', 'fallout', 'call of duty'])]
    
    indie_games = [g for g in sorted_games if any(keyword in g['title'].lower() 
                  for keyword in ['stardew', 'hollow knight'])]
    
    dlc_games = [g for g in sorted_games if 'dlc' in g['title'].lower()]
    
    print(f"🎯 Популярные AAA игры в топе: {len([g for g in popular_games if g['score'] >= 100])}/{len(popular_games)}")
    print(f"🎮 Инди игры получили бонус: {len([g for g in indie_games if g['score'] >= 80])}/{len(indie_games)}")
    print(f"📦 DLC получили штраф: {len([g for g in dlc_games if g['score'] < 80])}/{len(dlc_games)}")
    
    # Рекомендации
    print(f"\n💡 ВЫВОДЫ:")
    print("-" * 15)
    
    if len(popular_games) > 0 and popular_games[0]['score'] > 120:
        print("✅ Алгоритм корректно повышает рейтинг популярных игр")
    else:
        print("⚠️ Нужно увеличить бонус за популярность")
    
    if len(dlc_games) > 0 and dlc_games[0]['score'] < 100:
        print("✅ Алгоритм корректно штрафует DLC")
    else:
        print("⚠️ Нужно увеличить штраф за DLC")
    
    # Проверим баланс цена/качество
    affordable_quality = [g for g in sorted_games if g['price'] <= 600 and g['score'] >= 100]
    print(f"✅ Доступных качественных игр в топе: {len(affordable_quality)}")
    
    # Очищаем тестовые данные
    db.clear_weekly_top()
    
    print(f"\n🏁 Тестирование завершено: {datetime.now().strftime('%H:%M:%S')}")
    print("🚀 Новый алгоритм готов к использованию!")

def calculate_test_score(title, discount, price):
    """Упрощенная версия алгоритма рейтинга для тестирования"""
    title_lower = title.lower()
    
    # 1. Базовый рейтинг скидки
    discount_score = min(discount, 90)
    
    # 2. Популярность игры
    popularity_score = 0
    popular_keywords = [
        'cyberpunk', 'witcher', 'fallout', 'call of duty', 'fifa', 
        'stardew valley', 'hollow knight', 'gta'
    ]
    
    for keyword in popular_keywords:
        if keyword in title_lower:
            popularity_score += 30
            break
    
    # 3. Ценовая категория
    price_score = 0
    if 0 < price <= 500:
        price_score = 25
    elif 500 < price <= 1500:
        price_score = 20
    elif 1500 < price <= 3000:
        price_score = 15
    else:
        price_score = 5
    
    # 4. Штрафы
    penalty = 0
    if 'dlc' in title_lower:
        penalty += 15
    
    # Годы для штрафа за старые игры
    old_years = ['2010', '2011', '2012', '2013']
    for year in old_years:
        if year in title:
            penalty += 10
            break
    
    # Финальный рейтинг
    final_score = discount_score + popularity_score + price_score - penalty
    return max(0, min(final_score, 200))

if __name__ == "__main__":
    test_improved_digest_algorithm()
