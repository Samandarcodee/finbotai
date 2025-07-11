# 🚀 FinBot AI Deploy Qo'llanmasi

## Railway (Tavsiya etiladi - Bepul)

### 1. Railway'ga kirish
- [railway.app](https://railway.app) ga o'ting
- GitHub bilan ro'yxatdan o'ting

### 2. Yangi loyiha yarating
- "New Project" → "Deploy from GitHub repo"
- GitHub repongizni tanlang

### 3. Environment o'zgaruvchilarini sozlang
- Settings → Variables
- `BOT_TOKEN` = `7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE`

### 4. Deploy qiling
- Railway avtomatik deploy qiladi
- Bot 24/7 ishlaydi

---

## Heroku

### 1. Heroku CLI o'rnating
```bash
# Windows uchun
winget install --id=Heroku.HerokuCLI
```

### 2. Login qiling
```bash
heroku login
```

### 3. Yangi app yarating
```bash
heroku create finbot-ai-bot
```

### 4. Environment o'zgaruvchisini sozlang
```bash
heroku config:set BOT_TOKEN=7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE
```

### 5. Deploy qiling
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

---

## Docker

### 1. Docker image yarating
```bash
docker build -t finbot-ai .
```

### 2. Docker container ishga tushiring
```bash
docker run -d -e BOT_TOKEN=7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE finbot-ai
```

---

## VPS (Virtual Private Server)

### 1. VPS o'rnating (Ubuntu 20.04)
### 2. Python va git o'rnating
```bash
sudo apt update
sudo apt install python3 python3-pip git
```

### 3. Loyihani klonlang
```bash
git clone <your-repo-url>
cd finbot
```

### 4. Dependencies o'rnating
```bash
pip3 install -r requirements.txt
```

### 5. Systemd service yarating
```bash
sudo nano /etc/systemd/system/finbot.service
```

Service fayli:
```ini
[Unit]
Description=FinBot AI Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/finbot
Environment=BOT_TOKEN=7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6. Service'ni ishga tushiring
```bash
sudo systemctl daemon-reload
sudo systemctl enable finbot
sudo systemctl start finbot
```

---

## ⚠️ Muhim eslatmalar

1. **BOT_TOKEN ni hech kimga bermang!**
2. **Database fayli avtomatik yaratiladi**
3. **Bot 24/7 ishlashi uchun server kerak**
4. **Railway eng oson va bepul variant**

## 🎯 Tavsiya

**Railway** ni tanlang - u bepul, oson va ishonchli! 