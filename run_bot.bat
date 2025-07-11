@echo off
echo === FinBot AI Telegram Bot ===
echo.

REM Check if BOT_TOKEN is set
if "%BOT_TOKEN%"=="" (
    echo ❌ BOT_TOKEN topilmadi!
    echo.
    echo Bot token olish uchun:
    echo 1. Telegram da @BotFather ga boring
    echo 2. /newbot buyrug'ini yuboring
    echo 3. Bot nomi va username bering
    echo 4. Token ni nusxalab oling
    echo.
    set /p BOT_TOKEN="Bot token ni kiriting: "
    echo ✅ BOT_TOKEN saqlandi!
) else (
    echo ✅ BOT_TOKEN topildi!
)

echo.
echo 🤖 Bot ishga tushmoqda...
echo To'xtatish uchun Ctrl+C bosing
echo.

REM Run the bot
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Xatolik yuz berdi!
    echo.
    echo Muammo hal qilish:
    echo 1. Python o'rnatilganligini tekshiring
    echo 2. requirements.txt ni o'rnatganligingizni tekshiring
    echo 3. BOT_TOKEN to'g'ri sozlanganligini tekshiring
    pause
) 