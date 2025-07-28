"""
Модуль для генерации AI-рекомендаций игр на основе предпочтений пользователя
Использует OpenAI API для анализа и рекомендаций
"""
import openai
import asyncio
import logging
import random
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GameRecommendationAI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            openai.api_key = api_key
        
        # Захардкоженные игры для демонстрации
        self.sample_games_with_discounts = [
            {
                'name': 'Cyberpunk 2077',
                'discount': 60,
                'original_price': 2999,
                'discounted_price': 1199,
                'description': 'Футуристическая RPG в мире киберпанка',
                'genres': ['RPG', 'Action', 'Open World'],
                'steam_url': 'https://store.steampowered.com/app/1091500/Cyberpunk_2077/'
            },
            {
                'name': 'The Witcher 3: Wild Hunt',
                'discount': 70,
                'original_price': 1999,
                'discounted_price': 599,
                'description': 'Эпическая фэнтези RPG о ведьмаке Геральте',
                'genres': ['RPG', 'Open World', 'Fantasy'],
                'steam_url': 'https://store.steampowered.com/app/292030/The_Witcher_3_Wild_Hunt/'
            },
            {
                'name': 'Red Dead Redemption 2',
                'discount': 50,
                'original_price': 2999,
                'discounted_price': 1499,
                'description': 'Приключения на Диком Западе',
                'genres': ['Action', 'Adventure', 'Open World'],
                'steam_url': 'https://store.steampowered.com/app/1174180/Red_Dead_Redemption_2/'
            },
            {
                'name': 'Disco Elysium',
                'discount': 65,
                'original_price': 1499,
                'discounted_price': 524,
                'description': 'Инновационная детективная RPG',
                'genres': ['RPG', 'Indie', 'Detective'],
                'steam_url': 'https://store.steampowered.com/app/632470/Disco_Elysium_The_Final_Cut/'
            },
            {
                'name': 'Hades',
                'discount': 40,
                'original_price': 849,
                'discounted_price': 509,
                'description': 'Рогалик о побеге из подземного мира',
                'genres': ['Roguelike', 'Action', 'Indie'],
                'steam_url': 'https://store.steampowered.com/app/1145360/Hades/'
            },
            {
                'name': 'Divinity: Original Sin 2',
                'discount': 55,
                'original_price': 1799,
                'discounted_price': 809,
                'description': 'Классическая изометрическая RPG',
                'genres': ['RPG', 'Turn-Based', 'Fantasy'],
                'steam_url': 'https://store.steampowered.com/app/435150/Divinity_Original_Sin_2_Definitive_Edition/'
            },
            {
                'name': 'Sekiro: Shadows Die Twice',
                'discount': 45,
                'original_price': 2499,
                'discounted_price': 1374,
                'description': 'Сложный action про ниндзя в феодальной Японии',
                'genres': ['Action', 'Souls-like', 'Adventure'],
                'steam_url': 'https://store.steampowered.com/app/814380/Sekiro_Shadows_Die_Twice__GOTY_Edition/'
            },
            {
                'name': 'Hollow Knight',
                'discount': 50,
                'original_price': 549,
                'discounted_price': 274,
                'description': 'Атмосферный 2D метроидвания',
                'genres': ['Metroidvania', 'Indie', 'Platformer'],
                'steam_url': 'https://store.steampowered.com/app/367520/Hollow_Knight/'
            },
            {
                'name': 'Stardew Valley',
                'discount': 35,
                'original_price': 399,
                'discounted_price': 259,
                'description': 'Уютная фермерская симуляция',
                'genres': ['Simulation', 'Indie', 'Farming'],
                'steam_url': 'https://store.steampowered.com/app/413150/Stardew_Valley/'
            },
            {
                'name': 'Dead Cells',
                'discount': 60,
                'original_price': 849,
                'discounted_price': 339,
                'description': 'Быстрый 2D рогалик с элементами метроидвании',
                'genres': ['Roguelike', 'Metroidvania', 'Action'],
                'steam_url': 'https://store.steampowered.com/app/588650/Dead_Cells/'
            }
        ]
    
    async def get_openai_recommendations(self, favorite_games: List[str]) -> Optional[str]:
        """Получает рекомендации от OpenAI API"""
        try:
            if not self.api_key:
                return None
            
            games_list = ", ".join(favorite_games)
            
            prompt = f"""
            Пользователь любит следующие игры: {games_list}
            
            На основе этих предпочтений, порекомендуй 5-7 похожих игр, которые могут понравиться.
            Для каждой игры укажи:
            1. Название
            2. Почему она подойдет (что общего с любимыми играми)
            3. Краткое описание
            
            Отвечай на русском языке в формате списка.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты эксперт по видеоиграм, который дает персонализированные рекомендации."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting OpenAI recommendations: {e}")
            return None
    
    def get_fallback_recommendations(self, favorite_games: List[str]) -> List[Dict]:
        """Возвращает рекомендации на основе простого сопоставления жанров"""
        try:
            # Простая логика сопоставления на основе ключевых слов
            genre_mapping = {
                'cyberpunk': ['RPG', 'Action', 'Sci-Fi'],
                'witcher': ['RPG', 'Fantasy', 'Open World'],
                'gta': ['Action', 'Open World', 'Crime'],
                'skyrim': ['RPG', 'Fantasy', 'Open World'],
                'dark souls': ['Souls-like', 'Action', 'RPG'],
                'minecraft': ['Sandbox', 'Survival', 'Creative'],
                'dota': ['MOBA', 'Strategy', 'Multiplayer'],
                'cs': ['FPS', 'Competitive', 'Multiplayer'],
                'stardew': ['Simulation', 'Farming', 'Relaxing'],
                'hollow knight': ['Metroidvania', 'Indie', 'Platformer']
            }
            
            # Определяем предпочтительные жанры
            preferred_genres = set()
            for game in favorite_games:
                game_lower = game.lower()
                for key, genres in genre_mapping.items():
                    if key in game_lower:
                        preferred_genres.update(genres)
            
            # Если не нашли совпадений, добавляем популярные жанры
            if not preferred_genres:
                preferred_genres = {'RPG', 'Action', 'Adventure'}
            
            # Фильтруем игры по жанрам
            recommended_games = []
            for game in self.sample_games_with_discounts:
                game_genres = set(game['genres'])
                if preferred_genres.intersection(game_genres):
                    # Добавляем объяснение почему игра подходит
                    matching_genres = preferred_genres.intersection(game_genres)
                    game['recommendation_reason'] = f"Подходит по жанрам: {', '.join(matching_genres)}"
                    recommended_games.append(game)
            
            # Сортируем по размеру скидки
            recommended_games.sort(key=lambda x: x['discount'], reverse=True)
            
            return recommended_games[:6]  # Возвращаем топ-6
            
        except Exception as e:
            logger.error(f"Error getting fallback recommendations: {e}")
            return []
    
    async def generate_recommendations(self, favorite_games: List[str]) -> Dict:
        """Основная функция для генерации рекомендаций"""
        try:
            # Сначала пробуем получить рекомендации от AI
            ai_text = await self.get_openai_recommendations(favorite_games)
            
            # Получаем рекомендации игр со скидками
            recommended_games = self.get_fallback_recommendations(favorite_games)
            
            return {
                'ai_recommendations': ai_text,
                'discounted_games': recommended_games,
                'total_games': len(recommended_games),
                'user_preferences': favorite_games
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                'ai_recommendations': None,
                'discounted_games': [],
                'total_games': 0,
                'user_preferences': favorite_games
            }

# Глобальный экземпляр (можно настроить API ключ)
game_ai = GameRecommendationAI()

async def get_game_recommendations(favorite_games: List[str], openai_api_key: Optional[str] = None) -> Dict:
    """Основная функция для получения рекомендаций"""
    if openai_api_key:
        ai = GameRecommendationAI(openai_api_key)
    else:
        ai = game_ai
    
    return await ai.generate_recommendations(favorite_games)
