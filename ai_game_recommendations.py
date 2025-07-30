"""
Модуль для ИИ-рекомендаций игр на основе Steam Wishlist и библиотеки
Использует OpenRouter AI для анализа предпочтений пользователя
"""
import logging
import asyncio
from typing import List, Dict, Optional
from openai import OpenAI
import json
import re

logger = logging.getLogger(__name__)

class GameRecommendationAI:
    def __init__(self, api_key: str, language: str = 'ru'):
        """Инициализация ИИ-помощника для рекомендаций игр"""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = "deepseek/deepseek-chat-v3-0324:free"
        self.language = language
    
    async def get_game_recommendations(self, wishlist_games: List[Dict], owned_games: List[Dict] = None, limit: int = 10) -> List[Dict]:
        """
        Получает рекомендации игр на основе wishlist и библиотеки
        
        Args:
            wishlist_games: Список игр из wishlist пользователя
            owned_games: Список игр из библиотеки пользователя
            limit: Максимальное количество рекомендаций
            
        Returns:
            Список рекомендованных игр с описанием
        """
        try:
            if not wishlist_games and not owned_games:
                logger.warning("🤖 No games provided for AI recommendations")
                return []
            
            total_games = len(wishlist_games) + (len(owned_games) if owned_games else 0)
            logger.info(f"🤖 Analyzing {total_games} games (wishlist: {len(wishlist_games)}, library: {len(owned_games) if owned_games else 0}) for AI recommendations...")
            
            # Подготавливаем данные для ИИ
            wishlist_names = [game.get('name', 'Unknown Game') for game in wishlist_games[:15]]
            owned_names = []
            owned_playtime = []
            
            if owned_games:
                # Берем топ игр по времени игры + недавние
                sorted_owned = sorted(owned_games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
                owned_names = [game.get('name', 'Unknown Game') for game in sorted_owned[:20]]
                owned_playtime = [(game.get('name', ''), game.get('playtime_forever', 0)) for game in sorted_owned[:10]]
            
            # Создаем промпт для ИИ
            prompt = self._create_comprehensive_recommendation_prompt(wishlist_names, owned_names, owned_playtime, limit)
            
            # Получаем рекомендации от ИИ
            recommendations = await self._get_ai_response(prompt)
            
            if recommendations:
                logger.info(f"🎮 AI generated {len(recommendations)} game recommendations")
                return recommendations
            else:
                logger.warning("🤖 AI didn't generate any recommendations")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting AI game recommendations: {e}")
            return []
    
    def _extract_genres_from_games(self, games: List[Dict]) -> List[str]:
        """Извлекает жанры из игр (если доступно)"""
        genres = set()
        
        for game in games:
            # Пытаемся извлечь жанры из тегов или других данных
            tags = game.get('tags', [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict) and 'name' in tag:
                        genres.add(tag['name'])
                    elif isinstance(tag, str):
                        genres.add(tag)
        
        return list(genres)[:10]  # Ограничиваем количество жанров
    
    def _create_comprehensive_recommendation_prompt(self, wishlist_names: List[str], owned_names: List[str], owned_playtime: List[tuple], limit: int) -> str:
        """Создает комплексный промпт для ИИ-рекомендаций на основе wishlist и библиотеки"""
        
        # Выбираем язык промпта
        if self.language == 'en':
            return self._create_english_comprehensive_prompt(wishlist_names, owned_names, owned_playtime, limit)
        else:
            return self._create_russian_comprehensive_prompt(wishlist_names, owned_names, owned_playtime, limit)
    
    def _create_russian_comprehensive_prompt(self, wishlist_names: List[str], owned_names: List[str], owned_playtime: List[tuple], limit: int) -> str:
        """Создает русский промпт для ИИ-рекомендаций"""
        # Формируем wishlist
        wishlist_section = ""
        if wishlist_names:
            wishlist_list = "\n".join([f"- {name}" for name in wishlist_names])
            wishlist_section = f"""
WISHLIST ПОЛЬЗОВАТЕЛЯ ({len(wishlist_names)} игр):
{wishlist_list}
"""
        
        # Формируем библиотеку с временем игры
        library_section = ""
        if owned_names:
            library_list = "\n".join([f"- {name}" for name in owned_names])
            library_section = f"""
БИБЛИОТЕКА ИГРОКА ({len(owned_names)} игр):
{library_list}
"""
        
        # Топ игр по времени игры
        playtime_section = ""
        if owned_playtime:
            playtime_list = "\n".join([
                f"- {name}: {playtime//60:.1f} часов" 
                for name, playtime in owned_playtime[:8] if playtime > 0
            ])
            if playtime_list:
                playtime_section = f"""
ЛЮБИМЫЕ ИГРЫ (по времени в игре):
{playtime_list}
"""
        
        prompt = f"""
Ты - эксперт по видеоиграм и Steam. Проанализируй данные игрока и порекомендуй {limit} игр.

{wishlist_section}{library_section}{playtime_section}

ЗАДАЧА:
1. Проанализируй игровые предпочтения на основе ВСЕХ данных:
   - Wishlist показывает будущие интересы
   - Библиотека показывает купленные игры
   - Время игры показывает РЕАЛЬНЫЕ предпочтения
2. Определи любимые жанры, механики, стили игр
3. Порекомендуй {limit} игр, которых НЕТ в wishlist и библиотеке
4. Учитывай современные и популярные игры Steam

ДЛЯ КАЖДОЙ РЕКОМЕНДАЦИИ УКАЖИ:
- Название игры
- Краткое описание (1-2 предложения)  
- Почему подходит (связь с играми игрока)
- Примерную цену в Steam
- Оценку совместимости (85-95%)

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "analysis": {{
    "top_genres": ["жанр1", "жанр2", "жанр3"],
    "preferred_mechanics": ["механика1", "механика2"],
    "gaming_style": "описание стиля игрока",
    "analysis_summary": "краткий анализ предпочтений"
  }},
  "recommendations": [
    {{
      "name": "Название игры",
      "description": "Описание игры",
      "reason": "Почему подходит игроку",
      "estimated_price": "цена в рублях",
      "similarity_score": 90
    }}
  ]
}}

ВАЖНО: Отвечай ТОЛЬКО JSON, без дополнительного текста!"""
        
        return prompt
    
    def _create_english_comprehensive_prompt(self, wishlist_names: List[str], owned_names: List[str], owned_playtime: List[tuple], limit: int) -> str:
        """Создает английский промпт для ИИ-рекомендаций"""
        # Form wishlist section
        wishlist_section = ""
        if wishlist_names:
            wishlist_list = "\n".join([f"- {name}" for name in wishlist_names])
            wishlist_section = f"""
USER'S WISHLIST ({len(wishlist_names)} games):
{wishlist_list}
"""
        
        # Form library section
        library_section = ""
        if owned_names:
            library_list = "\n".join([f"- {name}" for name in owned_names])
            library_section = f"""
PLAYER'S LIBRARY ({len(owned_names)} games):
{library_list}
"""
        
        # Top games by playtime
        playtime_section = ""
        if owned_playtime:
            playtime_list = "\n".join([
                f"- {name}: {playtime//60:.1f} hours" 
                for name, playtime in owned_playtime[:8] if playtime > 0
            ])
            if playtime_list:
                playtime_section = f"""
FAVORITE GAMES (by playtime):
{playtime_list}
"""
        
        prompt = f"""
You are a video game expert and Steam specialist. Analyze player data and recommend {limit} games.

{wishlist_section}{library_section}{playtime_section}

TASK:
1. Analyze gaming preferences based on ALL data:
   - Wishlist shows future interests
   - Library shows purchased games
   - Playtime shows REAL preferences
2. Identify favorite genres, mechanics, game styles
3. Recommend {limit} games that are NOT in wishlist or library
4. Consider modern and popular Steam games

FOR EACH RECOMMENDATION SPECIFY:
- Game title
- Brief description (1-2 sentences)
- Why it fits (connection to player's games)
- Estimated Steam price
- Compatibility score (85-95%)

RESPONSE FORMAT (strict JSON):
{{
  "analysis": {{
    "top_genres": ["genre1", "genre2", "genre3"],
    "preferred_mechanics": ["mechanic1", "mechanic2"],
    "gaming_style": "player style description",
    "analysis_summary": "brief preference analysis"
  }},
  "recommendations": [
    {{
      "name": "Game Title",
      "description": "Game description",
      "reason": "Why it fits the player",
      "estimated_price": "price in USD",
      "similarity_score": 90
    }}
  ]
}}

IMPORTANT: Reply ONLY with JSON, no additional text!"""
        
        return prompt
    
    def _create_recommendation_prompt(self, game_names: List[str], genres: List[str], limit: int) -> str:
        """Создает простой промпт для ИИ-рекомендаций (fallback)"""
        games_list = "\n".join([f"- {name}" for name in game_names])
        genres_list = ", ".join(genres) if genres else "Unknown"
        
        prompt = f"""
Ты - эксперт по видеоиграм и Steam. Проанализируй wishlist пользователя и порекомендуй {limit} похожих игр.

WISHLIST ПОЛЬЗОВАТЕЛЯ:
{games_list}

ПРЕДПОЧИТАЕМЫЕ ЖАНРЫ: {genres_list}

ЗАДАЧА:
1. Проанализируй игры в wishlist и определи игровые предпочтения пользователя
2. Порекомендуй {limit} игр, которые НЕ входят в этот список, но похожи по стилю/жанру/механикам
3. Для каждой игры укажи:
   - Название игры
   - Краткое описание (1-2 предложения)
   - Почему она подходит пользователю
   - Примерную цену в Steam (если знаешь)

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "recommendations": [
    {{
      "name": "Название игры",
      "description": "Краткое описание игры",
      "reason": "Почему подходит пользователю",
      "estimated_price": "Примерная цена",
      "similarity_score": 85
    }}
  ]
}}

ВАЖНО:
- Рекомендуй только существующие игры из Steam
- НЕ рекомендуй игры, которые уже есть в wishlist
- Учитывай разнообразие жанров из wishlist
- Отвечай ТОЛЬКО в формате JSON
"""
        return prompt
    
    async def _get_ai_response(self, prompt: str) -> List[Dict]:
        """Получает ответ от ИИ и парсит его"""
        try:
            logger.debug("🤖 Sending request to AI...")
            
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/InJeCTrL/NeedFree",
                    "X-Title": "Steam Wishlist AI Recommendations",
                },
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по видеоиграм Steam. Анализируешь игровые предпочтения и даешь точные рекомендации. Отвечаешь только в формате JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = completion.choices[0].message.content
            logger.debug(f"🤖 AI Response received: {len(ai_response)} characters")
            
            # Парсим JSON ответ
            recommendations = self._parse_ai_response(ai_response)
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting AI response: {e}")
            return []
    
    def _parse_ai_response(self, response: str) -> List[Dict]:
        """Парсит ответ ИИ и извлекает рекомендации"""
        try:
            # Пытаемся найти JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.error("🤖 No JSON found in AI response")
                return []
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            recommendations = data.get('recommendations', [])
            
            # Валидируем рекомендации
            validated_recommendations = []
            for rec in recommendations:
                if self._validate_recommendation(rec):
                    validated_recommendations.append(rec)
            
            logger.info(f"🎮 Parsed {len(validated_recommendations)} valid recommendations from AI")
            return validated_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            logger.debug(f"AI response: {response[:500]}")
            return []
        except Exception as e:
            logger.error(f"❌ Error parsing AI response: {e}")
            return []
    
    def _validate_recommendation(self, recommendation: Dict) -> bool:
        """Валидирует рекомендацию от ИИ"""
        required_fields = ['name', 'description', 'reason']
        
        for field in required_fields:
            if field not in recommendation or not recommendation[field]:
                logger.warning(f"🤖 Invalid recommendation: missing {field}")
                return False
        
        # Проверяем длину полей
        if len(recommendation['name']) > 100:
            logger.warning(f"🤖 Game name too long: {recommendation['name'][:50]}...")
            return False
        
        if len(recommendation['description']) > 500:
            recommendation['description'] = recommendation['description'][:497] + "..."
        
        if len(recommendation['reason']) > 300:
            recommendation['reason'] = recommendation['reason'][:297] + "..."
        
        return True
    
    async def get_comprehensive_analysis(self, wishlist_games: List[Dict], owned_games: List[Dict] = None) -> Dict:
        """Комплексный анализ предпочтений пользователя на основе wishlist и библиотеки"""
        try:
            if not wishlist_games and not owned_games:
                return {}
            
            wishlist_names = [game.get('name', 'Unknown Game') for game in wishlist_games[:15]]
            owned_names = []
            owned_playtime = []
            
            if owned_games:
                sorted_owned = sorted(owned_games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
                owned_names = [game.get('name', 'Unknown Game') for game in sorted_owned[:15]]
                owned_playtime = [(game.get('name', ''), game.get('playtime_forever', 0)) for game in sorted_owned[:8]]
            
            # Создаем промпт для анализа
            prompt = self._create_analysis_prompt(wishlist_names, owned_names, owned_playtime)
            
            response = await self._get_ai_analysis_response(prompt)
            return response if response else {}
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {}
    
    def _create_analysis_prompt(self, wishlist_names: List[str], owned_names: List[str], owned_playtime: List[tuple]) -> str:
        """Создает промпт для анализа игровых предпочтений"""
        
        wishlist_section = ""
        if wishlist_names:
            wishlist_list = "\n".join([f"- {name}" for name in wishlist_names])
            wishlist_section = f"WISHLIST ({len(wishlist_names)} игр):\n{wishlist_list}\n\n"
        
        library_section = ""
        if owned_names:
            library_list = "\n".join([f"- {name}" for name in owned_names])
            library_section = f"БИБЛИОТЕКА ({len(owned_names)} игр):\n{library_list}\n\n"
        
        playtime_section = ""
        if owned_playtime:
            playtime_list = "\n".join([
                f"- {name}: {playtime//60:.1f} часов" 
                for name, playtime in owned_playtime if playtime > 0
            ])
            if playtime_list:
                playtime_section = f"ЛЮБИМЫЕ ИГРЫ (по времени):\n{playtime_list}\n\n"
        
        prompt = f"""
Проанализируй игровые предпочтения пользователя Steam на основе его данных:

{wishlist_section}{library_section}{playtime_section}

ЗАДАЧА: Определи игровые предпочтения пользователя:
1. Топ-5 любимых жанров
2. Предпочитаемые игровые механики
3. Стиль игрока (казуальный/хардкорный/соревновательный)
4. Краткий анализ предпочтений

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "top_genres": ["жанр1", "жанр2", "жанр3", "жанр4", "жанр5"],
  "preferred_mechanics": ["механика1", "механика2", "механика3"],
  "gaming_style": "описание стиля игрока",
  "analysis_summary": "краткий анализ предпочтений пользователя"
}}

ВАЖНО: Отвечай ТОЛЬКО JSON, без дополнительного текста!"""
        
        return prompt
    
    async def _get_ai_analysis_response(self, prompt: str) -> Dict:
        """Получает ответ от ИИ для анализа"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_analysis_response(content)
            
        except Exception as e:
            logger.error(f"Error getting AI analysis response: {e}")
            return {}
    
    def _parse_analysis_response(self, content: str) -> Dict:
        """Парсит ответ ИИ с анализом"""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
                
                # Валидируем структуру
                required_fields = ['top_genres', 'preferred_mechanics', 'gaming_style', 'analysis_summary']
                if all(field in analysis for field in required_fields):
                    return analysis
            
            logger.warning("Invalid analysis response format")
            return {}
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing analysis JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error in analysis response parsing: {e}")
            return {}

    async def get_genre_analysis(self, wishlist_games: List[Dict]) -> Dict:
        """Анализирует жанры и предпочтения пользователя"""
        try:
            if not wishlist_games:
                return {}
            
            game_names = [game.get('name', 'Unknown Game') for game in wishlist_games[:15]]
            
            prompt = f"""
Проанализируй wishlist Steam пользователя и определи его игровые предпочтения.

ИГРЫ В WISHLIST:
{chr(10).join([f"- {name}" for name in game_names])}

Проанализируй и определи:
1. Основные жанры (топ-5)
2. Игровые механики, которые нравятся пользователю
3. Тип игр (инди, AAA, кооператив и т.д.)
4. Настроение игр (темные, веселые, серьезные)

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "top_genres": ["жанр1", "жанр2", "жанр3", "жанр4", "жанр5"],
  "preferred_mechanics": ["механика1", "механика2", "механика3"],
  "game_types": ["тип1", "тип2", "тип3"],
  "mood_preferences": ["настроение1", "настроение2"],
  "analysis_summary": "Краткий анализ предпочтений пользователя"
}}
"""
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по видеоиграм. Анализируешь игровые предпочтения. Отвечаешь только в формате JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            response = completion.choices[0].message.content
            
            # Парсим JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error in genre analysis: {e}")
            return {}

# Функция для интеграции с основным ботом
async def get_ai_game_recommendations(wishlist_games: List[Dict], owned_games: List[Dict], api_key: str, limit: int = 8, language: str = 'ru') -> Dict:
    """
    Получает ИИ-рекомендации игр на основе wishlist и библиотеки
    
    Args:
        wishlist_games: Список игр из wishlist
        owned_games: Список игр из библиотеки
        api_key: API ключ для OpenRouter
        limit: Количество рекомендаций
        language: Язык пользователя ('ru' или 'en')
        
    Returns:
        Словарь с рекомендациями и анализом
    """
    try:
        ai = GameRecommendationAI(api_key, language)
        
        # Получаем рекомендации на основе обеих источников
        recommendations = await ai.get_game_recommendations(wishlist_games, owned_games, limit)
        
        # Получаем комплексный анализ
        analysis = await ai.get_comprehensive_analysis(wishlist_games, owned_games)
        
        total_games = len(wishlist_games) + (len(owned_games) if owned_games else 0)
        
        return {
            'recommendations': recommendations,
            'analysis': analysis,
            'total_wishlist_games': len(wishlist_games),
            'total_owned_games': len(owned_games) if owned_games else 0,
            'total_games_analyzed': total_games,
            'success': len(recommendations) > 0 or bool(analysis)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in AI game recommendations: {e}")
        return {
            'recommendations': [],
            'analysis': {},
            'total_wishlist_games': len(wishlist_games),
            'total_owned_games': len(owned_games) if owned_games else 0,
            'total_games_analyzed': 0,
            'success': False,
            'error': str(e)
        }
