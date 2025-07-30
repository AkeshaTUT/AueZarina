"""
Модуль для многоязычной поддержки бота
"""
from typing import List

# Словарь переводов
TRANSLATIONS = {
    'ru': {
        # Команда /start
        'welcome_title': '🎮 Добро пожаловать в ZarinAI!',
        'welcome_description': 'Этот бот поможет вам находить лучшие скидки на игры в Steam от 30% до 100%!',
        'main_features': '🔥 <b>Основные возможности:</b>',
        'genre_filter': '🎯 Фильтр по жанрам - выберите интересующие категории',
        'free_games': '🆓 Бесплатные раздачи - актуальные раздачи игр',
        'price_history': '📊 История цен - отслеживание лучших предложений',
        'personal_settings': '⚙️ Персональные настройки скидок',
        'weekly_digest': '📅 Еженедельный ТОП-5 игр',
        'new_features': '🚀 <b>Новые функции:</b>',
        'wishlist_analysis': '💝 Анализ Steam Wishlist - проверка скидок на желаемые игры',
        'ai_recommendations': '🤖 AI-рекомендации - персональные советы на базе ваших предпочтений',
        'basic_commands': '<b>Основные команды:</b>',
        'new_commands': '<b>Новые команды:</b>',
        'auto_notifications': 'Бот автоматически присылает новые скидки каждые 6 часов и еженедельный ТОП по пятницам в 19:00!',
        
        # Описания команд
        'cmd_subscribe': '/subscribe - Подписаться на уведомления о скидках',
        'cmd_deals': '/deals - Получить текущие скидки',
        'cmd_genres': '/genres - Настроить жанры игр',
        'cmd_free': '/free - Посмотреть бесплатные раздачи',
        'cmd_discount': '/discount - Настроить минимальную скидку',
        'cmd_settings': '/settings - Ваши настройки',
        'cmd_wishlist': '/wishlist - Проверить скидки в вашем Steam Wishlist',
        'cmd_recommend': '/recommend - Получить AI-рекомендации игр',
        'cmd_help': '/help - Полная справка по всем командам',
        
        # Команда /help
        'all_commands': '🔧 <b>Все команды бота:</b>',
        'basic_title': '<b>Основные:</b>',
        'start_desc': '/start - Приветственное сообщение и регистрация',
        'subscribe_desc': '/subscribe - Подписаться на автоматические уведомления',
        'unsubscribe_desc': '/unsubscribe - Отписаться от уведомлений',
        'deals_desc': '/deals - Получить список текущих скидок',
        'free_desc': '/free - Актуальные бесплатные раздачи игр',
        'genres_desc': '/genres - Выбрать интересующие жанры игр',
        'discount_desc': '/discount - Настроить минимальный процент скидки',
        'settings_desc': '/settings - Просмотр ваших текущих настроек',
        'weeklydigest_desc': '/weeklydigest - Получить ТОП-5 игр недели',
        'feedback_desc': '/feedback - Оставить отзыв или предложение',
        'new_title': '<b>Новые возможности:</b>',
        'wishlist_desc': '/wishlist - Проверить скидки в Steam Wishlist',
        'recommend_desc': '/recommend - Получить персональные AI-рекомендации',
        'help_footer': 'Для получения дополнительной помощи обращайтесь к разработчику через /feedback',
        
        # Дополнительные команды и сообщения
        'searching_deals': '🔍 Ищу актуальные скидки... Пожалуйста, подождите.',
        'no_suitable_deals': '😔 На данный момент нет подходящих скидок от {min_discount}% с выбранными жанрами.',
        'error_getting_deals': '❌ Произошла ошибка при получении скидок. Попробуйте позже.',
        'generating_weekly_digest': '📊 Формирую еженедельный дайджест...',
        'no_weekly_data': '📊 Еще нет данных для еженедельного дайджеста. Попробуйте позже.',
        'error_getting_digest': '❌ Произошла ошибка при получении дайджеста.',
        'analyzing_wishlist': '🔍 Анализирую ваш Steam Wishlist... Это может занять некоторое время.',
        'select_genres_message': '🎮 <b>Выберите интересующие вас жанры игр:</b>\n\nВыбранные жанры: {selected_genres}\n\nВы можете выбрать несколько жанров. Бот будет показывать скидки только на игры выбранных жанров.',
        'genres_saved': '✅ Жанры сохранены! Теперь бот будет показывать скидки только на выбранные жанры.',
        'discount_settings_title': '💰 <b>Настройки минимальной скидки</b>\n\nВыберите минимальный процент скидки для уведомлений:',
        'discount_updated': '💰 Минимальная скидка обновлена до {discount}%',
        'feedback_prompt': '💬 <b>Отзывы и предложения</b>\n\nОтправьте ваш отзыв, предложение или сообщение о баге. Это поможет улучшить бота!\n\n📝 Просто напишите сообщение следующим текстом.',
        'feedback_received': '✅ Спасибо за ваш отзыв! Мы обязательно его рассмотрим.',
        
        # Кнопки и интерфейс
        'choose_language': 'Выберите язык / Choose language:',
        'language_russian': '🇷🇺 Русский',
        'language_english': '🇺🇸 English',
        'back_button': '⬅️ Назад',
        'next_page': 'Следующая страница ➡️',
        'prev_page': '⬅️ Предыдущая страница',
        'select_genres': 'Выберите жанры:',
        'save_settings': '💾 Сохранить настройки',
        'my_genres': 'Мои жанры: ',
        'no_genres': 'Жанры не выбраны',
        
        # Сообщения о состоянии
        'already_subscribed': 'ℹ️ Вы уже подписаны на уведомления.',
        'subscribed_success': '✅ Вы успешно подписались на уведомления о скидках!',
        'unsubscribed_success': '❌ Вы успешно отписались от уведомлений.',
        'not_subscribed': 'ℹ️ Вы не были подписаны на уведомления.',
        'searching_deals': '🔍 Ищу актуальные скидки... Пожалуйста, подождите.',
        'searching_free_games': '🔍 Ищу актуальные бесплатные раздачи... Пожалуйста, подождите.',
        'no_free_games': '😔 На данный момент не удалось получить информацию о бесплатных раздачах. Попробуйте позже.',
        'error_free_games': '❌ Произошла ошибка при получении бесплатных раздач. Попробуйте позже.',
        'no_deals_found': '😔 На данный момент нет подходящих скидок от {min_discount}% с выбранными жанрами.',
        'error_deals': '❌ Произошла ошибка при получении скидок. Попробуйте позже.',
        'language_changed': '✅ Язык изменен на русский!',
        
        # Настройки пользователя
        'your_settings': '⚙️ <b>Ваши настройки:</b>',
        'subscription_status': 'Подписка: ',
        'subscribed': 'Активна ✅',
        'not_subscribed_status': 'Неактивна ❌',
        'min_discount_setting': 'Минимальная скидка: ',
        'selected_genres': 'Выбранные жанры: ',
        'no_genres_selected': 'Не выбраны',
        'change_language': 'Изменить язык',
        
        # AI рекомендации
        'ai_not_available': '❌ AI-рекомендации временно недоступны. Проверьте настройки API.',
        'generating_recommendations': '🤖 Генерирую персональные рекомендации игр...',
        'wishlist_check': '💝 Проверяю ваш Steam Wishlist на скидки...',
        'enter_steam_id': 'Введите ваш Steam ID или ссылку на профиль:',
        'invalid_steam_id': '❌ Некорректный Steam ID. Попробуйте еще раз.',
        
        # Общие сообщения
        'error_occurred': '❌ Произошла ошибка. Попробуйте позже.',
        'please_wait': 'Пожалуйста, подождите...',
        'done': 'Готово!',
        'cancel': 'Отмена',
        'yes': 'Да',
        'no': 'Нет',
        
        # Еженедельный дайджест
        'generating_digest': '📊 Формирую еженедельный дайджест...',
        'no_weekly_data': '📊 Данных для еженедельного дайджеста пока нет. Попробуйте позже.',
        'error_getting_digest': '❌ Ошибка при получении дайджеста.',
        
        # Дополнительные переводы команд
        'select_genres_title': '🎮 <b>Выберите интересующие жанры игр:</b>\n\n',
        'selected_genres': 'Выбрано: {genres}\n\n',
        'all_genres_selected': 'Сейчас выбраны все жанры\n\n',
        'genres_instruction': 'Нажмите на жанр чтобы добавить/убрать его из списка',
        'clear_all_genres': '🔄 Сбросить все',
        'save_genres': '✅ Сохранить',
        'discount_settings_title': '💰 <b>Настройка минимальной скидки</b>\n\n',
        'current_discount': 'Текущая настройка: <b>{discount}%</b>\n\n',
        'select_min_discount': 'Выберите минимальную скидку для показа игр:',
        'feedback_menu_title': '💬 <b>Отзывы и предложения</b>\n\nВыберите тип отзыва:',
        'report_bug': '🐛 Сообщить о баге',
        'suggest_feature': '💡 Предложить идею',
        'leave_review': '❤️ Оставить отзыв',
        'feedback_prompt': 'Опишите ваш отзыв подробно. Это поможет улучшить бота!\n\n📝 Напишите ваше сообщение:',
        'feedback_received': '✅ Спасибо за отзыв! Мы обязательно его рассмотрим.',
        'weekly_top_games': '🏆 <b>ТОП-5 игр недели:</b>',
        
        # Еженедельный дайджест
        'weekly_digest_title': '📊 <b>Еженедельный дайджест Steam</b>',
        'weekly_digest_subtitle': '🏆 <b>Топ-5 игр недели по размеру скидки:</b>',
        'weekly_digest_cta': '🎮 Хотите получать персональные уведомления? Настройте жанры командой /genres',
        'admin_only': '❌ Команда доступна только администраторам.',
        'digest_test_title': '📊 <b>Тест еженедельного дайджеста</b>',
        'no_digest_data': '❌ Нет данных для дайджеста.\n\nИспользуйте команду /deals чтобы собрать данные.',
        'digest_data_found': '✅ Найдено {count} игр в базе:',
        'sending_digest': '📤 Отправляю еженедельный дайджест всем подписчикам...',
        'digest_sent': '✅ Еженедельный дайджест отправлен!',
        'digest_error': '❌ Ошибка при тестировании дайджеста.',
        'digest_send_error': '❌ Ошибка при отправке дайджеста.',
        
        # Прочее
        'free_games_title': '🎁 <b>Актуальные бесплатные раздачи:</b>',
        'current_deals': '🔥 <b>Текущие скидки от {min_discount}%:</b>',
        'game_ends': 'До: ',
        'forever_free': 'Навсегда',
        'original_price': 'Обычная цена: ',
        'discount_price': 'Цена со скидкой: ',
        'discount_percent': 'Скидка: ',
        'steam_rating': 'Рейтинг: ',
    },
    
    'en': {
        # Command /start
        'welcome_title': '🎮 Welcome to ZarinAI!',
        'welcome_description': 'This bot will help you find the best Steam game deals from 30% to 100% off!',
        'main_features': '🔥 <b>Main features:</b>',
        'genre_filter': '🎯 Genre filter - choose categories of interest',
        'free_games': '🆓 Free giveaways - current game giveaways',
        'price_history': '📊 Price history - tracking the best deals',
        'personal_settings': '⚙️ Personal discount settings',
        'weekly_digest': '📅 Weekly TOP-5 games',
        'new_features': '🚀 <b>New features:</b>',
        'wishlist_analysis': '💝 Steam Wishlist analysis - check discounts on your wishlist games',
        'ai_recommendations': '🤖 AI recommendations - personalized game suggestions based on your preferences',
        'basic_commands': '<b>Basic commands:</b>',
        'new_commands': '<b>New commands:</b>',
        'auto_notifications': 'The bot automatically sends new deals every 6 hours and weekly TOP on Fridays at 7 PM!',
        
        # Command descriptions
        'cmd_subscribe': '/subscribe - Subscribe to deal notifications',
        'cmd_deals': '/deals - Get current deals',
        'cmd_genres': '/genres - Set up game genres',
        'cmd_free': '/free - View free giveaways',
        'cmd_discount': '/discount - Set minimum discount',
        'cmd_settings': '/settings - Your settings',
        'cmd_wishlist': '/wishlist - Check discounts in your Steam Wishlist',
        'cmd_recommend': '/recommend - Get AI game recommendations',
        'cmd_help': '/help - Complete help for all commands',
        
        # Command /help
        'all_commands': '🔧 <b>All bot commands:</b>',
        'basic_title': '<b>Basic:</b>',
        'start_desc': '/start - Welcome message and registration',
        'subscribe_desc': '/subscribe - Subscribe to automatic notifications',
        'unsubscribe_desc': '/unsubscribe - Unsubscribe from notifications',
        'deals_desc': '/deals - Get list of current deals',
        'free_desc': '/free - Current free game giveaways',
        'genres_desc': '/genres - Choose game genres of interest',
        'discount_desc': '/discount - Set minimum discount percentage',
        'settings_desc': '/settings - View your current settings',
        'weeklydigest_desc': '/weeklydigest - Get weekly TOP-5 games',
        'feedback_desc': '/feedback - Leave feedback or suggestions',
        'new_title': '<b>New features:</b>',
        'wishlist_desc': '/wishlist - Check discounts in Steam Wishlist',
        'recommend_desc': '/recommend - Get personalized AI recommendations',
        'help_footer': 'For additional help, contact the developer via /feedback',
        
        # Additional commands and messages
        'searching_deals': '🔍 Searching for current deals... Please wait.',
        'no_suitable_deals': '😔 Currently no suitable deals from {min_discount}% with selected genres.',
        'error_getting_deals': '❌ An error occurred while getting deals. Try again later.',
        'generating_weekly_digest': '📊 Generating weekly digest...',
        'no_weekly_data': '📊 No data available for weekly digest yet. Please try later.',
        'error_getting_digest': '❌ An error occurred while getting digest.',
        'analyzing_wishlist': '🔍 Analyzing your Steam Wishlist... This may take some time.',
        'select_genres_message': '🎮 <b>Select your favorite game genres:</b>\n\nSelected genres: {selected_genres}\n\nYou can select multiple genres. The bot will show deals only for selected genres.',
        'genres_saved': '✅ Genres saved! The bot will now show deals only for selected genres.',
        'discount_settings_title': '💰 <b>Minimum Discount Settings</b>\n\nSelect minimum discount percentage for notifications:',
        'discount_updated': '💰 Minimum discount updated to {discount}%',
        'feedback_prompt': '💬 <b>Feedback and Suggestions</b>\n\nSend your feedback, suggestion, or bug report. This will help improve the bot!\n\n📝 Just write your message in the next text.',
        'feedback_received': '✅ Thank you for your feedback! We will definitely review it.',
        
        # Buttons and interface
        'choose_language': 'Выберите язык / Choose language:',
        'language_russian': '🇷🇺 Русский',
        'language_english': '🇺🇸 English',
        'back_button': '⬅️ Back',
        'next_page': 'Next page ➡️',
        'prev_page': '⬅️ Previous page',
        'select_genres': 'Select genres:',
        'save_settings': '💾 Save settings',
        'my_genres': 'My genres: ',
        'no_genres': 'No genres selected',
        
        # Additional command translations
        'select_genres_title': '🎮 <b>Select your favorite game genres:</b>\n\n',
        'selected_genres': 'Selected: {genres}\n\n',
        'all_genres_selected': 'All genres are currently selected\n\n',
        'genres_instruction': 'Click on a genre to add/remove it from the list',
        'clear_all_genres': '🔄 Clear All',
        'save_genres': '✅ Save',
        'discount_settings_title': '💰 <b>Minimum Discount Settings</b>\n\n',
        'current_discount': 'Current setting: <b>{discount}%</b>\n\n',
        'select_min_discount': 'Select minimum discount percentage for showing games:',
        'feedback_menu_title': '💬 <b>Feedback and Suggestions</b>\n\nChoose feedback type:',
        'report_bug': '🐛 Report a Bug',
        'suggest_feature': '💡 Suggest Feature',
        'leave_review': '❤️ Leave Review',
        'feedback_prompt': 'Please describe your feedback in detail. This will help improve the bot!\n\n📝 Write your message:',
        'feedback_received': '✅ Thank you for your feedback! We will review it.',
        
        # Weekly digest
        'weekly_digest_title': '📊 <b>Weekly Steam Digest</b>',
        'weekly_digest_subtitle': '🏆 <b>Top-5 Games of the Week by Discount:</b>',
        'weekly_digest_cta': '🎮 Want personalized notifications? Set up genres with /genres command',
        'admin_only': '❌ This command is only available to administrators.',
        'digest_test_title': '📊 <b>Weekly Digest Test</b>',
        'no_digest_data': '❌ No data for digest.\n\nUse /deals command to collect data.',
        'digest_data_found': '✅ Found {count} games in database:',
        'sending_digest': '📤 Sending weekly digest to all subscribers...',
        'digest_sent': '✅ Weekly digest sent!',
        'digest_error': '❌ Error testing digest.',
        'digest_send_error': '❌ Error sending digest.',
        
        # Status messages
        'already_subscribed': 'ℹ️ You are already subscribed to notifications.',
        'subscribed_success': '✅ You have successfully subscribed to deal notifications!',
        'unsubscribed_success': '❌ You have successfully unsubscribed from notifications.',
        'not_subscribed': 'ℹ️ You were not subscribed to notifications.',
        'searching_deals': '🔍 Searching for current deals... Please wait.',
        'searching_free_games': '🔍 Searching for current free giveaways... Please wait.',
        'no_free_games': '😔 Currently unable to get information about free giveaways. Try again later.',
        'error_free_games': '❌ An error occurred while getting free giveaways. Try again later.',
        'no_deals_found': '😔 Currently no suitable deals from {min_discount}% with selected genres.',
        'error_deals': '❌ An error occurred while getting deals. Try again later.',
        'language_changed': '✅ Language changed to English!',
        
        # User settings
        'your_settings': '⚙️ <b>Your settings:</b>',
        'subscription_status': 'Subscription: ',
        'subscribed': 'Active ✅',
        'not_subscribed_status': 'Inactive ❌',
        'min_discount_setting': 'Minimum discount: ',
        'selected_genres': 'Selected genres: ',
        'no_genres_selected': 'None selected',
        'change_language': 'Change language',
        
        # AI recommendations
        'ai_not_available': '❌ AI recommendations are temporarily unavailable. Check API settings.',
        'generating_recommendations': '🤖 Generating personalized game recommendations...',
        'wishlist_check': '💝 Checking your Steam Wishlist for discounts...',
        'enter_steam_id': 'Enter your Steam ID or profile link:',
        'invalid_steam_id': '❌ Invalid Steam ID. Please try again.',
        
        # General messages
        'error_occurred': '❌ An error occurred. Please try again later.',
        'please_wait': 'Please wait...',
        'done': 'Done!',
        'cancel': 'Cancel',
        'yes': 'Yes',
        'no': 'No',
        
        # Weekly digest
        'generating_digest': '📊 Generating weekly digest...',
        'weekly_top_games': '🏆 <b>Weekly TOP-5 games:</b>',
        
        # Miscellaneous
        'free_games_title': '🎁 <b>Current free giveaways:</b>',
        'current_deals': '🔥 <b>Current deals from {min_discount}%:</b>',
        'game_ends': 'Until: ',
        'forever_free': 'Forever',
        'original_price': 'Regular price: ',
        'discount_price': 'Discounted price: ',
        'discount_percent': 'Discount: ',
        'steam_rating': 'Rating: ',
    }
}

def get_text(user_language: str, key: str, **kwargs) -> str:
    """
    Получить переведенный текст для указанного языка
    
    Args:
        user_language: Код языка пользователя ('ru' или 'en')
        key: Ключ для поиска текста
        **kwargs: Параметры для форматирования строки
    
    Returns:
        Переведенный и отформатированный текст
    """
    # Если язык не поддерживается, используем русский как fallback
    lang = user_language if user_language in TRANSLATIONS else 'ru'
    
    # Получаем текст из словаря переводов
    text = TRANSLATIONS[lang].get(key, f"[MISSING: {key}]")
    
    # Форматируем текст с переданными параметрами
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as e:
            # Если не удалось отформатировать, возвращаем исходный текст
            pass
    
    return text

def get_available_languages() -> List[str]:
    """Получить список доступных языков"""
    return list(TRANSLATIONS.keys())
