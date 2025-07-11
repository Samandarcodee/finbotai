import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os
from datetime import datetime, timedelta
import random
from ai_service import ai_service

# ==== CONFIG ====
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "finbot.db"

# ==== CONSTANTS ====
ADMIN_ID = 786171158  # Sizning Telegram ID'ingiz
ASK_SUPPORT = 100  # yangi state

# ==== MESSAGES (to'liq sozlamalarsiz) ====
MESSAGES = {
    "uz": {
        "main_menu": "\U0001F3E0 Bosh menyu",
        "invalid_choice": "\u274c Noto'g'ri tanlov. Qaytadan tanlang."
    },
    "ru": {
        "main_menu": "\U0001F3E0 \u0413\u043B\u0430\u0432\u043D\u043E\u0435 \u043C\u0435\u043D\u044E",
        "invalid_choice": "\u274c \u041D\u0435\u0432\u0435\u0440\u043D\u044B\u0439 \u0432\u044B\u0431\u043E\u0440. \u041F\u043E\u0436\u0430\u043B\u0443\u0439\u0441\u0442\u0430, \u0432\u044B\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u043D\u043E\u0432\u0430."
    },
    "en": {
        "main_menu": "\U0001F3E0 Main menu",
        "invalid_choice": "\u274c Invalid choice. Please try again."
    }
}

# ==== MAIN MENU KEYBOARD (Sozlamalarsiz) ====
MAIN_MENU_KEYBOARD = [
    ["\U0001F4B0 Kirim qo'shish", "\U0001F4B8 Chiqim qo'shish"],
    ["\U0001F4CA Balans", "\U0001F4C8 Tahlil"],
    ["\U0001F4CB Kategoriyalar", "\U0001F3AF Byudjet"],
    ["\U0001F4E4 Export", "\U0001F3C6 Rekorlar"],
    ["\U0001F916 AI maslahat", "\U0001F4CA AI Tahlil"],
    ["\u2753 Yordam"]
]

# ==== LOGGING ====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==== DATABASE INITIALIZATION ====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    user_id INTEGER,
                    type TEXT,
                    amount INTEGER,
                    note TEXT,
                    category TEXT DEFAULT 'Boshqa',
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                    user_id INTEGER,
                    category TEXT,
                    amount INTEGER,
                    month TEXT,
                    PRIMARY KEY (user_id, category, month)
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
            return None, "Miqdor 0 dan katta bo'lishi kerak!"
        if amount > 999999999:
            return None, "Miqdor juda katta! Iltimos, kichikroq miqdorni kiriting."
        return amount, None
    except ValueError:
        return None, "Noto'g'ri format! Faqat raqam kiriting."

# ==== COMMANDS ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    from_user = getattr(update.message, 'from_user', None)
    if not from_user or not hasattr(from_user, 'id'):
        return
    user_id = getattr(from_user, 'id', None)
    user_name = getattr(from_user, 'first_name', 'Foydalanuvchi')
    if user_id is None:
        return
    # Initialize user settings
    # get_user_settings(user_id) # Removed as per edit hint
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
    welcome_text = f"""👋 Assalomu alaykum, {user_name}!

    Men FinBot AI - sizning aqlli moliyaviy yordamchingiz! 💰

    🎯 Asosiy funksiyalar:
    • 💰 Kirim va chiqimlarni qo'shish
    • 📊 Balans va tahlil ko'rish  
    • 📋 Kategoriyalar bo'yicha hisobot
    • 🎯 Byudjet nazorati
    • 📈 Moliyaviy maslahatlar

    Quyidagi tugmalardan foydalaning:"""
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    await update.message.reply_text(
        "Yordam uchun savolingizni yozing. Admin sizga javob beradi.\n\nBekor qilish uchun /cancel yozing."
    )
    return ASK_SUPPORT

async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    user = update.message.from_user
    user_message = update.message.text
    admin_text = (
        f"🆘 Yangi yordam so'rovi!\n"
        f"👤 Foydalanuvchi: {getattr(user, 'first_name', 'Foydalanuvchi')} ({getattr(user, 'id', 'Noma' + 'lum')})\n"
        f"✉️ Xabar: {user_message}\n\n"
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
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("❌ Amal bekor qilindi. Boshqa funksiyani tanlang:", reply_markup=reply_markup)
    return ConversationHandler.END

# ==== HANDLERS ====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if text.lower() in ["/start", "/cancel", "\U0001F3E0 Bosh menyu", "\U0001F3E0 \u0413\u043B\u0430\u0432\u043D\u043E\u0435 \u043C\u0435\u043D\u044E", "\U0001F3E0 Main menu"]:
        return await start(update, context)
    if user_id is None:
        return ConversationHandler.END

    if text == "\U0001F4B0 Kirim qo'shish":
        categories_keyboard = [
            ["\U0001F354 Oziq-ovqat", "\U0001F697 Transport"],
            ["\U0001F48A Sog'liq", "\U0001F4DA Ta'lim"],
            ["\U0001F3AE O'yin-kulgi", "\U0001F455 Kiyim"],
            ["\U0001F3E0 Uy", "\U0001F4F1 Aloqa"],
            ["\U0001F4B3 Boshqa", "\U0001F519 Orqaga"]
        ]
        category_markup = ReplyKeyboardMarkup(categories_keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "\U0001F4B0 KIRIM QO'SHISH\n\n"
            "Kategoriyani tanlang:",
            reply_markup=category_markup
        )
        return 4
    elif text == "\U0001F4B8 Chiqim qo'shish":
        categories_keyboard = [
            ["\U0001F354 Oziq-ovqat", "\U0001F697 Transport"],
            ["\U0001F48A Sog'liq", "\U0001F4DA Ta'lim"],
            ["\U0001F3AE O'yin-kulgi", "\U0001F455 Kiyim"],
            ["\U0001F3E0 Uy", "\U0001F4F1 Aloqa"],
            ["\U0001F4B3 Boshqa", "\U0001F519 Orqaga"]
        ]
        category_markup = ReplyKeyboardMarkup(categories_keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "\U0001F4B8 CHIQIM QO'SHISH\n\n"
            "Kategoriyani tanlang:",
            reply_markup=category_markup
        )
        return 3
    elif text == "\U0001F4CA Balans":
        return await show_balance(update, user_id)
    elif text == "\U0001F4C8 Tahlil":
        return await show_analysis(update, user_id)
    elif text == "\U0001F916 AI maslahat":
        return await show_ai_advice(update, user_id)
    elif text == "\U0001F4CA AI Tahlil":
        return await show_ai_analysis(update, user_id)
    elif text == "\U0001F4CB Kategoriyalar":
        return await show_categories(update, user_id)
    elif text == "\U0001F3AF Byudjet":
        return await show_budget_status(update, user_id)
    elif text == "\U0001F4E4 Export":
        return await export_data(update, user_id)
    elif text == "\U0001F3C6 Rekorlar":
        return await show_records(update, user_id)
    elif text == "\u2753 Yordam":
        return await help_command(update, context)
    else:
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"])
        return ConversationHandler.END

# BALANS
async def show_balance(update: Update, user_id: int):
    """Show user balance with improved formatting"""
    try:
        # settings = get_user_settings(user_id) # Removed as per edit hint
        # currency = settings['currency'] # Removed as per edit hint
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current month data
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        
        # Get total data
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
        
        balance_emoji = "💚" if total_balance >= 0 else "❤️"
        month_emoji = "📈" if month_balance >= 0 else "📉"
        
        balance_text = f"""📊 BALANS HISOBOTI

💰 Bu oy ({datetime.now().strftime('%B %Y')}):
{month_emoji} Kirim: {format_currency(month_income)}
💸 Chiqim: {format_currency(month_expense)}
{balance_emoji} Balans: {format_currency(month_balance)}

📈 Jami (barcha vaqt):
💰 Kirim: {format_currency(total_income)}
💸 Chiqim: {format_currency(total_expense)}
{balance_emoji} Balans: {format_currency(total_balance)}

💡 Maslahat: {get_balance_advice(total_balance, month_balance)}"""
        
        if update.message:
            await update.message.reply_text(balance_text)
        
    except Exception as e:
        logger.error(f"Balance error: {e}")
        if update.message:
            await update.message.reply_text("❌ Balansni ko'rishda xatolik. Qaytadan urinib ko'ring.")

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
                    "📈 TAHLIL\n\n"
                    "Hali tranzaksiyalar yo'q. Avval kirim yoki chiqim qo'shing!"
                )
            return
        
        analysis_text = "📈 TAHLIL HISOBOTI\n\n"
        
        # Recent transactions
        analysis_text += "🕐 Oxirgi tranzaksiyalar:\n"
        for t in transactions[:5]:
            emoji = "💰" if t[0] == "income" else "💸"
            date_str = datetime.fromisoformat(t[4].replace('Z', '+00:00')).strftime("%d.%m")
            analysis_text += f"{emoji} {date_str} - {format_currency(t[1])} - {t[2]}\n"
        
        # Category analysis
        if categories:
            analysis_text += "\n Eng ko'p xarajat qilgan kategoriyalar:\n"
            for cat, count, total in categories:
                analysis_text += f"🏷️ {cat}: {format_currency(total)} ({count} ta)\n"
        
        if update.message:
            await update.message.reply_text(analysis_text)
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        if update.message:
            await update.message.reply_text("❌ Tahlilni ko'rishda xatolik. Qaytadan urinib ko'ring.")

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
    
    if text.lower() in ['/cancel', 'bekor', 'cancel']:
        return await cancel(update, context)
    
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"❌ {error}\n\nQaytadan kiriting yoki /cancel yozing")
        return 1
    
    # Extract note from text
    parts = text.split(" ", 1)
    note = parts[1] if len(parts) > 1 else "Kirim"
    selected_category = context.user_data['selected_income_category'] if hasattr(context, 'user_data') and isinstance(context.user_data, dict) and 'selected_income_category' in context.user_data else 'Boshqa kirim'
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'income', ?, ?, ?)", 
                (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        
        success_text = f"""✅ KIRIM QO'SHILDI!

💰 Miqdor: {format_currency(amount)}
📂 Kategoriya: {selected_category}
📝 Izoh: {note}
📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 Davom eting - har bir kirim muhim!"""
        
        await update.message.reply_text(success_text)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Income add error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def income_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    if text == "\U0001F519 Orqaga":
        return await cancel(update, context)
    
    income_category_map = {
        "\U0001F354 Oziq-ovqat": "Oziq-ovqat",
        "\U0001F697 Transport": "Transport", 
        "\U0001F48A Sog'liq": "Sog'liq",
        "\U0001F4DA Ta'lim": "Ta'lim",
        "\U0001F3AE O'yin-kulgi": "O'yin-kulgi",
        "\U0001F455 Kiyim": "Kiyim",
        "\U0001F3E0 Uy": "Uy",
        "\U0001F4F1 Aloqa": "Aloqa",
        "\U0001F4B3 Boshqa": "Boshqa"
    }
    
    selected_category = income_category_map[text] if isinstance(income_category_map, dict) and text in income_category_map else "Boshqa kirim"
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['selected_income_category'] = selected_category
    
    keyboard = [
        ["\U0001F4B0 Kirim qo'shish", "\U0001F4B8 Chiqim qo'shish"],
        ["\U0001F4CA Balans", "\U0001F4C8 Tahlil"],
        ["\U0001F4CB Kategoriyalar", "\U0001F3AF Byudjet"],
        ["\U0001F4E4 Export", "\U0001F3C6 Rekorlar"],
        ["\U0001F916 AI maslahat", "\U0001F4CA AI Tahlil"],
        ["\u2753 Yordam"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Kategoriya tanlandi: {selected_category}\n\n"
        f"💰 Endi kirim miqdorini kiriting:\n"
        f"Masalan: 50000 ish haqi\n\n"
        f"Bekor qilish uchun /cancel yozing",
        reply_markup=reply_markup
    )
    return 1

async def expense_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    if text == "\U0001F519 Orqaga":
        return await cancel(update, context)
    
    expense_category_map = {
        "\U0001F354 Oziq-ovqat": "Oziq-ovqat",
        "\U0001F697 Transport": "Transport", 
        "\U0001F48A Sog'liq": "Sog'liq",
        "\U0001F4DA Ta'lim": "Ta'lim",
        "\U0001F3AE O'yin-kulgi": "O'yin-kulgi",
        "\U0001F455 Kiyim": "Kiyim",
        "\U0001F3E0 Uy": "Uy",
        "\U0001F4F1 Aloqa": "Aloqa",
        "\U0001F4B3 Boshqa": "Boshqa"
    }
    
    selected_category = expense_category_map[text] if isinstance(expense_category_map, dict) and text in expense_category_map else "Boshqa"
    if hasattr(context, 'user_data') and context.user_data is not None:
        context.user_data['selected_expense_category'] = selected_category
    
    keyboard = [
        ["\U0001F4B0 Kirim qo'shish", "\U0001F4B8 Chiqim qo'shish"],
        ["\U0001F4CA Balans", "\U0001F4C8 Tahlil"],
        ["\U0001F4CB Kategoriyalar", "\U0001F3AF Byudjet"],
        ["\U0001F4E4 Export", "\U0001F3C6 Rekorlar"],
        ["\U0001F916 AI maslahat", "\U0001F4CA AI Tahlil"],
        ["\u2753 Yordam"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Kategoriya tanlandi: {selected_category}\n\n"
        f"💸 Endi chiqim miqdorini kiriting:\n"
        f"Masalan: 25000 kofe\n\n"
        f"Bekor qilish uchun /cancel yozing",
        reply_markup=reply_markup
    )
    return 2

# CHIQIM QO'SHISH
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END

    # settings = get_user_settings(user_id) # Removed as per edit hint
    # currency = settings['currency'] # Removed as per edit hint
    text = update.message.text.strip()
    selected_category = context.user_data['selected_expense_category'] if hasattr(context, 'user_data') and isinstance(context.user_data, dict) and 'selected_expense_category' in context.user_data else 'Boshqa'
    
    if text.lower() in ['/cancel', 'bekor', 'cancel']:
        return await cancel(update, context)
    
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"❌ {error}\n\nQaytadan kiriting yoki /cancel yozing")
        return 2
    
    # Extract note from text
    parts = text.split(" ", 1)
    note = parts[1] if len(parts) > 1 else "Chiqim"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'expense', ?, ?, ?)", 
                (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        
        success_text = f"""✅ CHIQIM QO'SHILDI!

💸 Miqdor: {format_currency(amount)}
📂 Kategoriya: {selected_category}
📝 Izoh: {note}
📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 Xarajatlaringizni nazorat qiling!"""
        
        await update.message.reply_text(success_text)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Expense add error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
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
                    "📋 KATEGORIYALAR\n\n"
                    "Hali kategoriyalar yo'q. Chiqimlar qo'shing!"
                )
            return
        
        text = "📋 KATEGORIYALAR BO'YICHA XARAJAT:\n\n"
        total_expense = sum(cat[2] for cat in categories)
        
        for cat, count, total in categories:
            percentage = (total / total_expense * 100) if total_expense > 0 else 0
            text += f"🏷️ {cat}:\n"
            text += f"   💰 {format_currency(total)}\n"
            text += f"   📊 {percentage:.1f}% xarajat\n\n"
        
        if update.message:
            await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Categories error: {e}")
        if update.message:
            await update.message.reply_text("❌ Kategoriyalarni ko'rishda xatolik.")

async def show_budget_status(update: Update, user_id: int):
    try:
        # settings = get_user_settings(user_id) # Removed as per edit hint
        # currency = settings['currency'] # Removed as per edit hint
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get budgets for current month
        c.execute("SELECT category, amount FROM budgets WHERE user_id = ? AND month = ?", (user_id, current_month))
        budgets = dict(c.fetchall())
        
        if not budgets:
            if update.message:
                await update.message.reply_text(
                    "🎯 BYUDJET\n\n"
                    "Hali byudjet belgilanmagan.\n\n"
                    "Byudjet belgilash uchun:\n"
                    "/setbudget [kategoriya] [miqdor]\n"
                    "Masalan: /setbudget Oziq-ovqat 500000"
                )
            return
        
        # Get spending by category this month
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
        """, (user_id, current_month))
        spending = dict(c.fetchall())
        conn.close()
        
        text = f"🎯 BYUDJET HOLATI ({current_month}):\n\n"
        
        for category, budget_amount in budgets.items():
            spent = spending.get(category, 0)
            remaining = budget_amount - spent
            percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
            
            if percentage < 70:
                status = "🟢"
            elif percentage < 90:
                status = "🟡"
            else:
                status = "🔴"
            
            text += f"{status} {category}:\n"
            text += f"   💰 Byudjet: {format_currency(budget_amount)}\n"
            text += f"   💸 Sarflangan: {format_currency(spent)} ({percentage:.1f}%)\n"
            text += f"   💵 Qolgan: {format_currency(remaining)}\n\n"
        
        if update.message:
            await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Budget error: {e}")
        if update.message:
            await update.message.reply_text("❌ Byudjetni ko'rishda xatolik.")

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
                    "📤 EXPORT\n\n"
                    "Export qilish uchun ma'lumot yo'q."
                )
            return
        
        export_text = "📤 EXPORT MA'LUMOTLARI (Oxirgi 50 ta):\n\n"
        export_text += "Sana | Tur | Miqdor | Kategoriya | Izoh\n"
        export_text += "=" * 60 + "\n"
        
        for t in transactions:
            t_type = "💰 Kirim" if t[0] == "income" else "💸 Chiqim"
            date_str = datetime.fromisoformat(t[4].replace('Z', '+00:00')).strftime("%d.%m.%Y")
            export_text += f"{date_str} | {t_type} | {format_currency(t[1])} | {t[3]} | {t[2]}\n"
        
        if update.message:
            await update.message.reply_text(export_text)
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        if update.message:
            await update.message.reply_text("❌ Export qilishda xatolik.")

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
        
        text = "🏆 REKORDLARINGIZ:\n\n"
        
        if max_income and max_income[0]:
            text += f"💰 Eng katta kirim: {format_currency(max_income[0])}\n"
            text += f"   📝 {max_income[1]}\n\n"
        
        if max_expense and max_expense[0]:
            text += f"💸 Eng katta chiqim: {format_currency(max_expense[0])}\n"
            text += f"   📝 {max_expense[1]}\n\n"
        
        if active_day and active_day[1]:
            date_str = datetime.fromisoformat(active_day[0]).strftime("%d.%m.%Y")
            text += f"📅 Eng faol kun: {date_str} ({active_day[1]} ta tranzaksiya)\n\n"
        
        text += f"📊 Jami tranzaksiyalar: {total_transactions} ta\n"
        text += f"📈 O'rtacha oylik xarajat: {format_currency(int(avg_monthly))}"
        
        if update.message:
            await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Records error: {e}")
        if update.message:
            await update.message.reply_text("❌ Rekordlarni ko'rishda xatolik.")

async def show_ai_analysis(update: Update, user_id: int):
    """Show AI-powered spending analysis"""
    try:
        # Foydalanuvchi tranzaksiyalarini olish
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT type, amount, category, note, date 
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
                    "📊 AI Tahlil\n\n"
                    "Tahlil qilish uchun tranzaksiyalar yo'q. "
                    "Avval kirim yoki chiqim qo'shing!"
                )
            return
        # Tranzaksiyalarni AI uchun formatlash
        formatted_transactions = []
        for t in transactions:
            formatted_transactions.append({
                'type': t[0],
                'amount': t[1],
                'category': t[2],
                'note': t[3],
                'date': t[4]
            })
        # AI tahlil olish (sinxron chaqiruv)
        try:
            analysis = ai_service.analyze_spending_patterns(formatted_transactions)
            if update.message:
                await update.message.reply_text(analysis)
        except Exception as e:
            if update.message:
                await update.message.reply_text(f"AI tahlil xatosi: {e}")
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        if update.message:
            await update.message.reply_text(
                f"❌ AI tahlil xatosi. {e}"
            )

async def show_ai_advice(update: Update, user_id: int):
    """Show AI financial advice based on user data"""
    try:
        # Foydalanuvchi ma'lumotlarini olish
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Joriy oy ma'lumotlari
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        # Jami balans
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        total_data = c.fetchone()
        # Eng ko'p xarajat qilgan kategoriyalar
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
        # Ma'lumotlarni tayyorlash
        month_income = month_data[0] or 0
        month_expense = month_data[1] or 0
        total_income = total_data[0] or 0
        total_expense = total_data[1] or 0
        balance = total_income - total_expense
        user_data = {
            'balance': balance,
            'income': month_income,
            'expenses': month_expense,
            'categories': categories
        }
        # AI maslahat olish (sinxron chaqiruv)
        try:
            advice = ai_service.get_financial_advice(user_data)
            if update.message:
                await update.message.reply_text(advice)
        except Exception as e:
            if update.message:
                await update.message.reply_text(f"AI maslahat xatosi: {e}")
    except Exception as e:
        logger.error(f"AI advice error: {e}")
        if update.message:
            await update.message.reply_text(ai_service.get_default_advice())

async def show_motivation(update: Update):
    """Show motivational messages"""
    motivations = [
        "💪 Motivatsiya:\n\n"
        "Har kuni kichik tejash ham katta natijaga olib keladi! "
        "Bugun 1000 so'm tejang, ertaga 1 million bo'ladi!",
        
        "🎯 Motivatsiya:\n\n"
        "Maqsadingizga qadam-baqadam yuring! "
        "Har bir so'm sizning kelajagingiz uchun investitsiya!",
        
        "💰 Motivatsiya:\n\n"
        "Bugungi tejashingiz - ertangi erkinligingiz! "
        "Moliyaviy erkinlik sizning qo'lingizda!",
        
        "📈 Motivatsiya:\n\n"
        "Har bir so'm muhim, nazorat qiling! "
        "Kichik o'zgarishlar katta natijalar keltiradi!",
        
        "🌟 Motivatsiya:\n\n"
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
        MAIN_MENU_KEYBOARD, resize_keyboard=True, one_time_keyboard=True
    )
    if update.message:
        await update.message.reply_text(
            "⚙️ Sozlamalar\n\n"
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
    if text.lower() in ["/start", "/cancel", "\U0001F3E0 Bosh menyu", "\U0001F3E0 \u0413\u043B\u0430\u0432\u043D\u043E\u0435 \u043C\u0435\u043D\u044E", "\U0001F3E0 Main menu"] or text == MESSAGES["uz"]["main_menu"]: # Changed to "uz" for consistency
        return await start(update, context)
    elif text in ["💰 Valyutani o'zgartirish", "💰 Изменить валюту", "💰 Change currency"]: # Changed to "uz" for consistency
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
        "\U0001F1FA\U0001F1FF Сум": "so'm",
        "\U0001F4B5 Доллар": "USD",
        "\U0001F4B6 Евро": "EUR",
        "\U0001F4B7 Рубль": "RUB",
        "\U0001F1FA\U0001F1FF So'm": "so'm",
        "\U0001F4B5 Dollar": "USD",
        "\U0001F4B6 Euro": "EUR",
        "\U0001F4B7 Ruble": "RUB"
    }
    if text.lower() in ["/start", "/cancel", "\U0001F3E0 Bosh menyu", "\U0001F3E0 \u0413\u043B\u0430\u0432\u043D\u043E\u0435 \u043C\u0435\u043D\u044E", "\U0001F3E0 Main menu"] or text == MESSAGES["uz"]["main_menu"]: # Changed to "uz" for consistency
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
    if text.lower() in ["/start", "/cancel", "\U0001F3E0 Bosh menyu"]:
        return await start(update, context)
    elif text == "✅ Ha, o'chirish":
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
        await update.message.reply_text("🗑️ Barcha ma'lumotlar muvaffaqiyatli o'chirildi!")
        # Show main menu
        return await start(update, context)
    
    elif text == "❌ Yo'q, bekor qilish":
        return await show_settings(update, user_id)
    
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return 7

# ==== MAIN ====
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! Iltimos, environment o'zgaruvchisini sozlang.")
        return
    
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    yangi_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("❓ Yordam"), help_command),
            CommandHandler("help", help_command)
        ],
        states={
            ASK_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_income)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_category_selected)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_category_selected)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)], # New state for settings
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_data_handler)],
            9: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)], # New state for currency selection
        },
        fallbacks=[CommandHandler("start", start), CommandHandler("cancel", cancel)]
    )

    app.add_handler(yangi_conv_handler)  # Yordam handleri birinchi
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.Regex("^/reply_"), admin_reply))

    logger.info("FinBot AI ishga tushmoqda...")
    app.run_polling()

if __name__ == "__main__":
    main() 