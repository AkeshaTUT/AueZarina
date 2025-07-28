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
        
        # Новые функции
        self.application.add_handler(CommandHandler("wishlist", self.wishlist_command))
        self.application.add_handler(CommandHandler("recommend", self.ai_recommendations_command))
        
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
        
        welcome_message = """
🎮 Добро пожаловать в Steam Discount Bot! 

Этот бот поможет вам находить лучшие скидки на игры в Steam от 30% до 100%!

🔥 <b>Основные возможности:</b>
🎯 Фильтр по жанрам - выберите интересующие категории
🆓 Бесплатные раздачи - актуальные раздачи игр
📊 История цен - отслеживание лучших предложений
⚙️ Персональные настройки скидок
📅 Еженедельный ТОП-5 игр

🚀 <b>Новые функции:</b>
💝 Анализ Steam Wishlist - проверка скидок на желаемые игры
🤖 AI-рекомендации - персональные советы на базе ваших предпочтений

<b>Основные команды:</b>
/subscribe - Подписаться на уведомления о скидках
/deals - Получить текущие скидки
/genres - Настроить жанры игр
/free - Посмотреть бесплатные раздачи
/discount - Настроить минимальную скидку
/settings - Ваши настройки

<b>Новые команды:</b>
/wishlist - Проверить скидки в вашем Steam Wishlist
/recommend - Получить AI-рекомендации игр
/help - Полная справка по всем командам

Бот автоматически присылает новые скидки каждые 6 часов и еженедельный ТОП по пятницам в 19:00!
        """
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = """
🔧 <b>Все команды бота:</b>

<b>Основные:</b>
/start - Приветственное сообщение и регистрация
/subscribe - Подписаться на автоматические уведомления
/unsubscribe - Отписаться от уведомлений
/deals - Получить список текущих скидок

<b>Настройки:</b>
/genres или /жанры - Выбрать интересующие жанры игр
/discount или /скидка - Установить минимальную скидку (30%, 50%, 70%, 90%)
/settings - Посмотреть ваши текущие настройки

<b>Стандартные функции:</b>
/free или /раздачи - Посмотреть актуальные бесплатные раздачи
/weeklydigest - Получить еженедельный ТОП-5 игр
/help - Показать эту справку

<b>🚀 НОВЫЕ ФУНКЦИИ:</b>
💝 /wishlist - Анализ вашего Steam Wishlist
   Отправьте ссылку на публичный Steam-профиль для проверки скидок

🤖 /recommend или /rekomend - ИИ-рекомендации игр на основе Wishlist и библиотеки
   Проанализирует ваш Steam Wishlist и библиотеку игр для персональных рекомендаций

<b>🤖 Автоматические функции:</b>
📊 Бот ищет скидки от 30% до 100% в Steam Store
🎯 Фильтрует по вашим жанрам и минимальной скидке
🔔 Присылает уведомления каждые 6 часов
📅 Отправляет ТОП-5 игр недели по воскресеньям в 18:00
💰 Показывает историю цен и лучшие предложения
        """
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /subscribe"""
        user_id = update.effective_user.id
        user = update.effective_user
        
        # Добавляем пользователя если его нет
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        if self.db.subscribe_user(user_id):
            settings = self.db.get_user_settings(user_id)
            
            response = "✅ Вы успешно подписались на уведомления о скидках!\n\n"
            response += f"📊 Ваши настройки:\n"
            response += f"💰 Минимальная скидка: {settings['min_discount']}%\n"
            
            if settings['preferred_genres']:
                response += f"🎮 Жанры: {', '.join(settings['preferred_genres'])}\n"
            else:
                response += f"🎮 Жанры: Все (настройте через /genres)\n"
            
            response += f"\n🔔 Бот будет присылать новые предложения каждые 6 часов"
            response += f"\n📅 И еженедельный ТОП-5 по пятницам в 19:00"
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("ℹ️ Вы уже подписаны на уведомления.")
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /unsubscribe"""
        user_id = update.effective_user.id
        if self.db.unsubscribe_user(user_id):
            await update.message.reply_text("❌ Вы успешно отписались от уведомлений.")
        else:
            await update.message.reply_text("ℹ️ Вы не были подписаны на уведомления.")
    
    async def genres_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /genres - настройка жанров"""
        user_id = update.effective_user.id
        user = update.effective_user
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
            InlineKeyboardButton("🔄 Сбросить все", callback_data="genre_clear"),
            InlineKeyboardButton("✅ Сохранить", callback_data="genre_save")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"🎮 <b>Выберите интересующие жанры игр:</b>\n\n"
        if current_genres:
            message += f"Выбрано: {', '.join(current_genres)}\n\n"
        else:
            message += "Сейчас выбраны все жанры\n\n"
        message += "Нажмите на жанр чтобы добавить/убрать его из списка"
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def free_games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /free - бесплатные раздачи"""
        user_id = update.effective_user.id
        user = update.effective_user
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        await update.message.reply_text("🔍 Ищу актуальные бесплатные раздачи... Пожалуйста, подождите.")
        
        try:
            # Импортируем упрощенный парсер бесплатных игр
            from simple_free_games_parser import get_current_free_games
            
            # Получаем реальные данные
            all_games = await get_current_free_games()
            
            # Обновляем базу данных актуальными играми
            await self._update_database_with_live_games(all_games)
            
            if not all_games:
                await update.message.reply_text("😔 На данный момент не удалось получить информацию о бесплатных раздачах. Попробуйте позже.")
                return
            
            # Ограничиваем количество для отображения
            display_games = all_games[:10]
            message = f"🆓 <b>Актуальные бесплатные раздачи ({len(display_games)}):</b>\n\n"
            
            for game in display_games:
                # Определяем эмодзи платформы
                platform_emoji = {
                    'Steam': '🟦',
                    'Epic Games Store': '🟪', 
                    'GOG': '🟫',
                    'Other': '⚪'
                }.get(game.get('platform', 'Other'), '⚪')
                
                title = game.get('title', 'Неизвестная игра')
                description = game.get('description', 'Описание отсутствует')
                end_date = game.get('end_date', 'Неизвестно')
                url = game.get('url', '')
                
                message += f"{platform_emoji} <b>{title}</b>\n"
                message += f"📝 {description}\n"
                message += f"🗓️ До: {end_date}\n"
                if url:
                    message += f"🔗 <a href='{url}'>Получить игру</a>\n"
                message += "\n"
            
            if len(all_games) > 10:
                message += f"💡 <i>И еще {len(all_games) - 10} раздач...</i>\n"
            
            message += "\n🔄 <i>Данные обновляются в реальном времени</i>"
            
            # Разбиваем сообщение если оно слишком длинное
            if len(message) > 4000:
                chunks = self.split_message(message, 4000)
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
            else:
                await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
                
        except Exception as e:
            logger.error(f"Error getting free games: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении бесплатных раздач. Попробуйте позже.")
    
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
        
        message = f"💰 <b>Настройка минимальной скидки</b>\n\n"
        message += f"Текущая настройка: <b>{current_discount}%</b>\n\n"
        message += f"Выберите минимальную скидку для показа игр:"
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def user_settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings - показ настроек пользователя"""
        user_id = update.effective_user.id
        user = update.effective_user
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        settings = self.db.get_user_settings(user_id)
        
        message = f"⚙️ <b>Ваши настройки:</b>\n\n"
        message += f"🔔 Уведомления: {'✅ Включены' if settings['is_subscribed'] else '❌ Выключены'}\n"
        message += f"💰 Минимальная скидка: <b>{settings['min_discount']}%</b>\n"
        
        if settings['preferred_genres']:
            message += f"🎮 Жанры ({len(settings['preferred_genres'])}): {', '.join(settings['preferred_genres'])}\n"
        else:
            message += f"🎮 Жанры: Все жанры\n"
        
        message += f"\n<b>Управление:</b>\n"
        message += f"/subscribe - Включить уведомления\n"
        message += f"/genres - Настроить жанры\n"
        message += f"/discount - Изменить минимальную скидку"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith("genre_"):
            await self.handle_genre_callback(query, user_id, data)
        elif data.startswith("discount_"):
            await self.handle_discount_callback(query, user_id, data)
    
    async def handle_genre_callback(self, query, user_id: int, data: str):
        """Обработка callback для жанров"""
        current_genres = self.db.get_user_genres(user_id)
        
        if data == "genre_clear":
            # Очищаем все жанры
            self.db.set_user_genres(user_id, [])
            await query.edit_message_text(
                "🎮 <b>Все жанры очищены!</b>\n\nТеперь будут показываться игры всех жанров.\n\nИспользуйте /genres для новых настроек.",
                parse_mode='HTML'
            )
            return
        elif data == "genre_save":
            # Сохраняем настройки
            genres_text = ', '.join(current_genres) if current_genres else "Все жанры"
            await query.edit_message_text(
                f"✅ <b>Настройки жанров сохранены!</b>\n\n🎮 Выбранные жанры: {genres_text}\n\nТеперь в рассылке будут только игры выбранных жанров.",
                parse_mode='HTML'
            )
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
            InlineKeyboardButton("🔄 Сбросить все", callback_data="genre_clear"),
            InlineKeyboardButton("✅ Сохранить", callback_data="genre_save")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"🎮 <b>Выберите интересующие жанры игр:</b>\n\n"
        if current_genres:
            message += f"Выбрано: {', '.join(current_genres)}\n\n"
        else:
            message += "Сейчас выбраны все жанры\n\n"
        message += "Нажмите на жанр чтобы добавить/убрать его из списка"
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_discount_callback(self, query, user_id: int, data: str):
        """Обработка callback для настройки скидки"""
        discount_value = int(data.replace("discount_", ""))
        self.db.set_user_min_discount(user_id, discount_value)
        
        await query.edit_message_text(
            f"✅ <b>Настройка сохранена!</b>\n\n💰 Минимальная скидка установлена: <b>{discount_value}%</b>\n\nТеперь в рассылке будут только игры со скидкой от {discount_value}% и выше.",
            parse_mode='HTML'
        )
    
    async def deals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /deals"""
        user_id = update.effective_user.id
        await update.message.reply_text("🔍 Ищу актуальные скидки... Пожалуйста, подождите.")
        
        try:
            # Регистрируем пользователя если его нет в базе
            self.db.add_user(user_id)
            
            # Получаем настройки пользователя
            user_genres = self.db.get_user_genres(user_id)
            min_discount = self.db.get_user_min_discount(user_id)
            
            deals = await self.scraper.get_discounted_games()
            
            # Фильтруем игры по пользовательским настройкам
            filtered_deals = self.filter_deals_by_user_preferences(deals, user_genres, min_discount)
            
            if filtered_deals:
                message = self.format_deals_message(filtered_deals, user_id)
                
                # Telegram имеет ограничение на длину сообщения в 4096 символов
                if len(message) > 4000:
                    # Разбиваем на несколько сообщений
                    chunks = self.split_message(message, 4000)
                    for chunk in chunks:
                        await update.message.reply_text(chunk, parse_mode='HTML')
                else:
                    await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text(f"😔 На данный момент нет подходящих скидок от {min_discount}% с выбранными жанрами.")
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении скидок. Попробуйте позже.")
    
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
    
    def format_deals_message(self, deals, user_id: int):
        """Форматирует сообщение со скидками с учетом истории цен"""
        if not deals:
            return "😔 На данный момент нет подходящих скидок."
        
        message = f"🎮 <b>Актуальные скидки Steam ({len(deals)} игр)</b>\n\n"
        
        # Показываем все найденные игры, не ограничивая до 20
        for deal in deals:
            discount = deal.get('discount', 0)
            title = deal.get('title', 'Неизвестная игра')
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
        await update.message.reply_text("📊 Формирую еженедельный дайджест...")
        
        try:
            # Получаем топ-5 игр за неделю
            weekly_top = self.db.get_weekly_top_games()
            
            if weekly_top:
                message = "📊 <b>Топ-5 игр недели по размеру скидки</b>\n\n"
                
                for i, game in enumerate(weekly_top[:5], 1):
                    emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
                    message += f"{emoji} <b>{game['title']}</b>\n"
                    message += f"💸 Скидка: <b>-{game['discount']}%</b>\n"
                    message += f"💰 Цена: <b>{game['price']}₽</b>\n\n"
                
                await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text("📊 Еще нет данных для еженедельного дайджеста.")
                
        except Exception as e:
            logger.error(f"Error getting weekly digest: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении дайджеста.")
    
    async def send_weekly_digest_to_all(self):
        """Отправляет еженедельный дайджест всем пользователям"""
        try:
            users = self.db.get_subscribed_users()
            weekly_top = self.db.get_weekly_top_games()
            
            if not weekly_top:
                return
            
            message = "📊 <b>Еженедельный дайджест Steam</b>\n\n"
            message += "🏆 <b>Топ-5 игр недели по размеру скидки:</b>\n\n"
            
            for i, game in enumerate(weekly_top[:5], 1):
                emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
                message += f"{emoji} <b>{game['title']}</b>\n"
                message += f"💸 Скидка: <b>-{game['discount']}%</b>\n"
                message += f"💰 Цена: <b>{game['price']}₽</b>\n\n"
            
            message += "🎮 Хотите получать персональные уведомления? Настройте жанры командой /genres"
            
            # Отправляем всем подписанным пользователям
            for user_id in users:
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(0.1)  # Небольшая задержка между отправками
                except Exception as e:
                    logger.error(f"Failed to send weekly digest to user {user_id}: {e}")
            
            # Очищаем данные для новой недели
            self.db.clear_weekly_top()
            
        except Exception as e:
            logger.error(f"Error sending weekly digest: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик для еженедельной рассылки"""
        def schedule_checker():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
        
        # Планируем отправку каждую неделю в воскресенье в 18:00
        schedule.every().sunday.at("18:00").do(
            lambda: asyncio.create_task(self.send_weekly_digest_to_all())
        )
        
        # Запускаем планировщик в отдельном потоке
        scheduler_thread = threading.Thread(target=schedule_checker, daemon=True)
        scheduler_thread.start()
        logger.info("Weekly digest scheduler started")

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
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        # Проверяем, есть ли аргументы команды (ссылка на профиль)
        if context.args:
            profile_url = ' '.join(context.args)
            await self._process_wishlist(update, profile_url)
        else:
            # Запрашиваем ссылку на профиль
            message = """
💝 <b>Анализ Steam Wishlist</b>

Отправьте ссылку на ваш <b>публичный</b> Steam-профиль для проверки скидок на игры из списка желаемого.

📝 <b>Примеры ссылок:</b>
• https://steamcommunity.com/id/ваш_ник
• https://steamcommunity.com/profiles/76561198XXXXXXXXX

⚠️ <b>Важно:</b> Профиль должен быть публичным, а список желаемого - открытым для просмотра.

💡 <b>Как использовать:</b>
Отправьте: /wishlist https://steamcommunity.com/id/ваш_ник
            """
            
            # Сохраняем состояние ожидания ссылки
            self.set_user_state(user_id, 'waiting_for_wishlist_url')
            
            await update.message.reply_text(message, parse_mode='HTML')
    
    async def _process_wishlist(self, update: Update, profile_url: str):
        """Обрабатывает анализ wishlist"""
        user_id = update.effective_user.id
        
        await update.message.reply_text("🔍 Анализирую ваш Steam Wishlist... Это может занять некоторое время.")
        
        try:
            # Очищаем состояние
            self.clear_user_state(user_id)
            
            # Проверяем валидность URL
            if not ('steamcommunity.com/id/' in profile_url or 'steamcommunity.com/profiles/' in profile_url):
                await update.message.reply_text(
                    "❌ <b>Неверная ссылка на профиль</b>\n\n"
                    "Отправьте ссылку в одном из форматов:\n"
                    "• https://steamcommunity.com/id/ваш_ник\n"
                    "• https://steamcommunity.com/profiles/76561198XXXXXXXXX",
                    parse_mode='HTML'
                )
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
        self.db.add_user(user_id, user.username, user.first_name, user.last_name)
        
        # Проверяем, включены ли ИИ-рекомендации
        if not AI_RECOMMENDATIONS_ENABLED:
            await update.message.reply_text("🤖 ИИ-рекомендации временно отключены.")
            return
        
        # Проверяем, указан ли wishlist в команде
        if context.args:
            profile_url = ' '.join(context.args)
            await self._process_wishlist_ai_recommendations(update, profile_url)
        else:
            # Запрашиваем ссылку на wishlist
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
• Анализ ваших игровых предпочтений по библиотеке
• Объяснение, почему каждая игра вам подойдет
• Учет времени в играх для более точных советов

💡 <i>Убедитесь, что ваши wishlist и библиотека игр публичные!</i>
            """
            
            # Сохраняем состояние ожидания wishlist
            self.set_user_state(user_id, 'waiting_for_wishlist_ai')
            
            await update.message.reply_text(message, parse_mode='HTML')
    
    async def _process_wishlist_ai_recommendations(self, update: Update, profile_url: str):
        """Обрабатывает ИИ-рекомендации на основе wishlist и библиотеки"""
        user_id = update.effective_user.id
        
        # Очищаем состояние
        self.clear_user_state(user_id)
        
        # Показываем индикатор загрузки
        loading_message = await update.message.reply_text("🤖 Загружаю ваш wishlist и библиотеку игр для анализа... Это может занять 2-3 минуты.")
        
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
                AI_MAX_RECOMMENDATIONS
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
                
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            self.clear_user_state(user_id)
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте команду заново.")

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
