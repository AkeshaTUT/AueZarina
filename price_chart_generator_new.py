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
import re
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

def extract_game_id_from_url(url: str) -> Optional[str]:
    """
    Извлекает game_id из Steam URL
    
    Поддерживаемые форматы:
    - https://store.steampowered.com/app/1091500/Cyberpunk_2077/
    - https://steamcommunity.com/app/1091500
    - steam://store/1091500
    
    Args:
        url: Steam URL
        
    Returns:
        game_id или None если не найден
    """
    try:
        # Паттерны для разных типов Steam URL
        patterns = [
            r'store\.steampowered\.com/app/(\d+)',  # Store page
            r'steamcommunity\.com/app/(\d+)',       # Community page  
            r'steam://store/(\d+)',                 # Steam protocol
            r'/app/(\d+)',                          # Любой URL с /app/ID
            r'(?:^|\D)(\d{6,7})(?:\D|$)'           # Просто ID из 6-7 цифр
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                game_id = match.group(1)
                # Проверяем, что ID в разумных пределах для Steam
                if len(game_id) >= 3 and int(game_id) > 0:
                    logger.info(f"📋 Extracted game_id: {game_id} from URL: {url}")
                    return game_id
        
        logger.warning(f"🔍 Could not extract game_id from URL: {url}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error extracting game_id from URL: {e}")
        return None

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
            
            # Основная линия графика
            ax.plot(dates, prices, linewidth=2.5, color='#1f77b4', label='Цена')
            
            # Заливка под графиком
            ax.fill_between(dates, prices, alpha=0.3, color='#1f77b4')
            
            # Отмечаем скидки красными точками
            discount_dates = []
            discount_prices = []
            for i, (date, price, original) in enumerate(zip(dates, prices, original_prices)):
                if price < original * 0.9:  # Скидка больше 10%
                    discount_dates.append(date)
                    discount_prices.append(price)
            
            if discount_dates:
                ax.scatter(discount_dates, discount_prices, color='red', s=50, zorder=5, label='Скидки')
            
            # Настройка осей
            ax.set_xlabel('Дата', fontsize=12)
            ax.set_ylabel('Цена (₽)', fontsize=12)
            ax.set_title(f'График изменения цены: {game_name}', fontsize=14, fontweight='bold')
            
            # Форматирование дат на оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            
            # Сетка
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Статистика
            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]
            
            # Добавляем текст со статистикой
            stats_text = f'Мин: {min_price}₽ | Макс: {max_price}₽ | Текущая: {current_price}₽'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Поворачиваем подписи дат
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Сохраняем в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating price chart: {e}")
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
            logger.error(f"Error searching game by name: {e}")
            return None
    
    async def get_game_info_by_id(self, game_id: str) -> Optional[Dict]:
        """Получает информацию об игре по Steam ID"""
        try:
            logger.info(f"🔍 Getting game info for ID: {game_id}")
            
            # Используем Steam Store API для получения информации об игре
            url = f"https://store.steampowered.com/api/appdetails?appids={game_id}&l=russian&cc=RU"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if game_id in data and data[game_id]['success']:
                            game_data = data[game_id]['data']
                            
                            game_info = {
                                'id': game_id,
                                'name': game_data.get('name', f'Game {game_id}'),
                                'short_description': game_data.get('short_description', ''),
                                'header_image': game_data.get('header_image', ''),
                                'price_overview': game_data.get('price_overview', {}),
                                'genres': [genre.get('description', '') for genre in game_data.get('genres', [])],
                                'release_date': game_data.get('release_date', {}).get('date', '')
                            }
                            
                            logger.info(f"🎮 Found game: {game_info['name']}")
                            return game_info
                        else:
                            logger.warning(f"⚠️ Game with ID {game_id} not found or not accessible")
                            return None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting game info by ID {game_id}: {e}")
            return None

async def generate_price_chart(game_input: str) -> Tuple[Optional[io.BytesIO], Optional[Dict]]:
    """
    Основная функция для генерации графика цен
    
    Args:
        game_input: Название игры или Steam URL
        
    Returns:
        Tuple с буфером графика и информацией об игре
    """
    try:
        generator = PriceChartGenerator()
        game_info = None
        
        # Проверяем, является ли input URL-ом
        game_id = extract_game_id_from_url(game_input)
        
        if game_id:
            # Получаем информацию об игре по ID
            game_info = await generator.get_game_info_by_id(game_id)
            if not game_info:
                # Если не удалось получить информацию, создаем базовую
                game_info = {'name': f'Game {game_id}', 'id': game_id}
        else:
            # Ищем игру по названию
            game_info = await generator.search_game_by_name(game_input)
            if not game_info:
                # Если не нашли, создаем базовую информацию
                game_info = {'name': game_input, 'id': None}
        
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
