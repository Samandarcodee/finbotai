"""
handlers/start.py
Onboarding and /start command logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from datetime import datetime
from db import init_db, get_db_connection, get_user_settings, get_currency_code, set_onboarded, DB_PATH
from loguru import logger

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
        # Check if user is new (onboarding needed)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT onboarding_done FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row is None or not isinstance(row, (list, tuple)) or not row[0]:
            # Onboarding: hissiyotli welcome va 3 bosqich
            welcome_text = (
                f"👋 Assalomu alaykum, {user_name}!\n\n"
                "💡 Siz o'z moliyaviy kelajagingizni nazorat qilmoqchimisiz?\n"
                "Men sizga bu yo'lda yordam beruvchi FinBot AIman 🤖\n\n"
                "⚡️ 3 daqiqa ichida sozlanamizmi?\n\n"
                "1️⃣ Valyutani tanlang (so'm, dollar, euro)"
            )
            currency_kb = ReplyKeyboardMarkup([
                ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"]
            ], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(welcome_text, reply_markup=currency_kb)
            return ONBOARDING_CURRENCY
        # Agar onboardingdan o'tgan bo'lsa, asosiy menyu
        return await show_main_menu(update)
    except sqlite3.Error as e:
        logger.exception(f"Database error in start: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def onboarding_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection during onboarding"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if user_id is None:
        await update.message.reply_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return ConversationHandler.END
    
    currency = get_currency_code(text)
    
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
        else:
            # Insert new user
            c.execute("INSERT INTO user_settings (user_id, currency, onboarding_done) VALUES (?, ?, 0)", (user_id, currency))
        
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            "2️⃣ Oylik taxminiy kirimingizni kiriting (masalan: 3 000 000):",
            reply_markup=ReplyKeyboardMarkup([["Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
        )
        return ONBOARDING_INCOME
    except sqlite3.Error as e:
        logger.exception(f"Database error in onboarding_currency: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def onboarding_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle income input during onboarding"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.replace(' ', '')
    try:
        income = int(text)
        if income <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri format! Masalan: 3 000 000 yoki 5000000.")
        return ONBOARDING_INCOME
    context.user_data['onboarding_income'] = income
    await update.message.reply_text(
        "3️⃣ Maqsad qo'yish: Nimani tejamoqchisiz? (masalan: telefon, o'qish, safar)",
        reply_markup=ReplyKeyboardMarkup([["Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ONBOARDING_GOAL

async def onboarding_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal input during onboarding"""
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
    
    try:
        # Save goal to DB (goals table) and mark onboarding as done
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)",
                  (user_id, text, income, None))
        c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        onboarding_done_msg = MESSAGES["uz"]["onboarding_done"]
        await update.message.reply_text(onboarding_done_msg, reply_markup=ReplyKeyboardRemove())
        return await show_main_menu(update)
    except sqlite3.Error as e:
        logger.exception(f"Database error in onboarding_goal: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def show_main_menu(update):
    """Show main menu with inline keyboard"""
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Balansni ko'rish 📊", callback_data="show_balance")],
        [InlineKeyboardButton("Tahlil qilish 📈", callback_data="show_analysis")],
        [InlineKeyboardButton("AI maslahat olish 🤖", callback_data="show_ai_advice")]
    ])
    await update.message.reply_text("Quyidagi amallardan birini tanlang:", reply_markup=inline_kb)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    await update.message.reply_text("❌ Amal bekor qilindi.")
    return ConversationHandler.END

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