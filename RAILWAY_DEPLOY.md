# Railway'da FinBot AI Deployment

## 🚀 Railway'da deployment qilish

### 1. Railway'ga kirish
- [railway.app](https://railway.app) ga boring
- GitHub account bilan tizimga kiring

### 2. Yangi project yarating
- "New Project" tugmasini bosing
- "Deploy from GitHub repo" ni tanlang
- Bu repository'ni tanlang

### 3. Environment Variables sozlang
Railway'da quyidagi environment variables'ni qo'shing:

```
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_admin_user_id
```

### 4. Database sozlang
- Railway'da "Variables" bo'limida
- `DATABASE_URL` qo'shing (agar kerak bo'lsa)

### 5. Deploy qiling
- Railway avtomatik deploy qiladi
- Logs'da xatoliklar yo'qligini tekshiring

## 🔧 Muhim eslatmalar

- Bot token'ni @BotFather dan oling
- Admin ID'ni o'zingizning Telegram ID'ngiz bilan almashtiring
- Database avtomatik yaratiladi
- Logs'da xatoliklar bo'lsa, environment variables'ni tekshiring

## 📝 Test qilish

Deployment tugagandan so'ng:
1. Telegram'da bot'ga /start yuboring
2. Onboarding jarayonini test qiling
3. Barcha funksiyalar ishlayotganini tekshiring 