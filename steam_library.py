"""
Модуль для работы с библиотекой игр Steam
Получает список игр пользователя из публичного профиля
"""
import aiohttp
import asyncio
import re
import json
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SteamLibraryParser:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def extract_steam_id(self, profile_url: str) -> Optional[str]:
        """Извлекает Steam ID из URL профиля"""
        try:
            patterns = [
                r'steamcommunity\.com/id/([^/]+)',
                r'steamcommunity\.com/profiles/(\d+)',
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
            if identifier.isdigit() and len(identifier) == 17:
                return identifier
                
            # Попробуем получить Steam ID64 через страницу профиля
            profile_url = f"https://steamcommunity.com/id/{identifier}"
            
            async with self.session.get(profile_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Ищем Steam ID64 в скриптах или данных страницы
                    steam_id_match = re.search(r'"steamid":"(\d{17})"', content)
                    if steam_id_match:
                        return steam_id_match.group(1)
                    
                    # Альтернативный поиск
                    steam_id_match = re.search(r'g_steamID = "(\d{17})";', content)
                    if steam_id_match:
                        return steam_id_match.group(1)
                        
                    # Ищем в метаданных профиля
                    steam_id_match = re.search(r'data-steamid="(\d{17})"', content)
                    if steam_id_match:
                        return steam_id_match.group(1)
            
            logger.error(f"Could not resolve Steam ID for: {identifier}")
            return None
            
        except Exception as e:
            logger.error(f"Error resolving Steam ID: {e}")
            return None
    
    async def check_library_accessibility(self, steam_id64: str) -> bool:
        """Проверяет доступность библиотеки игр"""
        try:
            games_url = f"https://steamcommunity.com/profiles/{steam_id64}/games/?tab=all"
            
            async with self.session.get(games_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    if 'This profile is private' in content:
                        logger.error(f"❌ Profile is private for Steam ID64: {steam_id64}")
                        return False
                    elif 'The specified profile could not be found' in content:
                        logger.error(f"❌ Profile not found for Steam ID64: {steam_id64}")
                        return False
                    elif 'This user has not yet set up their Steam Community profile' in content:
                        logger.error(f"❌ Profile not set up for Steam ID64: {steam_id64}")
                        return False
                    elif 'game_name' in content or 'gameListRow' in content:
                        logger.info(f"✅ Game library accessible for Steam ID64: {steam_id64}")
                        return True
                    elif 'no games' in content.lower() or 'This user has no games' in content:
                        logger.info(f"📋 Game library is empty for Steam ID64: {steam_id64}")
                        return True  # Доступен, но пустой
                    else:
                        logger.warning(f"⚠️ Unexpected games page content for Steam ID64: {steam_id64}")
                        return True  # Попробуем получить данные
                        
                elif response.status in [403, 401]:
                    logger.error(f"❌ Access denied to game library for Steam ID64: {steam_id64}")
                    return False
                elif response.status == 404:
                    logger.error(f"❌ Games page not found for Steam ID64: {steam_id64}")
                    return False
                else:
                    logger.error(f"❌ HTTP {response.status} when accessing games for Steam ID64: {steam_id64}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking library accessibility: {e}")
            return False
    
    async def get_owned_games(self, steam_id64: str, limit: int = 50) -> List[Dict]:
        """Получает список игр пользователя"""
        try:
            logger.info(f"Getting owned games for Steam ID64: {steam_id64}")
            
            # Сначала проверим доступность
            if not await self.check_library_accessibility(steam_id64):
                return []
            
            games = []
            
            # Метод 1: Парсинг страницы всех игр
            games_data = await self._parse_games_page(steam_id64)
            if games_data:
                games.extend(games_data)
            
            # Если мало игр, попробуем другие методы
            if len(games) < 10:
                # Метод 2: Парсинг через AJAX
                ajax_games = await self._parse_games_ajax(steam_id64)
                if ajax_games:
                    # Объединяем, избегая дубликатов
                    existing_ids = {g.get('appid') for g in games}
                    for game in ajax_games:
                        if game.get('appid') not in existing_ids:
                            games.append(game)
            
            # Ограничиваем количество и сортируем по времени игры
            games = sorted(games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
            
            logger.info(f"Found {len(games)} games for Steam ID64: {steam_id64}")
            return games[:limit]
            
        except Exception as e:
            logger.error(f"Error getting owned games: {e}")
            return []
    
    async def _parse_games_page(self, steam_id64: str) -> List[Dict]:
        """Парсит страницу с играми пользователя"""
        try:
            games_url = f"https://steamcommunity.com/profiles/{steam_id64}/games/?tab=all"
            
            async with self.session.get(games_url) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                games = []
                
                # Ищем JavaScript данные с играми
                script_match = re.search(r'var rgGames = (\[.*?\]);', content, re.DOTALL)
                if script_match:
                    try:
                        games_json = script_match.group(1)
                        games_data = json.loads(games_json)
                        
                        for game in games_data:
                            if isinstance(game, dict):
                                game_info = {
                                    'appid': game.get('appid'),
                                    'name': game.get('name', '').strip(),
                                    'playtime_forever': game.get('hours_forever', '0').replace(',', ''),
                                    'playtime_2weeks': game.get('hours', '0').replace(',', ''),
                                    'img_icon_url': game.get('logo', ''),
                                    'has_community_visible_stats': True
                                }
                                
                                # Конвертируем время в минуты
                                try:
                                    playtime_str = str(game_info['playtime_forever']).replace(',', '')
                                    if playtime_str and playtime_str != '0':
                                        # Время указано в часах, конвертируем в минуты
                                        game_info['playtime_forever'] = int(float(playtime_str) * 60)
                                    else:
                                        game_info['playtime_forever'] = 0
                                except:
                                    game_info['playtime_forever'] = 0
                                
                                if game_info['name']:  # Только если есть название
                                    games.append(game_info)
                        
                        return games
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing games JSON: {e}")
                
                # Альтернативный метод: парсинг HTML
                soup = BeautifulSoup(content, 'html.parser')
                game_rows = soup.find_all('div', class_='gameListRow')
                
                for row in game_rows:
                    try:
                        name_elem = row.find('div', class_='gameListRowItemName')
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            
                            # Извлекаем app ID из ссылки или атрибутов
                            app_id = None
                            link = row.find('a')
                            if link and 'href' in link.attrs:
                                app_match = re.search(r'/app/(\d+)', link['href'])
                                if app_match:
                                    app_id = int(app_match.group(1))
                            
                            # Извлекаем время игры
                            hours_elem = row.find('div', class_='gameListRowHours')
                            playtime = 0
                            if hours_elem:
                                hours_text = hours_elem.get_text(strip=True)
                                hours_match = re.search(r'([\d,\.]+)', hours_text.replace(',', ''))
                                if hours_match:
                                    try:
                                        playtime = int(float(hours_match.group(1)) * 60)  # В минуты
                                    except:
                                        playtime = 0
                            
                            if name and app_id:
                                games.append({
                                    'appid': app_id,
                                    'name': name,
                                    'playtime_forever': playtime,
                                    'playtime_2weeks': 0,
                                    'img_icon_url': '',
                                    'has_community_visible_stats': True
                                })
                    except Exception as e:
                        logger.error(f"Error parsing game row: {e}")
                        continue
                
                return games
                
        except Exception as e:
            logger.error(f"Error parsing games page: {e}")
            return []
    
    async def _parse_games_ajax(self, steam_id64: str) -> List[Dict]:
        """Пытается получить игры через AJAX запросы"""
        try:
            # Пробуем различные AJAX endpoints Steam
            ajax_urls = [
                f"https://steamcommunity.com/profiles/{steam_id64}/games/?tab=all&xml=1",
                f"https://steamcommunity.com/profiles/{steam_id64}/games/?xml=1",
            ]
            
            for url in ajax_urls:
                try:
                    await asyncio.sleep(1)  # Пауза между запросами
                    
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Парсим XML ответ
                            games = self._parse_games_xml(content)
                            if games:
                                return games
                                
                except Exception as e:
                    logger.debug(f"AJAX method failed for {url}: {e}")
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Error in AJAX games parsing: {e}")
            return []
    
    def _parse_games_xml(self, xml_content: str) -> List[Dict]:
        """Парсит XML с играми"""
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            games = []
            
            for game in soup.find_all('game'):
                try:
                    app_id = game.find('appID')
                    name = game.find('name')
                    hours = game.find('hoursOnRecord')
                    
                    if app_id and name:
                        playtime = 0
                        if hours and hours.text:
                            try:
                                # Извлекаем число из текста вида "123.4 hrs"
                                hours_match = re.search(r'([\d\.]+)', hours.text)
                                if hours_match:
                                    playtime = int(float(hours_match.group(1)) * 60)  # В минуты
                            except:
                                playtime = 0
                        
                        games.append({
                            'appid': int(app_id.text),
                            'name': name.text.strip(),
                            'playtime_forever': playtime,
                            'playtime_2weeks': 0,
                            'img_icon_url': '',
                            'has_community_visible_stats': True
                        })
                except Exception as e:
                    logger.error(f"Error parsing XML game: {e}")
                    continue
            
            return games
            
        except Exception as e:
            logger.error(f"Error parsing games XML: {e}")
            return []

    async def get_recently_played_games(self, steam_id64: str, limit: int = 20) -> List[Dict]:
        """Получает список недавно сыгранных игр"""
        try:
            # Получаем все игры и фильтруем по недавней активности
            all_games = await self.get_owned_games(steam_id64, limit * 2)
            
            # Сначала игры с недавней активностью (playtime_2weeks > 0)
            recent_games = [g for g in all_games if g.get('playtime_2weeks', 0) > 0]
            
            # Затем добавляем игры с наибольшим общим временем
            other_games = [g for g in all_games if g.get('playtime_2weeks', 0) == 0]
            other_games = sorted(other_games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
            
            combined = recent_games + other_games
            return combined[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recently played games: {e}")
            return []


# Функция для удобного использования в боте
async def get_steam_library(profile_url: str, limit: int = 50) -> List[Dict]:
    """
    Получает библиотеку игр Steam пользователя
    
    Args:
        profile_url: URL профиля Steam
        limit: Максимальное количество игр для возврата
    
    Returns:
        Список словарей с информацией об играх
    """
    async with SteamLibraryParser() as parser:
        # Извлекаем Steam ID
        steam_identifier = parser.extract_steam_id(profile_url)
        if not steam_identifier:
            logger.error("Could not extract Steam ID from URL")
            return []
        
        # Получаем Steam ID64
        steam_id64 = await parser.resolve_steam_id(steam_identifier)
        if not steam_id64:
            logger.error("Could not resolve Steam ID64")
            return []
        
        # Получаем игры
        games = await parser.get_owned_games(steam_id64, limit)
        return games


async def get_recently_played_games(profile_url: str, limit: int = 20) -> List[Dict]:
    """
    Получает недавно сыгранные игры пользователя
    
    Args:
        profile_url: URL профиля Steam
        limit: Максимальное количество игр
    
    Returns:
        Список словарей с информацией об играх
    """
    async with SteamLibraryParser() as parser:
        steam_identifier = parser.extract_steam_id(profile_url)
        if not steam_identifier:
            return []
        
        steam_id64 = await parser.resolve_steam_id(steam_identifier)
        if not steam_id64:
            return []
        
        games = await parser.get_recently_played_games(steam_id64, limit)
        return games


# Пример использования
if __name__ == "__main__":
    async def test():
        profile_url = "https://steamcommunity.com/id/example"
        
        print("Getting library...")
        library = await get_steam_library(profile_url, 20)
        
        print(f"Found {len(library)} games:")
        for game in library[:5]:
            hours = game.get('playtime_forever', 0) / 60  # Конвертируем в часы
            print(f"- {game.get('name', 'Unknown')} ({hours:.1f} hours)")
    
    # asyncio.run(test())
