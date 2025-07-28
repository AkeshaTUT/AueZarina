"""
Модуль для генерации графиков изменения цен игр
Использует matplotlib для создания графиков
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import io
import random
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class PriceChartGenerator:
    def __init__(self):
        # Настройка matplotlib для русского языка
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Liberation Sans', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
        
    def generate_sample_price_data(self, game_name: str, months: int = 6) -> List[Dict]:
        """Генерирует примерные данные о ценах для демонстрации"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Базовая цена игры (зависит от названия для консистентности)
        random.seed(hash(game_name) % 1000)
        base_price = random.randint(500, 3000)
        
        prices = []
        current_date = start_date
        current_price = base_price
        
        while current_date <= end_date:
            # Генерируем реалистичные изменения цен
            if random.random() < 0.1:  # 10% шанс на скидку
                discount = random.uniform(0.2, 0.8)  # Скидка 20-80%
                current_price = int(base_price * (1 - discount))
            elif random.random() < 0.05:  # 5% шанс на возврат к обычной цене
                current_price = base_price
            
            prices.append({
                'date': current_date,
                'price': current_price,
                'original_price': base_price
            })
            
            current_date += timedelta(days=random.randint(1, 7))
        
        return prices
    
    async def get_real_price_data(self, app_id: str) -> List[Dict]:
        """Получает реальные данные о ценах (заглушка для будущей интеграции с SteamDB)"""
        try:
            # Здесь можно добавить интеграцию с реальными API
            # Например, SteamDB, IsThereAnyDeal, или SteamSpy
            
            # Пока возвращаем None, чтобы использовать sample данные
            return None
            
        except Exception as e:
            logger.error(f"Error getting real price data: {e}")
            return None
    
    def create_price_chart(self, game_name: str, price_data: List[Dict]) -> io.BytesIO:
        """Создает график изменения цен"""
        try:
            # Настройка размера и стиля графика
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Извлекаем данные
            dates = [item['date'] for item in price_data]
            prices = [item['price'] for item in price_data]
            original_prices = [item['original_price'] for item in price_data]
            
            # Строим основной график цены
            ax.plot(dates, prices, linewidth=2.5, color='#1f77b4', label='Цена', marker='o', markersize=4)
            
            # Добавляем линию оригинальной цены
            if original_prices and len(set(original_prices)) > 1:
                ax.axhline(y=original_prices[0], color='red', linestyle='--', alpha=0.7, label='Базовая цена')
            
            # Заливка области скидок
            for i, (date, price, orig_price) in enumerate(zip(dates, prices, original_prices)):
                if price < orig_price * 0.9:  # Если скидка больше 10%
                    discount_percent = int((1 - price / orig_price) * 100)
                    ax.scatter(date, price, color='red', s=80, zorder=5)
                    ax.annotate(f'-{discount_percent}%', 
                              (date, price), 
                              xytext=(10, 10), 
                              textcoords='offset points',
                              bbox=dict(boxstyle='round,pad=0.3', fc='red', alpha=0.7),
                              color='white', fontsize=9, fontweight='bold')
            
            # Настройка осей
            ax.set_xlabel('Дата', fontsize=12, fontweight='bold')
            ax.set_ylabel('Цена (₽)', fontsize=12, fontweight='bold')
            ax.set_title(f'График изменения цены: {game_name}', fontsize=14, fontweight='bold', pad=20)
            
            # Форматирование дат на оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Сетка
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8f9fa')
            
            # Легенда
            ax.legend(loc='upper right', framealpha=0.9)
            
            # Добавляем информацию о ценах
            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]
            
            info_text = f'Текущая цена: {current_price}₽\nМинимум: {min_price}₽\nМаксимум: {max_price}₽'
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                   fontsize=10)
            
            # Плотная компоновка
            plt.tight_layout()
            
            # Сохраняем в байты
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            
            # Очищаем память
            plt.close(fig)
            
            return buf
            
        except Exception as e:
            logger.error(f"Error creating price chart: {e}")
            plt.close('all')  # Очищаем все графики в случае ошибки
            return None
    
    async def search_game_by_name(self, game_name: str) -> Optional[Dict]:
        """Ищет игру в Steam по названию"""
        try:
            # Упрощенный поиск игры
            url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=russian&cc=RU"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        if items:
                            game = items[0]  # Берем первый результат
                            return {
                                'id': game.get('id'),
                                'name': game.get('name'),
                                'tiny_image': game.get('tiny_image'),
                                'small_capsule_image': game.get('small_capsule_image')
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching game: {e}")
            return None

async def generate_price_chart(game_name: str) -> Tuple[Optional[io.BytesIO], Optional[Dict]]:
    """Основная функция для генерации графика цен"""
    try:
        generator = PriceChartGenerator()
        
        # Ищем игру
        game_info = await generator.search_game_by_name(game_name)
        
        if not game_info:
            # Если не нашли, создаем базовую информацию
            game_info = {'name': game_name, 'id': None}
        
        # Пытаемся получить реальные данные
        real_data = await generator.get_real_price_data(str(game_info.get('id', '')))
        
        # Если нет реальных данных, генерируем примерные
        if not real_data:
            price_data = generator.generate_sample_price_data(game_info['name'])
        else:
            price_data = real_data
        
        # Создаем график
        chart_buffer = generator.create_price_chart(game_info['name'], price_data)
        
        return chart_buffer, game_info
        
    except Exception as e:
        logger.error(f"Error generating price chart: {e}")
        return None, None
