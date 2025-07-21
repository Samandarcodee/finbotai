"""
handlers/start.py
Onboarding and /start command logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from db import init_db, get_db_connection, get_user_settings, get_currency_code, set_onboarded, is_onboarded, DB_PATH
from loguru import logger
from utils import get_navigation_keyboard, build_reply_keyboard

ONBOARDING_CURRENCY, ONBOARDING_INCOME, ONBOARDING_GOAL = 301, 302, 303

# MESSAGES constant
MESSAGES = {
    "uz": {
        "main_menu": "🏠 Bosh menyu",
        "invalid_choice": "❌ Noto'g'ri tanlov. Qaytadan tanlang.",
        "onboarding_done": "🎯 Onboarding yakunlandi! Endi asosiy menyudan foydalanishingiz mumkin.",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with onboarding logic"""
    if not update.message:
        return
    user = getattr(update.message, 'from_user', None)
    if not user:
        return
    user_id = getattr(user, 'id', None)
    user_name = getattr(user, 'first_name', 'Foydalanuvchi')
    try:
        # Onboarding: til tanlash bosqichi olib tashlandi, doim uzbek
        from constants import get_message
        welcome_text = get_message("welcome", user_id, name=user_name)
        await update.message.reply_text(welcome_text, parse_mode="HTML")
        # To'g'ridan-to'g'ri keyingi bosqichga o'tamiz (valyuta tanlash yoki asosiy menyu)
        return await show_main_menu(update)
    except Exception as e:
        logger.exception(f"Error in start: {e}")
        from constants import get_message
        await update.message.reply_text(get_message("error_general", user_id))
        return ConversationHandler.END

async def onboarding_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection during onboarding"""
    if not update.message or not update.message.text:
        logger.error("No message or text in onboarding_currency")
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    logger.info(f"onboarding_currency called with text: {text}, user_id: {user_id}")
    
    if user_id is None:
        await update.message.reply_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return ConversationHandler.END
    
    currency = get_currency_code(text)
    logger.info(f"Selected currency: {currency}")
    
    try:
        # Save currency to DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if user exists in user_settings
        c.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
        exists = c.fetchone()
        
        if exists:
            # Update existing user
            c.execute("UPDATE user_settings SET currency = ? WHERE user_id = ?", (currency, user_id))
            logger.info(f"Updated user {user_id} with currency {currency}")
        else:
            # Insert new user
            c.execute("INSERT INTO user_settings (user_id, currency, onboarding_done) VALUES (?, ?, 0)", (user_id, currency))
            logger.info(f"Inserted new user {user_id} with currency {currency}")
        
        conn.commit()
        conn.close()
        
        # Save currency to context for next steps
        context.user_data['currency'] = currency
        
        logger.info(f"Sending optional income step message to user {user_id}")
        from utils import get_user_language
        from constants import MESSAGES
        language = get_user_language(user_id)
        income_text = MESSAGES.get(language, MESSAGES["uz"]).get("income_input", "3️⃣ Oylik taxminiy daromadingizni kiriting yoki o'tkazib yuboring:")
        skip_option = MESSAGES.get(language, MESSAGES["uz"]).get("skip_option", "⏭ O'tkazib yuborish")
        await update.message.reply_text(
            income_text,
            reply_markup=build_reply_keyboard([
                [skip_option]
            ], resize=True, one_time=True, add_navigation=False)
        )
        logger.info(f"Returning ONBOARDING_INCOME state: {ONBOARDING_INCOME}")
        return ONBOARDING_INCOME
    except sqlite3.Error as e:
        logger.exception(f"Database error in onboarding_currency: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def onboarding_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle income input during onboarding"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if user_id is None:
        await update.message.reply_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return ConversationHandler.END
    
    # Check if user wants to skip
    from utils import get_user_language
    from constants import MESSAGES
    language = get_user_language(user_id)
    skip_text = MESSAGES.get(language, MESSAGES["uz"]).get("skip_option", "⏭ O'tkazib yuborish")
    
    if text == skip_text:
        # Skip income step, go to goal
        logger.info(f"User {user_id} skipped income step")
        goal_text = MESSAGES.get(language, MESSAGES["uz"]).get("goal_input", "4️⃣ Maqsad qo'yish yoki o'tkazib yuboring:")
        await update.message.reply_text(
            goal_text,
            reply_markup=ReplyKeyboardMarkup([
                [skip_text]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ONBOARDING_GOAL
    
    # Validate income amount
    from db import validate_amount
    amount, error = validate_amount(text)
    
    if error:
        await update.message.reply_text(error)
        return ONBOARDING_INCOME
    
    # Save income to context (optional step)
    context.user_data['income'] = amount
    
    # Go to goal step
    goal_text = MESSAGES.get(language, MESSAGES["uz"]).get("goal_input", "4️⃣ Maqsad qo'yish yoki o'tkazib yuboring:")
    await update.message.reply_text(
        goal_text,
        reply_markup=ReplyKeyboardMarkup([
            [skip_text]
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return ONBOARDING_GOAL

async def onboarding_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal input during onboarding"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if user_id is None:
        await update.message.reply_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return ConversationHandler.END
    
    # Check if user wants to skip
    from utils import get_user_language
    from constants import MESSAGES
    language = get_user_language(user_id)
    skip_text = MESSAGES.get(language, MESSAGES["uz"]).get("skip_option", "⏭ O'tkazib yuborish")
    
    if text == skip_text:
        # Skip goal step, complete onboarding
        logger.info(f"User {user_id} skipped goal step")
        await complete_onboarding(update, user_id, context)
        return ConversationHandler.END
    
    # Save goal to context (optional step)
    context.user_data['goal'] = text
    
    # Complete onboarding
    await complete_onboarding(update, user_id, context)
    return ConversationHandler.END

async def complete_onboarding(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Complete onboarding process"""
    try:
        # Mark user as onboarded
        set_onboarded(user_id)
        # Get completion message based on what was completed
        from utils import get_user_language
        from constants import MESSAGES
        language = get_user_language(user_id)
        # Defensive: context.user_data may be None
        user_data = context.user_data if context and hasattr(context, 'user_data') and context.user_data else {}
        income_completed = 'income' in user_data
        goal_completed = 'goal' in user_data
        if income_completed and goal_completed:
            completion_text = MESSAGES.get(language, MESSAGES["uz"]).get("completion_full") or "🎉 Onboarding yakunlandi!"
        elif goal_completed:
            completion_text = MESSAGES.get(language, MESSAGES["uz"]).get("completion_partial") or "🎉 Onboarding yakunlandi!"
        else:
            completion_text = MESSAGES.get(language, MESSAGES["uz"]).get("completion_minimal") or "🎉 Onboarding yakunlandi!"
        await update.message.reply_text(completion_text or "🎉 Onboarding yakunlandi!")
        from main import navigate_to_main_menu
        return await navigate_to_main_menu(update, context)
    except Exception as e:
        logger.exception(f"Error completing onboarding: {e}")
        await update.message.reply_text("❌ Onboarding yakunlashda xatolik.")

async def show_main_menu(update, context=None):
    keyboard = [
        ["💰 Kirim/Chiqim", "📊 Balans/Tahlil"],
        ["🤖 AI vositalar", "⚙️ Sozlamalar/Yordam"]
    ]
    await update.message.reply_text(
        "Quyidagi funksiyalardan birini tanlang:",
        reply_markup=build_reply_keyboard(keyboard, resize=True, one_time=True, add_navigation=False)
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    if update.message:
        await update.message.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
    return ConversationHandler.END

# Conversation handler for onboarding
onboarding_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ONBOARDING_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_currency)],
        ONBOARDING_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_income)],
        ONBOARDING_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_goal)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
) 