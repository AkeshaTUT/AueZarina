@echo off
echo 🎮 Steam Discount Bot - Установка токена
echo ========================================
echo.

set /p BOT_TOKEN="Введите токен бота: "

if "%BOT_TOKEN%"=="" (
    echo ❌ Токен не может быть пустым!
    pause
    exit /b 1
)

echo.
echo 💾 Установка переменной окружения...
setx TELEGRAM_BOT_TOKEN "%BOT_TOKEN%"

if errorlevel 1 (
    echo ❌ Ошибка при установке токена
    pause
    exit /b 1
)

echo ✅ Токен успешно установлен!
echo.
echo 🚀 Теперь можно запустить бота командой: start_bot.bat
echo    Или в новом окне командной строки: py run_bot.py
echo.
echo ⚠️  ВАЖНО: Перезапустите командную строку для применения изменений!
pause
