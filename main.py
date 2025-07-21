# main.py
# Entry point for FinBot AI Telegram bot. Only contains bot setup, handler registration, and startup logic.

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from loguru import logger
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.error import TelegramError
from dotenv import load_dotenv
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

# Load environment variables (for local development)
try:
    load_dotenv()
except Exception:
    pass  # Railway'da environment variables avtomatik yuklanadi

# Import all handlers and functions from modules
from handlers.start import (
    start, onboarding_currency, onboarding_income, onboarding_goal, 
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
    SETTINGS_CURRENCY, SETTINGS_LANGUAGE, SETTINGS_DELETE, SETTINGS_MENU
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

# Import shared constants and functions
from constants import (
    ASK_SUPPORT, INCOME_AMOUNT, INCOME_NOTE, EXPENSE_AMOUNT, EXPENSE_NOTE,
    MESSAGES, MAIN_MODULES_KEYBOARD, get_message, get_keyboard, NAV_COMMANDS
)

# Import utils for shared functions
from utils import get_user_language, get_user_currency, format_amount, build_reply_keyboard, is_navigation_command

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

async def handle_kirim_chiqim_menu(update, context):
    """Kirim/Chiqim menyusi uchun universal handler"""
    if not update.message or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if text in ["🔙 Orqaga", "🏠 Bosh menyu", "/start"]:
        return await start(update, context)
    if text == "💵 Kirim qo'shish":
        return await income_category_selected(update, context)
    if text == "💸 Chiqim qo'shish":
        return await expense_category_selected(update, context)
    # Faqat Bosh menyu tugmasi
    keyboard = [
        ["💵 Kirim qo'shish", "💸 Chiqim qo'shish"],
        ["🏠 Bosh menyu"]
    ]
    await update.message.reply_text(
        "Kirim yoki chiqim qo'shish uchun tanlang:",
        reply_markup=build_reply_keyboard(keyboard, resize=True, one_time=True, add_navigation=False)
    )
    return ConversationHandler.END

async def navigate_to_main_menu(update, context):
    from handlers.start import show_main_menu
    return await show_main_menu(update, context)

async def message_handler(update, context):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if is_navigation_command(text):
        return await navigate_to_main_menu(update, context)
    match text:
        case "💰 Kirim/Chiqim":
            return await handle_kirim_chiqim_menu(update, context)
        case "📊 Balans/Tahlil":
            keyboard = [
                ["📊 Balans", "📈 Tahlil"],
                ["🏠 Bosh menyu"]
            ]
            await update.message.reply_text(
                "Balans yoki tahlilni tanlang:",
                reply_markup=build_reply_keyboard(keyboard, resize=True, one_time=True, add_navigation=False)
            )
            return
        case "📊 Balans":
            user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
            if user_id is None:
                await update.message.reply_text("❌ Foydalanuvchi aniqlanmadi.")
                return ConversationHandler.END
            return await show_balance(update, user_id)
        case "📈 Tahlil":
            user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
            if user_id is None:
                await update.message.reply_text("❌ Foydalanuvchi aniqlanmadi.")
                return ConversationHandler.END
            return await show_analysis(update, user_id)
        case "🤖 AI vositalar":
            return await show_ai_menu(update, context)
        case "⚙️ Sozlamalar/Yordam":
            return await show_settings(update, context)
        case _:
            await update.message.reply_text("❌ Noto'g'ri tanlov. Bosh menyuga qaytmoqdamiz.")
            return await navigate_to_main_menu(update, context)

async def universal_fallback(update, context):
    if update.message and update.message.text:
        text = update.message.text.strip()
        if is_navigation_command(text):
            return await navigate_to_main_menu(update, context)
        else:
            await update.message.reply_text("❌ Noto'g'ri tanlov. Bosh menyuga qaytmoqdamiz.")
            return await navigate_to_main_menu(update, context)
    return ConversationHandler.END

async def inline_button_handler(update, context):
    if not update.callback_query:
        return await navigate_to_main_menu(update, context)
    query = update.callback_query
    await query.answer()
    # Qolgan callback ishlovchi kod shu yerda bo‘ladi
    if query.data.startswith("balance_"):
        user_id = query.from_user.id
        await show_balance(update, user_id)
    elif query.data.startswith("analysis_"):
        user_id = query.from_user.id
        await show_analysis(update, user_id)
    elif query.data.startswith("ai_advice_"):
        user_id = query.from_user.id
        await show_ai_advice(update, user_id)

async def show_stats(update, context):
    """Show bot statistics for admin"""
    if not update.message or not hasattr(update.message, 'from_user'):
        return
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID:
        return
    
    try:
        conn = sqlite3.connect('finbot.db')
        c = conn.cursor()
        
        # Get user count
        c.execute("SELECT COUNT(DISTINCT user_id) FROM user_settings")
        user_count = c.fetchone()[0]
        
        # Get transaction count
        c.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = c.fetchone()[0]
        
        # Get today's transactions
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM transactions WHERE date LIKE ?", (f"{today}%",))
        today_transactions = c.fetchone()[0]
        
        conn.close()
        
        stats_text = (
            f"📊 <b>Bot statistikasi</b>\n\n"
            f"👥 Foydalanuvchilar: {user_count}\n"
            f"📝 Jami tranzaksiyalar: {transaction_count}\n"
            f"📅 Bugungi tranzaksiyalar: {today_transactions}\n"
            f"🕐 Hisobot vaqti: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        await update.message.reply_text(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"Stats error: {e}")
        await update.message.reply_text("❌ Statistika olishda xatolik.")

async def show_history(update, context):
    """Show recent transaction history for admin"""
    if not update.message or not hasattr(update.message, 'from_user'):
        return
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id != ADMIN_ID:
        return
    
    try:
        conn = sqlite3.connect('finbot.db')
        c = conn.cursor()
        
        c.execute("""
            SELECT t.user_id, t.type, t.amount, t.note, t.date, u.first_name
            FROM transactions t
            LEFT JOIN user_settings u ON t.user_id = u.user_id
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
        
        # Add conversation handlers in correct order
        app.add_handler(onboarding_conv_handler)
        app.add_handler(push_conv_handler)
        app.add_handler(ai_goal_conv_handler)
        app.add_handler(ai_budget_conv_handler)
        
        # Add finance conversation handler with improved structure
        from handlers.finance import (
            add_income, income_category_selected, income_amount, income_note,
            expense_category_selected, expense_amount, expense_note, cancel
        )
        
        finance_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^💵 Kirim qo'shish$"), income_category_selected),
                MessageHandler(filters.Regex("^💸 Chiqim qo'shish$"), expense_category_selected)
            ],
            states={
                INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_amount)],
                INCOME_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_note)],
                EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
                EXPENSE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_note)],
            },
            fallbacks=[
                MessageHandler(filters.Regex("^(❌ Bekor qilish|🏠 Bosh menyu|🔙 Orqaga|/cancel)$"), cancel)
            ]
        )
        app.add_handler(finance_conv_handler)
        
        # Add settings conversation handlers with improved structure
        settings_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^⚙️ Sozlamalar/Yordam$"), show_settings)
            ],
            states={
                SETTINGS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)],
                SETTINGS_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_selection_handler)],
                SETTINGS_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_selection_handler)],
                SETTINGS_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_data_handler)],
            },
            fallbacks=[
                MessageHandler(filters.Regex("|".join(NAV_COMMANDS)), navigate_to_main_menu)
            ]
        )
        app.add_handler(settings_conv_handler)
        
        # Add AI menu handler with improved structure
        ai_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^🤖 AI vositalar$"), show_ai_menu)
            ],
            states={
                100: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_menu)]
            },
            fallbacks=[
                MessageHandler(filters.Regex("^(🔙 Orqaga|🏠 Bosh menyu|/cancel)$"), start)
            ]
        )
        app.add_handler(ai_conv_handler)
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", show_stats))
        app.add_handler(CommandHandler("history", show_history))
        app.add_handler(CommandHandler("admin", admin_panel))
        
        # Add callback query handler
        app.add_handler(CallbackQueryHandler(inline_button_handler))
        
        # Add message handlers - this should be last to catch unmatched messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
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