# 🤖 AI API O'rnatish Qo'llanmasi

## OpenAI API o'rnatish

### 1. OpenAI API kalitini olish
1. [OpenAI Platform](https://platform.openai.com/) ga o'ting
2. Ro'yxatdan o'ting yoki tizimga kiring
3. API Keys bo'limiga o'ting
4. "Create new secret key" tugmasini bosing
5. API kalitini nusxalab oling

### 2. Environment variable sozlash

#### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY = "your_openai_api_key_here"
```

#### Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=your_openai_api_key_here
```

#### Linux/Mac:
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 3. Botni ishga tushirish
```bash
python main.py
```

## 🤖 AI Funksiyalari

### 1. AI Maslahat
- Foydalanuvchi ma'lumotlari asosida shaxsiy moliyaviy maslahat
- Balans, kirim, chiqim va kategoriyalar tahlili
- O'zbek tilida javob

### 2. AI Tahlil
- Xarajatlar tahlili
- Kategoriyalar bo'yicha statistika
- Tejash maslahatlari

## ⚙️ Sozlamalar

### AI yoqish/o'chirish:
```python
# ai_service.py faylida
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
AI_ENABLED = bool(OPENAI_API_KEY)
```

### Model o'zgartirish:
```python
# ai_service.py faylida
data = {
    "model": "gpt-3.5-turbo",  # yoki "gpt-4"
    "messages": [...],
    "max_tokens": 200,
    "temperature": 0.7
}
```

## 💰 Xarajatlar

- **GPT-3.5-turbo**: ~$0.002 per 1K tokens
- **GPT-4**: ~$0.03 per 1K tokens

## 🔧 Xatoliklar

### API kalit xatosi:
```
AI API xatosi: 401 Unauthorized
```
**Yechim**: API kalitni tekshiring

### Internet xatosi:
```
AI API xatosi: Connection error
```
**Yechim**: Internet aloqasini tekshiring

### Token chegarasi:
```
AI API xatosi: 429 Too Many Requests
```
**Yechim**: Bir necha daqiqa kutib, qayta urinib ko'ring

## 🎯 Tavsiyalar

1. **API kalitni himoya qiling** - hech kimga bermang
2. **Xarajatlarni nazorat qiling** - usage dashboard dan kuzating
3. **Backup plan** - AI yo'q bo'lganda standart maslahatlar ishlaydi
4. **Testing** - avval kichik so'rovlar bilan sinab ko'ring

## 📞 Yordam

Agar muammolar bo'lsa:
1. API kalitni tekshiring
2. Internet aloqasini tekshiring
3. Log fayllarini ko'ring
4. OpenAI support ga murojaat qiling 