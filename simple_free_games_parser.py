import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

class SimpleFreeGamesParser:
    """Упрощенный парсер для получения бесплатных игр"""
    
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    async def get_all_free_games(self) -> List[Dict]:
        """Получение всех доступных бесплатных игр"""
        free_games = []
        
        # Добавляем известные постоянно бесплатные игры
        permanent_free = self._get_permanent_free_games()
        free_games.extend(permanent_free)
        
        # Пытаемся получить данные из Epic Games Store
        try:
            epic_games = await self._get_epic_free_games_simple()
            free_games.extend(epic_games)
        except Exception as e:
            logger.error(f"Epic Games parsing failed: {e}")
        
        # Добавляем популярные F2P игры Steam
        steam_f2p = self._get_steam_f2p_games()
        free_games.extend(steam_f2p)
        
        return free_games
    
    def _get_permanent_free_games(self) -> List[Dict]:
        """Список постоянно бесплатных популярных игр"""
        return [
            {
                'title': 'Counter-Strike 2',
                'description': '🔥 Легендарный тактический шутер от Valve',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/730/CounterStrike_2/',
                'end_date': 'Навсегда',
                'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg'
            },
            {
                'title': 'Dota 2',
                'description': '⚔️ Популярная MOBA от создателей Steam',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/570/Dota_2/',
                'end_date': 'Навсегда',
                'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg'
            },
            {
                'title': 'Team Fortress 2',
                'description': '🎯 Командный шутер с уникальным стилем',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/440/Team_Fortress_2/',
                'end_date': 'Навсегда',
                'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg'
            },
            {
                'title': 'Warframe',
                'description': '🚀 Кооперативный шутер от третьего лица',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/230410/Warframe/',
                'end_date': 'Навсегда',
                'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/230410/header.jpg'
            },
            {
                'title': 'Fortnite',
                'description': '🏆 Популярная королевская битва',
                'platform': 'Epic Games Store',
                'url': 'https://store.epicgames.com/en-US/p/fortnite',
                'end_date': 'Навсегда',
                'image_url': ''
            }
        ]
    
    def _get_steam_f2p_games(self) -> List[Dict]:
        """Дополнительные популярные F2P игры Steam"""
        return [
            {
                'title': 'Apex Legends',
                'description': '🎮 Battle Royale от создателей Titanfall',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/1172470/Apex_Legends/',
                'end_date': 'Навсегда',
                'image_url': ''
            },
            {
                'title': 'Path of Exile',
                'description': '⚔️ Мрачная action-RPG',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/238960/Path_of_Exile/',
                'end_date': 'Навсегда',
                'image_url': ''
            },
            {
                'title': 'Lost Ark',
                'description': '🏛️ MMORPG с изометрическим видом',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/1599340/Lost_Ark/',
                'end_date': 'Навсегда',
                'image_url': ''
            }
        ]
    
    async def _get_epic_free_games_simple(self) -> List[Dict]:
        """Упрощенное получение бесплатных игр Epic Games"""
        games = []
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"
                params = {
                    'locale': 'en-US',
                    'country': 'US',
                    'allowCountries': 'US'
                }
                
                headers = {
                    'User-Agent': self.user_agent,
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache'
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            
                            # Проверяем структуру ответа
                            if data and 'data' in data:
                                catalog = data['data'].get('Catalog', {})
                                search_store = catalog.get('searchStore', {})
                                elements = search_store.get('elements', [])
                                
                                for element in elements:
                                    if self._has_free_promotion(element):
                                        game_info = self._parse_epic_game_simple(element)
                                        if game_info:
                                            games.append(game_info)
                                            
                        except Exception as parse_error:
                            logger.error(f"Error parsing Epic Games response: {parse_error}")
                    else:
                        logger.warning(f"Epic Games API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching Epic Games data: {e}")
        
        return games
    
    def _has_free_promotion(self, element: dict) -> bool:
        """Проверяет есть ли у игры бесплатная промо-акция"""
        try:
            promotions = element.get('promotions')
            if not promotions:
                return False
            
            current_promotions = promotions.get('promotionalOffers', [])
            upcoming_promotions = promotions.get('upcomingPromotionalOffers', [])
            
            return len(current_promotions) > 0 or len(upcoming_promotions) > 0
            
        except Exception:
            return False
    
    def _parse_epic_game_simple(self, element: dict) -> Optional[Dict]:
        """Простой парсинг игры Epic Games"""
        try:
            title = element.get('title', 'Неизвестная игра')
            description = element.get('description', 'Описание отсутствует')
            
            # URL игры
            url_slug = element.get('catalogNs', {}).get('mappings', [])
            game_url = "https://store.epicgames.com/en-US/free-games"
            if url_slug and len(url_slug) > 0:
                page_slug = url_slug[0].get('pageSlug', '')
                if page_slug:
                    game_url = f"https://store.epicgames.com/en-US/p/{page_slug}"
            
            # Определяем статус промо-акции
            promotions = element.get('promotions', {})
            current_promos = promotions.get('promotionalOffers', [])
            upcoming_promos = promotions.get('upcomingPromotionalOffers', [])
            
            if current_promos:
                end_date = "До конца недели"
                status = "🔥 Доступна сейчас"
            elif upcoming_promos:
                end_date = "Скоро будет доступна"
                status = "⏳ Ожидается"
            else:
                return None
            
            # Ограничиваем длину описания
            if len(description) > 100:
                description = description[:97] + "..."
            
            return {
                'title': title,
                'description': f'{status} - {description}',
                'platform': 'Epic Games Store',
                'url': game_url,
                'end_date': end_date,
                'image_url': ''
            }
            
        except Exception as e:
            logger.error(f"Error parsing Epic game: {e}")
            return None

# Функция для получения актуальной информации о раздачах
async def get_current_free_games() -> List[Dict]:
    """Главная функция для получения актуальных бесплатных игр"""
    parser = SimpleFreeGamesParser()
    
    try:
        games = await parser.get_all_free_games()
        
        # Сортируем: сначала Epic Games (временные акции), потом постоянные
        epic_games = [g for g in games if g['platform'] == 'Epic Games Store']
        other_games = [g for g in games if g['platform'] != 'Epic Games Store']
        
        return epic_games + other_games
        
    except Exception as e:
        logger.error(f"Error getting free games: {e}")
        return []

# Для обратной совместимости
FreeGamesParser = SimpleFreeGamesParser

class FreeGamesScraper:
    """Простой скрапер для дополнительной информации"""
    
    async def get_freebies_info(self) -> List[Dict]:
        """Получение дополнительной информации о раздачах"""
        return [
            {
                'title': 'Еженедельные раздачи Epic Games',
                'description': '🎁 Каждый четверг новая бесплатная игра',
                'platform': 'Epic Games Store',
                'url': 'https://store.epicgames.com/en-US/free-games',
                'end_date': 'Каждую неделю',
                'image_url': ''
            },
            {
                'title': 'Steam Free-to-Play',
                'description': '🎮 Сотни бесплатных игр разных жанров',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/genre/Free%20to%20Play/',
                'end_date': 'Навсегда',
                'image_url': ''
            }
        ]
