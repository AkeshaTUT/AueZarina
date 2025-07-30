"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "steam_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        is_subscribed BOOLEAN DEFAULT 0,
                        min_discount INTEGER DEFAULT 30,
                        preferred_genres TEXT DEFAULT '[]',
                        language TEXT DEFAULT 'ru',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Добавляем колонку языка если её нет
                try:
                    cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "ru"')
                    conn.commit()
                except sqlite3.OperationalError:
                    # Колонка уже существует
                    pass
                
                # Таблица истории цен (эмуляция)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id TEXT,
                        game_title TEXT,
                        price REAL,
                        discount INTEGER,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица бесплатных игр
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS free_games (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        description TEXT,
                        platform TEXT,
                        url TEXT,
                        end_date TEXT,
                        image_url TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица топовых игр недели
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weekly_top (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_title TEXT,
                        discount INTEGER,
                        original_price TEXT,
                        discounted_price TEXT,
                        url TEXT,
                        rating REAL DEFAULT 0.0,
                        week_start DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица отзывов и предложений
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        username TEXT,
                        feedback_type TEXT DEFAULT 'general',
                        message TEXT NOT NULL,
                        rating INTEGER DEFAULT NULL,
                        is_resolved BOOLEAN DEFAULT 0,
                        admin_response TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Добавление нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, datetime.now()))
                conn.commit()
                logger.info(f"User {user_id} added/updated")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
    
    def remove_user(self, user_id: int) -> bool:
        """Удаление пользователя (для тестирования)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing user {user_id}: {e}")
            return False
    
    def subscribe_user(self, user_id: int) -> bool:
        """Подписка пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET is_subscribed = 1, last_activity = ?
                    WHERE user_id = ?
                ''', (datetime.now(), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error subscribing user {user_id}: {e}")
            return False
    
    def unsubscribe_user(self, user_id: int) -> bool:
        """Отписка пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET is_subscribed = 0, last_activity = ?
                    WHERE user_id = ?
                ''', (datetime.now(), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error unsubscribing user {user_id}: {e}")
            return False
    
    def get_subscribed_users(self) -> List[int]:
        """Получение списка подписанных пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM users WHERE is_subscribed = 1')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting subscribed users: {e}")
            return []
    
    def set_user_genres(self, user_id: int, genres: List[str]):
        """Установка жанров пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET preferred_genres = ?, last_activity = ?
                    WHERE user_id = ?
                ''', (json.dumps(genres), datetime.now(), user_id))
                conn.commit()
                logger.info(f"Genres updated for user {user_id}: {genres}")
        except Exception as e:
            logger.error(f"Error setting genres for user {user_id}: {e}")
    
    def get_user_genres(self, user_id: int) -> List[str]:
        """Получение жанров пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT preferred_genres FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
                return []
        except Exception as e:
            logger.error(f"Error getting genres for user {user_id}: {e}")
            return []
    
    def set_user_min_discount(self, user_id: int, min_discount: int):
        """Установка минимальной скидки для пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET min_discount = ?, last_activity = ?
                    WHERE user_id = ?
                ''', (min_discount, datetime.now(), user_id))
                conn.commit()
                logger.info(f"Min discount updated for user {user_id}: {min_discount}%")
        except Exception as e:
            logger.error(f"Error setting min discount for user {user_id}: {e}")
    
    def get_user_min_discount(self, user_id: int) -> int:
        """Получение минимальной скидки пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT min_discount FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 30
        except Exception as e:
            logger.error(f"Error getting min discount for user {user_id}: {e}")
            return 30
    
    def add_price_record(self, app_id: str, game_title: str, price: float, discount: int):
        """Добавление записи о цене"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO price_history (app_id, game_title, price, discount)
                    VALUES (?, ?, ?, ?)
                ''', (app_id, game_title, price, discount))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding price record: {e}")
    
    def add_price_history(self, app_id: int, title: str, price: float, discount: int = 0):
        """Алиас для add_price_record для совместимости"""
        self.add_price_record(str(app_id), title, price, discount)
    
    def get_price_history(self, app_id: str) -> List[Dict]:
        """Получение истории цен"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT price, discount, recorded_at 
                    FROM price_history 
                    WHERE app_id = ? 
                    ORDER BY recorded_at DESC 
                    LIMIT 10
                ''', (app_id,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'price': row[0],
                        'discount': row[1],
                        'recorded_at': row[2]
                    })
                return results
        except Exception as e:
            logger.error(f"Error getting price history for {app_id}: {e}")
            return []
    
    def add_free_game(self, title: str, description: str, platform: str, url: str, end_date: str = None, image_url: str = None):
        """Добавление бесплатной игры"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO free_games (title, description, platform, url, end_date, image_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, platform, url, end_date, image_url))
                conn.commit()
                logger.info(f"Free game added: {title}")
        except Exception as e:
            logger.error(f"Error adding free game: {e}")
    
    def get_active_free_games(self) -> List[Dict]:
        """Получение активных бесплатных игр"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT title, description, platform, url, end_date, image_url
                    FROM free_games 
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                ''')
                
                games = []
                for row in cursor.fetchall():
                    games.append({
                        'title': row[0],
                        'description': row[1],
                        'platform': row[2],
                        'url': row[3],
                        'end_date': row[4],
                        'image_url': row[5]
                    })
                return games
        except Exception as e:
            logger.error(f"Error getting free games: {e}")
            return []
    
    def get_free_games(self) -> List[Dict]:
        """Алиас для get_active_free_games для совместимости"""
        return self.get_active_free_games()
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Получение всех настроек пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT is_subscribed, min_discount, preferred_genres, language
                    FROM users WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'is_subscribed': bool(result[0]),
                        'min_discount': result[1],
                        'preferred_genres': json.loads(result[2]) if result[2] else [],
                        'language': result[3] if result[3] else 'ru'
                    }
                return {
                    'is_subscribed': False,
                    'min_discount': 30,
                    'preferred_genres': [],
                    'language': 'ru'
                }
        except Exception as e:
            logger.error(f"Error getting user settings for {user_id}: {e}")
            return {
                'is_subscribed': False,
                'min_discount': 30,
                'preferred_genres': [],
                'language': 'ru'
            }

    def add_weekly_top_game(self, title: str, discount: int, price: float, score: float = None):
        """Добавление игры в еженедельный топ с рейтингом"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем, есть ли колонка score в таблице
                cursor.execute("PRAGMA table_info(weekly_top)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'score' not in columns:
                    # Добавляем колонку score если её нет
                    cursor.execute('ALTER TABLE weekly_top ADD COLUMN score REAL DEFAULT 0')
                
                if score is not None:
                    cursor.execute('''
                        INSERT OR REPLACE INTO weekly_top (game_title, discount, discounted_price, score)
                        VALUES (?, ?, ?, ?)
                    ''', (title, discount, str(price), score))
                else:
                    cursor.execute('''
                        INSERT OR REPLACE INTO weekly_top (game_title, discount, discounted_price)
                        VALUES (?, ?, ?)
                    ''', (title, discount, str(price)))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding weekly top game: {e}")

    def get_weekly_top_games(self, limit: int = 5) -> List[Dict]:
        """Получение топ игр недели с учетом рейтинга"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем, есть ли колонка score
                cursor.execute("PRAGMA table_info(weekly_top)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'score' in columns:
                    # Сортируем по рейтингу, если колонка есть
                    cursor.execute('''
                        SELECT game_title, discount, discounted_price, COALESCE(score, discount) as final_score
                        FROM weekly_top 
                        ORDER BY final_score DESC, discount DESC
                        LIMIT ?
                    ''', (limit,))
                else:
                    # Fallback к старому методу
                    cursor.execute('''
                        SELECT game_title, discount, discounted_price, discount as final_score
                        FROM weekly_top 
                        ORDER BY discount DESC 
                        LIMIT ?
                    ''', (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'title': row[0],
                        'discount': row[1],
                        'price': row[2],
                        'score': row[3] if len(row) > 3 else row[1]
                    })
                return results
                
        except Exception as e:
            logger.error(f"Error getting weekly top games: {e}")
            return []

    def clear_weekly_top(self):
        """Очистка еженедельного топа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM weekly_top')
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing weekly top: {e}")

    def add_feedback(self, user_id: int, username: str, feedback_type: str, message: str, rating: int = None):
        """Добавление отзыва от пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO feedback 
                    (user_id, username, feedback_type, message, rating, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, feedback_type, message, rating, datetime.now()))
                conn.commit()
                logger.info(f"Feedback added from user {user_id}: {feedback_type}")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding feedback from user {user_id}: {e}")
            return None

    def get_feedback_stats(self):
        """Получение статистики отзывов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN feedback_type = 'bug' THEN 1 END) as bugs,
                        COUNT(CASE WHEN feedback_type = 'feature' THEN 1 END) as features,
                        COUNT(CASE WHEN feedback_type = 'compliment' THEN 1 END) as compliments,
                        COUNT(CASE WHEN is_resolved = 1 THEN 1 END) as resolved,
                        AVG(rating) as avg_rating
                    FROM feedback
                ''')
                
                row = cursor.fetchone()
                if row:
                    return {
                        'total': row[0],
                        'bugs': row[1],
                        'features': row[2],
                        'compliments': row[3],
                        'resolved': row[4],
                        'avg_rating': round(row[5] or 0, 1)
                    }
                return {}
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {}

    def get_recent_feedback(self, limit: int = 10):
        """Получение последних отзывов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, username, feedback_type, message, rating, 
                           is_resolved, created_at
                    FROM feedback 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'user_id': row[1],
                        'username': row[2],
                        'type': row[3],
                        'message': row[4],
                        'rating': row[5],
                        'resolved': row[6],
                        'created_at': row[7]
                    })
                return results
        except Exception as e:
            logger.error(f"Error getting recent feedback: {e}")
            return []

    def set_user_language(self, user_id: int, language: str):
        """Установка языка пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET language = ?, last_activity = ?
                    WHERE user_id = ?
                ''', (language, datetime.now(), user_id))
                conn.commit()
                logger.info(f"Language updated for user {user_id}: {language}")
        except Exception as e:
            logger.error(f"Error setting language for user {user_id}: {e}")

    def get_user_language(self, user_id: int) -> str:
        """Получение языка пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else 'ru'
        except Exception as e:
            logger.error(f"Error getting language for user {user_id}: {e}")
            return 'ru'

    def is_user_subscribed(self, user_id: int) -> bool:
        """Проверка подписки пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_subscribed FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id}: {e}")
            return False
