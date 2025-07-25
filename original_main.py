import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import os
from datetime import datetime, timedelta
import random
from ai_service import ai_service
from telegram.constants import ParseMode
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.error import TelegramError

# ==== CONFIG ====
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "finbot.db"

# ==== CONSTANTS ====
ADMIN_ID = 786171158  # Sizning Telegram ID'ingiz
ASK_SUPPORT = 100  # yangi state

# ==== MESSAGES (multi-language, DRY) ====
MESSAGES = {
    "uz": {
        "main_menu": "ЁЯПа Bosh menyu",
        "invalid_choice": "тЭМ Noto'g'ri tanlov. Qaytadan tanlang.",
        "enter_income": "Kirim miqdorini kiriting (masalan: 1 000 000):",
        "enter_expense": "Chiqim miqdorini kiriting (masalan: 250 000):",
        "add_note": "Izoh qo'shmoqchimisiz? (Masalan: nonushta, yo'l puli)\n\nIzoh kiriting yoki 'Orqaga' tugmasini bosing.",
        "success_income": "тЬЕ Kirim muvaffaqiyatli qo'shildi!",
        "success_expense": "тЬЕ Chiqim muvaffaqiyatli qo'shildi!",
        "error": "тЭМ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
        "cancelled": "тЭМ Amal bekor qilindi.",
        "choose_category": "Kategoriya tanlang:",
        "onboarding_done": "ЁЯОп Onboarding yakunlandi! Endi asosiy menyudan foydalanishingiz mumkin.",
        "push_daily": "ЁЯМЮ Yangi kun yangi imkoniyatlar bilan keldi! Bugun moliyaviy odatingizni davom ettiring: xarajatlaringizni yozishni unutmang!\n\nЁЯТб Bugun hech bo'lmasa bitta xarajatingizni yozib qo'ydingizmi?",
        "push_weekly": "ЁЯУК Haftalik yakun:\nтАУ Kirim: {income} so'm\nтАУ Chiqim: {expense} so'm\nтАУ Tejaganingiz: {saved} so'm ЁЯСП\n\nЁЯТ░ Tejamkorlik odatingizni davom ettirasizmi? Shunday qiling, kelajakdagi siz minnatdor bo'ladi.",
        "error_soft": "тЪая╕П Xatolik yuz berdi, lekin qo'rqmang, jamoamiz bu haqida xabardor.",
        "feedback_push": "ЁЯЩП FinBot AI sizga yordam berayaptimi? Takliflaringiz bormi?"
    },
    "ru": {
        "main_menu": "\U0001F3E0 \u0413\u043B\u0430\u0432\u043D\u043E\u0435 \u043C\u0435\u043D\u044E",
        "invalid_choice": "\u274c \u041D\u0435\u0432\u0435\u0440\u043D\u044B\u0439 \u0432\u044B\u0431\u043E\u0440. \u041F\u043E\u0436\u0430\u043B\u0443\u0439\u0441\u0442\u0430, \u0432\u044B\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u043D\u043E\u0432\u0430.",
        "currencies": ["ЁЯТ░ ╨Ш╨╖╨╝╨╡╨╜╨╕╤В╤М ╨▓╨░╨╗╤О╤В╤Г", "ЁЯТ░ Change currency"]
    },
    "en": {
        "main_menu": "\U0001F3E0 Main menu",
        "invalid_choice": "\u274c Invalid choice. Please try again.",
        "currencies": ["ЁЯТ░ Change currency"]
    }
}

# ==== MAIN MENU KEYBOARDS (MODULLAR) ====
MAIN_MODULES_KEYBOARD = [
    ["ЁЯУе Kirim/Chiqim"],
    ["ЁЯУК Balans/Tahlil"],
    ["ЁЯдЦ AI vositalar"],
    ["тЪЩя╕П Sozlamalar/Yordam"]
]
KIRIM_CHIQIM_KEYBOARD = [
    ["ЁЯТ░ Kirim qo'shish", "ЁЯТ╕ Chiqim qo'shish"],
    ["ЁЯФЩ Orqaga"]
]
BALANS_TAHLIL_KEYBOARD = [
    ["ЁЯУК Balans", "ЁЯУИ Tahlil"],
    ["ЁЯФЩ Orqaga"]
]
AI_VOSITALAR_KEYBOARD = [
    ["ЁЯдЦ AI maslahat", "ЁЯУК AI Tahlil"],
    ["ЁЯдЦ AI Byudjet", "ЁЯОп AI Maqsad"],
    ["ЁЯФЩ Orqaga"]
]
SOZLAMALAR_YORDAM_KEYBOARD = [
    ["тЪЩя╕П Sozlamalar", "тЭУ Yordam"],
    ["ЁЯФЩ Orqaga"]
]

# ==== MAIN MENU KEYBOARD (Sozlamalarsiz) ====
MAIN_MENU_KEYBOARD = [
    ["\U0001F4B0 Kirim qo'shish", "\U0001F4B8 Chiqim qo'shish"],
    ["\U0001F4CA Balans", "\U0001F4C8 Tahlil"],
    ["\U0001F4CB Kategoriyalar", "\U0001F3AF Byudjet"],
    ["\U0001F4E4 Export", "\U0001F3C6 Rekorlar"],
    ["\U0001F916 AI maslahat", "\U0001F4CA AI Tahlil"],
    ["ЁЯдЦ AI Byudjet", "ЁЯОп AI Maqsad"],
    ["\u2753 Yordam"]
]

# ==== LOGGING ====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==== DATABASE INITIALIZATION (add goals table) ====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    user_id INTEGER,
                    type TEXT,
                    amount INTEGER,
                    note TEXT,
                    category TEXT,
                    date TEXT DEFAULT (datetime('now'))
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    joined_at TEXT DEFAULT (datetime('now'))
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'uz',
                    currency TEXT DEFAULT "so'm",
                    onboarding_done INTEGER DEFAULT 0
                )''')
    # Add onboarding_done column if missing (for existing DB)
    try:
        c.execute("ALTER TABLE user_settings ADD COLUMN onboarding_done INTEGER DEFAULT 0")
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                    user_id INTEGER,
                    category TEXT,
                    amount INTEGER,
                    month TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
                    user_id INTEGER,
                    goal_name TEXT,
                    target_amount INTEGER,
                    deadline TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )''')
    conn.commit()
    conn.close()

def get_db_connection():
    """Database connection helper with error handling"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# ==== UTILITY FUNCTIONS ====
def format_currency(amount, currency="so'm"):
    """Format currency with proper spacing"""
    return f"{amount:,} {currency}"

def validate_amount(amount_str):
    """Validate and parse amount string"""
    try:
        # Remove spaces and common separators
        cleaned = amount_str.replace(' ', '').replace(',', '').replace('.', '')
        amount = int(cleaned)
        if amount <= 0:
            return None, "Miqdor 0 dan katta bo'lishi kerak! Masalan: 1 000 000"
        if amount > 999999999:
            return None, "Miqdor juda katta! Iltimos, kichikroq miqdorni kiriting. Masalan: 1 000 000"
        return amount, None
    except ValueError:
        return None, "Noto'g'ri format! Masalan: 1 000 000 yoki 5000000."

def get_category_keyboard(is_income=True):
    if is_income:
        categories = [
            ["ЁЯТ╡ Maosh", "ЁЯПж Kredit/qarz"],
            ["ЁЯОБ Sovg'a/yordam", "ЁЯТ╕ Qo'shimcha daromad"],
            ["ЁЯТ│ Boshqa daromad"],
            ["ЁЯФЩ Orqaga", "тЭМ Bekor qilish", "ЁЯПа Bosh menyu"]
        ]
    else:
        categories = [
            ["ЁЯНФ Oziq-ovqat", "ЁЯЪЧ Transport"],
            ["ЁЯТК Sog'liq", "ЁЯУЪ Ta'lim"],
            ["ЁЯОо O'yin-kulgi", "ЁЯСХ Kiyim"],
            ["ЁЯПа Uy", "ЁЯУ▒ Aloqa"],
            ["ЁЯТ│ Boshqa chiqim", "ЁЯФЩ Orqaga"],
            ["тЭМ Bekor qilish", "ЁЯПа Bosh menyu"]
        ]
    return ReplyKeyboardMarkup(categories, resize_keyboard=True, one_time_keyboard=True)

# ==== COMMANDS ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = getattr(update.message, 'from_user', None)
    if not user:
        return
    user_id = getattr(user, 'id', None)
    user_name = getattr(user, 'first_name', 'Foydalanuvchi')
    # Check if user is new (onboarding needed)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT onboarding_done FROM user_settings WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None or not isinstance(row, (list, tuple)) or not row[0]:
        # Onboarding: hissiyotli welcome va 3 bosqich
        welcome_text = (
            f"ЁЯСЛ Assalomu alaykum, {user_name}!\n\n"
            "ЁЯТб Siz o'z moliyaviy kelajagingizni nazorat qilmoqchimisiz?\n"
            "Men sizga bu yo'lda yordam beruvchi FinBot AIman ЁЯдЦ\n\n"
            "тЪбя╕П 3 daqiqa ichida sozlanamizmi?\n\n"
            "1я╕ПтГг Valyutani tanlang (so'm, dollar, euro)"
        )
        currency_kb = ReplyKeyboardMarkup([
            ["ЁЯЗ║ЁЯЗ┐ So'm", "ЁЯТ╡ Dollar", "ЁЯТ╢ Euro"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(welcome_text, reply_markup=currency_kb)
        return ONBOARDING_CURRENCY
    # Agar onboardingdan o'tgan bo'lsa, asosiy menyu (faqat InlineKeyboard)
    return await show_main_menu(update)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    help_text = (
        "тД╣я╕П <b>Yordam</b>\n\n"
        "тАв <b>Kirim/Chiqim qo'shish</b> тАФ mos tugmani bosing va miqdorni kiriting.\n"
        "тАв <b>Balans/Tahlil</b> тАФ moliyaviy holatingizni ko'ring.\n"
        "тАв <b>AI maslahat</b> тАФ shaxsiy moliyaviy tavsiya oling.\n"
        "тАв <b>AI Byudjet</b> тАФ AI yordamida byudjet tuzing.\n"
        "тАв <b>AI Maqsad</b> тАФ maqsad qo'ying va monitoring qiling.\n\n"
        "тЭМ <b>Bekor qilish</b> тАФ istalgan vaqtda dialogni to'xtatadi.\n"
        "ЁЯПа <b>Bosh menyu</b> тАФ asosiy menyuga qaytadi."
    )
    await update.message.reply_text(help_text, reply_markup=ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    user = update.message.from_user
    user_message = update.message.text
    admin_text = (
        f"ЁЯЖШ Yangi yordam so'rovi!\n"
        f"ЁЯСд Foydalanuvchi: {getattr(user, 'first_name', 'Foydalanuvchi')} ({getattr(user, 'id', 'Noma' + 'lum')})\n"
        f"тЬЙя╕П Xabar: {user_message}\n\n"
        f"Javob berish uchun: /reply_{getattr(user, 'id', '')} <javob matni>"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    await update.message.reply_text("Yordam so'rovingiz yuborildi. Admin tez orada javob beradi.")
    return ConversationHandler.END

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return
    from_user = getattr(update.message, 'from_user', None)
    if not from_user or not hasattr(from_user, 'id'):
        return
    if from_user.id != ADMIN_ID:
        return
    text = update.message.text
    if text.startswith("/reply_"):
        try:
            parts = text.split(" ", 1)
            user_id_str = parts[0].replace("/reply_", "")
            user_id = int(user_id_str) if user_id_str.isdigit() else getattr(getattr(update.message, 'from_user', None), 'id', None)
            reply_text = parts[1] if len(parts) > 1 else "Admin javobi yo'q."
            if user_id:
                await context.bot.send_message(chat_id=user_id, text=f"Admin javobi: {reply_text}")
                if update.message is not None:
                    await update.message.reply_text("Javob foydalanuvchiga yuborildi.")
            else:
                if update.message is not None:
                    await update.message.reply_text("Foydalanuvchi ID aniqlanmadi.")
        except Exception as e:
            if update.message is not None:
                await update.message.reply_text(f"Xatolik: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    await update.message.reply_text("тЭМ Amal bekor qilindi.", reply_markup=ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True))
    return ConversationHandler.END

# ==== HANDLERS ====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if text.lower() in ["/start", "/cancel", "ЁЯПа Bosh menyu", "ЁЯПа Bosh menyu"]:
        return await start(update, context)
    if user_id is None:
        return ConversationHandler.END

    # MODULLAR
    if text == "ЁЯУе Kirim/Chiqim":
        await update.message.reply_text(
            "Kirim yoki chiqim qo'shish uchun tanlang:",
            reply_markup=ReplyKeyboardMarkup(KIRIM_CHIQIM_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    elif text == "ЁЯУК Balans/Tahlil":
        await update.message.reply_text(
            "Balans yoki tahlilni tanlang:",
            reply_markup=ReplyKeyboardMarkup(BALANS_TAHLIL_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    elif text == "ЁЯдЦ AI vositalar":
        await update.message.reply_text(
            "AI vositalaridan birini tanlang:",
            reply_markup=ReplyKeyboardMarkup(AI_VOSITALAR_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    elif text == "тЪЩя╕П Sozlamalar/Yordam":
        await update.message.reply_text(
            "Sozlamalar yoki yordam bo'limini tanlang:",
            reply_markup=ReplyKeyboardMarkup(SOZLAMALAR_YORDAM_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    # MODUL ichidan orqaga
    elif text == "ЁЯФЩ Orqaga":
        await update.message.reply_text(
            "Asosiy modullar menyusi:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True)
        )
        return ConversationHandler.END
    # Kirim/Chiqim tugmalari
    elif text == "ЁЯТ░ Kirim qo'shish":
        await update.message.reply_text(
            "ЁЯТ░ Kirim uchun kategoriya tanlang (masalan: Maosh, Sovg'a/yordam, Qo'shimcha daromad):",
            reply_markup=get_category_keyboard(is_income=True)
        )
        return 4
    elif text == "ЁЯТ╕ Chiqim qo'shish":
        await update.message.reply_text(
            "ЁЯТ╕ Chiqim uchun kategoriya tanlang:",
            reply_markup=get_category_keyboard(is_income=False)
        )
        return 3
    # Balans/Tahlil tugmalari
    elif text == "ЁЯУК Balans":
        return await show_balance(update, user_id)
    elif text == "ЁЯУИ Tahlil":
        return await show_analysis(update, user_id)
    # AI vositalari
    elif text == "ЁЯдЦ AI maslahat":
        return await show_ai_advice(update, user_id)
    elif text == "ЁЯУК AI Tahlil":
        return await show_ai_analysis(update, user_id)
    elif text == "ЁЯдЦ AI Byudjet":
        await update.message.reply_text("AI byudjet funksiyasi uchun /ai_byudjet buyrug'ini yuboring yoki shu komandani bosing.")
        return ConversationHandler.END
    elif text == "ЁЯОп AI Maqsad":
        await update.message.reply_text("AI maqsad funksiyasi uchun /ai_maqsad buyrug'ini yuboring yoki shu komandani bosing.")
        return ConversationHandler.END
    # Sozlamalar/Yordam
    elif text == "тЪЩя╕П Sozlamalar":
        return await show_settings(update, user_id)
    elif text == "тЭУ Yordam":
        return await help_command(update, context)
    # Default
    else:
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"], reply_markup=ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True))
        return ConversationHandler.END

# Universal navigation keyboards
UNIVERSAL_CANCEL = ReplyKeyboardMarkup([["тЭМ Bekor qilish"], ["ЁЯПа Bosh menyu"]], resize_keyboard=True, one_time_keyboard=True)
UNIVERSAL_MENU = ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True)

# ==== STATE CONSTANTS (for ConversationHandler) ====
INCOME_AMOUNT, INCOME_NOTE = 101, 102
EXPENSE_AMOUNT, EXPENSE_NOTE = 201, 202

# ==== ONBOARDING STATE CONSTANTS ====
ONBOARDING_CURRENCY, ONBOARDING_INCOME, ONBOARDING_GOAL = 301, 302, 303

# BALANS
async def show_balance(update: Update, user_id: int):
    """Show user balance with improved formatting and emoji sections"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        total_data = c.fetchone()
        conn.close()
        month_income = month_data[0] or 0
        month_expense = month_data[1] or 0
        month_balance = month_income - month_expense
        total_income = total_data[0] or 0
        total_expense = total_data[1] or 0
        total_balance = total_income - total_expense
        balance_text = (
            "ЁЯУК <b>BALANS HISOBOTI</b>\n\n"
            "ЁЯЧУя╕П <b>Bu oy:</b>\n"
            f"ЁЯТ░ Kirim: {format_currency(month_income)}\n"
            f"ЁЯТ╕ Chiqim: {format_currency(month_expense)}\n"
            f"ЁЯТ╡ Balans: {format_currency(month_balance)}\n\n"
            "ЁЯУИ <b>Jami:</b>\n"
            f"ЁЯТ░ Kirim: {format_currency(total_income)}\n"
            f"ЁЯТ╕ Chiqim: {format_currency(total_expense)}\n"
            f"ЁЯТ╡ Balans: {format_currency(total_balance)}\n\n"
            f"ЁЯТб <b>Maslahat:</b> {get_balance_advice(total_balance, month_balance)}"
        )
        if update.message:
            await update.message.reply_text(balance_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Balance error: {e}")
        if update.message:
            await update.message.reply_text("тЭМ Balansni ko'rishda xatolik. Qaytadan urinib ko'ring.")

def get_balance_advice(total_balance, month_balance):
    """Get personalized balance advice"""
    if total_balance < 0:
        return "Balansingiz salbiy. Tejash rejangizni ko'rib chiqing."
    elif month_balance < 0:
        return "Bu oy xarajatlar ko'p. Keyingi oyga reja tuzing."
    elif month_balance > total_balance * 0.3:
        return "Ajoyib! Bu oy yaxshi tejayapsiz."
    else:
        return "Balansingiz barqaror. Davom eting!"

# TAHLIL
async def show_analysis(update: Update, user_id: int):
    """Show transaction analysis with improved formatting"""
    try:
        # settings = get_user_settings(user_id) # Removed as per edit hint
        # currency = settings['currency'] # Removed as per edit hint
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get recent transactions
        c.execute("""
            SELECT type, amount, note, category, date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 10
        """, (user_id,))
        transactions = c.fetchall()
        
        # Get category statistics
        c.execute("""
            SELECT category, COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 5
        """, (user_id,))
        categories = c.fetchall()
        
        conn.close()
        
        if not transactions:
            if update.message:
                await update.message.reply_text(
                    "ЁЯУИ TAHLIL\n\n"
                    "Hali tranzaksiyalar yo'q. Avval kirim yoki chiqim qo'shing!"
                )
            return
        
        analysis_text = "ЁЯУИ TAHLIL HISOBOTI\n\n"
        
        # Recent transactions
        analysis_text += "ЁЯХР Oxirgi tranzaksiyalar:\n"
        for t in transactions[:5]:
            emoji = "ЁЯТ░" if t[0] == "income" else "ЁЯТ╕"
            date_str = datetime.fromisoformat(t[4].replace('Z', '+00:00')).strftime("%d.%m")
            analysis_text += f"{emoji} {date_str} - {format_currency(t[1])} - {t[2]}\n"
        
        # Category analysis
        if categories:
            analysis_text += "\n Eng ko'p xarajat qilgan kategoriyalar:\n"
            for cat, count, total in categories:
                analysis_text += f"ЁЯП╖я╕П {cat}: {format_currency(total)} ({count} ta)\n"
        
        if update.message:
            await update.message.reply_text(analysis_text)
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        if update.message:
            await update.message.reply_text("тЭМ Tahlilni ko'rishda xatolik. Qaytadan urinib ko'ring.")

# KIRIM QO'SHISH
async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END

    # settings = get_user_settings(user_id) # Removed as per edit hint
    # currency = settings['currency'] # Removed as per edit hint
    text = update.message.text.strip()
    
    if text.lower() in ['/cancel', 'bekor', 'cancel', 'тЭМ bekor qilish', 'ЁЯПа bosh menyu']:
        return await cancel(update, context)
    
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"тЭМ {error}\n\nQaytadan kiriting yoki 'Bekor qilish' tugmasini bosing.", reply_markup=UNIVERSAL_CANCEL)
        return 1
    
    # Extract note from text
    parts = text.split(" ", 1)
    note = parts[1] if len(parts) > 1 else "Kirim"
    selected_category = context.user_data['selected_income_category'] if hasattr(context, 'user_data') and isinstance(context.user_data, dict) and 'selected_income_category' in context.user_data else 'Boshqa daromad'
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'income', ?, ?, ?)", 
                (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        
        success_text = f"""тЬЕ KIRIM QO'SHILDI!

ЁЯТ░ Miqdor: {format_currency(amount)}
ЁЯУВ Kategoriya: {selected_category}
ЁЯУЭ Izoh: {note}
ЁЯУЕ Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}

ЁЯТб Davom eting - har bir kirim muhim!"""
        
        await update.message.reply_text(success_text, reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Income add error: {e}")
        await update.message.reply_text("тЭМ Xatolik yuz berdi. Qaytadan urinib ko'ring.", reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END

async def income_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    if text == "ЁЯФЩ Orqaga" or text == "тЭМ Bekor qilish" or text == "ЁЯПа Bosh menyu":
        return await cancel(update, context)
    income_category_map = {
        "ЁЯТ╡ Maosh": "Maosh",
        "ЁЯПж Kredit/qarz": "Kredit/qarz",
        "ЁЯОБ Sovg'a/yordam": "Sovg'a/yordam",
        "ЁЯТ╕ Qo'shimcha daromad": "Qo'shimcha daromad",
        "ЁЯТ│ Boshqa daromad": "Boshqa daromad"
    }
    selected_category = income_category_map.get(text, "Boshqa daromad")
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['selected_income_category'] = selected_category
    await update.message.reply_text(
        f"тЬЕ Kategoriya: {selected_category}\n\nKirim miqdorini kiriting (masalan: 1 000 000):",
        reply_markup=UNIVERSAL_CANCEL
    )
    return INCOME_AMOUNT

async def income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"тЭМ {error}\n\nQaytadan kiriting yoki 'Bekor qilish' tugmasini bosing.", reply_markup=UNIVERSAL_CANCEL)
        return 101
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['income_amount'] = amount
    await update.message.reply_text(
        "Izoh qo'shmoqchimisiz? (Masalan: ish haqi, sovg'a, bonus)\n\nIzoh kiriting yoki 'Orqaga' tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup([["Orqaga"], ["Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return 102

async def income_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text.lower() in ["orqaga"]:
        await update.message.reply_text(
            "Kirim miqdorini kiriting (masalan: 500000):",
            reply_markup=UNIVERSAL_CANCEL
        )
        return INCOME_AMOUNT
    if text.lower() in ["bekor qilish", "/cancel", "cancel"]:
        return await cancel(update, context)
    note = text if text else "Kirim"
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    user_data = context.user_data if hasattr(context, 'user_data') and context.user_data is not None else {}
    selected_category = user_data.get('selected_income_category', 'Boshqa daromad')
    amount = user_data.get('income_amount', 0)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'income', ?, ?, ?)",
                  (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        success_text = f"""тЬЕ KIRIM QO'SHILDI!\n\nЁЯТ░ Miqdor: {format_currency(amount)}\nЁЯУВ Kategoriya: {selected_category}\nЁЯУЭ Izoh: {note}\nЁЯУЕ Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\nЁЯТб Davom eting - har bir kirim muhim!"""
        await update.message.reply_text(success_text, reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Income add error: {e}")
        await update.message.reply_text("тЭМ Xatolik yuz berdi. Qaytadan urinib ko'ring.", reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END

async def expense_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    if text == "я┐╜я┐╜ Orqaga" or text == "тЭМ Bekor qilish" or text == "ЁЯПа Bosh menyu":
        return await cancel(update, context)
    expense_category_map = {
        "ЁЯНФ Oziq-ovqat": "Oziq-ovqat",
        "ЁЯЪЧ Transport": "Transport",
        "ЁЯТК Sog'liq": "Sog'liq",
        "ЁЯУЪ Ta'lim": "Ta'lim",
        "ЁЯОо O'yin-kulgi": "O'yin-kulgi",
        "ЁЯСХ Kiyim": "Kiyim",
        "ЁЯПа Uy": "Uy",
        "ЁЯУ▒ Aloqa": "Aloqa",
        "ЁЯТ│ Boshqa chiqim": "Boshqa chiqim"
    }
    selected_category = expense_category_map.get(text, "Boshqa chiqim")
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['selected_expense_category'] = selected_category
    await update.message.reply_text(
        f"тЬЕ Kategoriya: {selected_category}\n\nChiqim miqdorini kiriting (masalan: 250 000):",
        reply_markup=UNIVERSAL_CANCEL
    )
    return EXPENSE_AMOUNT

async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"тЭМ {error}\n\nQaytadan kiriting yoki 'Bekor qilish' tugmasini bosing.", reply_markup=UNIVERSAL_CANCEL)
        return 201
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['expense_amount'] = amount
    await update.message.reply_text(
        "Izoh qo'shmoqchimisiz? (Masalan: nonushta, yo'l puli)\n\nIzoh kiriting yoki 'Orqaga' tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup([["Orqaga"], ["Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return 202

async def expense_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text.lower() in ["orqaga"]:
        await update.message.reply_text(
            "Chiqim miqdorini kiriting (masalan: 25000):",
            reply_markup=UNIVERSAL_CANCEL
        )
        return EXPENSE_AMOUNT
    if text.lower() in ["bekor qilish", "/cancel", "cancel"]:
        return await cancel(update, context)
    note = text if text else "Chiqim"
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    user_data = context.user_data if hasattr(context, 'user_data') and context.user_data is not None else {}
    selected_category = user_data.get('selected_expense_category', 'Boshqa chiqim')
    amount = user_data.get('expense_amount', 0)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'expense', ?, ?, ?)",
                  (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        success_text = f"""тЬЕ CHIQIM QO'SHILDI!\n\nЁЯТ╕ Miqdor: {format_currency(amount)}\nЁЯУВ Kategoriya: {selected_category}\nЁЯУЭ Izoh: {note}\nЁЯУЕ Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\nЁЯТб Xarajatlaringizni nazorat qiling!"""
        await update.message.reply_text(success_text, reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Expense add error: {e}")
        await update.message.reply_text("тЭМ Xatolik yuz berdi. Qaytadan urinib ko'ring.", reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END

# ==== ADDITIONAL FEATURES ====
async def show_categories(update: Update, user_id: int):
    try:
        # settings = get_user_settings(user_id) # Removed as per edit hint
        # currency = settings['currency'] # Removed as per edit hint
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT category, COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC
        """, (user_id,))
        categories = c.fetchall()
        conn.close()
        
        if not categories:
            if update.message:
                await update.message.reply_text(
                    "ЁЯУЛ KATEGORIYALAR\n\n"
                    "Hali kategoriyalar yo'q. Chiqimlar qo'shing!"
                )
            return
        
        text = "ЁЯУЛ KATEGORIYALAR BO'YICHA XARAJAT:\n\n"
        total_expense = sum(cat[2] for cat in categories)
        
        for cat, count, total in categories:
            percentage = (total / total_expense * 100) if total_expense > 0 else 0
            text += f"ЁЯП╖я╕П {cat}:\n"
            text += f"   ЁЯТ░ {format_currency(total)}\n"
            text += f"   ЁЯУК {percentage:.1f}% xarajat\n\n"
        
        if update.message:
            await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Categories error: {e}")
        if update.message:
            await update.message.reply_text("тЭМ Kategoriyalarni ko'rishda xatolik.")

async def show_budget_status(update: Update, user_id: int):
    try:
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT category, amount FROM budgets WHERE user_id = ? AND month = ?", (user_id, current_month))
        budgets = dict(c.fetchall())
        if not budgets:
            if update.message:
                await update.message.reply_text(
                    "ЁЯОп Byudjet belgilanmagan. /setbudget orqali byudjet qo'shing.",
                    reply_markup=UNIVERSAL_MENU
                )
            return
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
        """, (user_id, current_month))
        spending = dict(c.fetchall())
        conn.close()
        text = f"ЁЯОп <b>Byudjet holati ({current_month}):</b>\n\n"
        for category, budget_amount in budgets.items():
            spent = spending.get(category, 0)
            remaining = budget_amount - spent
            percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
            if percentage < 70:
                status = "ЁЯЯв"
            elif percentage < 90:
                status = "ЁЯЯб"
            else:
                status = "ЁЯФ┤"
            text += f"{status} <b>{category}</b>\nByudjet: {format_currency(budget_amount)}\nSarflangan: {format_currency(spent)} ({percentage:.1f}%)\nQolgan: {format_currency(remaining)}\n\n"
        if update.message:
            await update.message.reply_text(text, reply_markup=UNIVERSAL_MENU, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Budget error: {e}")
        if update.message:
            await update.message.reply_text("тЭМ Byudjetni ko'rishda xatolik.", reply_markup=UNIVERSAL_MENU)

async def export_data(update: Update, user_id: int):
    try:
        # settings = get_user_settings(user_id) # Removed as per edit hint
        # currency = settings['currency'] # Removed as per edit hint
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT type, amount, note, category, date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 50
        """, (user_id,))
        transactions = c.fetchall()
        conn.close()
        
        if not transactions:
            if update.message:
                await update.message.reply_text(
                    "ЁЯУд EXPORT\n\n"
                    "Export qilish uchun ma'lumot yo'q."
                )
            return
        
        export_text = "ЁЯУд EXPORT MA'LUMOTLARI (Oxirgi 50 ta):\n\n"
        export_text += "Sana | Tur | Miqdor | Kategoriya | Izoh\n"
        export_text += "=" * 60 + "\n"
        
        for t in transactions:
            t_type = "ЁЯТ░ Kirim" if t[0] == "income" else "ЁЯТ╕ Chiqim"
            date_str = datetime.fromisoformat(t[4].replace('Z', '+00:00')).strftime("%d.%m.%Y")
            export_text += f"{date_str} | {t_type} | {format_currency(t[1])} | {t[3]} | {t[2]}\n"
        
        if update.message:
            await update.message.reply_text(export_text)
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        if update.message:
            await update.message.reply_text("тЭМ Export qilishda xatolik.")

async def show_records(update: Update, user_id: int):
    try:
        # settings = get_user_settings(user_id) # Removed as per edit hint
        # currency = settings['currency'] # Removed as per edit hint
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Biggest income and expense
        c.execute("SELECT MAX(amount), note FROM transactions WHERE user_id = ? AND type = 'income'", (user_id,))
        max_income = c.fetchone()
        
        c.execute("SELECT MAX(amount), note FROM transactions WHERE user_id = ? AND type = 'expense'", (user_id,))
        max_expense = c.fetchone()
        
        # Most active day
        c.execute("""
            SELECT DATE(date), COUNT(*) 
            FROM transactions 
            WHERE user_id = ? 
            GROUP BY DATE(date) 
            ORDER BY COUNT(*) DESC 
            LIMIT 1
        """, (user_id,))
        active_day = c.fetchone()
        
        # Total transactions
        c.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
        total_transactions = c.fetchone()[0]
        
        # Monthly average
        c.execute("""
            SELECT AVG(monthly_total) FROM (
                SELECT strftime('%Y-%m', date) as month, SUM(amount) as monthly_total
                FROM transactions 
                WHERE user_id = ? AND type = 'expense'
                GROUP BY strftime('%Y-%m', date)
            )
        """, (user_id,))
        avg_monthly = c.fetchone()[0] or 0
        
        conn.close()
        
        text = "ЁЯПЖ REKORDLARINGIZ:\n\n"
        
        if max_income and max_income[0]:
            text += f"ЁЯТ░ Eng katta kirim: {format_currency(max_income[0])}\n"
            text += f"   ЁЯУЭ {max_income[1]}\n\n"
        
        if max_expense and max_expense[0]:
            text += f"ЁЯТ╕ Eng katta chiqim: {format_currency(max_expense[0])}\n"
            text += f"   ЁЯУЭ {max_expense[1]}\n\n"
        
        if active_day and active_day[1]:
            date_str = datetime.fromisoformat(active_day[0]).strftime("%d.%m.%Y")
            text += f"ЁЯУЕ Eng faol kun: {date_str} ({active_day[1]} ta tranzaksiya)\n\n"
        
        text += f"ЁЯУК Jami tranzaksiyalar: {total_transactions} ta\n"
        text += f"ЁЯУИ O'rtacha oylik xarajat: {format_currency(int(avg_monthly))}"
        
        if update.message:
            await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Records error: {e}")
        if update.message:
            await update.message.reply_text("тЭМ Rekordlarni ko'rishda xatolik.")

async def show_ai_analysis(update: Update, user_id: int):
    """Show AI-powered spending analysis with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text("ЁЯза AI moliyaviy tahlil qilmoqdaтАж")
        await asyncio.sleep(5)
        # AI tahlil natijasi (demo)
        ai_analysis = (
            "Tayyor! Sizning xarajatlaringizga qarab 3 tahlil:\n\n"
            "ЁЯНФ Oziq-ovqatga oyda 32% ketmoqda, imkon bo'lsa 25% ga tushiring.\n"
            "ЁЯЪЧ Transport xarajatlari o'tgan oyga nisbatan 10% oshgan.\n"
            "ЁЯТ╕ Bu oy kirimdan 10% tejab qo'yayotganingiz ajoyib, davom eting!"
        )
        if loading_msg:
            await loading_msg.edit_text(f"ЁЯУК <b>AI tahlil natijasi:</b>\n\n{ai_analysis}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        if loading_msg:
            await loading_msg.edit_text("AI tahlil xatosi yoki ma'lumot yetarli emas.")

async def show_ai_advice(update: Update, user_id: int):
    """Show AI financial advice with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text("ЁЯза AI moliyaviy maslahatchi hisob-kitob qilmoqdaтАж")
        await asyncio.sleep(5)
        # AI javobini olish (real API chaqiruvi bo'lsa, shu yerda await)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        total_data = c.fetchone()
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 3
        """, (user_id,))
        categories = [cat[0] for cat in c.fetchall()]
        conn.close()
        # Demo natija (real AI javobi o'rniga)
        ai_advice = (
            "Tayyor! Sizning xarajatlaringizga qarab 3 maslahat:\n\n"
            "ЁЯНФ Oziq-ovqatga oyda 32% ketmoqda, imkon bo'lsa 25% ga tushiring.\n"
            "тШХя╕П Kofega 150,000 so'm ketgan, haftada 2 marta uyda tayyorlab tejang.\n"
            "ЁЯТ╕ Bu oy kirimdan 10% tejab qo'yayotganingiz ajoyib, davom eting!"
        )
        if loading_msg:
            await loading_msg.edit_text(f"ЁЯдЦ <b>AI maslahat:</b>\n\n{ai_advice}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"AI advice error: {e}")
        if loading_msg:
            await loading_msg.edit_text("AI maslahat xatosi yoki ma'lumot yetarli emas.")

async def show_motivation(update: Update):
    """Show motivational messages"""
    motivations = [
        "ЁЯТк Motivatsiya:\n\n"
        "Har kuni kichik tejash ham katta natijaga olib keladi! "
        "Bugun 1000 so'm tejang, ertaga 1 million bo'ladi!",
        
        "ЁЯОп Motivatsiya:\n\n"
        "Maqsadingizga qadam-baqadam yuring! "
        "Har bir so'm sizning kelajagingiz uchun investitsiya!",
        
        "ЁЯТ░ Motivatsiya:\n\n"
        "Bugungi tejashingiz - ertangi erkinligingiz! "
        "Moliyaviy erkinlik sizning qo'lingizda!",
        
        "ЁЯУИ Motivatsiya:\n\n"
        "Har bir so'm muhim, nazorat qiling! "
        "Kichik o'zgarishlar katta natijalar keltiradi!",
        
        "ЁЯМЯ Motivatsiya:\n\n"
        "Moliyaviy erkinlik sizning qo'lingizda! "
        "Bugun boshlang, ertaga natijasini ko'rasiz!"
    ]
    
    motivation = random.choice(motivations)
    if update.message:
        await update.message.reply_text(motivation)

# Robust fallback for settings
async def show_settings(update: Update, user_id: int):
    """Show user settings with full menu and handle navigation"""
    # settings = get_user_settings(user_id) # Removed as per edit hint
    # lang = settings.get('language', 'uz') # Removed as per edit hint
    # currency = settings.get('currency', "so'm") # Removed as per edit hint
    reply_markup = ReplyKeyboardMarkup(
        MAIN_MODULES_KEYBOARD, resize_keyboard=True, one_time_keyboard=True
    )
    if update.message:
        await update.message.reply_text(
            "тЪЩя╕П Sozlamalar\n\n"
            "Valyuta: {currency}\n\n"
            "Quyidagilardan birini tanlang:".format(currency="so'm"), # Placeholder for currency
            reply_markup=reply_markup
        )
    return 5

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    # lang = get_user_settings(user_id)['language'] # Removed as per edit hint
    if text.lower() in ["/start", "/cancel", "ЁЯПа Bosh menyu", "ЁЯПа Bosh menyu"]: # Changed to "uz" for consistency
        return await start(update, context)
    elif text in ["ЁЯТ░ Valyutani o'zgartirish", "ЁЯТ░ ╨Ш╨╖╨╝╨╡╨╜╨╕╤В╤М ╨▓╨░╨╗╤О╤В╤Г", "ЁЯТ░ Change currency"]: # Changed to "uz" for consistency
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in MESSAGES["uz"]["currencies"]] + [[MESSAGES["uz"]["main_menu"]]], # Changed to "uz" for consistency
            resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(MESSAGES["uz"]["choose_currency"], reply_markup=reply_markup) # Changed to "uz" for consistency
        return 9
    else:
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"]) # Changed to "uz" for consistency
        return 5

async def currency_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    # lang = get_user_settings(user_id)['language'] # Removed as per edit hint
    currency_map = {
        "\U0001F1FA\U0001F1FF So'm": "so'm",
        "\U0001F4B5 Dollar": "USD",
        "\U0001F4B6 Euro": "EUR",
        "\U0001F4B7 Rubl": "RUB",
        "\U0001F1FA\U0001F1FF ╨б╤Г╨╝": "so'm",
        "\U0001F4B5 ╨Ф╨╛╨╗╨╗╨░╤А": "USD",
        "\U0001F4B6 ╨Х╨▓╤А╨╛": "EUR",
        "\U0001F4B7 ╨а╤Г╨▒╨╗╤М": "RUB",
        "\U0001F1FA\U0001F1FF So'm": "so'm",
        "\U0001F4B5 Dollar": "USD",
        "\U0001F4B6 Euro": "EUR",
        "\U0001F4B7 Ruble": "RUB"
    }
    if text.lower() in ["/start", "/cancel", "ЁЯПа Bosh menyu", "ЁЯПа Bosh menyu"]: # Changed to "uz" for consistency
        return await start(update, context)
    elif text in currency_map:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE user_settings SET currency = ? WHERE user_id = ?", (currency_map[text], user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(MESSAGES["uz"]["currency_changed"].format(currency=text)) # Changed to "uz" for consistency
        return await show_settings(update, user_id)
    else:
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in MESSAGES["uz"]["currencies"]] + [[MESSAGES["uz"]["main_menu"]]], # Changed to "uz" for consistency
            resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"], reply_markup=reply_markup) # Changed to "uz" for consistency
        return 9

async def delete_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data deletion confirmation. Universal /start, /cancel, bosh menyu."""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    if not update.message or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    if text.lower() in ["/start", "/cancel", "ЁЯПа Bosh menyu"]:
        return await start(update, context)
    elif text == "тЬЕ Ha, o'chirish":
        # Delete all user data
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        # Clear session/context
        if hasattr(context, 'user_data') and context.user_data is not None:
            context.user_data.clear()
        await update.message.reply_text("ЁЯЧСя╕П Barcha ma'lumotlar muvaffaqiyatli o'chirildi!")
        # Show main menu
        return await start(update, context)
    
    elif text == "тЭМ Yo'q, bekor qilish":
        return await show_settings(update, user_id)
    
    else:
        await update.message.reply_text("тЭМ Noto'g'ri tanlov. Qaytadan tanlang.")
        return 7

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.from_user:
        return
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Sizda ruxsat yo'q.", reply_markup=UNIVERSAL_MENU)
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Total users
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    # Total transactions
    c.execute("SELECT COUNT(*) FROM transactions")
    transaction_count = c.fetchone()[0]
    # Most active user
    c.execute("""
        SELECT u.first_name, u.username, COUNT(t.user_id) as cnt
        FROM users u LEFT JOIN transactions t ON u.user_id = t.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        LIMIT 1
    """)
    row = c.fetchone()
    if row:
        most_active = f"{row[0] or ''} (@{row[1] or ''}) - {row[2]} ta tranzaksiya"
    else:
        most_active = "Yo'q"
    # Most recent user
    c.execute("SELECT first_name, username, joined_at FROM users ORDER BY joined_at DESC LIMIT 1")
    row = c.fetchone()
    if row:
        most_recent = f"{row[0] or ''} (@{row[1] or ''}) - {row[2]}"
    else:
        most_recent = "Yo'q"
    # Most active day
    c.execute("""
        SELECT DATE(date), COUNT(*) as cnt
        FROM transactions
        GROUP BY DATE(date)
        ORDER BY cnt DESC
        LIMIT 1
    """)
    row = c.fetchone()
    if row:
        most_active_day = f"{row[0]} - {row[1]} ta tranzaksiya"
    else:
        most_active_day = "Yo'q"
    conn.close()
    await update.message.reply_text(
        f"ЁЯСе Foydalanuvchilar soni: {user_count}\n"
        f"ЁЯТ╕ Umumiy tranzaksiyalar: {transaction_count}\n"
        f"ЁЯПЖ Eng faol foydalanuvchi: {most_active}\n"
        f"ЁЯЖХ Eng so'nggi foydalanuvchi: {most_recent}\n"
        f"ЁЯУЕ Eng faol kun: {most_active_day}"
    )

# ==== PUSH NOTIFICATION (ADMIN) ====
PUSH_TOPIC, PUSH_CONFIRM = range(200, 202)

async def push_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.from_user:
        return ConversationHandler.END
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Sizda ruxsat yo'q.", reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END
    await update.message.reply_text(
        "ЁЯУЭ Push xabar mavzusini yoki qisqacha mazmunini kiriting:\n\nBekor qilish uchun /cancel yozing."
    )
    return PUSH_TOPIC

async def push_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    topic = update.message.text.strip()
    if topic.lower() in ["/cancel", "bekor", "cancel"]:
        await update.message.reply_text("тЭМ Bekor qilindi.")
        return ConversationHandler.END
    await update.message.reply_text("тП│ AI push xabar matnini tayyorlamoqda...")
    # AI orqali push matnini generatsiya qilish
    prompt = f"Foydalanuvchilarga motivatsion va foydali push xabar yozing. Mavzu yoki qisqacha mazmun: {topic}. Xabar qisqa, aniq va ijobiy bo'lsin. Til: o'zbek."
    ai_text = await ai_service.get_financial_advice({'topic': topic, 'mode': 'push'})
    ai_text = ai_text.replace('**', '') if ai_text else ai_text
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['push_text'] = ai_text
    await update.message.reply_text(
        f"AI tomonidan tayyorlangan push xabar:\n\n{ai_text}\n\nYuborishni tasdiqlaysizmi? (Ha/Yo'q)",
        parse_mode=ParseMode.HTML
    )
    return PUSH_CONFIRM

async def push_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip().lower()
    if text in ["yo'q", "yoq", "bekor", "/cancel", "cancel"]:
        await update.message.reply_text("тЭМ Bekor qilindi.")
        return ConversationHandler.END
    if text in ["ha", "yes", "ok", "yubor", "tasdiqla"]:
        push_text = None
        if hasattr(context, 'user_data') and context.user_data is not None:
            push_text = context.user_data.get('push_text', None)
        if not push_text:
            await update.message.reply_text("Xabar topilmadi.")
            return ConversationHandler.END
        # Barcha user_id larni olish va xabar yuborish
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in c.fetchall()]
        conn.close()
        count = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=push_text)
                count += 1
            except Exception as e:
                continue
        await update.message.reply_text(f"тЬЕ Push xabar {count} foydalanuvchiga yuborildi!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Iltimos, 'Ha' yoki 'Yo'q' deb javob bering.")
        return PUSH_CONFIRM

# ==== ConversationHandler for PUSH ====
push_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("push", push_command)],
    states={
        PUSH_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_topic_handler)],
        PUSH_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_confirm_handler)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# ==== AI-BASED BUDGET PLANNING ====
AI_BUDGET_START, AI_BUDGET_INCOME, AI_BUDGET_CONFIRM = range(300, 303)

async def ai_budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    await update.message.reply_text(
        "AI asosida byudjet tuzish uchun oylik daromadingizni kiriting (so'mda):\n\nBekor qilish uchun /cancel yozing."
    )
    return AI_BUDGET_INCOME

async def ai_budget_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text.lower() in ["/cancel", "bekor", "cancel"]:
        await update.message.reply_text("тЭМ Bekor qilindi.")
        return ConversationHandler.END
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"тЭМ {error}\n\nQaytadan kiriting yoki /cancel yozing")
        return AI_BUDGET_INCOME
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['ai_budget_income'] = amount
    await update.message.reply_text("AI byudjet tuzmoqda, iltimos kuting...")
    # Get user_id and transactions
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT type, amount, category, note, date FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 50", (user_id,))
    transactions = c.fetchall()
    conn.close()
    transactions_list = [
        {'type': t[0], 'amount': t[1], 'category': t[2], 'note': t[3], 'date': t[4]} for t in transactions
    ]
    user_data = {'income': amount}
    ai_text = await ai_service.generate_budget_plan(user_data, transactions_list)
    ai_text = ai_text.replace('**', '') if ai_text else ai_text
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['ai_budget_result'] = ai_text
    reply_markup = ReplyKeyboardMarkup([["Ha"], ["Yo'q"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"AI byudjet reja:\n\n{ai_text}\n\nYana bir bor ko'rib chiqilsinmi? (Ha/Yo'q)", reply_markup=reply_markup)
    return AI_BUDGET_CONFIRM

async def ai_budget_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip().lower()
    if text in ["yo'q", "yoq", "bekor", "/cancel", "cancel"]:
        await update.message.reply_text("тЭМ Bekor qilindi.")
        return ConversationHandler.END
    if text in ["ha", "yes", "ok", "tasdiqla"]:
        ai_text = None
        if hasattr(context, 'user_data') and context.user_data is not None:
            ai_text = context.user_data.get('ai_budget_result', None)
        if ai_text:
            reply_markup = ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True)
            await update.message.reply_text(f"тЬЕ AI byudjet reja saqlandi (yoki qayta ko'rib chiqildi):\n\n{ai_text}", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Iltimos, 'Ha' yoki 'Yo'q' deb javob bering.")
        return AI_BUDGET_CONFIRM

ai_budget_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("ai_byudjet", ai_budget_start)],
    states={
        AI_BUDGET_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_budget_income)],
        AI_BUDGET_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_budget_confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# ==== AI-BASED GOAL SETTING & MONITORING ====
AI_GOAL_NAME, AI_GOAL_AMOUNT, AI_GOAL_DEADLINE, AI_GOAL_MONITOR = range(310, 314)

async def ai_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    await update.message.reply_text(
        "Moliyaviy maqsad qo'yish uchun maqsad nomini kiriting (masalan: '3 oyda 1 mln so'm tejash').\n\nBekor qilish uchun /cancel yozing."
    )
    return AI_GOAL_NAME

async def ai_goal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text.lower() in ["/cancel", "bekor", "cancel"]:
        await update.message.reply_text("тЭМ Bekor qilindi.")
        return ConversationHandler.END
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['goal_name'] = text
    await update.message.reply_text("Maqsad uchun umumiy miqdorni kiriting (so'mda):")
    return AI_GOAL_AMOUNT

async def ai_goal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"тЭМ {error}\n\nQaytadan kiriting yoki /cancel yozing")
        return AI_GOAL_AMOUNT
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['goal_amount'] = amount
    await update.message.reply_text("Maqsad uchun oxirgi muddatni kiriting (masalan: 2024-12-31):")
    return AI_GOAL_DEADLINE

async def ai_goal_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['goal_deadline'] = text
    # Save to DB
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    goal_name = None
    goal_amount = None
    goal_deadline = None
    if hasattr(context, 'user_data') and context.user_data is not None:
        goal_name = context.user_data.get('goal_name', None)
        goal_amount = context.user_data.get('goal_amount', None)
        goal_deadline = context.user_data.get('goal_deadline', None)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)",
              (user_id, goal_name, goal_amount, goal_deadline))
    conn.commit()
    conn.close()
    reply_markup = ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("Maqsad saqlandi! Progress monitoring uchun 'Ha' deb yozing yoki bekor qilish uchun 'Yo'q'.", reply_markup=reply_markup)
    return AI_GOAL_MONITOR

async def ai_goal_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip().lower()
    if text in ["yo'q", "yoq", "bekor", "/cancel", "cancel", "тЭМ bekor qilish", "ЁЯПа bosh menyu"]:
        await update.message.reply_text("тЭМ Amal bekor qilindi.", reply_markup=UNIVERSAL_MENU)
        return ConversationHandler.END
    if text in ["ha", "yes", "ok", "tasdiqla"]:
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT goal_name, target_amount, deadline FROM goals WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        goal_row = c.fetchone()
        c.execute("SELECT type, amount, category, note, date FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 50", (user_id,))
        transactions = c.fetchall()
        conn.close()
        if not goal_row:
            await update.message.reply_text("Maqsad topilmadi.", reply_markup=UNIVERSAL_MENU)
            return ConversationHandler.END
        goal_data = {'goal_name': goal_row[0], 'target_amount': goal_row[1], 'deadline': goal_row[2]}
        transactions_list = [
            {'type': t[0], 'amount': t[1], 'category': t[2], 'note': t[3], 'date': t[4]} for t in transactions
        ]
        ai_text = await ai_service.monitor_goal_progress(goal_data, transactions_list)
        ai_text = ai_text.replace('**', '') if ai_text else ai_text
        await update.message.reply_text(f"ЁЯОп <b>Maqsad monitoringi:</b>\n\n{ai_text}", reply_markup=UNIVERSAL_MENU, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Iltimos, 'Ha' yoki 'Yo'q' deb javob bering.", reply_markup=ReplyKeyboardMarkup([["Ha"], ["Yo'q"]], resize_keyboard=True, one_time_keyboard=True))
        return AI_GOAL_MONITOR

ai_goal_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("ai_maqsad", ai_goal_start)],
    states={
        AI_GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_name)],
        AI_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_amount)],
        AI_GOAL_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_deadline)],
        AI_GOAL_MONITOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_monitor)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# ==== ONBOARDING HANDLERS ====
def get_currency_code(text):
    if "so'm" in text.lower() or "uz" in text.lower():
        return "so'm"
    elif "dollar" in text.lower() or "$" in text or "usd" in text.lower():
        return "USD"
    elif "euro" in text.lower() or "eur" in text.lower():
        return "EUR"
    return "so'm"

async def onboarding_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    currency = get_currency_code(text)
    # Save currency to DB, but preserve other columns (like onboarding_done)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_settings (user_id, currency)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET currency = excluded.currency
    """, (user_id, currency))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        "2я╕ПтГг Oylik taxminiy kirimingizni kiriting (masalan: 3 000 000):",
        reply_markup=ReplyKeyboardMarkup([["Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ONBOARDING_INCOME

async def onboarding_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.replace(' ', '')
    try:
        income = int(text)
        if income <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("тЭМ Noto'g'ri format! Masalan: 3 000 000 yoki 5000000.")
        return ONBOARDING_INCOME
    context.user_data['onboarding_income'] = income
    await update.message.reply_text(
        "3я╕ПтГг Maqsad qo'yish: Nimani tejamoqchisiz? (masalan: telefon, o'qish, safar)",
        reply_markup=ReplyKeyboardMarkup([["Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ONBOARDING_GOAL

async def onboarding_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MESSAGES
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user') or update.message.from_user is None:
        return ConversationHandler.END
    text = update.message.text.strip()
    user_id = getattr(update.message.from_user, 'id', None)
    if user_id is None:
        return ConversationHandler.END
    user_data = getattr(context, 'user_data', {})
    if not isinstance(user_data, dict):
        user_data = {}
    income = user_data.get('onboarding_income', 0)
    # Save goal to DB (goals table) and mark onboarding as done
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)",
              (user_id, text, income, None))
    c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    onboarding_done_msg = None
    try:
        onboarding_done_msg = MESSAGES["uz"]["onboarding_done"]
    except Exception:
        onboarding_done_msg = "ЁЯОп Onboarding yakunlandi! Endi asosiy menyudan foydalanishingiz mumkin."
    await update.message.reply_text(onboarding_done_msg, reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update)

# ONBOARDING CONV HANDLER
onboarding_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ONBOARDING_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_currency)],
        ONBOARDING_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_income)],
        ONBOARDING_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_goal)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# ==== MAIN ====
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! Iltimos, environment o'zgaruvchisini sozlang.")
        return
    
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(global_error_handler)

    yangi_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("тЭУ Yordam"), help_command),
            CommandHandler("help", help_command)
        ],
        states={
            ASK_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(
            filters.Regex(r"^(ЁЯУе Kirim/Chiqim|ЁЯУК Balans/Tahlil|ЁЯдЦ AI vositalar|тЪЩя╕П Sozlamalar/Yordam)$"),
            message_handler
        )],
        states={
            INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_amount)],
            INCOME_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_note)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
            EXPENSE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_note)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_category_selected)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_category_selected)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_data_handler)],
            9: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
        },
        fallbacks=[CommandHandler("start", start), CommandHandler("cancel", cancel)]
    )

    app.add_handler(yangi_conv_handler)  # Yordam handleri birinchi
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.Regex("^/reply_"), admin_reply))
    app.add_handler(CommandHandler("stat", show_stats))
    app.add_handler(push_conv_handler)
    app.add_handler(ai_budget_conv_handler)
    app.add_handler(ai_goal_conv_handler)
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(onboarding_conv_handler)
    app.add_handler(CommandHandler("history", show_history))
    app.add_handler(CommandHandler("admin_panel", admin_panel))

    logger.info("FinBot AI ishga tushmoqda...")
    app.run_polling()

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, 'callback_query', None)
    if not query or not hasattr(query, 'from_user'):
        return ConversationHandler.END
    user_id = getattr(query.from_user, 'id', None)
    if user_id is None:
        return ConversationHandler.END
    await query.answer()
    if query.data == "show_balance":
        await show_balance(update, int(user_id))
    elif query.data == "show_analysis":
        await show_analysis(update, int(user_id))
    elif query.data == "show_ai_advice":
        await show_ai_advice(update, int(user_id))

def get_all_user_ids():
    conn = sqlite3.connect(DB_PATH)
    if conn is None:
        return []
    c = conn.cursor() if conn else None
    if c is None:
        conn.close()
        return []
    c.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return user_ids

def get_weekly_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    if conn is None:
        return 0, 0
    c = conn.cursor() if conn else None
    if c is None:
        conn.close()
        return 0, 0
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income' AND date >= ?", (user_id, week_ago))
    kirim = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense' AND date >= ?", (user_id, week_ago))
    chiqim = c.fetchone()[0] or 0
    conn.close()
    return kirim, chiqim

def is_onboarded(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT onboarding_done FROM user_settings WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None or not isinstance(row, (list, tuple)):
        return False
    return bool(row[0])

def set_onboarded(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# InlineKeyboard navigatsiya uchun universal funksiya
async def show_main_menu(update):
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Balansni ko'rish ЁЯУК", callback_data="show_balance")],
        [InlineKeyboardButton("Tahlil qilish ЁЯУИ", callback_data="show_analysis")],
        [InlineKeyboardButton("AI maslahat olish ЁЯдЦ", callback_data="show_ai_advice")]
    ])
    await update.message.reply_text("Quyidagi amallardan birini tanlang:", reply_markup=inline_kb)
    return ConversationHandler.END

async def send_daily_push(context):
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=MESSAGES["uz"]["push_daily"]
            )
        except Exception as e:
            logger.error(f"Daily push error for user {user_id}: {e}")

async def send_weekly_push(context):
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            kirim, chiqim = get_weekly_stats(user_id)
            tejagan = kirim - chiqim
            await context.bot.send_message(
                chat_id=user_id,
                text=MESSAGES["uz"]["push_weekly"].format(income=f"{kirim:,}", expense=f"{chiqim:,}", saved=f"{tejagan:,}") ,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Weekly push error for user {user_id}: {e}")

async def send_monthly_goal_push(context):
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="ЁЯОп Yangi oy keldi! Shu oy uchun yangi moliyaviy maqsad qo'yishga tayyormisiz?"
            )
        except Exception as e:
            logger.error(f"Monthly goal push error for user {user_id}: {e}")

async def send_monthly_feedback_push(context):
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=MESSAGES["uz"]["feedback_push"]
            )
        except Exception as e:
            logger.error(f"Monthly feedback push error for user {user_id}: {e}")

def setup_schedulers(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: send_daily_push(app), 'cron', hour=8, minute=0)
    scheduler.add_job(lambda: send_weekly_push(app), 'cron', day_of_week='sun', hour=8, minute=0)
    scheduler.add_job(lambda: send_monthly_goal_push(app), 'cron', day=1, hour=8, minute=0)
    scheduler.add_job(lambda: send_monthly_feedback_push(app), 'cron', day=1, hour=12, minute=0)
    scheduler.start()

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None or not update.message:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Kirgan sanasi
    c.execute("SELECT joined_at FROM users WHERE user_id = ?", (user_id,))
    joined_at = c.fetchone()
    joined_at_str = joined_at[0][:10] if joined_at and joined_at[0] else "-"
    # Kirim/chiqimlar soni
    c.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
    total_ops = c.fetchone()[0] or 0
    # Tejalgan umumiy miqdor
    c.execute("SELECT SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) FROM transactions WHERE user_id = ?", (user_id,))
    sums = c.fetchone()
    total_income = sums[0] or 0
    total_expense = sums[1] or 0
    saved = total_income - total_expense
    conn.close()
    text = (
        "ЁЯХУ <b>Harakatlar tarixi</b>\n\n"
        f"ЁЯСд <b>Botga kirgan sana:</b> {joined_at_str}\n"
        f"ЁЯУЛ <b>Qo'shgan kirim/chiqimlar soni:</b> {total_ops} ta\n"
        f"ЁЯТ░ <b>Tejalgan umumiy miqdor:</b> {format_currency(saved)}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def global_error_handler(update, context):
    try:
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text(MESSAGES["uz"]["error_soft"])
        # Adminga xatolik tafsiloti
        error_text = f"[Xatolik]\nUser: {getattr(getattr(update, 'message', None), 'from_user', None)}\nError: {context.error}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except Exception:
        pass

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID or not update.message:
        if update.message:
            await update.message.reply_text("тЫФя╕П Sizda ruxsat yo'q.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Kunlik faol foydalanuvchilar soni
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(DISTINCT user_id) FROM transactions WHERE date(date) = ?", (today,))
    active_users = c.fetchone()[0] or 0
    # Bugun qo'shilgan kirim/chiqimlar soni
    c.execute("SELECT COUNT(*) FROM transactions WHERE date(date) = ?", (today,))
    ops_today = c.fetchone()[0] or 0
    # Eng faol foydalanuvchi (bugun)
    c.execute("""
        SELECT u.first_name, u.username, COUNT(t.user_id) as cnt
        FROM users u JOIN transactions t ON u.user_id = t.user_id
        WHERE date(t.date) = ?
        GROUP BY u.user_id
        ORDER BY cnt DESC
        LIMIT 1
    """, (today,))
    row = c.fetchone()
    if row:
        most_active = f"{row[0] or ''} (@{row[1] or ''}) - {row[2]} ta"
    else:
        most_active = "Yo'q"
    conn.close()
    # Server log (oxirgi 10 qator)
    log_tail = ""
    try:
        with open("errorlog.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            log_tail = ''.join(lines[-10:]) if lines else "Loglar yo'q."
    except Exception:
        log_tail = "Loglar yo'q."
    text = (
        "<b>ЁЯЫая╕П Admin Panel</b>\n\n"
        f"ЁЯСе <b>Kunlik faol foydalanuvchilar:</b> {active_users}\n"
        f"ЁЯУЭ <b>Bugun qo'shilgan kirim/chiqimlar:</b> {ops_today} ta\n"
        f"ЁЯПЖ <b>Eng faol foydalanuvchi:</b> {most_active}\n\n"
        f"<b>ЁЯЦея╕П Server loglari (oxirgi 10 qator):</b>\n<pre>{log_tail}</pre>"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

if __name__ == "__main__":
    main() 
