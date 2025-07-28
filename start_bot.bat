@echo off
cd /d "%~dp0"
echo 🎮 Steam Discount Telegram Bot
echo ==============================
echo.

echo 🚀 Запуск бота...
py run_bot.py

if errorlevel 1 (
    echo.
    echo ❌ Бот завершился с ошибкой
    pause
)
