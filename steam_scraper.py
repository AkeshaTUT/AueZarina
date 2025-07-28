import asyncio
import aiohttp
import bs4
import re
import json
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class SteamScraper:
    def __init__(self):
        self.base_url = "https://store.steampowered.com"
        self.search_url = "https://store.steampowered.com/search/results/"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_discounted_games(self, min_discount: int = 30, max_results: int = 50) -> List[Dict]:
        """
        Получает список игр со скидками от min_discount% до 100%
        
        Args:
            min_discount: Минимальная скидка в процентах (по умолчанию 30)
            max_results: Максимальное количество результатов
            
        Returns:
            Список словарей с информацией об играх
        """
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        ) as session:
            self.session = session
            return await self._fetch_discounted_games(min_discount, max_results)
    
    async def _fetch_discounted_games(self, min_discount: int, max_results: int) -> List[Dict]:
        """Внутренний метод для получения скидок"""
        games = []
        start = 0
        page_size = 25
        
        try:
            while len(games) < max_results and start < 200:  # Ограничиваем поиск
                params = {
                    'query': '',
                    'start': start,
                    'count': page_size,
                    'infinite': 1,
                    'sort_by': '_ASC',  # Сортировка по релевантности
                    'specials': 1,  # Только товары со скидкой
                    'ndl': 1,  # Не показывать DLC
                    'category1': 998,  # Только игры
                }
                
                logger.info(f"Fetching page with start={start}, looking for discounts >= {min_discount}%")
                page_games = await self._parse_search_page(params, min_discount)
                
                if not page_games:
                    logger.info(f"No games found on page starting at {start}, stopping search")
                    break
                    
                games.extend(page_games)
                start += page_size
                
                # Небольшая задержка между запросами
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error fetching discounted games: {e}")
        
        # Сортируем по размеру скидки (от большей к меньшей)
        games.sort(key=lambda x: x.get('discount', 0), reverse=True)
        return games[:max_results]
    
    async def _parse_search_page(self, params: dict, min_discount: int) -> List[Dict]:
        """Парсит страницу поиска Steam"""
        games = []
        
        try:
            async with self.session.get(self.search_url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Bad response status: {response.status}")
                    return games
                
                data = await response.json()
                html_content = data.get('results_html', '')
                
                if not html_content:
                    logger.warning("No HTML content in response")
                    return games
                
                soup = bs4.BeautifulSoup(html_content, 'html.parser')
                game_containers = soup.find_all('a', class_='search_result_row')
                
                logger.info(f"Found {len(game_containers)} game containers")
                
                for container in game_containers:
                    game_info = await self._parse_game_container(container, min_discount)
                    if game_info:
                        games.append(game_info)
                        logger.info(f"Added game: {game_info['title']} (-{game_info['discount']}%)")
                        
        except Exception as e:
            logger.error(f"Error parsing search page: {e}")
            
        return games
    
    async def _parse_game_container(self, container, min_discount: int) -> Optional[Dict]:
        """Парсит контейнер с информацией об игре"""
        try:
            # Получаем название игры
            title_elem = container.find('span', class_='title')
            if not title_elem:
                logger.debug("No title found in container")
                return None
            title = title_elem.get_text(strip=True)
            
            # Получаем URL игры и app_id
            game_url = container.get('href', '')
            app_id = 0
            
            # Извлекаем app_id из URL или data-ds-appid
            if container.get('data-ds-appid'):
                try:
                    app_id = int(container.get('data-ds-appid'))
                except (ValueError, TypeError):
                    pass
            elif game_url:
                # Пытаемся извлечь app_id из URL
                app_id_match = re.search(r'/app/(\d+)/', game_url)
                if app_id_match:
                    try:
                        app_id = int(app_id_match.group(1))
                    except (ValueError, TypeError):
                        pass
            
            # Ищем информацию о скидке - несколько вариантов
            discount_percent = 0
            
            # Вариант 1: ищем в data-discount атрибуте
            discount_div = container.find('div', attrs={'data-discount': True})
            if discount_div:
                try:
                    discount_percent = int(discount_div.get('data-discount', 0))
                except (ValueError, TypeError):
                    pass
            
            # Вариант 2: ищем текст скидки
            if discount_percent == 0:
                discount_elem = container.find('div', class_='search_discount')
                if discount_elem:
                    discount_text = discount_elem.get_text(strip=True)
                    discount_match = re.search(r'-(\d+)%', discount_text)
                    if discount_match:
                        discount_percent = int(discount_match.group(1))
            
            # Вариант 3: ищем в других местах
            if discount_percent == 0:
                discount_spans = container.find_all('span', class_=re.compile(r'discount'))
                for span in discount_spans:
                    discount_text = span.get_text(strip=True)
                    discount_match = re.search(r'-?(\d+)%', discount_text)
                    if discount_match:
                        discount_percent = int(discount_match.group(1))
                        break
            
            # Проверяем минимальную скидку
            if discount_percent < min_discount:
                logger.debug(f"Game {title} has discount {discount_percent}% < {min_discount}%")
                return None
            
            # Получаем информацию о ценах
            original_price = ""
            discounted_price = ""
            
            # Ищем контейнер с ценами
            price_containers = [
                container.find('div', class_='search_price_discount_combined'),
                container.find('div', class_='search_price'),
                container.find('div', class_='col search_price_discount_combined responsive_secondrow')
            ]
            
            for price_container in price_containers:
                if price_container:
                    # Оригинальная цена (зачеркнутая)
                    original_elem = price_container.find('span', class_='search_discount_orig_price')
                    if original_elem:
                        original_price = original_elem.get_text(strip=True)
                    
                    # Цена со скидкой
                    discounted_elem = price_container.find('span', class_='search_discount_final_price')
                    if discounted_elem:
                        discounted_price = discounted_elem.get_text(strip=True)
                    
                    if original_price or discounted_price:
                        break
            
            # Получаем дату релиза
            release_date = ""
            release_elem = container.find('div', class_='search_released')
            if release_elem:
                release_date = release_elem.get_text(strip=True)
            
            # Получаем теги платформ
            platforms = []
            platform_icons = container.find_all('span', class_=lambda x: x and 'platform_img' in x)
            for icon in platform_icons:
                classes = icon.get('class', [])
                if any('win' in cls for cls in classes):
                    platforms.append('Windows')
                elif any('mac' in cls for cls in classes):
                    platforms.append('Mac')
                elif any('linux' in cls for cls in classes):
                    platforms.append('Linux')
            
            # Извлекаем жанры из тегов
            genres = []
            # Ищем теги игры
            tag_elems = container.find_all('span', class_='search_tag')
            for tag_elem in tag_elems:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    genres.append(tag_text)
            
            # Если тегов нет, пытаемся найти жанры в других местах
            if not genres:
                genre_container = container.find('div', class_='search_misc_row')
                if genre_container:
                    genre_links = genre_container.find_all('a')
                    for link in genre_links:
                        genre_text = link.get_text(strip=True)
                        if genre_text and genre_text not in genres:
                            genres.append(genre_text)
            
            result = {
                'title': title,
                'url': game_url,
                'app_id': app_id,
                'discount': discount_percent,
                'original_price': original_price,
                'discounted_price': discounted_price,
                'release_date': release_date,
                'platforms': platforms,
                'genres': genres
            }
            
            logger.debug(f"Parsed game: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing game container: {e}")
            return None
    
    async def get_free_games(self) -> List[Dict]:
        """Получает список бесплатных игр (100% скидка)"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        ) as session:
            self.session = session
            return await self._fetch_discounted_games(min_discount=100, max_results=20)


# Для обратной совместимости с существующим кодом
def get_free_goods_updated(min_discount: int = 30, max_results: int = 50) -> List[Dict]:
    """
    Синхронная обертка для получения скидок
    Совместима с существующим кодом
    """
    async def _async_wrapper():
        scraper = SteamScraper()
        return await scraper.get_discounted_games(min_discount, max_results)
    
    return asyncio.run(_async_wrapper())


if __name__ == "__main__":
    # Тестирование скрапера
    async def test_scraper():
        scraper = SteamScraper()
        
        print("Получаем скидки от 30%...")
        deals = await scraper.get_discounted_games(min_discount=30, max_results=10)
        
        print(f"Найдено {len(deals)} игр со скидками:")
        for deal in deals:
            print(f"- {deal['title']} (-{deal['discount']}%)")
            print(f"  {deal['original_price']} → {deal['discounted_price']}")
            print(f"  {deal['url']}")
            print()
    
    asyncio.run(test_scraper())
