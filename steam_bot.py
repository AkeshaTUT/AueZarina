import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import List
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import schedule
import time
import threading
from steam_scraper import SteamScraper
from database import DatabaseManager
from steam_wishlist import get_wishlist_discounts
from steam_library import get_steam_library, get_recently_played_games
from ai_recommendations import get_game_recommendations
from ai_game_recommendations import get_ai_game_recommendations
from config import OPENROUTER_API_KEY, AI_RECOMMENDATIONS_ENABLED, AI_MAX_RECOMMENDATIONS
from translations import get_text, get_available_languages
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SteamDiscountBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
        self.application = Application.builder().token(bot_token).build()
        self.db = DatabaseManager()
        self.scraper = SteamScraper()
        
        # Жанры Steam
        self.available_genres = [
            "Action", "Adventure", "Casual", "Indie", "Massively Multiplayer",
            "Racing", "RPG", "Simulation", "Sports", "Strategy", 
            "Early Access", "Free to Play", "Horror", "Puzzle"
        ]
        
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("deals", self.deals_command))
        self.application.add_handler(CommandHandler("genres", self.genres_command))
        self.application.add_handler(CommandHandler("free", self.free_games_command))
        self.application.add_handler(CommandHandler("discount", self.discount_settings_command))
        self.application.add_handler(CommandHandler("settings", self.user_settings_command))
        self.application.add_handler(CommandHandler("weeklydigest", self.weeklydigest_command))
        self.application.add_handler(CommandHandler("feedback", self.feedback_command))
        
        # Новые функции
        self.application.add_handler(CommandHandler("wishlist", self.wishlist_command))
        self.application.add_handler(CommandHandler("recommend", self.ai_recommendations_command))
        
        # Команды для администратора
        self.application.add_handler(CommandHandler("test_digest", self.test_weekly_digest_command))
        self.application.add_handler(CommandHandler("send_digest", self.admin_send_digest_command))
        
        # Добавляем алиасы для русских пользователей (только латиница)
        self.application.add_handler(CommandHandler("rekomend", self.ai_recommendations_command))
        
        # Обработчик callback запросов (inline кнопки)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик текстовых сообщений только для пользователей в состоянии ожидания
        from telegram.ext import MessageHandler, filters
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_text_messages_conditionally
        ))
        
        # Состояния для многошаговых команд
        self.user_states = {}
        self.user_state_timestamps = {}  # Для отслеживания времени состояний
        
        # Инициализируем базу с примерами бесплатных игр
        self.init_sample_data()
        
    def init_sample_data(self):
        """Инициализация примеров данных"""
        # Добавляем примеры бесплатных игр
        sample_free_games = [
            {
                'title': 'Epic Games Store - Control',
                'description': 'Сверхъестественный экшен-триллер с захватывающим сюжетом',
                'platform': 'Epic Games',
                'url': 'https://store.epicgames.com/en-US/p/control',
                'end_date': '2025-08-02',
                'image_url': 'https://cdn1.epicgames.com/offer/870a3f6935d84ed8a8ad7c12e8b03a2c/EGS_Control_RemedyEntertainment_S1_2560x1440-61c3a5fcf5becd21e8c5696c40e0bafe'
            },
            {
                'title': 'Steam - Counter-Strike 2',
                'description': 'Обновленная версия легендарного шутера',
                'platform': 'Steam',
                'url': 'https://store.steampowered.com/app/730/CounterStrike_2/',
                'end_date': 'Навсегда',
                'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg'
            },
            {
                'title': 'GOG - Cyberpunk 2077 DLC',
                'description': 'Дополнение к киберпанк-RPG (требуется основная игра)',
                'platform': 'GOG',
                'url': 'https://www.gog.com/game/cyberpunk_2077',
                'end_date': '2025-07-30',
                'image_url': 'https://images.gog-statics.com/8e52d66fe0b56d5de96346b64b6ca95a25c1f9eb8c1fb28c58e3eb23f8b5c34c.jpg'
            }
        ]
        
        # Проверяем, есть ли уже данные в базе
        existing_games = self.db.get_active_free_games()
        if not existing_games:
            for game in sample_free_games:
                self.db.add_free_game(**game)
    
    def set_user_state(self, user_id: int, state: str):
        """Устанавливает состояние пользователя с таймаутом"""
        import time
        self.user_states[user_id] = state
        self.user_state_timestamps[user_id] = time.time()
    
    def clear_user_state(self, user_id: int):
        """Очищает состояние пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_state_timestamps:
            del self.user_state_timestamps[user_id]
    
    def cleanup_expired_states(self):
        """Очищает просроченные состояния (старше 10 минут)"""
        import time
        current_time = time.time()
        expired_users = []
        
        for user_id, timestamp in self.user_state_timestamps.items():
            if current_time - timestamp > 600:  # 10 минут
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.clear_user_state(user_id)
    
    def load_subscribers(self):
        """Загружает подписчиков из базы данных (совместимость)"""
        # Метод для совместимости со старым кодом
        pass
        
    def save_subscribers(self):
        """Сохраняет подписчиков (совместимость)"""
        # Метод для совместимости со старым кодом
        pass
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        # Проверяем, выбрал ли пользователь язык
        user_language = self.db.get_user_language(user.id)
        
        # Если язык не установлен или это новый пользователь, показываем выбор языка
        if not user_language or user_language == 'ru':
            # Показываем выбор языка
            keyboard = [
                [
                    InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                    InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                get_text('ru', 'choose_language'),
                reply_markup=reply_markup
            )
        else:
            # Показываем приветствие на выбранном языке
            await self.show_welcome_message(update, user_language)
    
    async def show_welcome_message(self, update: Update, language: str):
        """Показать приветственное сообщение на выбранном языке"""
        welcome_message = f"""
{get_text(language, 'welcome_title')} 

{get_text(language, 'welcome_description')}

{get_text(language, 'main_features')}
{get_text(language, 'genre_filter')}
{get_text(language, 'free_games')}
{get_text(language, 'price_history')}
{get_text(language, 'personal_settings')}
{get_text(language, 'weekly_digest')}

{get_text(language, 'new_features')}
{get_text(language, 'wishlist_analysis')}
{get_text(language, 'ai_recommendations')}

{get_text(language, 'basic_commands')}
{get_text(language, 'cmd_subscribe')}
{get_text(language, 'cmd_deals')}
{get_text(language, 'cmd_genres')}
{get_text(language, 'cmd_free')}
{get_text(language, 'cmd_discount')}
{get_text(language, 'cmd_settings')}

{get_text(language, 'new_commands')}
{get_text(language, 'cmd_wishlist')}
{get_text(language, 'cmd_recommend')}
{get_text(language, 'cmd_help')}

{get_text(language, 'auto_notifications')}
        """
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        language = self.db.get_user_language(user_id)
        
        help_message = f"""
{get_text(language, 'all_commands')}

{get_text(language, 'basic_title')}
{get_text(language, 'start_desc')}
{get_text(language, 'subscribe_desc')}
{get_text(language, 'unsubscribe_desc')}
{get_text(language, 'deals_desc')}
{get_text(language, 'free_desc')}
{get_text(language, 'genres_desc')}
{get_text(language, 'discount_desc')}
{get_text(language, 'settings_desc')}
{get_text(language, 'weeklydigest_desc')}
{get_text(language, 'feedback_desc')}

{get_text(language, 'new_title')}
{get_text(language, 'wishlist_desc')}
{get_text(language, 'recommend_desc')}

{get_text(language, 'help_footer')}
        """
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /subscribe"""
        user_id = update.effective_user.id
        user = update.effective_user
        language = self.db.get_user_language(user_id)
        
        # Добавляем пользователя если его нет
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        if self.db.subscribe_user(user_id):
            response = get_text(language, 'subscribed_success')
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(get_text(language, 'already_subscribed'))
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /unsubscribe"""
        user_id = update.effective_user.id
        language = self.db.get_user_language(user_id)
        
        if self.db.unsubscribe_user(user_id):
            await update.message.reply_text(get_text(language, 'unsubscribed_success'))
        else:
            await update.message.reply_text(get_text(language, 'not_subscribed'))
    
    async def genres_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /genres - настройка жанров"""
        user_id = update.effective_user.id
        user = update.effective_user
        language = self.db.get_user_language(user_id)
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        current_genres = self.db.get_user_genres(user_id)
        
        # Создаем inline клавиатуру с жанрами
        keyboard = []
        for i in range(0, len(self.available_genres), 2):
            row = []
            for j in range(2):
                if i + j < len(self.available_genres):
                    genre = self.available_genres[i + j]
                    # Отмечаем выбранные жанры
                    prefix = "✅ " if genre in current_genres else ""
                    row.append(InlineKeyboardButton(
                        f"{prefix}{genre}", 
                        callback_data=f"genre_{genre}"
                    ))
            keyboard.append(row)
        
        # Добавляем кнопки управления
        keyboard.append([
            InlineKeyboardButton(get_text(language, 'clear_all_genres'), callback_data="genre_clear"),
            InlineKeyboardButton(get_text(language, 'save_genres'), callback_data="genre_save")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = get_text(language, 'select_genres_title')
        if current_genres:
            message += get_text(language, 'selected_genres', genres=', '.join(current_genres))
        else:
            message += get_text(language, 'all_genres_selected')
        message += get_text(language, 'genres_instruction')
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def free_games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /free - бесплатные раздачи"""
        user_id = update.effective_user.id
        user = update.effective_user
        language = self.db.get_user_language(user_id)
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        await update.message.reply_text(get_text(language, 'searching_free_games'))
        
        try:
            # Импортируем упрощенный парсер бесплатных игр
            from simple_free_games_parser import get_current_free_games
            
            # Получаем реальные данные
            all_games = await get_current_free_games()
            
            # Обновляем базу данных актуальными играми
            await self._update_database_with_live_games(all_games)
            
            if not all_games:
                await update.message.reply_text(get_text(language, 'no_free_games'))
                return
            
            # Ограничиваем количество для отображения
            display_games = all_games[:10]
            message = f"{get_text(language, 'free_games_title')}\n\n"
            
            for game in display_games:
                # Определяем эмодзи платформы
                platform_emoji = {
                    'Steam': '🟦',
                    'Epic Games Store': '🟪', 
                    'GOG': '🟫',
                    'Other': '⚪'
                }.get(game.get('platform', 'Other'), '⚪')
                
                title = game.get('title', 'Unknown Game' if language == 'en' else 'Неизвестная игра')
                description = game.get('description', 'No description' if language == 'en' else 'Описание отсутствует')
                end_date = game.get('end_date', 'Unknown' if language == 'en' else 'Неизвестно')
                url = game.get('url', '')
                
                message += f"{platform_emoji} <b>{title}</b>\n"
                message += f"📝 {description}\n"
                message += f"🗓️ {get_text(language, 'game_ends')}{end_date}\n"
                if url:
                    get_game_text = "Get game" if language == 'en' else "Получить игру"
                    message += f"🔗 <a href='{url}'>{get_game_text}</a>\n"
                message += "\n"
            
            if len(all_games) > 10:
                more_text = f"And {len(all_games) - 10} more giveaways..." if language == 'en' else f"И еще {len(all_games) - 10} раздач..."
                message += f"💡 <i>{more_text}</i>\n"
            
            realtime_text = "Data updated in real time" if language == 'en' else "Данные обновляются в реальном времени"
            message += f"\n🔄 <i>{realtime_text}</i>"
            
            # Разбиваем сообщение если оно слишком длинное
            if len(message) > 4000:
                chunks = self.split_message(message, 4000)
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
            else:
                await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
                
        except Exception as e:
            logger.error(f"Error getting free games: {e}")
            await update.message.reply_text(get_text(language, 'error_free_games'))
    
    async def _update_database_with_live_games(self, games: list):
        """Обновляет базу данных актуальными играми"""
        try:
            # Очищаем старые записи
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM free_games WHERE created_at < datetime("now", "-1 day")')
                conn.commit()
            
            # Добавляем новые игры
            for game in games:
                try:
                    self.db.add_free_game(
                        title=game.get('title', 'Неизвестная игра'),
                        description=game.get('description', 'Описание отсутствует'),
                        platform=game.get('platform', 'Other'),
                        url=game.get('url', ''),
                        end_date=game.get('end_date', 'Неизвестно'),
                        image_url=game.get('image_url', '')
                    )
                except Exception as e:
                    logger.error(f"Error adding game to database: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating database with live games: {e}")
    
    async def discount_settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /discount - настройка минимальной скидки"""
        user_id = update.effective_user.id
        user = update.effective_user
        language = self.db.get_user_language(user_id)
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        current_discount = self.db.get_user_min_discount(user_id)
        
        # Создаем inline клавиатуру с вариантами скидок
        keyboard = [
            [
                InlineKeyboardButton("30%" + (" ✅" if current_discount == 30 else ""), callback_data="discount_30"),
                InlineKeyboardButton("50%" + (" ✅" if current_discount == 50 else ""), callback_data="discount_50")
            ],
            [
                InlineKeyboardButton("70%" + (" ✅" if current_discount == 70 else ""), callback_data="discount_70"),
                InlineKeyboardButton("90%" + (" ✅" if current_discount == 90 else ""), callback_data="discount_90")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = get_text(language, 'discount_settings_title')
        message += get_text(language, 'current_discount', discount=current_discount)
        message += get_text(language, 'select_min_discount')
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def user_settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings - показ настроек пользователя"""
        user_id = update.effective_user.id
        user = update.effective_user
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        settings = self.db.get_user_settings(user_id)
        language = settings.get('language', 'ru')
        
        subscription_status = get_text(language, 'subscribed') if settings['is_subscribed'] else get_text(language, 'not_subscribed_status')
        genres_text = ', '.join(settings['preferred_genres']) if settings['preferred_genres'] else get_text(language, 'no_genres_selected')
        
        message = f"{get_text(language, 'your_settings')}\n\n"
        message += f"🔔 {get_text(language, 'subscription_status')}{subscription_status}\n"
        message += f"💰 {get_text(language, 'min_discount_setting')}<b>{settings['min_discount']}%</b>\n"
        message += f"🎮 {get_text(language, 'selected_genres')}{genres_text}\n"
        message += f"🌍 Language: {'🇷🇺 Русский' if language == 'ru' else '🇺🇸 English'}\n"
        
        # Добавляем кнопку для смены языка
        keyboard = [
            [InlineKeyboardButton(get_text(language, 'change_language'), callback_data="change_language")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith("lang_"):
            await self.handle_language_callback(query, user_id, data)
        elif data == "change_language":
            await self.handle_change_language_callback(query, user_id)
        elif data.startswith("genre_"):
            await self.handle_genre_callback(query, user_id, data)
        elif data.startswith("discount_"):
            await self.handle_discount_callback(query, user_id, data)
        elif data.startswith("feedback_"):
            await self.handle_feedback_callback(query, user_id, data)
    
    async def handle_language_callback(self, query, user_id: int, data: str):
        """Обработка callback для выбора языка"""
        language = data.replace("lang_", "")
        
        # Сохраняем выбранный язык
        self.db.set_user_language(user_id, language)
        
        # Отправляем подтверждение и приветственное сообщение
        await query.edit_message_text(get_text(language, 'language_changed'))
        
        # Создаем фиктивное обновление для отправки приветственного сообщения
        from telegram import Message, Chat, User
        fake_message = Message(
            message_id=0,
            date=None,
            chat=query.message.chat,
            from_user=query.from_user
        )
        fake_update = type('Update', (), {
            'message': fake_message,
            'effective_user': query.from_user
        })()
        
        # Отправляем приветственное сообщение на выбранном языке
        await self.show_welcome_message(fake_update, language)
    
    async def handle_change_language_callback(self, query, user_id: int):
        """Обработка callback для смены языка из настроек"""
        current_language = self.db.get_user_language(user_id)
        
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
            ],
            [InlineKeyboardButton(get_text(current_language, 'back_button'), callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_text(current_language, 'choose_language'),
            reply_markup=reply_markup
        )
    
    async def handle_genre_callback(self, query, user_id: int, data: str):
        """Обработка callback для жанров"""
        language = self.db.get_user_language(user_id)
        current_genres = self.db.get_user_genres(user_id)
        
        if data == "genre_clear":
            # Очищаем все жанры
            self.db.set_user_genres(user_id, [])
            if language == 'ru':
                message = "🎮 <b>Все жанры очищены!</b>\n\nТеперь будут показываться игры всех жанров.\n\nИспользуйте /genres для новых настроек."
            else:
                message = "🎮 <b>All genres cleared!</b>\n\nNow games of all genres will be shown.\n\nUse /genres for new settings."
            await query.edit_message_text(message, parse_mode='HTML')
            return
        elif data == "genre_save":
            # Сохраняем настройки
            genres_text = ', '.join(current_genres) if current_genres else (
                "Все жанры" if language == 'ru' else "All genres"
            )
            if language == 'ru':
                message = f"✅ <b>Настройки жанров сохранены!</b>\n\n🎮 Выбранные жанры: {genres_text}\n\nТеперь в рассылке будут только игры выбранных жанров."
            else:
                message = f"✅ <b>Genre settings saved!</b>\n\n🎮 Selected genres: {genres_text}\n\nNow only games of selected genres will be shown in notifications."
            await query.edit_message_text(message, parse_mode='HTML')
            return
        else:
            # Переключаем жанр
            genre = data.replace("genre_", "")
            if genre in current_genres:
                current_genres.remove(genre)
            else:
                current_genres.append(genre)
            
            self.db.set_user_genres(user_id, current_genres)
        
        # Обновляем клавиатуру
        keyboard = []
        for i in range(0, len(self.available_genres), 2):
            row = []
            for j in range(2):
                if i + j < len(self.available_genres):
                    genre = self.available_genres[i + j]
                    prefix = "✅ " if genre in current_genres else ""
                    row.append(InlineKeyboardButton(
                        f"{prefix}{genre}", 
                        callback_data=f"genre_{genre}"
                    ))
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton(get_text(language, 'clear_all_genres'), callback_data="genre_clear"),
            InlineKeyboardButton(get_text(language, 'save_genres'), callback_data="genre_save")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = get_text(language, 'select_genres_title')
        if current_genres:
            message += get_text(language, 'selected_genres', genres=', '.join(current_genres))
        else:
            message += get_text(language, 'all_genres_selected')
        message += get_text(language, 'genres_instruction')
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_discount_callback(self, query, user_id: int, data: str):
        """Обработка callback для настройки скидки"""
        language = self.db.get_user_language(user_id)
        discount_value = int(data.replace("discount_", ""))
        self.db.set_user_min_discount(user_id, discount_value)
        
        message = get_text(language, 'discount_updated', discount=discount_value)
        if language == 'ru':
            message += f"\n\nТеперь в рассылке будут только игры со скидкой от {discount_value}% и выше."
        else:
            message += f"\n\nNow notifications will only include games with discounts of {discount_value}% and higher."
        
        await query.edit_message_text(message, parse_mode='HTML')

    async def handle_feedback_callback(self, query, user_id: int, data: str):
        """Обработка callback для отзывов"""
        language = self.db.get_user_language(user_id)
        user = query.from_user
        username = user.username or user.first_name or str(user_id)
        
        if data == "feedback_bug":
            # Устанавливаем состояние ожидания сообщения о баге
            self.set_user_state(user_id, "waiting_bug_report")
            message = get_text(language, 'feedback_prompt')
            await query.edit_message_text(message, parse_mode='HTML')
            
        elif data == "feedback_feature":
            # Устанавливаем состояние ожидания предложения
            self.set_user_state(user_id, "waiting_feature_request")
            message = get_text(language, 'feedback_prompt')
            await query.edit_message_text(message, parse_mode='HTML')
            
        elif data == "feedback_review":
            # Устанавливаем состояние ожидания отзыва
            self.set_user_state(user_id, "waiting_review")
            message = get_text(language, 'feedback_prompt')
            await query.edit_message_text(message, parse_mode='HTML')
            
        elif data == "feedback_stats":
            # Показываем статистику отзывов
            stats = self.db.get_feedback_stats()
            if stats.get('total', 0) > 0:
                message = (
                    f"📊 **Статистика отзывов**\n\n"
                    f"📝 Всего сообщений: **{stats['total']}**\n"
                    f"🐛 Багов: **{stats['bugs']}**\n"
                    f"💡 Идей: **{stats['features']}**\n"
                    f"❤️ Отзывов: **{stats['compliments']}**\n"
                    f"✅ Решено: **{stats['resolved']}**\n"
                )
                if stats.get('avg_rating', 0) > 0:
                    rating_stars = "⭐" * int(stats['avg_rating'])
                    message += f"⭐ Средняя оценка: **{stats['avg_rating']}/5** {rating_stars}"
            else:
                message = "📊 **Статистика отзывов**\n\nПока что отзывов нет. Станьте первым!"
                
            await query.edit_message_text(message, parse_mode='Markdown')
    
    async def deals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /deals"""
        user_id = update.effective_user.id
        language = self.db.get_user_language(user_id)
        
        await update.message.reply_text(get_text(language, 'searching_deals'))
        
        try:
            # Регистрируем пользователя если его нет в базе
            self.db.add_user(user_id)
            
            # Получаем настройки пользователя
            user_genres = self.db.get_user_genres(user_id)
            min_discount = self.db.get_user_min_discount(user_id)
            
            deals = await self.scraper.get_discounted_games()
            
            # Фильтруем игры по пользовательским настройкам
            filtered_deals = self.filter_deals_by_user_preferences(deals, user_genres, min_discount)
            
            # Обновляем данные для еженедельного дайджеста
            self.update_weekly_digest_data(deals)
            
            if filtered_deals:
                message = self.format_deals_message(filtered_deals, user_id, language)
                
                # Telegram имеет ограничение на длину сообщения в 4096 символов
                if len(message) > 4000:
                    # Разбиваем на несколько сообщений
                    chunks = self.split_message(message, 4000)
                    for chunk in chunks:
                        await update.message.reply_text(chunk, parse_mode='HTML')
                else:
                    await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text(get_text(language, 'no_suitable_deals', min_discount=min_discount))
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            await update.message.reply_text(get_text(language, 'error_getting_deals'))
    
    def filter_deals_by_user_preferences(self, deals, user_genres, min_discount):
        """Фильтрует игры по пользовательским настройкам"""
        if not deals:
            return []
        
        filtered_deals = []
        
        for deal in deals:
            # Проверяем минимальную скидку
            discount = deal.get('discount', 0)
            if discount < min_discount:
                continue
            
            # Если у пользователя выбраны жанры, проверяем соответствие
            if user_genres:
                game_genres = deal.get('genres', [])
                if not any(genre in user_genres for genre in game_genres):
                    continue
            
            filtered_deals.append(deal)
        
        return filtered_deals
    
    def format_deals_message(self, deals, user_id: int, language: str = 'ru'):
        """Форматирует сообщение со скидками с учетом истории цен"""
        if not deals:
            return get_text(language, 'no_suitable_deals', min_discount=30)
        
        # Заголовок на соответствующем языке
        title_text = "Актуальные скидки Steam" if language == 'ru' else "Current Steam Deals"
        games_text = "игр" if language == 'ru' else "games"
        message = f"🎮 <b>{title_text} ({len(deals)} {games_text})</b>\n\n"
        
        # Показываем все найденные игры, не ограничивая до 20
        for deal in deals:
            discount = deal.get('discount', 0)
            title = deal.get('title', 'Unknown Game' if language == 'en' else 'Неизвестная игра')
            url = deal.get('url', '')
            original_price = deal.get('original_price', '')
            discounted_price = deal.get('discounted_price', '')
            game_id = deal.get('app_id', 0)
            
            # Эмодзи в зависимости от размера скидки
            if discount >= 90:
                emoji = "🔥"
            elif discount >= 70:
                emoji = "⚡"
            elif discount >= 50:
                emoji = "💥"
            else:
                emoji = "💰"
            
            message += f"{emoji} <b>{title}</b>\n"
            message += f"💸 Скидка: <b>-{discount}%</b>\n"
            
            if original_price and discounted_price:
                message += f"💰 <s>{original_price}</s> → <b>{discounted_price}</b>\n"
            
            # Добавляем информацию об истории цен
            price_history = self.db.get_price_history(game_id)
            if price_history:
                lowest_price = min([p['price'] for p in price_history])
                try:
                    current_price = float(discounted_price.replace('₽', '').replace(',', '').strip())
                    if current_price <= lowest_price:
                        message += f"🎯 <b>Исторический минимум!</b>\n"
                    else:
                        message += f"📊 Мин. цена: <b>{lowest_price}₽</b>\n"
                except:
                    pass
            
            if url:
                message += f"🔗 <a href='{url}'>Перейти в Steam</a>\n"
            
            message += "\n"
            
            # Сохраняем историю цен
            if game_id and discounted_price:
                try:
                    price = float(discounted_price.replace('₽', '').replace(',', '').strip())
                    self.db.add_price_history(game_id, title, price)
                except:
                    pass
        
        return message
    
    async def weeklydigest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет еженедельный дайджест топ-5 игр с самыми большими скидками"""
        user_id = update.effective_user.id
        language = self.db.get_user_language(user_id)
        
        await update.message.reply_text(get_text(language, 'generating_weekly_digest'))
        
        try:
            # Получаем топ-5 игр за неделю
            weekly_top = self.db.get_weekly_top_games()
            
            if weekly_top:
                message = get_text(language, 'weekly_digest_title') + "\n\n"
                message += get_text(language, 'weekly_digest_subtitle') + "\n\n"
                
                for i, game in enumerate(weekly_top[:5], 1):
                    emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
                    message += f"{emoji} <b>{game['title']}</b>\n"
                    
                    if language == 'ru':
                        message += f"💸 Скидка: <b>-{game['discount']}%</b>\n"
                        message += f"💰 Цена: <b>{game['price']}₽</b>\n\n"
                    else:
                        message += f"� Discount: <b>-{game['discount']}%</b>\n"
                        message += f"💰 Price: <b>${game['price']}</b>\n\n"
                
                await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text(get_text(language, 'no_weekly_data'))
                
        except Exception as e:
            logger.error(f"Error getting weekly digest: {e}")
            await update.message.reply_text(get_text(language, 'error_getting_digest'))
    
    async def send_weekly_digest_to_all(self):
        """Отправляет еженедельный дайджест всем пользователям"""
        try:
            users = self.db.get_subscribed_users()
            weekly_top = self.db.get_weekly_top_games()
            
            if not weekly_top:
                logger.info("No weekly data available for digest")
                return
            
            logger.info(f"Sending weekly digest to {len(users)} users")
            
            # Отправляем всем подписанным пользователям
            sent_count = 0
            failed_count = 0
            
            for user_id in users:
                try:
                    # Получаем язык пользователя
                    language = self.db.get_user_language(user_id)
                    
                    # Формируем сообщение на языке пользователя
                    message = get_text(language, 'weekly_digest_title') + "\n\n"
                    message += get_text(language, 'weekly_digest_subtitle') + "\n\n"
                    
                    for i, game in enumerate(weekly_top[:5], 1):
                        emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
                        message += f"{emoji} <b>{game['title']}</b>\n"
                        
                        if language == 'ru':
                            message += f"💸 Скидка: <b>-{game['discount']}%</b>\n"
                            message += f"💰 Цена: <b>{game['price']}₽</b>\n\n"
                        else:
                            message += f"💸 Discount: <b>-{game['discount']}%</b>\n"
                            message += f"💰 Price: <b>${game['price']}</b>\n\n"
                    
                    # Добавляем призыв к действию
                    message += get_text(language, 'weekly_digest_cta')
                    
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)  # Небольшая задержка между отправками
                    
                except Exception as e:
                    logger.error(f"Failed to send weekly digest to user {user_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Weekly digest sent: {sent_count} successful, {failed_count} failed")
            
            # Очищаем данные для новой недели
            self.db.clear_weekly_top()
            
        except Exception as e:
            logger.error(f"Error sending weekly digest: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик для еженедельной рассылки"""
        def schedule_checker():
            logger.info("Weekly digest scheduler thread started")
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Проверяем каждую минуту
                except Exception as e:
                    logger.error(f"Error in scheduler: {e}")
                    time.sleep(60)
        
        # Планируем отправку каждую неделю в воскресенье в 18:00 МСК
        def run_weekly_digest():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.send_weekly_digest_to_all())
                loop.close()
            except Exception as e:
                logger.error(f"Error running weekly digest: {e}")
        
        schedule.every().sunday.at("18:00").do(run_weekly_digest)
        
        # Для тестирования - можно раскомментировать для отправки каждые 5 минут
        # schedule.every(5).minutes.do(run_weekly_digest)
        
        # Запускаем планировщик в отдельном потоке
        scheduler_thread = threading.Thread(target=schedule_checker, daemon=True)
        scheduler_thread.start()
        logger.info("Weekly digest scheduler configured: every Sunday at 18:00 MSK")

    def update_weekly_digest_data(self, deals):
        """Обновляет данные для еженедельного дайджеста на основе полученных скидок с учетом популярности"""
        try:
            if not deals:
                return
            
            # Рассчитываем рейтинг для каждой игры на основе нескольких факторов
            scored_deals = []
            
            for deal in deals:
                title = deal.get('title', '')
                discount = deal.get('discount', 0)
                discounted_price = deal.get('discounted_price', '0')
                
                # Извлекаем числовое значение цены
                try:
                    price_str = str(discounted_price).replace('₽', '').replace('$', '').replace(',', '.').strip()
                    price = float(price_str) if price_str else 0.0
                except (ValueError, AttributeError):
                    price = 0.0
                
                if not title or discount <= 0:
                    continue
                
                # Рассчитываем комплексный рейтинг игры
                score = self._calculate_game_score(deal)
                
                scored_deals.append({
                    'deal': deal,
                    'title': title,
                    'discount': discount,
                    'price': price,
                    'score': score
                })
            
            # Сортируем по комплексному рейтингу (по убыванию)
            sorted_deals = sorted(scored_deals, key=lambda x: x['score'], reverse=True)
            
            # Берем топ-15 игр с лучшим рейтингом для еженедельного дайджеста
            top_deals = sorted_deals[:15]
            
            for scored_deal in top_deals:
                title = scored_deal['title']
                discount = scored_deal['discount']
                price = scored_deal['price']
                score = scored_deal['score']
                
                # Сохраняем в базу с дополнительной информацией о рейтинге
                self.db.add_weekly_top_game(title, discount, price, score)
                    
            logger.info(f"Updated weekly digest data with {len(top_deals)} games (algorithm: discount + popularity)")
            
        except Exception as e:
            logger.error(f"Error updating weekly digest data: {e}")
    
    def _calculate_game_score(self, deal):
        """Рассчитывает комплексный рейтинг игры для еженедельного дайджеста"""
        try:
            # Базовые параметры
            discount = deal.get('discount', 0)
            title = deal.get('title', '').lower()
            
            # Извлекаем цену
            discounted_price = deal.get('discounted_price', '0')
            try:
                price_str = str(discounted_price).replace('₽', '').replace('$', '').replace(',', '.').strip()
                price = float(price_str) if price_str else 0.0
            except:
                price = 0.0
            
            # 1. Базовый рейтинг скидки (0-100 баллов)
            discount_score = min(discount, 90)  # Максимум 90 баллов за скидку
            
            # 2. Популярность игры (эвристический подход)
            popularity_score = 0
            
            # Известные популярные игры/серии (бонус +30 баллов)
            popular_keywords = [
                'cyberpunk', 'witcher', 'gta', 'elder scrolls', 'fallout', 'assassin',
                'call of duty', 'battlefield', 'counter-strike', 'dota', 'steam',
                'fifa', 'tomb raider', 'far cry', 'watch dogs', 'rainbow six',
                'grand theft', 'red dead', 'mass effect', 'dragon age', 'bioshock',
                'borderlands', 'civilization', 'total war', 'mortal kombat', 'tekken',
                'street fighter', 'dark souls', 'elden ring', 'sekiro', 'bloodborne',
                'resident evil', 'silent hill', 'dead space', 'metro', 'stalker',
                'dying light', 'left 4 dead', 'portal', 'half-life', 'team fortress',
                'dishonored', 'prey', 'doom', 'wolfenstein', 'quake', 'unreal',
                'forza', 'need for speed', 'burnout', 'dirt', 'f1', 'wreckfest',
                'xcom', 'cities skylines', 'europa universalis', 'crusader kings',
                'hearts of iron', 'stellaris', 'age of empires', 'starcraft',
                'warcraft', 'world of warcraft', 'overwatch', 'diablo', 'heroes',
                'destiny', 'division', 'ghost recon', 'splinter cell', 'prince',
                'just cause', 'saints row', 'mafia', 'hitman', 'deus ex',
                'batman', 'spider-man', 'mortal kombat', 'injustice', 'marvel',
                'dc comics', 'lego', 'minecraft', 'terraria', 'stardew valley',
                'hollow knight', 'ori and', 'cuphead', 'celeste', 'hades',
                'rocket league', 'fall guys', 'among us', 'valheim', 'rust',
                'pubg', 'fortnite', 'apex legends', 'titanfall', 'warframe'
            ]
            
            for keyword in popular_keywords:
                if keyword in title:
                    popularity_score += 30
                    break  # Только один бонус за популярность
            
            # 3. Ценовая категория (баланс цена/качество)
            price_score = 0
            if 0 < price <= 500:      # Доступные игры
                price_score = 25
            elif 500 < price <= 1500: # Средний сегмент
                price_score = 20
            elif 1500 < price <= 3000: # Премиум игры
                price_score = 15
            else:                     # Очень дорогие
                price_score = 5
            
            # 4. Бонусы за особые ключевые слова
            bonus_score = 0
            
            # Свежие/популярные жанры (+10 баллов)
            trending_keywords = [
                'battle royale', 'survival', 'crafting', 'open world', 'rpg',
                'multiplayer', 'co-op', 'indie', 'early access', 'vr',
                'roguelike', 'metroidvania', 'soulslike', 'tactical', 'strategy'
            ]
            
            game_description = deal.get('description', '').lower()
            full_text = title + ' ' + game_description
            
            for keyword in trending_keywords:
                if keyword in full_text:
                    bonus_score += 5
                    break
            
            # 5. Штрафы
            penalty = 0
            
            # Штраф за DLC/Season Pass (-15 баллов)
            dlc_keywords = ['dlc', 'season pass', 'expansion', 'add-on', 'downloadable content']
            for keyword in dlc_keywords:
                if keyword in title:
                    penalty += 15
                    break
            
            # Штраф за очень старые игры (примерно по году в названии)
            old_years = ['2010', '2011', '2012', '2013', '2014', '2015']
            for year in old_years:
                if year in title:
                    penalty += 10
                    break
            
            # Финальный рейтинг
            final_score = discount_score + popularity_score + price_score + bonus_score - penalty
            
            # Нормализуем в диапазон 0-200
            final_score = max(0, min(final_score, 200))
            
            logger.debug(f"Game score for '{deal.get('title', '')}': {final_score} "
                        f"(discount: {discount_score}, popularity: {popularity_score}, "
                        f"price: {price_score}, bonus: {bonus_score}, penalty: {penalty})")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating game score: {e}")
            return deal.get('discount', 0)  # Fallback к старому алгоритму

    async def test_weekly_digest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для тестирования еженедельного дайджеста (только для администратора)"""
        user_id = update.effective_user.id
        language = self.db.get_user_language(user_id)
        
        # Проверяем, является ли пользователь администратором (можно добавить список админов)
        admin_ids = [user_id]  # Временно делаем пользователя админом для тестирования
        
        if user_id not in admin_ids:
            await update.message.reply_text(get_text(language, 'admin_only'))
            return
        
        try:
            weekly_top = self.db.get_weekly_top_games()
            
            if not weekly_top:
                message = get_text(language, 'digest_test_title') + "\n\n" + get_text(language, 'no_digest_data')
            else:
                message = get_text(language, 'digest_test_title') + "\n\n"
                message += get_text(language, 'digest_data_found', count=len(weekly_top)) + "\n\n"
                
                for i, game in enumerate(weekly_top[:10], 1):
                    if language == 'ru':
                        message += f"{i}. <b>{game['title']}</b> - {game['discount']}% (-{game['price']}₽)\n"
                    else:
                        message += f"{i}. <b>{game['title']}</b> - {game['discount']}% (${game['price']})\n"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in test digest command: {e}")
            await update.message.reply_text(get_text(language, 'digest_error'))

    async def admin_send_digest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для принудительной отправки еженедельного дайджеста (только для администратора)"""
        user_id = update.effective_user.id
        language = self.db.get_user_language(user_id)
        
        # Проверяем, является ли пользователь администратором
        admin_ids = [user_id]  # Временно делаем пользователя админом для тестирования
        
        if user_id not in admin_ids:
            await update.message.reply_text(get_text(language, 'admin_only'))
            return
        
        try:
            await update.message.reply_text(get_text(language, 'sending_digest'))
            await self.send_weekly_digest_to_all()
            await update.message.reply_text(get_text(language, 'digest_sent'))
                
        except Exception as e:
            logger.error(f"Error in admin send digest command: {e}")
            await update.message.reply_text(get_text(language, 'digest_send_error'))

    def split_message(self, message, max_length):
        """Разбивает длинное сообщение на части"""
        chunks = []
        current_chunk = ""
        header_added = False
        
        lines = message.split('\n')
        header = lines[0] + '\n\n' if lines else ""
        
        for line in lines:
            # Добавляем заголовок только в первый чанк
            if not header_added and line.startswith("🎮"):
                header_added = True
                current_chunk = line + '\n\n'
                continue
                
            if len(current_chunk + line + '\n') > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Для последующих чанков добавляем сокращенный заголовок
                    current_chunk = f"🎮 <b>Продолжение списка скидок</b>\n\n{line}\n"
                else:
                    chunks.append(line)
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    async def send_deals_to_subscribers(self):
        """Отправляет скидки всем подписчикам"""
        if not self.subscribers:
            logger.info("No subscribers to send deals to")
            return
        
        try:
            deals = await self.scraper.get_discounted_games()
            if not deals:
                logger.info("No deals found to send")
                return
            
            message = "🔔 <b>Новые скидки в Steam!</b>\n\n" + self.format_deals_message(deals)
            
            failed_sends = []
            for subscriber_id in self.subscribers.copy():
                try:
                    if len(message) > 4000:
                        chunks = self.split_message(message, 4000)
                        for chunk in chunks:
                            await self.bot.send_message(
                                chat_id=subscriber_id,
                                text=chunk,
                                parse_mode='HTML'
                            )
                    else:
                        await self.bot.send_message(
                            chat_id=subscriber_id,
                            text=message,
                            parse_mode='HTML'
                        )
                    logger.info(f"Sent deals to subscriber {subscriber_id}")
                except Exception as e:
                    logger.error(f"Failed to send to subscriber {subscriber_id}: {e}")
                    failed_sends.append(subscriber_id)
            
            # Удаляем неактивных подписчиков
            for failed_id in failed_sends:
                self.subscribers.discard(failed_id)
            
            if failed_sends:
                self.save_subscribers()
                
        except Exception as e:
            logger.error(f"Error sending deals to subscribers: {e}")

    # ================== НОВЫЕ ФУНКЦИИ ==================
    
    async def wishlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /wishlist - анализ Steam Wishlist"""
        user_id = update.effective_user.id
        user = update.effective_user
        language = self.db.get_user_language(user_id)
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        # Проверяем, есть ли аргументы команды (ссылка на профиль)
        if context.args:
            profile_url = ' '.join(context.args)
            await self._process_wishlist(update, profile_url, language)
        else:
            # Запрашиваем ссылку на профиль
            if language == 'en':
                message = """
💝 <b>Steam Wishlist Analysis</b>

Send a link to your <b>public</b> Steam profile to check discounts on games from your wishlist.

📝 <b>Example links:</b>
• https://steamcommunity.com/id/your_username
• https://steamcommunity.com/profiles/76561198XXXXXXXXX

⚠️ <b>Important:</b> Profile must be public and wishlist must be open for viewing.

🔗 Just send your Steam profile link to get started!
                """
            else:
                message = """
💝 <b>Анализ Steam Wishlist</b>

Отправьте ссылку на ваш <b>публичный</b> Steam-профиль для проверки скидок на игры из списка желаемого.

📝 <b>Примеры ссылок:</b>
• https://steamcommunity.com/id/ваш_ник
• https://steamcommunity.com/profiles/76561198XXXXXXXXX

⚠️ <b>Важно:</b> Профиль должен быть публичным, а список желаемого - открытым для просмотра.

🔗 Просто отправьте ссылку на ваш Steam-профиль!
                """
            
            # Сохраняем состояние ожидания ссылки
            self.set_user_state(user_id, 'waiting_for_wishlist_url')
            
            await update.message.reply_text(message, parse_mode='HTML')
    
    async def _process_wishlist(self, update: Update, profile_url: str, language: str = 'ru'):
        """Обрабатывает анализ wishlist"""
        user_id = update.effective_user.id
        
        await update.message.reply_text(get_text(language, 'analyzing_wishlist'))
        
        try:
            # Очищаем состояние
            self.clear_user_state(user_id)
            
            # Проверяем валидность URL
            if not ('steamcommunity.com/id/' in profile_url or 'steamcommunity.com/profiles/' in profile_url):
                if language == 'en':
                    error_msg = (
                        "❌ <b>Invalid profile link</b>\n\n"
                        "Send a link in one of the formats:\n"
                        "• https://steamcommunity.com/id/your_username\n"
                        "• https://steamcommunity.com/profiles/76561198XXXXXXXXX"
                    )
                else:
                    error_msg = (
                        "❌ <b>Неверная ссылка на профиль</b>\n\n"
                        "Отправьте ссылку в одном из форматов:\n"
                        "• https://steamcommunity.com/id/ваш_ник\n"
                        "• https://steamcommunity.com/profiles/76561198XXXXXXXXX"
                    )
                await update.message.reply_text(error_msg, parse_mode='HTML')
                return
            
            # Получаем скидки из wishlist
            discounted_games = await get_wishlist_discounts(profile_url)
            
            if not discounted_games:
                message = """
😔 <b>Результат анализа Wishlist:</b>

К сожалению, не удалось найти игры со скидками в вашем Wishlist.

<b>Наиболее частые причины:</b>
• 🔒 <b>Wishlist приватный</b> - даже если профиль публичный, wishlist может быть скрыт
• 📋 <b>Wishlist пустой</b> - в списке желаемого нет игр
• 💰 <b>Нет текущих скидок</b> - на игры из wishlist сейчас нет акций
• ⏱️ <b>Ограничения Steam</b> - слишком много запросов к API

<b>🔧 Как проверить настройки wishlist:</b>
1. Зайдите в Steam → Ваш профиль
2. Нажмите "Редактировать профиль"
3. Выберите "Настройки приватности"
4. Найдите "Детали игры" → установите <b>"Публичные"</b>
5. Найдите "Список желаемого" → установите <b>"Публичный"</b>

<b>🎯 Важно:</b> Steam имеет отдельные настройки для:
• Профиля (может быть публичным)
• Деталей игр (библиотека, время в играх)
• Списка желаемого (wishlist)

<b>💡 Что еще попробовать:</b>
• Убедитесь, что в wishlist есть игры
• Подождите 10-15 минут и попробуйте снова
• Проверьте, что ваш профиль действительно публичный с компьютера (без входа в аккаунт)

<b>🔗 Для проверки настроек:</b>
Steam → Профиль → Редактировать профиль → Настройки приватности
                """
                await update.message.reply_text(message, parse_mode='HTML')
                return
            
            # Формируем сообщение с результатами
            message = f"💝 <b>Скидки в вашем Steam Wishlist ({len(discounted_games)} игр):</b>\n\n"
            
            for game in discounted_games[:15]:  # Показываем до 15 игр
                discount = game.get('discount_percent', 0)
                name = game.get('name', 'Неизвестная игра')
                final_price = game.get('final_formatted', '')
                initial_price = game.get('initial_formatted', '')
                url = game.get('url', '')
                
                # Эмодзи в зависимости от размера скидки
                if discount >= 75:
                    emoji = "🔥"
                elif discount >= 50:
                    emoji = "⚡"
                elif discount >= 25:
                    emoji = "💥"
                else:
                    emoji = "💰"
                
                message += f"{emoji} <b>{name}</b>\n"
                message += f"💸 Скидка: <b>-{discount}%</b>\n"
                
                if initial_price and final_price:
                    message += f"💰 <s>{initial_price}</s> → <b>{final_price}</b>\n"
                
                if url:
                    message += f"🔗 <a href='{url}'>Купить в Steam</a>\n"
                
                message += "\n"
            
            if len(discounted_games) > 15:
                message += f"💡 <i>И еще {len(discounted_games) - 15} игр со скидками...</i>\n"
            
            message += "\n🎯 <i>Успейте купить до окончания акций!</i>"
            
            # Разбиваем длинное сообщение
            if len(message) > 4000:
                chunks = self.split_message(message, 4000)
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
            else:
                await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
                
        except Exception as e:
            logger.error(f"Error processing wishlist: {e}")
            error_message = """
❌ <b>Ошибка при анализе Wishlist</b>

Произошла техническая ошибка при обработке вашего запроса.

<b>Что можно попробовать:</b>
• ⏱️ Подождать несколько минут и попробовать снова
• 🔗 Проверить правильность ссылки на профиль
• 🔒 Убедиться что профиль и wishlist публичные
• 🔄 Использовать другой формат ссылки (ID вместо никнейма или наоборот)

💬 Если проблема продолжается, обратитесь к администратору бота.
            """
            await update.message.reply_text(error_message, parse_mode='HTML')
    
    
    async def ai_recommendations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /recommend - AI-рекомендации игр на основе wishlist и библиотеки"""
        user_id = update.effective_user.id
        user = update.effective_user
        language = self.db.get_user_language(user_id)
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        # Проверяем, включены ли ИИ-рекомендации
        if not AI_RECOMMENDATIONS_ENABLED:
            await update.message.reply_text(get_text(language, 'ai_not_available'))
            return
        
        # Проверяем, указан ли wishlist в команде
        if context.args:
            profile_url = ' '.join(context.args)
            await self._process_wishlist_ai_recommendations(update, profile_url, language)
        else:
            # Запрашиваем ссылку на wishlist
            if language == 'en':
                message = """
🤖 <b>AI Game Recommendations based on your Steam Wishlist</b>

Send a link to your Steam profile, and AI will analyze your wishlist and suggest similar games!

📝 <b>Example links:</b>
• https://steamcommunity.com/profiles/76561198000000000
• https://steamcommunity.com/id/your_username

🔍 <b>What AI analyzes:</b>
• Genres of games in your wishlist
• Your Steam game library
• Time spent in games
• Game mechanics and preferences
• Preferred game style
• Game mood (dark, fun, etc.)

🎯 <b>What you get:</b>
• Personalized game recommendations based on real preferences
• Analysis of your gaming style
• Compatibility score for each recommendation
• Price estimates for recommended games

💡 <b>How to use:</b>
1. Make your Steam profile public
2. Send the profile link
3. Wait for AI analysis
4. Get personalized recommendations!

🔗 Just send your Steam profile link to get started!
                """
            else:
                message = """
🤖 <b>ИИ-рекомендации игр на основе вашего Steam Wishlist</b>

Отправьте ссылку на ваш Steam профиль, и ИИ проанализирует ваш список желаемого и предложит похожие игры!

📝 <b>Примеры ссылок:</b>
• https://steamcommunity.com/profiles/76561198000000000
• https://steamcommunity.com/id/your_username

🔍 <b>Что анализирует ИИ:</b>
• Жанры игр в вашем wishlist
• Ваша библиотека игр Steam
• Время, проведенное в играх
• Игровые механики и предпочтения
• Предпочитаемый стиль игр
• Настроение игр (темные, веселые и т.д.)

🎯 <b>Что получите:</b>
• Персональные рекомендации игр на основе реальных предпочтений
• Анализ вашего игрового стиля
• Оценка совместимости для каждой рекомендации
• Примерные цены на рекомендуемые игры

💡 <b>Как использовать:</b>
1. Сделайте ваш Steam профиль публичным
2. Отправьте ссылку на профиль
3. Дождитесь анализа ИИ
4. Получите персональные рекомендации!

🔗 Просто отправьте ссылку на ваш Steam профиль для начала!
                """
            
            # Сохраняем состояние ожидания wishlist
            self.set_user_state(user_id, 'waiting_for_wishlist_ai')
            
            await update.message.reply_text(message, parse_mode='HTML')
    
    async def _process_wishlist_ai_recommendations(self, update: Update, profile_url: str, language: str = 'ru'):
        """Обрабатывает ИИ-рекомендации на основе wishlist и библиотеки"""
        user_id = update.effective_user.id
        
        # Очищаем состояние
        self.clear_user_state(user_id)
        
        # Показываем индикатор загрузки
        loading_text = get_text(language, 'generating_recommendations') if language == 'en' else '🤖 Загружаю ваш wishlist и библиотеку игр для анализа... Это может занять 2-3 минуты.'
        loading_message = await update.message.reply_text(loading_text)
        
        try:
            # Получаем данные wishlist
            from steam_wishlist import SteamWishlistParser
            
            wishlist_games = []
            owned_games = []
            
            # Получаем wishlist
            try:
                async with SteamWishlistParser() as parser:
                    steam_id = parser.extract_steam_id(profile_url)
                    if not steam_id:
                        await loading_message.edit_text("❌ Не удалось извлечь Steam ID из ссылки. Проверьте правильность ссылки.")
                        return
                    
                    steam_id64 = await parser.resolve_steam_id(steam_id)
                    if steam_id64:
                        wishlist_games = await parser.get_wishlist_data(steam_id64)
                
                await loading_message.edit_text(f"📋 Wishlist загружен ({len(wishlist_games)} игр). Загружаю библиотеку игр...")
            
            except Exception as e:
                logger.warning(f"Could not load wishlist: {e}")
                await loading_message.edit_text("⚠️ Не удалось загрузить wishlist. Попробую получить только библиотеку игр...")
            
            # Получаем библиотеку игр
            try:
                owned_games = await get_steam_library(profile_url, limit=30)
                
                if owned_games:
                    total_games = len(wishlist_games) + len(owned_games)
                    await loading_message.edit_text(f"� Данные загружены: wishlist ({len(wishlist_games)} игр) + библиотека ({len(owned_games)} игр) = {total_games} игр. ИИ анализирует...")
                else:
                    if not wishlist_games:
                        await loading_message.edit_text("❌ Не удалось получить ни wishlist, ни библиотеку игр. Убедитесь, что профиль публичный.")
                        return
                    else:
                        await loading_message.edit_text(f"📋 Библиотека недоступна, но wishlist загружен ({len(wishlist_games)} игр). ИИ анализирует...")
            
            except Exception as e:
                logger.warning(f"Could not load library: {e}")
                if not wishlist_games:
                    await loading_message.edit_text("❌ Не удалось получить игровые данные. Убедитесь, что профиль и настройки приватности публичные.")
                    return
            
            # Проверяем, что у нас есть достаточно данных для анализа
            total_games = len(wishlist_games) + len(owned_games)
            if total_games < 3:
                await loading_message.edit_text("📋 Слишком мало игр для качественного анализа. Добавьте больше игр в wishlist или откройте библиотеку игр.")
                return
                
            # Получаем ИИ-рекомендации
            ai_result = await get_ai_game_recommendations(
                wishlist_games, 
                owned_games,
                OPENROUTER_API_KEY, 
                AI_MAX_RECOMMENDATIONS,
                language
            )
            
            if not ai_result['success']:
                error_msg = ai_result.get('error', 'Неизвестная ошибка')
                await loading_message.edit_text(f"❌ Ошибка ИИ-анализа: {error_msg}")
                return
            
            # Формируем ответ
            await self._send_ai_recommendations_response(update, ai_result, loading_message)
            
        except Exception as e:
            logger.error(f"Error in AI recommendations: {e}")
            await loading_message.edit_text("❌ Произошла ошибка при обработке рекомендаций. Попробуйте позже.")
    
    async def _send_ai_recommendations_response(self, update: Update, ai_result: dict, loading_message):
        """Отправляет ответ с ИИ-рекомендациями"""
        try:
            recommendations = ai_result['recommendations']
            analysis = ai_result['analysis']
            total_wishlist = ai_result['total_wishlist_games']
            total_owned = ai_result.get('total_owned_games', 0)
            total_analyzed = ai_result.get('total_games_analyzed', total_wishlist)
            
            # Основное сообщение
            message = f"🤖 <b>ИИ-анализ вашего Steam профиля</b>\n\n"
            message += f"📊 <b>Проанализировано игр:</b> {total_analyzed}\n"
            message += f"   💝 Wishlist: {total_wishlist} игр\n"
            if total_owned > 0:
                message += f"   📚 Библиотека: {total_owned} игр\n"
            message += "\n"
            
            # Анализ предпочтений
            if analysis:
                if 'top_genres' in analysis and analysis['top_genres']:
                    genres = ', '.join(analysis['top_genres'][:3])
                    message += f"🎮 <b>Ваши любимые жанры:</b> {genres}\n"
                
                if 'preferred_mechanics' in analysis and analysis['preferred_mechanics']:
                    mechanics = ', '.join(analysis['preferred_mechanics'][:3])
                    message += f"⚙️ <b>Предпочитаемые механики:</b> {mechanics}\n"
                
                if 'gaming_style' in analysis:
                    style = analysis['gaming_style'][:150]
                    message += f"🎯 <b>Ваш стиль игры:</b> {style}\n"
                
                if 'analysis_summary' in analysis:
                    summary = analysis['analysis_summary'][:200]
                    message += f"\n💭 <b>Анализ ИИ:</b> {summary}\n"
                
                message += "\n"
            
            # Рекомендации
            if recommendations:
                message += f"🎯 <b>Персональные рекомендации ({len(recommendations)}):</b>\n\n"
                
                for i, rec in enumerate(recommendations[:6], 1):
                    name = rec.get('name', 'Неизвестная игра')
                    description = rec.get('description', '')[:120]
                    reason = rec.get('reason', '')[:120]
                    price = rec.get('estimated_price', 'Цена неизвестна')
                    similarity = rec.get('similarity_score', 0)
                    
                    # Эмодзи в зависимости от совместимости
                    if similarity >= 90:
                        emoji = "🔥"
                    elif similarity >= 85:
                        emoji = "⭐"  
                    else:
                        emoji = "✨"
                    
                    message += f"{emoji} <b>{i}. {name}</b> ({similarity}% совместимость)\n"
                    if description:
                        message += f"📝 {description}\n"
                    if reason:
                        message += f"💡 <i>{reason}</i>\n"
                    if price != 'Цена неизвестна':
                        message += f"💰 {price}\n"
                    message += "\n"
            else:
                message += "😔 ИИ не смог сгенерировать рекомендации. Попробуйте позже.\n\n"
            
            # Дополнительная информация
            message += "� <b>Хотите найти скидки?</b>\n"
            message += "Используйте /wishlist с той же ссылкой для поиска скидок на игры из вашего списка желаемого!"
            
            # Добавляем информацию о том, что анализировалось
            if total_owned > 0:
                message += f"\n\n💡 ИИ проанализировал не только ваш wishlist, но и реальные игровые предпочтения на основе библиотеки игр!"
            
            # Ограничиваем длину сообщения
            if len(message) > 4000:
                message = message[:3900] + "\n\n... <i>Сообщение сокращено</i>"
            
            await loading_message.edit_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error sending AI recommendations response: {e}")
            await loading_message.edit_text("❌ Ошибка при отправке рекомендаций.")
    
    async def _process_ai_recommendations(self, update: Update, favorite_games: List[str]):
        """Старый метод для совместимости - теперь перенаправляет на wishlist-анализ"""
        message = """
🤖 <b>Новая функция ИИ-рекомендаций!</b>

Теперь ИИ анализирует ваш Steam Wishlist для более точных рекомендаций.

Используйте: /recommend
И отправьте ссылку на ваш Steam профиль.

Это даст гораздо более персонализированные рекомендации! 🎯
        """
        await update.message.reply_text(message, parse_mode='HTML')

    async def handle_text_messages_conditionally(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений только для пользователей в состоянии ожидания"""
        user_id = update.effective_user.id
        
        # Очищаем просроченные состояния
        self.cleanup_expired_states()
        
        # Проверяем, ожидает ли пользователь ввода
        if user_id not in self.user_states:
            # Если пользователь не в состоянии ожидания, игнорируем сообщение
            return
        
        # Если пользователь в состоянии ожидания, обрабатываем как раньше
        await self.handle_text_messages(update, context)

    async def handle_text_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений для многошаговых команд (только для пользователей в состоянии ожидания)"""
        user_id = update.effective_user.id
        
        # Эта функция вызывается только если пользователь в состоянии ожидания
        state = self.user_states[user_id]
        message_text = update.message.text.strip()
        
        try:
            if state == 'waiting_for_wishlist_url':
                # Пользователь отправил ссылку на Steam профиль
                if 'steamcommunity.com/' in message_text:
                    await self._process_wishlist(update, message_text)
                else:
                    await update.message.reply_text(
                        "❌ Некорректная ссылка. Отправьте ссылку вида:\n"
                        "https://steamcommunity.com/id/ваш_ник\n"
                        "или\n"
                        "https://steamcommunity.com/profiles/76561198XXXXXXXXX"
                    )
            
            elif state == 'waiting_for_wishlist_ai':
                # Пользователь отправил ссылку для ИИ-анализа wishlist
                if 'steamcommunity.com/' in message_text:
                    await self._process_wishlist_ai_recommendations(update, message_text)
                else:
                    await update.message.reply_text(
                        "❌ Некорректная ссылка. Отправьте ссылку вида:\n"
                        "https://steamcommunity.com/id/ваш_ник\n"
                        "или\n"
                        "https://steamcommunity.com/profiles/76561198XXXXXXXXX"
                    )
            
            elif state == 'waiting_for_favorite_games':
                # Пользователь отправил список любимых игр
                # Парсим игры, разделенные запятыми
                favorite_games = [game.strip() for game in message_text.split(',')]
                if len(favorite_games) < 2:
                    # Попробуем разделить по другим разделителям
                    separators = [';', '\n', ' и ', ' and ']
                    for sep in separators:
                        if sep in message_text:
                            favorite_games = [game.strip() for game in message_text.split(sep)]
                            break
                
                if len(favorite_games) < 2:
                    await update.message.reply_text(
                        "😔 Пожалуйста, укажите хотя бы 2 игры для лучших рекомендаций.\n"
                        "Разделите их запятыми, например: The Witcher 3, Skyrim, Cyberpunk 2077"
                    )
                    return
                
                await self._process_ai_recommendations(update, favorite_games)
                
            elif state == 'waiting_bug_report':
                # Пользователь отправил сообщение о баге
                await self._process_bug_report(update, message_text)
                
            elif state == 'waiting_feature_request':
                # Пользователь отправил предложение
                await self._process_feature_request(update, message_text)
                
            elif state == 'waiting_review':
                # Пользователь отправил отзыв
                await self._process_user_review(update, message_text)
                
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            self.clear_user_state(user_id)
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте команду заново.")

    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для отправки отзывов и предложений"""
        try:
            user = update.effective_user
            user_id = user.id
            username = user.username or user.first_name or str(user_id)
            language = self.db.get_user_language(user_id)
            
            # Добавляем/обновляем пользователя в БД
            self.db.add_user(user_id, user.username, user.first_name, user.last_name)
            
            # Проверяем аргументы команды
            args = context.args
            if not args:
                # Показываем меню выбора типа отзыва
                keyboard = [
                    [
                        InlineKeyboardButton(get_text(language, 'report_bug'), callback_data="feedback_bug"),
                        InlineKeyboardButton(get_text(language, 'suggest_feature'), callback_data="feedback_feature")
                    ],
                    [
                        InlineKeyboardButton(get_text(language, 'leave_review'), callback_data="feedback_review"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = get_text(language, 'feedback_menu_title')
                
                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return
                
            # Если есть аргументы - сохраняем как общий отзыв
            feedback_text = " ".join(args)
            
            if len(feedback_text) < 10:
                await update.message.reply_text(
                    "❌ Слишком короткое сообщение. Минимум 10 символов.\n"
                    "Пример: `/feedback Бот отличный, но хотелось бы больше фильтров`"
                )
                return
                
            if len(feedback_text) > 1000:
                await update.message.reply_text(
                    "❌ Слишком длинное сообщение. Максимум 1000 символов."
                )
                return
                
            # Сохраняем отзыв в БД
            feedback_id = self.db.add_feedback(user_id, username, "general", feedback_text)
            
            if feedback_id:
                await update.message.reply_text(
                    f"✅ **Спасибо за отзыв!**\n\n"
                    f"Ваше сообщение получено и будет рассмотрено.\n"
                    f"ID отзыва: `{feedback_id}`\n\n"
                    f"💡 Используйте `/feedback` для выбора конкретного типа обращения",
                    parse_mode='Markdown'
                )
                
                # Логируем получение отзыва
                logger.info(f"New feedback from {username} (ID: {user_id}): {feedback_text[:50]}...")
            else:
                await update.message.reply_text(
                    "❌ Ошибка при сохранении отзыва. Попробуйте позже."
                )
                
        except Exception as e:
            logger.error(f"Error in feedback command: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке отзыва. Попробуйте позже."
            )

    async def _process_bug_report(self, update: Update, message_text: str):
        """Обработка сообщения о баге"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name or str(user_id)
        
        if len(message_text) < 10:
            await update.message.reply_text(
                "❌ Слишком короткое описание бага. Минимум 10 символов.\n"
                "Опишите проблему подробнее."
            )
            return
            
        if len(message_text) > 1000:
            await update.message.reply_text("❌ Слишком длинное сообщение. Максимум 1000 символов.")
            return
            
        # Сохраняем баг-репорт
        feedback_id = self.db.add_feedback(user_id, username, "bug", message_text)
        
        if feedback_id:
            await update.message.reply_text(
                f"🐛 **Спасибо за сообщение о баге!**\n\n"
                f"Ваш баг-репорт получен и будет рассмотрен разработчиками.\n"
                f"ID сообщения: `{feedback_id}`\n\n"
                f"🔧 Мы постараемся исправить проблему в ближайших обновлениях.",
                parse_mode='Markdown'
            )
            logger.info(f"Bug report from {username} (ID: {user_id}): {message_text[:50]}...")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении баг-репорта. Попробуйте позже.")
            
        self.clear_user_state(user_id)

    async def _process_feature_request(self, update: Update, message_text: str):
        """Обработка предложения новой функции"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name or str(user_id)
        
        if len(message_text) < 10:
            await update.message.reply_text(
                "❌ Слишком короткое описание идеи. Минимум 10 символов.\n"
                "Опишите ваше предложение подробнее."
            )
            return
            
        if len(message_text) > 1000:
            await update.message.reply_text("❌ Слишком длинное сообщение. Максимум 1000 символов.")
            return
            
        # Сохраняем предложение
        feedback_id = self.db.add_feedback(user_id, username, "feature", message_text)
        
        if feedback_id:
            await update.message.reply_text(
                f"💡 **Спасибо за предложение!**\n\n"
                f"Ваша идея получена и будет рассмотрена.\n"
                f"ID предложения: `{feedback_id}`\n\n"
                f"🚀 Если идея будет полезной, мы добавим её в следующих версиях бота!",
                parse_mode='Markdown'
            )
            logger.info(f"Feature request from {username} (ID: {user_id}): {message_text[:50]}...")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении предложения. Попробуйте позже.")
            
        self.clear_user_state(user_id)

    async def _process_user_review(self, update: Update, message_text: str):
        """Обработка отзыва пользователя"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name or str(user_id)
        
        if len(message_text) < 5:
            await update.message.reply_text(
                "❌ Слишком короткий отзыв. Минимум 5 символов.\n"
                "Поделитесь своими впечатлениями о боте."
            )
            return
            
        if len(message_text) > 1000:
            await update.message.reply_text("❌ Слишком длинное сообщение. Максимум 1000 символов.")
            return
            
        # Пытаемся извлечь рейтинг из сообщения
        rating = None
        rating_patterns = [
            r'([1-5])/5',  # "4/5"
            r'([1-5]) звезд',  # "4 звезды"
            r'([1-5]) из 5',  # "4 из 5"
            r'⭐{1,5}',  # звездочки
            r'([1-5]) балл',  # "4 балла"
        ]
        
        for pattern in rating_patterns:
            import re
            match = re.search(pattern, message_text)
            if match:
                if pattern == r'⭐{1,5}':
                    rating = len(match.group())
                else:
                    rating = int(match.group(1))
                break
        
        # Сохраняем отзыв
        feedback_id = self.db.add_feedback(user_id, username, "compliment", message_text, rating)
        
        if feedback_id:
            rating_text = f" (⭐ {rating}/5)" if rating else ""
            await update.message.reply_text(
                f"❤️ **Спасибо за отзыв!**{rating_text}\n\n"
                f"Ваше мнение очень важно для нас!\n"
                f"ID отзыва: `{feedback_id}`\n\n"
                f"🙏 Благодаря таким отзывам мы делаем бота лучше!",
                parse_mode='Markdown'
            )
            logger.info(f"Review from {username} (ID: {user_id}): {message_text[:50]}... Rating: {rating}")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении отзыва. Попробуйте позже.")
            
        self.clear_user_state(user_id)

    # ================== КОНЕЦ НОВЫХ ФУНКЦИЙ ==================
    
    def run_scheduler(self):
        """Запускает планировщик в отдельном потоке"""
        schedule.every(6).hours.do(lambda: asyncio.run(self.send_deals_to_subscribers()))
        # Добавляем очистку просроченных состояний каждые 5 минут
        schedule.every(5).minutes.do(self.cleanup_expired_states)
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
    
    def run(self):
        """Запускает бота"""
        # Запускаем планировщик скидок в отдельном потоке
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Запускаем планировщик еженедельного дайджеста
        self.start_scheduler()
        
        logger.info("Starting bot...")
        self.application.run_polling()

if __name__ == "__main__":
    # Токен бота
    BOT_TOKEN = "7915606832:AAGLp_s79kuESeGZPRClXybqEAj65TzAn_E"
    
    if not BOT_TOKEN:
        print("❌ Ошибка: Не установлен токен бота!")
        print("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        print("Или измените код, указав токен напрямую")
        exit(1)
    
    bot = SteamDiscountBot(BOT_TOKEN)
    bot.run()
