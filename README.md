# 🤖 FinBot AI - Moliyaviy Yordamchi Bot

FinBot AI - bu sizning shaxsiy moliyaviy yordamchingiz. Bu bot sizga moliyaviy holatingizni nazorat qilish, xarajatlaringizni kuzatish va AI yordamida moliyaviy maslahat olish imkonini beradi.

## ✨ Asosiy funksiyalar

### 💰 Moliyaviy boshqaruv
- **Kirim/Chiqim qo'shish** - Daromad va xarajatlaringizni kiritish
- **Balans ko'rish** - Joriy moliyaviy holat
- **Tahlil** - Xarajatlar tahlili va statistikasi
- **Kategoriyalar** - Xarajatlar kategoriyalari bo'yicha tahlil

### 🤖 AI vositalar
- **AI Moliyaviy Maslahat** - Shaxsiy moliyaviy tavsiyalar
- **AI Byudjet Tavsiyasi** - AI yordamida byudjet tuzish
- **AI Xarajatlar Tahlili** - Xarajatlar patternlarini tahlil qilish
- **AI Maqsad Monitoring** - Maqsadlaringizni kuzatish
- **AI Tejash Maslahatlari** - Tejash bo'yicha tavsiyalar
- **AI Investitsiya Maslahati** - Investitsiya bo'yicha maslahat

### ⚙️ Sozlamalar
- **Til o'zgartirish** - O'zbekcha, Ruscha, Inglizcha
- **Valyuta o'zgartirish** - So'm, Dollar, Euro va boshqalar
- **Bildirishnomalar** - Push-bildirishnomalar sozlamalari
- **Avtomatik hisobotlar** - Kunlik, haftalik, oylik hisobotlar
- **Ma'lumotlarni eksport qilish** - Ma'lumotlaringizni saqlash
- **Zaxira nusxasi** - Ma'lumotlaringizni zaxiralash

### 🎯 Maqsadlar va monitoring
- **Maqsad qo'yish** - Moliyaviy maqsadlar belgilash
- **Progress kuzatish** - Maqsadlarga erishish darajasi
- **AI monitoring** - AI yordamida maqsadlarni kuzatish

### 📊 Hisobotlar va tahlil
- **Kunlik hisobotlar** - Har kungi xarajatlar
- **Haftalik hisobotlar** - Haftalik statistikalar
- **Oylik hisobotlar** - Oylik moliyaviy holat
- **Kategoriyalar bo'yicha tahlil** - Xarajatlar tuzilishi

## 🚀 O'rnatish va ishga tushirish

### Talablar
- Python 3.8+
- Telegram Bot Token
- SQLite ma'lumotlar bazasi

### O'rnatish
```bash
# Loyihani klonlash
git clone https://github.com/your-username/finbot.git
cd finbot

# Virtual environment yaratish
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows

# Kerakli paketlarni o'rnatish
pip install -r requirements.txt

# Environment o'zgaruvchilarini sozlash
cp .env.example .env
# .env faylini tahrirlash va BOT_TOKEN qo'shish
```

### Ishga tushirish
```bash
# Botni ishga tushirish
python main.py

# Yoki PowerShell orqali (Windows)
.\run_bot.ps1

# Yoki batch fayl orqali (Windows)
run_bot.bat
```

## 📁 Loyiha tuzilishi

```
finbot/
├── main.py                 # Asosiy bot fayli
├── db.py                   # Ma'lumotlar bazasi operatsiyalari
├── utils.py                # Yordamchi funksiyalar
├── ai_service.py           # AI xizmatlari
├── requirements.txt        # Kerakli paketlar
├── handlers/              # Bot handlerlari
│   ├── start.py          # Boshlash va onboarding
│   ├── finance.py        # Moliyaviy operatsiyalar
│   ├── ai.py             # AI vositalar
│   ├── settings.py       # Sozlamalar
│   ├── goals.py          # Maqsadlar
│   ├── budget.py         # Byudjet
│   └── push.py           # Push-bildirishnomalar
├── README.md             # Loyiha haqida ma'lumot
└── Dockerfile            # Docker konfiguratsiyasi
```

## 🔧 Yangi funksiyalar

### 🤖 AI vositalar
- **Moliyaviy maslahat** - Shaxsiy moliyaviy tavsiyalar
- **Byudjet tavsiyasi** - AI yordamida byudjet tuzish
- **Xarajatlar tahlili** - Patternlar va trendlar
- **Maqsad monitoring** - Maqsadlarni kuzatish
- **Tejash maslahatlari** - Tejash bo'yicha tavsiyalar
- **Investitsiya maslahati** - Investitsiya strategiyalari

### ⚙️ Kengaytirilgan sozlamalar
- **Til o'zgartirish** - 3 tilda qo'llab-quvvatlash
- **Valyuta o'zgartirish** - 9 ta valyuta
- **Bildirishnomalar** - Push-bildirishnomalar
- **Avtomatik hisobotlar** - Kunlik/haftalik/oylik
- **Ma'lumotlarni eksport** - JSON formatda
- **Zaxira nusxasi** - Ma'lumotlarni saqlash

### 📊 Yangi tahlil funksiyalari
- **Kategoriyalar bo'yicha tahlil** - Xarajatlar tuzilishi
- **Vaqt bo'yicha tahlil** - Kunlik/haftalik/oylik
- **Trend tahlili** - Xarajatlar dinamikasi
- **Taqqoslash tahlili** - O'zgarishlar

## 🎯 Maqsadlar va monitoring

### Maqsad qo'yish
- Moliyaviy maqsadlar belgilash
- Vaqt chegarasi qo'yish
- Progress kuzatish
- AI yordamida tavsiyalar

### Monitoring
- Maqsadlarga erishish darajasi
- Vaqt bo'yicha progress
- AI maslahatlar
- Avtomatik hisobotlar

## 📈 Hisobotlar va statistikalar

### Kunlik hisobotlar
- Bugungi xarajatlar
- Daromadlar
- Balans holati
- Kategoriyalar bo'yicha tahlil

### Haftalik hisobotlar
- Haftalik statistikalar
- O'zgarishlar dinamikasi
- Trend tahlili
- AI tavsiyalari

### Oylik hisobotlar
- Oylik moliyaviy holat
- Maqsadlar progressi
- Katta tahlil
- Kelgusi oy rejalari

## 🔔 Bildirishnomalar

### Push-bildirishnomalar
- Kunlik eslatmalar
- Haftalik hisobotlar
- Oylik hisobotlar
- Maqsad eslatmalari

### Sozlamalar
- Bildirishnomalarni yoqish/o'chirish
- Vaqt sozlash
- Turli xil bildirishnomalar

## 🌐 Til qo'llab-quvvatlash

### O'zbekcha
- To'liq qo'llab-quvvatlash
- Mahalliy valyutalar
- O'zbekcha interfeys

### Ruscha
- To'liq tarjima
- Rossiya valyutalari
- Mahalliy sozlamalar

### Inglizcha
- Xalqaro standartlar
- Ko'p valyuta qo'llab-quvvatlash
- Global funksiyalar

## 💾 Ma'lumotlar boshqaruvi

### Ma'lumotlarni saqlash
- SQLite ma'lumotlar bazasi
- Avtomatik zaxiralash
- Ma'lumotlarni eksport qilish

### Xavfsizlik
- Foydalanuvchi ma'lumotlari himoyasi
- Shaxsiy ma'lumotlar
- Ma'lumotlarni o'chirish

## 🚀 Deployment

### Railway
```bash
# Railway'da deployment
railway login
railway init
railway up
```

### Docker
```bash
# Docker orqali ishga tushirish
docker build -t finbot .
docker run -d finbot
```

### Heroku
```bash
# Heroku'da deployment
heroku create finbot-ai
git push heroku main
```

## 📊 Monitoring va admin paneli

### Admin funksiyalari
- Bot statistikasi
- Foydalanuvchilar ro'yxati
- Tranzaksiyalar tarixi
- Xatoliklar monitoringi

### Statistika
- Foydalanuvchilar soni
- Tranzaksiyalar soni
- Faol maqsadlar
- Kunlik faollik

## 🤝 Hissa qo'shish

Loyihaga hissa qo'shish uchun:

1. Repository'ni fork qiling
2. Yangi branch yarating
3. O'zgarishlarni qiling
4. Pull request yuboring

## 📞 Yordam va qo'llab-quvvatlash

- **Telegram**: @finbot_support
- **Email**: support@finbot.ai
- **GitHub Issues**: [Issues sahifasi](https://github.com/your-username/finbot/issues)

## 📄 Litsenziya

Bu loyiha MIT litsenziyasi ostida tarqatiladi. Batafsil ma'lumot uchun [LICENSE](LICENSE) faylini ko'ring.

## 🙏 Minnatdorchilik

- Telegram Bot API
- Python-telegram-bot kutubxonasi
- SQLite ma'lumotlar bazasi
- Barcha foydalanuvchilar va hissa qo'shganlar

---

**FinBot AI** - Sizning moliyaviy kelajagingizni nazorat qilish uchun yaratilgan zamonaviy yordamchi bot. 🤖💰