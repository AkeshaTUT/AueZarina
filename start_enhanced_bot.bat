@echo off
echo ===================================
echo   Steam Discount Bot v2.0
echo   Enhanced with 5 new features:
echo   1. Genre filtering
echo   2. Free games listings  
echo   3. Price history tracking
echo   4. Discount thresholds
echo   5. Weekly digest
echo ===================================
echo.

cd /d "%~dp0"

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo Warning: Some packages might not have been installed properly
)

echo.
echo Starting Steam Discount Bot...
echo Bot will run with enhanced features:
echo - Personalized genre filtering
echo - Free games notifications
echo - Price history tracking  
echo - Custom discount thresholds
echo - Weekly top-5 digest
echo.
echo Press Ctrl+C to stop the bot
echo.

python steam_bot.py

echo.
echo Bot stopped. Press any key to exit...
pause >nul
