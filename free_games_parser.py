import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class FreeGamesParser:
    """Парсер для получения актуальных бесплатных игр"""
    
    def __init__(self):
        self.session = None
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_free_games(self) -> List[Dict]:
        """Получение всех актуальных бесплатных игр"""
        free_games = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': self.user_agent}
        ) as session:
            self.session = session
            
            # Получаем данные с разных источников
            steam_free = await self._get_steam_free_games()
            epic_free = await self._get_epic_free_games()
            gog_free = await self._get_gog_free_games()
            
            free_games.extend(steam_free)
            free_games.extend(epic_free)
            free_games.extend(gog_free)
        
        return free_games
    
    async def _get_steam_free_games(self) -> List[Dict]:
        """Получение бесплатных игр из Steam"""
        games = []
        try:
            # Steam API для поиска бесплатных игр
            url = "https://store.steampowered.com/search/results/"
            params = {
                'query': '',
                'start': 0,
                'count': 50,
                'dynamic_data': '',
                'sort_by': '_ASC',
                'maxprice': 'free',
                'category1': 998,
                'infinitescroll': 'false',
                'cc': 'US',
                'l': 'english'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Steam request failed with status {response.status}")
                    return games
                
                data = await response.json()
                html_content = data.get('results_html', '')
                
                if not html_content:
                    return games
                
                soup = BeautifulSoup(html_content, 'html.parser')
                game_containers = soup.find_all('a', class_='search_result_row')
                
                for container in game_containers[:10]:  # Ограничиваем до 10
                    game_info = await self._parse_steam_free_game(container)
                    if game_info:
                        games.append(game_info)
                        
        except Exception as e:
            logger.error(f"Error getting Steam free games: {e}")
        
        return games
    
    async def _parse_steam_free_game(self, container) -> Optional[Dict]:
        """Парсинг информации о бесплатной игре Steam"""
        try:
            # Название игры
            title_elem = container.find('span', class_='title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # URL игры
            game_url = container.get('href', '')
            
            # Проверяем что игра действительно бесплатная
            price_elem = container.find('div', class_='search_price')
            if not price_elem or 'free' not in price_elem.get_text(strip=True).lower():
                return None
            
            # Дата релиза
            release_elem = container.find('div', class_='search_released')
            release_date = release_elem.get_text(strip=True) if release_elem else "Неизвестно"
            
            return {
                'title': title,
                'description': f'Бесплатная игра в Steam',
                'platform': 'Steam',
                'url': game_url,
                'end_date': 'Навсегда',
                'image_url': '',
                'release_date': release_date
            }
            
        except Exception as e:
            logger.error(f"Error parsing Steam game: {e}")
            return None
    
    async def _get_epic_free_games(self) -> List[Dict]:
        """Получение бесплатных игр из Epic Games Store"""
        games = []
        try:
            # Epic Games Store API для еженедельных раздач
            url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
            params = {
                'locale': 'en-US',
                'country': 'US',
                'allowCountries': 'US'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Epic Games request failed with status {response.status}")
                    return games
                
                data = await response.json()
                elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
                
                for game in elements:
                    if not game.get('promotions'):
                        continue
                    
                    # Проверяем актуальные промо-акции
                    promotions = game.get('promotions', {}).get('promotionalOffers', [])
                    upcoming = game.get('promotions', {}).get('upcomingPromotionalOffers', [])
                    
                    if promotions or upcoming:
                        game_info = self._parse_epic_game(game, promotions, upcoming)
                        if game_info:
                            games.append(game_info)
                            
        except Exception as e:
            logger.error(f"Error getting Epic Games free games: {e}")
        
        return games
    
    def _parse_epic_game(self, game_data: Dict, promotions: List, upcoming: List) -> Optional[Dict]:
        """Парсинг информации об игре Epic Games"""
        try:
            title = game_data.get('title', 'Неизвестная игра')
            description = game_data.get('description', 'Описание отсутствует')
            
            # URL игры
            product_slug = game_data.get('productSlug', '')
            game_url = f"https://store.epicgames.com/en-US/p/{product_slug}" if product_slug else ""
            
            # Изображение
            key_images = game_data.get('keyImages', [])
            image_url = ""
            for img in key_images:
                if img.get('type') == 'DieselStoreFrontWide':
                    image_url = img.get('url', '')
                    break
            
            # Определяем статус раздачи
            if promotions:
                # Текущая раздача
                promo = promotions[0].get('promotionalOffers', [{}])[0]
                end_date = promo.get('endDate', '')
                if end_date:
                    try:
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        end_date = end_dt.strftime('%d.%m.%Y %H:%M')
                    except:
                        end_date = "Скоро закончится"
                status = "🔥 Доступна сейчас"
            elif upcoming:
                # Предстоящая раздача
                promo = upcoming[0].get('promotionalOffers', [{}])[0]
                start_date = promo.get('startDate', '')
                if start_date:
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        start_date = start_dt.strftime('%d.%m.%Y %H:%M')
                        end_date = f"С {start_date}"
                    except:
                        end_date = "Скоро будет доступна"
                else:
                    end_date = "Скоро будет доступна"
                status = "⏳ Скоро будет доступна"
            else:
                return None
            
            return {
                'title': title,
                'description': f'{status} - {description[:100]}...' if len(description) > 100 else f'{status} - {description}',
                'platform': 'Epic Games Store',
                'url': game_url,
                'end_date': end_date,
                'image_url': image_url
            }
            
        except Exception as e:
            logger.error(f"Error parsing Epic game: {e}")
            return None
    
    async def _get_gog_free_games(self) -> List[Dict]:
        """Получение бесплатных игр из GOG"""
        games = []
        try:
            # GOG API для бесплатных игр
            url = "https://www.gog.com/games/ajax/filtered"
            params = {
                'mediaType': 'game',
                'price': 'free',
                'page': 1,
                'sort': 'popularity'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"GOG request failed with status {response.status}")
                    return games
                
                data = await response.json()
                products = data.get('products', [])
                
                for product in products[:5]:  # Ограничиваем до 5
                    game_info = self._parse_gog_game(product)
                    if game_info:
                        games.append(game_info)
                        
        except Exception as e:
            logger.error(f"Error getting GOG free games: {e}")
        
        return games
    
    def _parse_gog_game(self, product: Dict) -> Optional[Dict]:
        """Парсинг информации об игре GOG"""
        try:
            title = product.get('title', 'Неизвестная игра')
            
            # URL игры
            slug = product.get('slug', '')
            game_url = f"https://www.gog.com/game/{slug}" if slug else ""
            
            # Проверяем что игра бесплатная
            price = product.get('price', {})
            if not price.get('isFree', False):
                return None
            
            # Изображение
            image = product.get('image', '')
            image_url = f"https:{image}" if image and image.startswith('//') else image
            
            return {
                'title': title,
                'description': 'Бесплатная игра на GOG',
                'platform': 'GOG',
                'url': game_url,
                'end_date': 'Навсегда',
                'image_url': image_url
            }
            
        except Exception as e:
            logger.error(f"Error parsing GOG game: {e}")
            return None

# Дополнительный парсер для сайтов с информацией о раздачах
class FreeGamesScraper:
    """Дополнительный скрапер для получения информации о раздачах"""
    
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    async def get_freebies_info(self) -> List[Dict]:
        """Получение информации о раздачах с тематических сайтов"""
        games = []
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20),
                headers={'User-Agent': self.user_agent}
            ) as session:
                
                # Пример дополнительных источников (если доступны)
                additional_games = [
                    {
                        'title': 'Постоянные бесплатные игры',
                        'description': 'Dota 2, CS2, Team Fortress 2, Warframe',
                        'platform': 'Steam',
                        'url': 'https://store.steampowered.com/genre/Free%20to%20Play/',
                        'end_date': 'Навсегда',
                        'image_url': ''
                    },
                    {
                        'title': 'Fortnite',
                        'description': 'Популярная королевская битва',
                        'platform': 'Epic Games Store',
                        'url': 'https://store.epicgames.com/en-US/p/fortnite',
                        'end_date': 'Навсегда',
                        'image_url': ''
                    }
                ]
                
                games.extend(additional_games)
                
        except Exception as e:
            logger.error(f"Error getting additional freebies: {e}")
        
        return games
