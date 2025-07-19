# main.py
# Entry point for FinBot AI Telegram bot. Only contains bot setup, handler registration, and startup logic.

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup
from loguru import logger
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables (for local development)
try:
    load_dotenv()
except Exception:
    pass  # Railway'da environment variables avtomatik yuklanadi

# Import all handlers and functions from modules
from handlers.start import (
    start, onboarding_language, onboarding_currency, onboarding_income, onboarding_goal, 
    show_main_menu, onboarding_conv_handler
)
from handlers.finance import (
    add_income, income_category_selected, income_amount, income_note,
    expense_category_selected, expense_amount, expense_note,
    show_balance, show_analysis, show_categories, show_budget_status,
    export_data, show_records, get_category_keyboard, cancel
)
from handlers.ai import show_ai_advice, show_ai_analysis
from handlers.push import (
    push_command, push_topic_handler, push_confirm_handler,
    send_daily_push, send_weekly_push, send_monthly_goal_push, 
    send_monthly_feedback_push, push_conv_handler
)
from handlers.settings import (
    show_settings, settings_handler, currency_selection_handler, 
    delete_data_handler
)
from handlers.goals import (
    ai_goal_start, ai_goal_name, ai_goal_amount, ai_goal_deadline,
    ai_goal_monitor, ai_goal_conv_handler
)
from handlers.budget import (
    ai_budget_start, ai_budget_income, ai_budget_confirm, ai_budget_conv_handler
)
from db import init_db

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "786171158"))

# Validate BOT_TOKEN
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Iltimos, environment o'zgaruvchisini sozlang.")

# Configure logging
logger.add("finbot.log", rotation="1 day", retention="7 days", level="INFO")

# Constants
ASK_SUPPORT = 100
INCOME_AMOUNT, INCOME_NOTE = 101, 102
EXPENSE_AMOUNT, EXPENSE_NOTE = 201, 202

# Currency symbols
CURRENCY_SYMBOLS = {
    "UZS": "so'm",
    "RUB": "₽",
    "USD": "$"
}

# MESSAGES constant
MESSAGES = {
    "uz": {
        "main_menu": "🏠 Bosh menyu",
        "invalid_choice": "❌ Noto'g'ri tanlov. Qaytadan tanlang.",
        "error_soft": "🤖 Xatolik yuz berdi, lekin qo'rqmang, jamoamiz bu haqida xabardor.",
        "welcome": "👋 Assalomu alaykum, {name}!\n\n💡 Siz o'z moliyaviy kelajagingizni nazorat qilmoqchimisiz?\nMen sizga bu yo'lda yordam beruvchi FinBot AIman 🤖\n\n🎯 <b>Onboarding (2-4 bosqich):</b>\n1️⃣ Til tanlash (majburiy)\n2️⃣ Valyuta tanlash (majburiy)\n3️⃣ Daromad kiritish (ixtiyoriy)\n4️⃣ Maqsad qo'yish (ixtiyoriy)\n\n⚡️ 2 daqiqa vaqt ketadi",
        "language_select": "1️⃣ Tilni tanlang:",
        "currency_select": "2️⃣ Valyutani tanlang:",
        "income_input": "3️⃣ Oylik taxminiy daromadingizni kiriting yoki o'tkazib yuboring:\n\n💡 Bu ma'lumot AI byudjet tavsiyalari uchun ishlatiladi\nMasalan: 3 000 000",
        "goal_input": "4️⃣ Maqsad qo'yish yoki o'tkazib yuboring:\n\n💡 Maqsad qo'yganingizda AI monitoring yordam beradi\nMasalan: iPhone 15 Pro, o'qish, safar",
        "skip_option": "⏭ O'tkazib yuborish",
        "completion_full": "🎉 Onboarding yakunlandi!\n\n✅ Til va valyuta sozlandi\n✅ Daromad kiritildi\n✅ Maqsad qo'yildi\n\n🤖 AI byudjet tavsiyalari mavjud!\n🏠 Asosiy menyudan foydalanishingiz mumkin!",
        "completion_partial": "🎉 Onboarding yakunlandi!\n\n✅ Til va valyuta sozlandi\n✅ Maqsad qo'yildi\n\n🏠 Asosiy menyudan foydalanishingiz mumkin!",
        "completion_minimal": "🎉 Onboarding yakunlandi!\n\n✅ Til va valyuta sozlandi\n⏭ Daromad va maqsad o'tkazib yuborildi\n\n🏠 Asosiy menyudan foydalanishingiz mumkin!",
        "error_format": "❌ Noto'g'ri format! Masalan: 3 000 000 yoki 5000000.\n\nYoki ⏭ O'tkazib yuborish tugmasini bosing.",
        "error_general": "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
        "user_not_found": "❌ Foydalanuvchi ma'lumotlari topilmadi."
    },
    "ru": {
        "main_menu": "🏠 Главное меню",
        "invalid_choice": "❌ Неправильный выбор. Выберите снова.",
        "error_soft": "🤖 Произошла ошибка, но не волнуйтесь, наша команда в курсе.",
        "welcome": "👋 Здравствуйте, {name}!\n\n💡 Хотите контролировать свое финансовое будущее?\nЯ FinBot AI, который поможет вам в этом 🤖\n\n🎯 <b>Настройка (2-4 этапа):</b>\n1️⃣ Выбор языка (обязательно)\n2️⃣ Выбор валюты (обязательно)\n3️⃣ Ввод дохода (по желанию)\n4️⃣ Постановка цели (по желанию)\n\n⚡️ Займет 2 минуты",
        "language_select": "1️⃣ Выберите язык:",
        "currency_select": "2️⃣ Выберите валюту:",
        "income_input": "3️⃣ Введите примерный месячный доход или пропустите:\n\n💡 Эта информация используется для AI рекомендаций по бюджету\nНапример: 3 000 000",
        "goal_input": "4️⃣ Поставьте цель или пропустите:\n\n💡 При постановке цели AI мониторинг поможет вам\nНапример: iPhone 15 Pro, учеба, путешествие",
        "skip_option": "⏭ Пропустить",
        "completion_full": "🎉 Настройка завершена!\n\n✅ Язык и валюта настроены\n✅ Доход введен\n✅ Цель поставлена\n\n🤖 Доступны AI рекомендации по бюджету!\n🏠 Можете использовать главное меню!",
        "completion_partial": "🎉 Настройка завершена!\n\n✅ Язык и валюта настроены\n✅ Цель поставлена\n\n🏠 Можете использовать главное меню!",
        "completion_minimal": "🎉 Настройка завершена!\n\n✅ Язык и валюта настроены\n⏭ Доход и цель пропущены\n\n🏠 Можете использовать главное меню!",
        "error_format": "❌ Неправильный формат! Например: 3 000 000 или 5000000.\n\nИли нажмите кнопку ⏭ Пропустить.",
        "error_general": "❌ Произошла ошибка. Попробуйте снова.",
        "user_not_found": "❌ Данные пользователя не найдены."
    },
    "en": {
        "main_menu": "🏠 Main Menu",
        "invalid_choice": "❌ Invalid choice. Please select again.",
        "error_soft": "🤖 An error occurred, but don't worry, our team is aware.",
        "welcome": "👋 Hello, {name}!\n\n💡 Want to control your financial future?\nI'm FinBot AI who will help you with this 🤖\n\n🎯 <b>Setup (2-4 steps):</b>\n1️⃣ Language selection (required)\n2️⃣ Currency selection (required)\n3️⃣ Income input (optional)\n4️⃣ Goal setting (optional)\n\n⚡️ Takes 2 minutes",
        "language_select": "1️⃣ Select language:",
        "currency_select": "2️⃣ Select currency:",
        "income_input": "3️⃣ Enter your approximate monthly income or skip:\n\n💡 This information is used for AI budget recommendations\nFor example: 3 000 000",
        "goal_input": "4️⃣ Set a goal or skip:\n\n💡 When setting a goal, AI monitoring will help you\nFor example: iPhone 15 Pro, study, travel",
        "skip_option": "⏭ Skip",
        "completion_full": "🎉 Setup completed!\n\n✅ Language and currency set\n✅ Income entered\n✅ Goal set\n\n🤖 AI budget recommendations available!\n🏠 You can use the main menu!",
        "completion_partial": "🎉 Setup completed!\n\n✅ Language and currency set\n✅ Goal set\n\n🏠 You can use the main menu!",
        "completion_minimal": "🎉 Setup completed!\n\n✅ Language and currency set\n⏭ Income and goal skipped\n\n🏠 You can use the main menu!",
        "error_format": "❌ Wrong format! For example: 3 000 000 or 5000000.\n\nOr press the ⏭ Skip button.",
        "error_general": "❌ An error occurred. Please try again.",
        "user_not_found": "❌ User data not found."
    }
}

# Keyboard layouts
MAIN_MODULES_KEYBOARD = {
    "uz": [
        ["💰 Kirim/Chiqim"],
        ["📊 Balans/Tahlil"],
        ["🤖 AI vositalar"],
        ["⚙️ Sozlamalar/Yordam"]
    ],
    "ru": [
        ["💰 Доходы/Расходы"],
        ["📊 Баланс/Анализ"],
        ["🤖 AI инструменты"],
        ["⚙️ Настройки/Помощь"]
    ],
    "en": [
        ["💰 Income/Expense"],
        ["📊 Balance/Analysis"],
        ["🤖 AI Tools"],
        ["⚙️ Settings/Help"]
    ]
}

def get_user_language(user_id):
    """Get user language from database"""
    try:
        from db import get_db_connection
        conn = get_db_connection()
        if conn is None:
            return "uz"  # Default to Uzbek
        
        c = conn.cursor()
        c.execute("SELECT language FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return row[0]
        return "uz"  # Default to Uzbek
    except Exception:
        return "uz"  # Default to Uzbek

def get_message(key, user_id=None, **kwargs):
    """Get message in user's language"""
    language = get_user_language(user_id) if user_id else "uz"
    message = MESSAGES.get(language, MESSAGES["uz"]).get(key, MESSAGES["uz"].get(key, key))
    return message.format(**kwargs) if kwargs else message

def get_keyboard(user_id=None):
    """Get keyboard in user's language"""
    language = get_user_language(user_id) if user_id else "uz"
    return MAIN_MODULES_KEYBOARD.get(language, MAIN_MODULES_KEYBOARD["uz"])

def get_user_currency(user_id):
    """Get user currency from database"""
    try:
        from db import get_db_connection
        conn = get_db_connection()
        if conn is None:
            return "UZS"  # Default to Uzbek som
        
        c = conn.cursor()
        c.execute("SELECT currency FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return row[0]
        return "UZS"  # Default to Uzbek som
    except Exception:
        return "UZS"  # Default to Uzbek som

def format_amount(amount, user_id):
    """Format amount with user's currency symbol"""
    currency = get_user_currency(user_id)
    symbol = CURRENCY_SYMBOLS.get(currency, "so'm")
    
    # Format number with spaces for thousands
    formatted_amount = "{:,}".format(amount).replace(",", " ")
    
    if currency == "UZS":
        return f"{formatted_amount} {symbol}"
    elif currency == "RUB":
        return f"{formatted_amount} {symbol}"
    elif currency == "USD":
        return f"{symbol}{formatted_amount}"
    else:
        return f"{formatted_amount} {symbol}"

async def help_command(update, context):
    """Help command handler"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    help_text = (
        "❓ <b>Yordam</b>\n\n"
        "• <b>Kirim/Chiqim qo'shish</b> — mos tugmani bosing va miqdorni kiriting.\n"
        "• <b>Balans/Tahlil</b> — moliyaviy holatingizni ko'ring.\n"
        "• <b>AI maslahat</b> — shaxsiy moliyaviy tavsiya oling.\n"
        "• <b>AI Byudjet</b> — AI yordamida byudjet tuzing.\n"
        "• <b>AI Maqsad</b> — maqsad qo'ying va monitoring qiling.\n\n"
        "❌ <b>Bekor qilish</b> — istalgan vaqtda dialogni to'xtatadi.\n"
        "🏠 <b>Bosh menyu</b> — asosiy menyuga qaytadi."
    )
    await update.message.reply_text(help_text, parse_mode="HTML")
    return ConversationHandler.END

async def handle_support_message(update, context):
    """Handle support message"""
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    user = update.message.from_user
    user_message = update.message.text
    admin_text = (
        f"🆘 Yangi yordam so'rovi!\n"
        f"👤 Foydalanuvchi: {getattr(user, 'first_name', 'Foydalanuvchi')} ({getattr(user, 'id', 'Noma' + 'lum')})\n"
        f"💬 Xabar: {user_message}\n\n"
        f"Javob berish uchun: /reply_{getattr(user, 'id', '')} <javob matni>"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    await update.message.reply_text("Yordam so'rovingiz yuborildi. Admin tez orada javob beradi.")
    return ConversationHandler.END

async def admin_reply(update, context):
    """Admin reply handler"""
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
            logger.exception(f"Admin reply error: {e}")
            if update.message is not None:
                await update.message.reply_text(f"Xatolik: {e}")

async def message_handler(update, context):
    """Main message handler"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if text.lower() in ["/start", "/cancel", "🏠 Bosh menyu", "🏠 Bosh menyu"]:
        return await start(update, context)
    if user_id is None:
        return ConversationHandler.END

    # MODULLAR
    if text == "💰 Kirim/Chiqim":
        await update.message.reply_text(
            "Kirim yoki chiqim qo'shish uchun tanlang:",
            reply_markup=ReplyKeyboardMarkup([
                ["💵 Kirim qo'shish", "💸 Chiqim qo'shish"],
                ["🔙 Orqaga"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    elif text == "📊 Balans/Tahlil":
        await update.message.reply_text(
            "Balans yoki tahlilni tanlang:",
            reply_markup=ReplyKeyboardMarkup([
                ["📊 Balans", "📈 Tahlil"],
                ["🔙 Orqaga"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    elif text == "🤖 AI vositalar":
        await update.message.reply_text(
            "AI vositalaridan birini tanlang:",
            reply_markup=ReplyKeyboardMarkup([
                ["🤖 AI maslahat", "📊 AI Tahlil"],
                ["🤖 AI Byudjet", "🎯 AI Maqsad"],
                ["🔙 Orqaga"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    elif text == "⚙️ Sozlamalar/Yordam":
        await update.message.reply_text(
            "Sozlamalar yoki yordam bo'limini tanlang:",
            reply_markup=ReplyKeyboardMarkup([
                ["⚙️ Sozlamalar", "❓ Yordam"],
                ["🔙 Orqaga"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ConversationHandler.END
    # MODUL ichidan orqaga
    elif text == "🔙 Orqaga":
        await update.message.reply_text(
            "Asosiy modullar menyusi:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True)
        )
        return ConversationHandler.END
    # Kirim/Chiqim tugmalari
    elif text == "💵 Kirim qo'shish":
        await update.message.reply_text(
            "💵 Kirim uchun kategoriya tanlang:",
            reply_markup=get_category_keyboard(is_income=True)
        )
        return 4
    elif text == "💸 Chiqim qo'shish":
        await update.message.reply_text(
            "💸 Chiqim uchun kategoriya tanlang:",
            reply_markup=get_category_keyboard(is_income=False)
        )
        return 3
    # Balans/Tahlil tugmalari
    elif text == "📊 Balans":
        return await show_balance(update, user_id)
    elif text == "📈 Tahlil":
        return await show_analysis(update, user_id)
    # AI vositalari
    elif text == "🤖 AI maslahat":
        return await show_ai_advice(update, user_id)
    elif text == "📊 AI Tahlil":
        return await show_ai_analysis(update, user_id)
    elif text == "🤖 AI Byudjet":
        return await ai_budget_start(update, context)
    elif text == "🎯 AI Maqsad":
        return await ai_goal_start(update, context)
    # Sozlamalar/Yordam
    elif text == "⚙️ Sozlamalar":
        return await show_settings(update, user_id)
    elif text == "❓ Yordam":
        return await help_command(update, context)
    # Default
    else:
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"], reply_markup=ReplyKeyboardMarkup(MAIN_MODULES_KEYBOARD, resize_keyboard=True))
        return ConversationHandler.END

async def inline_button_handler(update, context):
    """Handle inline button callbacks"""
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

async def show_stats(update, context):
    """Show admin statistics"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID or not update.message:
        if update.message:
            await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    
    try:
        from db import get_db_connection
        conn = get_db_connection()
        if conn is None:
            await update.message.reply_text("❌ Ma'lumotlar bazasiga ulanishda xatolik.")
            return
        
        c = conn.cursor()
        
        # Get statistics
        c.execute("SELECT COUNT(DISTINCT user_id) FROM users")
        total_users = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM transactions WHERE date >= date('now', '-7 days')")
        weekly_transactions = c.fetchone()[0] or 0
        
        conn.close()
        
        stats_text = (
            "📊 <b>STATISTIKA</b>\n\n"
            f"👥 Jami foydalanuvchilar: {total_users}\n"
            f"💳 Jami tranzaksiyalar: {total_transactions}\n"
            f"📈 Haftalik tranzaksiyalar: {weekly_transactions}\n"
        )
        
        await update.message.reply_text(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"Stats error: {e}")
        await update.message.reply_text("❌ Statistika olishda xatolik.")

async def show_history(update, context):
    """Show user history"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None or not update.message:
            return
    
    try:
        from db import get_db_connection, format_currency
        conn = get_db_connection()
        if conn is None:
            await update.message.reply_text("❌ Ma'lumotlar bazasiga ulanishda xatolik.")
            return
        
        c = conn.cursor()
        
        # Get user info
        c.execute("SELECT joined_at FROM users WHERE user_id = ?", (user_id,))
        joined_at = c.fetchone()
        joined_at_str = joined_at[0][:10] if joined_at and joined_at[0] else "-"
        
        # Get transaction counts
        c.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
        total_ops = c.fetchone()[0] or 0
        
        # Get total amounts
        c.execute("SELECT SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) FROM transactions WHERE user_id = ?", (user_id,))
        sums = c.fetchone()
        total_income = sums[0] or 0
        total_expense = sums[1] or 0
        saved = total_income - total_expense
        
        conn.close()
        
        text = (
            "📜 <b>Harakatlar tarixi</b>\n\n"
            f"👤 <b>Botga kirgan sana:</b> {joined_at_str}\n"
            f"📊 <b>Qo'shgan kirim/chiqimlar soni:</b> {total_ops} ta\n"
            f"💰 <b>Tejalgan umumiy miqdor:</b> {format_currency(saved)}\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"History error: {e}")
        await update.message.reply_text("❌ Tarixni ko'rishda xatolik.")

async def admin_panel(update, context):
    """Admin panel handler"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID or not update.message:
        if update.message:
            await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return
    
    try:
        from db import get_db_connection
        conn = get_db_connection()
        if conn is None:
            await update.message.reply_text("❌ Ma'lumotlar bazasiga ulanishda xatolik.")
            return
        
        c = conn.cursor()
        
        # Get daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(DISTINCT user_id) FROM transactions WHERE date(date) = ?", (today,))
        active_users = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM transactions WHERE date(date) = ?", (today,))
        ops_today = c.fetchone()[0] or 0
        
        # Get most active user
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
        
        # Get server logs
        log_tail = ""
        try:
            with open("errorlog.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                log_tail = ''.join(lines[-10:]) if lines else "Loglar yo'q."
        except Exception:
            log_tail = "Loglar yo'q."
        
        text = (
            "<b>🔧 Admin Panel</b>\n\n"
            f"👥 <b>Kunlik faol foydalanuvchilar:</b> {active_users}\n"
            f"💳 <b>Bugun qo'shilgan kirim/chiqimlar:</b> {ops_today} ta\n"
            f"🏆 <b>Eng faol foydalanuvchi:</b> {most_active}\n\n"
            f"<b>📋 Server loglari (oxirgi 10 qator):</b>\n<pre>{log_tail}</pre>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"Admin panel error: {e}")
        await update.message.reply_text("❌ Admin panelda xatolik.")

async def global_error_handler(update, context):
    """Global error handler"""
    try:
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text(MESSAGES["uz"]["error_soft"])
        # Send error to admin
        error_text = f"[Xatolik]\nUser: {getattr(getattr(update, 'message', None), 'from_user', None)}\nError: {context.error}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except Exception:
        pass

def setup_schedulers(app):
    """Setup scheduled tasks"""
    try:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(lambda: send_daily_push(app), 'cron', hour=8, minute=0)
        scheduler.add_job(lambda: send_weekly_push(app), 'cron', day_of_week='sun', hour=8, minute=0)
        scheduler.add_job(lambda: send_monthly_goal_push(app), 'cron', day=1, hour=8, minute=0)
        scheduler.add_job(lambda: send_monthly_feedback_push(app), 'cron', day=1, hour=12, minute=0)
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        # Continue without scheduler if it fails

def main():
    """Main function to start the bot"""
    logger.info("FinBot AI ishga tushmoqda...")
    
    # Initialize database
    init_db()
    
    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(global_error_handler)

    # Support conversation handler
    support_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("❓ Yordam"), help_command),
            CommandHandler("help", help_command)
        ],
        states={
            ASK_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Main conversation handler - commented out to avoid conflicts
    # main_conv_handler = ConversationHandler(
    #     entry_points=[MessageHandler(
    #         filters.Regex(r"^(💰 Kirim/Chiqim|📊 Balans/Tahlil|🤖 AI vositalar|⚙️ Sozlamalar/Yordam)$"),
    #         message_handler
    #     )],
    #     states={
    #         INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_amount)],
    #         INCOME_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_note)],
    #         EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
    #         EXPENSE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_note)],
    #         3: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_category_selected)],
    #         4: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_category_selected)],
    #         5: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)],
    #         6: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
    #         7: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_data_handler)],
    #         9: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
    #     },
    #     fallbacks=[CommandHandler("cancel", cancel)]
    # )

    # Add all handlers
    app.add_handler(support_conv_handler)
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
    
    # Main conversation handler for all text messages
    main_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
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
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(main_conv_handler)
    
    # Add AI and Budget conversation handlers
    app.add_handler(ai_goal_conv_handler)
    app.add_handler(ai_budget_conv_handler)
    app.add_handler(push_conv_handler)

    # Setup schedulers
    setup_schedulers(app)
    
    # Start polling
    logger.info("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main() 