# FinBot AI Telegram Bot Runner
# Bu script botni ishga tushirish uchun ishlatiladi

Write-Host "=== FinBot AI Telegram Bot ===" -ForegroundColor Green
Write-Host ""

# BOT_TOKEN ni tekshirish
if (-not $env:BOT_TOKEN) {
    Write-Host "❌ BOT_TOKEN topilmadi!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bot token olish uchun:" -ForegroundColor Yellow
    Write-Host "1. Telegram da @BotFather ga boring" -ForegroundColor White
    Write-Host "2. /newbot buyrug'ini yuboring" -ForegroundColor White
    Write-Host "3. Bot nomi va username bering" -ForegroundColor White
    Write-Host "4. Token ni nusxalab oling" -ForegroundColor White
    Write-Host ""
    
    $token = Read-Host "Bot token ni kiriting" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
    $env:BOT_TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    Write-Host "✅ BOT_TOKEN saqlandi!" -ForegroundColor Green
} else {
    Write-Host "✅ BOT_TOKEN topildi!" -ForegroundColor Green
}

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