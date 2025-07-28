"""
Модуль для работы с Steam Wishlist
Парсит список желаемых игр пользователя и проверяет скидки на них
"""
import aiohttp
import asyncio
import re
import logging
from typing import List, Dict, Optional
from config import WISHLIST_MAX_GAMES_CHECK, WISHLIST_CHECK_DELAY, WISHLIST_ENABLE_FULL_CHECK

logger = logging.getLogger(__name__)

class SteamWishlistParser:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def extract_steam_id(self, profile_url: str) -> Optional[str]:
        """Извлекает Steam ID из URL профиля"""
        try:
            # Паттерны для разных типов Steam URL
            patterns = [
                r'steamcommunity\.com/id/([^/]+)',  # Кастомный URL
                r'steamcommunity\.com/profiles/(\d+)',  # Числовой ID
            ]
            
            for pattern in patterns:
                match = re.search(pattern, profile_url)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting Steam ID: {e}")
            return None
    
    async def resolve_steam_id(self, identifier: str) -> Optional[str]:
        """Преобразует кастомный URL в Steam ID64"""
        try:
            # Если это уже Steam ID64 (17 цифр)
            if identifier.isdigit() and len(identifier) == 17:
                return identifier
            
            # Если это кастомный URL, пробуем получить Steam ID64
            url = f"https://steamcommunity.com/id/{identifier}/?xml=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Проверяем есть ли ошибка в ответе
                    if 'The specified profile could not be found' in content:
                        logger.error(f"Profile not found: {identifier}")
                        return None
                    
                    match = re.search(r'<steamID64>(\d+)</steamID64>', content)
                    if match:
                        steam_id64 = match.group(1)
                        logger.info(f"Resolved {identifier} to Steam ID64: {steam_id64}")
                        return steam_id64
                    else:
                        logger.error(f"Could not find Steam ID64 in XML response for: {identifier}")
                        return None
                else:
                    logger.error(f"Failed to resolve Steam ID: HTTP {response.status}")
                    return None
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout resolving Steam ID: {identifier}")
            return None
        except Exception as e:
            logger.error(f"Error resolving Steam ID: {e}")
            return None
    
    async def check_wishlist_accessibility(self, steam_id64: str) -> bool:
        """Проверяет доступность wishlist профиля"""
        try:
            # Сначала проверяем основную страницу wishlist
            url = f"https://store.steampowered.com/wishlist/profiles/{steam_id64}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=15, allow_redirects=False) as response:
                logger.info(f"Wishlist page status: {response.status} for Steam ID64: {steam_id64}")
                
                if response.status == 200:
                    content = await response.text()
                    
                    # Более детальная проверка содержимого страницы
                    if 'This profile is private' in content:
                        logger.error(f"❌ Profile is private for Steam ID64: {steam_id64}")
                        return False
                    elif 'The specified profile could not be found' in content:
                        logger.error(f"❌ Profile not found for Steam ID64: {steam_id64}")
                        return False
                    elif 'wishlist_ctn' in content or 'wishlist' in content.lower():
                        # Проверяем, есть ли игры в wishlist или он пустой
                        if 'Your Wishlist is empty' in content or 'wishlist is empty' in content.lower():
                            logger.info(f"📋 Wishlist is empty for Steam ID64: {steam_id64}")
                            return True  # Доступен, но пустой
                        elif 'wishlist_row' in content or 'game' in content.lower():
                            logger.info(f"✅ Wishlist accessible with games for Steam ID64: {steam_id64}")
                            return True
                        else:
                            logger.info(f"🔍 Wishlist page accessible but content unclear for Steam ID64: {steam_id64}")
                            return True  # Попробуем обратиться к API
                    elif 'Community :: Error' in content:
                        logger.error(f"❌ Steam Community error for Steam ID64: {steam_id64}")
                        return False
                    elif 'Access Denied' in content:
                        logger.error(f"❌ Access denied to wishlist for Steam ID64: {steam_id64}")
                        return False
                    else:
                        logger.warning(f"⚠️ Unexpected wishlist page content for Steam ID64: {steam_id64}")
                        logger.debug(f"Content preview: {content[:300]}")
                        return True  # Попробуем обратиться к API
                        
                elif response.status in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get('Location', 'Unknown')
                    logger.error(f"🔄 Wishlist page redirected to: {redirect_url}")
                    
                    # Проверяем, куда именно идет редирект
                    if 'steamcommunity.com' in redirect_url:
                        logger.error(f"❌ Redirected to Steam Community - profile/wishlist likely private")
                    elif 'store.steampowered.com' in redirect_url and 'login' in redirect_url:
                        logger.error(f"❌ Redirected to Steam login - authentication required")
                    else:
                        logger.error(f"❌ Unexpected redirect destination")
                    return False
                elif response.status == 403:
                    logger.error(f"❌ Forbidden (403) - wishlist access denied for Steam ID64: {steam_id64}")
                    return False
                elif response.status == 404:
                    logger.error(f"❌ Not found (404) - profile doesn't exist for Steam ID64: {steam_id64}")
                    return False
                elif response.status == 429:
                    logger.error(f"⏱️ Rate limited (429) - too many requests for Steam ID64: {steam_id64}")
                    return False
                else:
                    logger.warning(f"⚠️ Wishlist page returned status {response.status} for Steam ID64: {steam_id64}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error checking wishlist accessibility for {steam_id64}: {e}")
            return False

    async def get_wishlist_data(self, steam_id: str) -> List[Dict]:
        """Получает данные wishlist пользователя через официальный Steam API"""
        try:
            steam_id64 = await self.resolve_steam_id(steam_id)
            if not steam_id64:
                logger.error(f"Could not resolve Steam ID for: {steam_id}")
                return []
            
            logger.info(f"🔍 Getting wishlist for Steam ID64: {steam_id64}")
            
            # Сначала пробуем официальный Steam Web API
            wishlist_data = await self.get_wishlist_via_api(steam_id64)
            if wishlist_data:
                logger.info(f"✅ Successfully retrieved wishlist via official API with {len(wishlist_data)} games")
                return wishlist_data
            
            logger.info(f"🔄 Official API failed, trying fallback methods...")
            
            # Если официальный API не сработал, пробуем старый метод
            return await self.get_wishlist_legacy(steam_id64)
                    
        except Exception as e:
            logger.error(f"❌ Error getting wishlist data for {steam_id}: {e}")
            return []

    async def get_wishlist_via_api(self, steam_id64: str) -> List[Dict]:
        """Получает wishlist через официальный Steam Web API"""
        try:
            # Пробуем получить wishlist через официальный API
            # Примечание: Для некоторых методов может потребоваться API ключ
            
            # Сначала пробуем GetWishlist без ключа (может работать для публичных профилей)
            url = f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/"
            
            params = {
                'steamid': steam_id64,
                'format': 'json'
            }
            
            headers = {
                'User-Agent': 'Steam App / Wishlist Checker',
                'Accept': 'application/json'
            }
            
            async with self.session.get(url, params=params, headers=headers, timeout=15) as response:
                logger.info(f"🌐 Official API response: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        
                        # Проверяем структуру ответа
                        if 'response' in data:
                            response_data = data['response']
                            
                            if 'items' in response_data:
                                items = response_data['items']
                                if items:
                                    logger.info(f"📋 Found {len(items)} items in wishlist via official API")
                                    return await self.parse_api_wishlist_data(items)
                                else:
                                    logger.info(f"📭 Wishlist is empty (official API)")
                                    return []
                            else:
                                logger.warning(f"⚠️ No 'items' field in API response")
                                logger.debug(f"API response: {data}")
                        else:
                            logger.warning(f"⚠️ Unexpected API response structure")
                            logger.debug(f"API response: {data}")
                            
                    except Exception as json_error:
                        logger.error(f"❌ JSON decode error from official API: {json_error}")
                        text_content = await response.text()
                        logger.debug(f"API response text: {text_content[:500]}")
                        
                elif response.status == 401:
                    logger.warning(f"🔐 Official API requires authentication (401)")
                elif response.status == 403:
                    logger.warning(f"🚫 Access forbidden via official API (403) - profile may be private")
                elif response.status == 429:
                    logger.warning(f"⏱️ Rate limited by official API (429)")
                else:
                    logger.warning(f"⚠️ Official API returned status {response.status}")
            
            # Если прямой вызов не сработал, пробуем другие endpoint'ы
            logger.info(f"🔄 Trying alternative official API endpoints...")
            
            # Пробуем GetWishlistItemCount для проверки доступности
            count_url = f"https://api.steampowered.com/IWishlistService/GetWishlistItemCount/v1/"
            count_params = {
                'steamid': steam_id64,
                'format': 'json'
            }
            
            async with self.session.get(count_url, params=count_params, headers=headers, timeout=10) as count_response:
                if count_response.status == 200:
                    try:
                        count_data = await count_response.json()
                        if 'response' in count_data and 'count' in count_data['response']:
                            item_count = count_data['response']['count']
                            logger.info(f"📊 Wishlist contains {item_count} items (via count API)")
                            
                            if item_count == 0:
                                return []  # Пустой wishlist
                        else:
                            logger.debug(f"Count API response: {count_data}")
                    except:
                        pass
                        
            return []  # Официальный API не сработал
            
        except Exception as e:
            logger.error(f"❌ Error with official Steam API: {e}")
            return []

    async def parse_api_wishlist_data(self, items: List[Dict]) -> List[Dict]:
        """Парсит данные wishlist из официального API"""
        games = []
        
        try:
            for item in items:
                # Структура данных из официального API может отличаться
                app_id = str(item.get('appid', ''))
                
                if app_id:
                    game_name = item.get('name', '')
                    
                    # Если нет названия, попробуем получить его через Steam Store API
                    if not game_name or game_name == 'Unknown Game':
                        game_name = await self.get_game_name(app_id)
                    
                    game = {
                        'app_id': app_id,
                        'name': game_name or 'Unknown Game',
                        'capsule': item.get('capsule', ''),
                        'review_score': item.get('review_score', 0),
                        'review_desc': item.get('review_desc', ''),
                        'reviews_total': str(item.get('reviews_total', '0')),
                        'reviews_percent': item.get('reviews_percent', 0),
                        'release_date': item.get('release_date', ''),
                        'release_string': item.get('release_string', ''),
                        'platform_icons': item.get('platform_icons', ''),
                        'subs': item.get('subs', []),
                        'type': item.get('type', ''),
                        'screenshots': item.get('screenshots', []),
                        'review_css': item.get('review_css', ''),
                        'priority': item.get('priority', 0),
                        'added': item.get('date_added', item.get('added', 0)),
                        'background': item.get('background', ''),
                        'rank': item.get('rank', 0),
                        'tags': item.get('tags', []),
                        'is_free_game': item.get('is_free_game', False),
                        'win': item.get('win', 0)
                    }
                    games.append(game)
                    
        except Exception as e:
            logger.error(f"❌ Error parsing API wishlist data: {e}")
            
        return games

    async def get_game_name(self, app_id: str) -> Optional[str]:
        """Получает название игры по app_id"""
        try:
            if not app_id or not str(app_id).isdigit():
                return None
                
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=basic"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        
                        if isinstance(data, dict) and app_id in data:
                            app_data = data[app_id]
                            
                            if isinstance(app_data, dict) and app_data.get('success'):
                                game_data = app_data.get('data', {})
                                game_name = game_data.get('name', '')
                                
                                if game_name:
                                    logger.debug(f"📋 Got game name for {app_id}: {game_name}")
                                    return game_name
                                    
                    except Exception as json_error:
                        logger.debug(f"⚠️ Error parsing game name for {app_id}: {json_error}")
                        
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Error getting game name for {app_id}: {e}")
            return None

    async def get_wishlist_legacy(self, steam_id64: str) -> List[Dict]:
        """Получает wishlist через старый метод (fallback)"""
        try:
            logger.info(f"🔄 Using legacy wishlist method for Steam ID64: {steam_id64}")
            
            # Сначала проверяем доступность wishlist
            is_accessible = await self.check_wishlist_accessibility(steam_id64)
            if not is_accessible:
                logger.error(f"❌ Wishlist is not accessible for Steam ID64: {steam_id64}")
                # Попробуем все равно обратиться к API - иногда страница недоступна, но API работает
                logger.info(f"🔄 Attempting direct API access despite accessibility check failure...")
            
            # URL для получения wishlist
            url = f"https://store.steampowered.com/wishlist/profiles/{steam_id64}/wishlistdata/"
            logger.info(f"🌐 Requesting wishlist from: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Referer': f'https://store.steampowered.com/wishlist/profiles/{steam_id64}/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            async with self.session.get(url, headers=headers, timeout=30, allow_redirects=False) as response:
                logger.info(f"📡 Legacy response status: {response.status}, content-type: {response.content_type}")
                
                # Проверяем на редиректы
                if response.status in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get('Location', 'Unknown')
                    logger.error(f"🔄 Wishlist request redirected to: {redirect_url}")
                    logger.error(f"❌ This usually means the profile is private or wishlist is not accessible")
                    return []
                
                if response.status == 200:
                    content_type = response.content_type
                    
                    # Проверяем тип контента
                    if 'application/json' in content_type or 'text/javascript' in content_type:
                        try:
                            data = await response.json()
                            if isinstance(data, dict):
                                if data:  # Не пустой словарь
                                    logger.info(f"✅ Successfully retrieved wishlist with {len(data)} games (legacy method)")
                                    return self.parse_wishlist_data(data)
                                else:
                                    logger.info(f"📭 Wishlist is empty for Steam ID: {steam_id64}")
                                    return []
                            else:
                                logger.error(f"❌ Unexpected data format: {type(data)}")
                                return []
                        except Exception as json_error:
                            logger.error(f"❌ JSON decode error: {json_error}")
                            # Попробуем получить текст ответа для диагностики
                            text_content = await response.text()
                            logger.error(f"📄 Response text (first 500 chars): {text_content[:500]}")
                            return []
                    else:
                        # Получили HTML вместо JSON
                        text_content = await response.text()
                        
                        # Проверяем специфические случаи
                        if 'This profile is private' in text_content:
                            logger.error(f"🔒 Profile is private for Steam ID: {steam_id64}")
                        elif 'profile could not be found' in text_content:
                            logger.error(f"❌ Profile not found for Steam ID: {steam_id64}")
                        elif 'Welcome to Steam' in text_content:
                            logger.error(f"🏠 Redirected to Steam homepage - wishlist likely private or inaccessible for Steam ID: {steam_id64}")
                        elif 'Access Denied' in text_content:
                            logger.error(f"🚫 Access denied to wishlist for Steam ID: {steam_id64}")
                        elif 'login' in text_content.lower():
                            logger.error(f"🔐 Redirected to login page - authentication required for Steam ID: {steam_id64}")
                        else:
                            logger.error(f"❌ Unexpected HTML response for Steam ID: {steam_id64}")
                            logger.error(f"📄 Response text (first 500 chars): {text_content[:500]}")
                        
                        # Попробуем альтернативный метод получения wishlist
                        logger.info(f"🔄 Trying alternative wishlist access method...")
                        return await self.get_wishlist_alternative(steam_id64)
                        
                elif response.status == 403:
                    logger.error(f"🚫 Access forbidden (403) - profile/wishlist is private: {steam_id64}")
                    return []
                elif response.status == 404:
                    logger.error(f"❌ Profile not found (404): {steam_id64}")
                    return []
                elif response.status == 429:
                    logger.error(f"⏱️ Rate limited (429) - too many requests for Steam ID: {steam_id64}")
                    return []
                else:
                    logger.error(f"❌ Failed to get wishlist data: HTTP {response.status} for Steam ID: {steam_id64}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout getting wishlist data for: {steam_id64}")
            return []
        except Exception as e:
            logger.error(f"❌ Error getting wishlist data for {steam_id64}: {e}")
            return []
    
    async def get_wishlist_alternative(self, steam_id64: str) -> List[Dict]:
        """Альтернативный метод получения wishlist через Steam Community API"""
        try:
            logger.info(f"Trying alternative wishlist method for Steam ID64: {steam_id64}")
            
            # Пробуем другой endpoint
            url = f"https://steamcommunity.com/profiles/{steam_id64}/wishlist/?xml=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Парсим XML ответ
                    games = []
                    import xml.etree.ElementTree as ET
                    
                    try:
                        root = ET.fromstring(content)
                        
                        # Проверяем, есть ли ошибки
                        error_elem = root.find('.//error')
                        if error_elem is not None:
                            logger.error(f"Steam Community API error: {error_elem.text}")
                            return []
                        
                        # Ищем игры в wishlist
                        game_elements = root.findall('.//game')
                        for game_elem in game_elements:
                            app_id = game_elem.find('appID')
                            name = game_elem.find('name')
                            
                            if app_id is not None and name is not None:
                                game = {
                                    'app_id': app_id.text,
                                    'name': name.text,
                                    'capsule': '',
                                    'review_score': 0,
                                    'review_desc': '',
                                    'reviews_total': '0',
                                    'reviews_percent': 0,
                                    'release_date': '',
                                    'release_string': '',
                                    'platform_icons': '',
                                    'subs': [],
                                    'type': '',
                                    'screenshots': [],
                                    'review_css': '',
                                    'priority': 0,
                                    'added': 0,
                                    'background': '',
                                    'rank': 0,
                                    'tags': [],
                                    'is_free_game': False,
                                    'win': 0
                                }
                                games.append(game)
                        
                        if games:
                            logger.info(f"Alternative method found {len(games)} games in wishlist")
                            return games
                        else:
                            logger.info(f"Alternative method: wishlist appears to be empty")
                            return []
                            
                    except ET.ParseError as xml_error:
                        logger.error(f"XML parsing error: {xml_error}")
                        logger.debug(f"Content preview: {content[:500]}")
                        return []
                        
                else:
                    logger.warning(f"Alternative method failed with status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error in alternative wishlist method: {e}")
            return []
    
    def parse_wishlist_data(self, data: Dict) -> List[Dict]:
        """Парсит данные wishlist"""
        games = []
        
        try:
            for app_id, game_data in data.items():
                game = {
                    'app_id': app_id,
                    'name': game_data.get('name', 'Unknown Game'),
                    'capsule': game_data.get('capsule', ''),
                    'review_score': game_data.get('review_score', 0),
                    'review_desc': game_data.get('review_desc', ''),
                    'reviews_total': game_data.get('reviews_total', '0'),
                    'reviews_percent': game_data.get('reviews_percent', 0),
                    'release_date': game_data.get('release_date', ''),
                    'release_string': game_data.get('release_string', ''),
                    'platform_icons': game_data.get('platform_icons', ''),
                    'subs': game_data.get('subs', []),
                    'type': game_data.get('type', ''),
                    'screenshots': game_data.get('screenshots', []),
                    'review_css': game_data.get('review_css', ''),
                    'priority': game_data.get('priority', 0),
                    'added': game_data.get('added', 0),
                    'background': game_data.get('background', ''),
                    'rank': game_data.get('rank', 0),
                    'tags': game_data.get('tags', []),
                    'is_free_game': game_data.get('is_free_game', False),
                    'win': game_data.get('win', 0)
                }
                games.append(game)
                
        except Exception as e:
            logger.error(f"Error parsing wishlist data: {e}")
            
        return games
    
    async def check_wishlist_discounts(self, steam_id: str) -> List[Dict]:
        """Получает игры из wishlist со скидками"""
        try:
            steam_id64 = await self.resolve_steam_id(steam_id)
            if not steam_id64:
                logger.error(f"Could not resolve Steam ID for: {steam_id}")
                return []
            
            logger.info(f"🔍 Checking discounts for Steam ID64: {steam_id64}")
            
            # Сначала пробуем официальный API для получения скидок
            discounted_games = await self.get_wishlist_discounts_via_api(steam_id64)
            if discounted_games:
                logger.info(f"✅ Found {len(discounted_games)} games with discounts via official API")
                return discounted_games
            
            logger.info(f"🔄 Official API didn't return discounts, trying legacy method...")
            
            # Fallback на старый метод
            wishlist_games = await self.get_wishlist_data(steam_id)
            
            if not wishlist_games:
                logger.info(f"📭 No wishlist games found for Steam ID: {steam_id}")
                return []
            
            logger.info(f"📋 Found {len(wishlist_games)} games in wishlist")
            
            # Получаем информацию о ценах для каждой игры
            discounted_games = []
            
            # Используем настройки из config.py для fallback метода
            if WISHLIST_ENABLE_FULL_CHECK:
                max_games_to_check = len(wishlist_games)
                logger.info(f"🌟 FALLBACK FULL CHECK MODE: Will check ALL {max_games_to_check} games for discounts!")
            else:
                max_games_to_check = min(WISHLIST_MAX_GAMES_CHECK, len(wishlist_games))
                logger.info(f"🎯 FALLBACK LIMITED CHECK MODE: Will check {max_games_to_check} out of {len(wishlist_games)} games for discounts")
            
            check_delay = WISHLIST_CHECK_DELAY + 0.1  # Немного больше задержка для fallback
            
            for i, game in enumerate(wishlist_games[:max_games_to_check]):
                app_id = game['app_id']
                game_name = game.get('name', 'Unknown')
                logger.info(f"🔍 Checking price for game {i+1}/{max_games_to_check}: {game_name} (ID: {app_id})")
                
                try:
                    price_info = await self.get_game_price_info(app_id)
                    
                    if price_info and price_info.get('discount_percent', 0) > 0:
                        game.update(price_info)
                        discounted_games.append(game)
                        
                        discount = price_info.get('discount_percent', 0)
                        final_price = price_info.get('final_formatted', 'N/A')
                        logger.info(f"🎉 FOUND DISCOUNT: {game_name} - {discount}% off, now {final_price}!")
                    else:
                        logger.debug(f"💸 No discount for {game_name}")
                    
                    # Используем настраиваемую задержку между запросами
                    if i < max_games_to_check - 1:
                        await asyncio.sleep(check_delay)
                        
                        # Показываем прогресс каждые 25 игр
                        if (i + 1) % 25 == 0:
                            logger.info(f"🔄 FALLBACK Progress: {i+1}/{max_games_to_check} games checked, {len(discounted_games)} discounts found so far")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error checking price for {game_name}: {e}")
                    continue
            
            logger.info(f"✅ FINAL RESULT: Found {len(discounted_games)} games with discounts (fallback method)!")
            
            # Логируем найденные скидки
            if discounted_games:
                logger.info(f"🎁 GAMES ON SALE (FALLBACK):")
                for i, game in enumerate(discounted_games):
                    discount = game.get('discount_percent', 0)
                    price = game.get('final_formatted', 'N/A')
                    logger.info(f"  {i+1}. {game.get('name', 'Unknown')} - {discount}% off, {price}")
            else:
                logger.info(f"😞 No games from wishlist are currently on sale (fallback)")
            
            return discounted_games
            
        except Exception as e:
            logger.error(f"❌ Error checking wishlist discounts: {e}")
            return []

    async def get_wishlist_discounts_via_api(self, steam_id64: str) -> List[Dict]:
        """Получает игры со скидками через официальный Steam API"""
        try:
            logger.info(f"🛍️ Trying to get discounted wishlist items for Steam ID64: {steam_id64}")
            
            # Сначала получаем весь wishlist через API
            wishlist_items = await self.get_wishlist_via_api(steam_id64)
            if not wishlist_items:
                logger.info(f"📭 No wishlist items found via API")
                return []
            
            logger.info(f"📋 Got {len(wishlist_items)} wishlist items, checking for discounts...")
            
            # Проверяем игры на скидки через обычный API Steam Store
            discounted_games = []
            
            # Используем настройки из config.py
            if WISHLIST_ENABLE_FULL_CHECK:
                max_games_to_check = len(wishlist_items)  # Проверяем ВСЕ игры
                logger.info(f"🌟 FULL CHECK MODE: Will check ALL {max_games_to_check} games for discounts!")
            else:
                max_games_to_check = min(WISHLIST_MAX_GAMES_CHECK, len(wishlist_items))
                logger.info(f"🎯 LIMITED CHECK MODE: Will check {max_games_to_check} out of {len(wishlist_items)} games for discounts")
            
            check_delay = WISHLIST_CHECK_DELAY
            
            for i, game in enumerate(wishlist_items[:max_games_to_check]):
                app_id = game.get('app_id', '')
                game_name = game.get('name', 'Unknown Game')
                
                if not app_id:
                    logger.debug(f"⚠️ Skipping game {i+1}: no app_id")
                    continue
                
                logger.info(f"🔍 Checking discounts for {i+1}/{max_games_to_check}: {game_name} (ID: {app_id})")
                
                try:
                    price_info = await self.get_game_price_info(app_id)
                    
                    if price_info and price_info.get('discount_percent', 0) > 0:
                        # Объединяем данные игры с информацией о цене
                        discounted_game = game.copy()
                        discounted_game.update(price_info)
                        discounted_games.append(discounted_game)
                        
                        discount = price_info.get('discount_percent', 0)
                        final_price = price_info.get('final_formatted', 'N/A')
                        logger.info(f"🎉 FOUND DISCOUNT: {game_name} - {discount}% off, now {final_price}!")
                    else:
                        logger.debug(f"💸 No discount for {game_name}")
                    
                    # Используем настраиваемую задержку между запросами
                    if i < max_games_to_check - 1:
                        await asyncio.sleep(check_delay)
                        
                        # Показываем прогресс каждые 25 игр
                        if (i + 1) % 25 == 0:
                            logger.info(f"🔄 Progress: {i+1}/{max_games_to_check} games checked, {len(discounted_games)} discounts found so far")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error checking price for {game_name}: {e}")
                    continue
            
            logger.info(f"✅ FINAL RESULT: Found {len(discounted_games)} games with discounts out of {max_games_to_check} checked!")
            
            # Логируем найденные скидки
            if discounted_games:
                logger.info(f"🎁 GAMES ON SALE:")
                for i, game in enumerate(discounted_games):
                    discount = game.get('discount_percent', 0)
                    price = game.get('final_formatted', 'N/A')
                    logger.info(f"  {i+1}. {game.get('name', 'Unknown')} - {discount}% off, {price}")
            else:
                logger.info(f"😞 No games from wishlist are currently on sale")
            
            return discounted_games
            
        except Exception as e:
            logger.error(f"❌ Error with API discounts method: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    async def get_game_price_info(self, app_id: str) -> Optional[Dict]:
        """Получает информацию о цене игры"""
        try:
            if not app_id or not str(app_id).isdigit():
                logger.warning(f"⚠️ Invalid app_id: {app_id}")
                return None
                
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=price_overview&cc=ru"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content_type = response.content_type
                    
                    if 'application/json' in content_type:
                        try:
                            data = await response.json()
                            
                            # Проверяем структуру ответа
                            if isinstance(data, dict) and app_id in data:
                                app_data = data[app_id]
                                
                                # Добавляем проверку типа app_data
                                if not isinstance(app_data, dict):
                                    logger.warning(f"⚠️ app_data for {app_id} is not dict: {type(app_data)} - {app_data}")
                                    return None
                                
                                if app_data.get('success'):
                                    game_data = app_data.get('data', {})
                                    
                                    # Проверяем тип game_data
                                    if not isinstance(game_data, dict):
                                        logger.warning(f"⚠️ game_data for {app_id} is not dict: {type(game_data)} - {game_data}")
                                        return None
                                        
                                    price_data = game_data.get('price_overview')
                                    
                                    if isinstance(price_data, dict):
                                        return {
                                            'currency': price_data.get('currency', 'RUB'),
                                            'initial_price': price_data.get('initial', 0),
                                            'final_price': price_data.get('final', 0),
                                            'discount_percent': price_data.get('discount_percent', 0),
                                            'initial_formatted': price_data.get('initial_formatted', ''),
                                            'final_formatted': price_data.get('final_formatted', ''),
                                            'url': f"https://store.steampowered.com/app/{app_id}/"
                                        }
                                    else:
                                        logger.debug(f"💰 No price_overview for app {app_id} (free game or not available)")
                                        return None
                                else:
                                    logger.debug(f"⚠️ API returned success=false for app {app_id}")
                                    return None
                            else:
                                logger.warning(f"⚠️ Unexpected data structure for app {app_id}: {type(data)}")
                                if isinstance(data, dict):
                                    logger.debug(f"Available keys: {list(data.keys())}")
                                return None
                                
                        except Exception as json_error:
                            logger.error(f"❌ JSON decode error for app {app_id}: {json_error}")
                            # Попробуем получить текст для диагностики
                            try:
                                text_content = await response.text()
                                logger.debug(f"Response text preview for app {app_id}: {text_content[:200]}")
                            except:
                                pass
                            return None
                    else:
                        logger.warning(f"⚠️ Unexpected content type for app {app_id}: {content_type}")
                        return None
                else:
                    logger.warning(f"⚠️ Failed to get price info for app {app_id}: HTTP {response.status}")
                    return None
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout getting price info for app {app_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting price info for {app_id}: {e}")
            import traceback
            logger.debug(f"Traceback for app {app_id}: {traceback.format_exc()}")
            return None

async def get_wishlist_discounts(profile_url: str) -> List[Dict]:
    """Основная функция для получения скидок из wishlist"""
    try:
        async with SteamWishlistParser() as parser:
            steam_id = parser.extract_steam_id(profile_url)
            if not steam_id:
                logger.error(f"Could not extract Steam ID from URL: {profile_url}")
                return []
            
            logger.info(f"Extracted Steam ID: {steam_id} from URL: {profile_url}")
            return await parser.check_wishlist_discounts(steam_id)
            
    except Exception as e:
        logger.error(f"Error in get_wishlist_discounts: {e}")
        return []
