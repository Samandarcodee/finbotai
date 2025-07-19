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
from handlers.ai import (
    show_ai_menu, show_ai_advice, show_ai_analysis, show_budget_advice,
    show_savings_tips, show_investment_advice, show_goal_monitoring, handle_ai_menu
)
from handlers.push import (
    push_command, push_topic_handler, push_confirm_handler,
    send_daily_push, send_weekly_push, send_monthly_goal_push, 
    send_monthly_feedback_push, push_conv_handler
)
from handlers.settings import (
    show_settings, settings_handler, currency_selection_handler, 
    language_selection_handler, delete_data_handler,
    SETTINGS_CURRENCY, SETTINGS_LANGUAGE, SETTINGS_DELETE
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

# Import utils for shared functions
from utils import get_user_language, get_user_currency, format_amount

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
        "user_not_found": "❌ Foydalanuvchi ma'lumotlari topilmadi.",
        "ai_menu": "🤖 <b>AI VOSITALAR</b>\n\nQuyidagi AI funksiyalaridan birini tanlang:",
        "settings_menu": "⚙️ <b>SOZLAMALAR</b>\n\nQuyidagi sozlamalardan birini tanlang:"
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
        "user_not_found": "❌ Данные пользователя не найдены.",
        "ai_menu": "🤖 <b>AI ИНСТРУМЕНТЫ</b>\n\nВыберите одну из AI функций:",
        "settings_menu": "⚙️ <b>НАСТРОЙКИ</b>\n\nВыберите одну из настроек:"
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
        "user_not_found": "❌ User data not found.",
        "ai_menu": "🤖 <b>AI TOOLS</b>\n\nSelect one of the AI functions:",
        "settings_menu": "⚙️ <b>SETTINGS</b>\n\nSelect one of the settings:"
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

def get_message(key, user_id=None, **kwargs):
    """Get message in user's language"""
    language = get_user_language(user_id) if user_id else "uz"
    message = MESSAGES.get(language, MESSAGES["uz"]).get(key, MESSAGES["uz"].get(key, key))
    return message.format(**kwargs) if kwargs else message

def get_keyboard(user_id=None):
    """Get keyboard in user's language"""
    language = get_user_language(user_id) if user_id else "uz"
    return MAIN_MODULES_KEYBOARD.get(language, MAIN_MODULES_KEYBOARD["uz"])

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
    """Main message handler with enhanced AI and settings support"""
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
        return await show_ai_menu(update, user_id)
    elif text == "⚙️ Sozlamalar/Yordam":
        return await show_settings(update, user_id)
    else:
        await update.message.reply_text(get_message("invalid_choice", user_id))
        return ConversationHandler.END

async def inline_button_handler(update, context):
    """Handle inline button callbacks"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("balance_"):
        user_id = query.from_user.id
        await show_balance(update, user_id)
    elif query.data.startswith("analysis_"):
        user_id = query.from_user.id
        await show_analysis(update, user_id)
    elif query.data.startswith("ai_advice_"):
        user_id = query.from_user.id
        await show_ai_advice(update, user_id)
    elif query.data.startswith("ai_analysis_"):
        user_id = query.from_user.id
        await show_ai_analysis(update, user_id)

async def show_stats(update, context):
    """Show bot statistics for admin"""
    if not update.message or not hasattr(update.message, 'from_user'):
        return
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID:
        return
    
    try:
        from db import get_db_connection
        conn = get_db_connection()
        if conn is None:
            await update.message.reply_text("❌ Ma'lumotlar bazasiga ulanishda xatolik.")
            return
        
        c = conn.cursor()
        
        # Get user count
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        
        # Get transaction count
        c.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = c.fetchone()[0]
        
        # Get today's transactions
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM transactions WHERE date LIKE ?", (f"{today}%",))
        today_transactions = c.fetchone()[0]
        
        # Get active goals
        c.execute("SELECT COUNT(*) FROM goals WHERE status = 'active'")
        active_goals = c.fetchone()[0]
        
        conn.close()
        
        stats_text = f"""📊 <b>Bot statistikasi:</b>

👥 <b>Foydalanuvchilar:</b> {user_count}
💰 <b>Jami tranzaksiyalar:</b> {transaction_count}
📅 <b>Bugungi tranzaksiyalar:</b> {today_transactions}
🎯 <b>Faol maqsadlar:</b> {active_goals}

⏰ <b>Vaqt:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
        
        await update.message.reply_text(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"Stats error: {e}")
        await update.message.reply_text("❌ Statistikani olishda xatolik.")

async def show_history(update, context):
    """Show recent transactions for admin"""
    if not update.message or not hasattr(update.message, 'from_user'):
        return
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID:
        return
    
    try:
        from db import get_db_connection
        conn = get_db_connection()
        if conn is None:
            await update.message.reply_text("❌ Ma'lumotlar bazasiga ulanishda xatolik.")
            return
        
        c = conn.cursor()
        
        # Get recent transactions
        c.execute("""
            SELECT t.user_id, t.type, t.amount, t.category, t.date, u.first_name
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            ORDER BY t.date DESC
            LIMIT 10
        """)
        
        transactions = c.fetchall()
        conn.close()
        
        if not transactions:
            await update.message.reply_text("📝 Hozircha tranzaksiyalar yo'q.")
            return
        
        history_text = "📝 <b>So'nggi tranzaksiyalar:</b>\n\n"
        
        for t in transactions:
            user_name = t[5] or f"User {t[0]}"
            amount = format_amount(t[2], t[0])
            date = t[4][:10] if t[4] else "N/A"
            emoji = "💵" if t[1] == "income" else "💸"
            
            history_text += f"{emoji} <b>{user_name}</b> - {amount} ({t[3]})\n📅 {date}\n\n"
        
        await update.message.reply_text(history_text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"History error: {e}")
        await update.message.reply_text("❌ Tarixni olishda xatolik.")

async def admin_panel(update, context):
    """Admin panel for bot management"""
    if not update.message or not hasattr(update.message, 'from_user'):
        return
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID:
        return
    
    admin_text = """🔧 <b>Admin paneli</b>

📊 <b>Statistika:</b>
• /stats - Bot statistikasi
• /history - So'nggi tranzaksiyalar

👥 <b>Foydalanuvchilar:</b>
• /users - Foydalanuvchilar ro'yxati
• /notify - Barcha foydalanuvchilarga xabar

🤖 <b>Bot boshqaruvi:</b>
• /restart - Botni qayta ishga tushirish
• /backup - Ma'lumotlar bazasini zaxiralash

📈 <b>Monitoring:</b>
• /logs - Log fayllarini ko'rish
• /errors - Xatoliklarni ko'rish"""

    await update.message.reply_text(admin_text, parse_mode="HTML")

async def global_error_handler(update, context):
    """Global error handler"""
    logger.exception(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            get_message("error_soft", update.effective_user.id if update.effective_user else None)
        )

def setup_schedulers(app):
    """Setup scheduled tasks"""
    scheduler = AsyncIOScheduler()
    
    # Create a wrapper function that provides the bot context
    async def send_daily_push_wrapper():
        from handlers.push import send_daily_push_to_all
        return await send_daily_push_to_all(app)
    
    async def send_weekly_push_wrapper():
        from handlers.push import send_weekly_push_to_all
        return await send_weekly_push_to_all(app)
    
    async def send_monthly_goal_push_wrapper():
        from handlers.push import send_monthly_goal_push_to_all
        return await send_monthly_goal_push_to_all(app)
    
    # Daily reminder at 9 AM
    scheduler.add_job(
        send_daily_push_wrapper, 
        'cron', 
        hour=9, 
        minute=0,
        id='daily_reminder'
    )
    
    # Weekly report on Monday at 8 AM
    scheduler.add_job(
        send_weekly_push_wrapper, 
        'cron', 
        day_of_week='mon',
        hour=8, 
        minute=0,
        id='weekly_report'
    )
    
    # Monthly report on 1st of month at 8 AM
    scheduler.add_job(
        send_monthly_goal_push_wrapper, 
        'cron', 
        day=1,
        hour=8, 
        minute=0,
        id='monthly_report'
    )
    
    scheduler.start()
    return scheduler

def main():
    """Main function to start the bot"""
    try:
        # Initialize database
        init_db()
        
        # Create application
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add conversation handlers
        app.add_handler(onboarding_conv_handler)
        app.add_handler(push_conv_handler)
        app.add_handler(ai_goal_conv_handler)
        app.add_handler(ai_budget_conv_handler)
        
        # Add settings conversation handlers
        settings_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^⚙️ Sozlamalar/Yordam$"), lambda u, c: show_settings(u, u.effective_user.id))],
            states={
                5: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)],  # Main settings menu state
                SETTINGS_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
                SETTINGS_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_selection_handler)],
                SETTINGS_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_data_handler)],
            },
            fallbacks=[MessageHandler(filters.Regex("^(🔙 Orqaga|/start|/cancel)$"), lambda u, c: start(u, c))]
        )
        app.add_handler(settings_conv_handler)
        
        # Add AI menu handler
        ai_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🤖 AI vositalar$"), lambda u, c: show_ai_menu(u, u.effective_user.id))],
            states={},
            fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_menu)]
        )
        app.add_handler(ai_conv_handler)
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", show_stats))
        app.add_handler(CommandHandler("history", show_history))
        app.add_handler(CommandHandler("admin", admin_panel))
        
        # Add message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        app.add_handler(CallbackQueryHandler(inline_button_handler))
        
        # Add error handler
        app.add_error_handler(global_error_handler)
        
        # Setup schedulers
        scheduler = setup_schedulers(app)
        
        # Start the bot
        logger.info("Bot ishga tushdi!")
        app.run_polling()
        
    except Exception as e:
        logger.exception(f"Bot ishga tushishda xatolik: {e}")
        raise

if __name__ == "__main__":
    main() 