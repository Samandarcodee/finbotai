# FinBot AI Telegram Bot Starter
# Bu script botni ishga tushirish uchun ishlatiladi

Write-Host "=== FinBot AI Telegram Bot ===" -ForegroundColor Green
Write-Host ""

# BOT_TOKEN ni o'rnatish
$env:BOT_TOKEN = "7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE"
Write-Host "✅ BOT_TOKEN o'rnatildi!" -ForegroundColor Green

Write-Host ""
Write-Host "🤖 Bot ishga tushmoqda..." -ForegroundColor Cyan
Write-Host "To'xtatish uchun Ctrl+C bosing" -ForegroundColor Yellow
Write-Host ""

# Botni ishga tushirish
try {
    python main.py
} catch {
    Write-Host "❌ Xatolik yuz berdi: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Muammo hal qilish:" -ForegroundColor Yellow
    Write-Host "1. Python o'rnatilganligini tekshiring" -ForegroundColor White
    Write-Host "2. requirements.txt ni o'rnatganligingizni tekshiring" -ForegroundColor White
    Write-Host "3. BOT_TOKEN to'g'ri sozlanganligini tekshiring" -ForegroundColor White
} 