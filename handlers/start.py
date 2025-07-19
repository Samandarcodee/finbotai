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

ONBOARDING_LANGUAGE, ONBOARDING_CURRENCY, ONBOARDING_INCOME, ONBOARDING_GOAL = 300, 301, 302, 303

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
            # Onboarding: til tanlash bilan boshlanadi
            from main import get_message
            welcome_text = get_message("welcome", user_id, name=user_name)
            language_kb = ReplyKeyboardMarkup([
                ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"]
            ], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(welcome_text, reply_markup=language_kb, parse_mode="HTML")
            return ONBOARDING_LANGUAGE
        # Agar onboardingdan o'tgan bo'lsa, asosiy menyu
        return await show_main_menu(update)
    except sqlite3.Error as e:
        logger.exception(f"Database error in start: {e}")
        from main import get_message
        await update.message.reply_text(get_message("error_general", user_id))
        return ConversationHandler.END

async def onboarding_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection during onboarding"""
    if not update.message or not update.message.text:
        logger.error("No message or text in onboarding_language")
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    logger.info(f"onboarding_language called with text: {text}, user_id: {user_id}")
    
    if user_id is None:
        await update.message.reply_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return ConversationHandler.END
    
    # Determine language code
    if "🇺🇿" in text or "o'zbek" in text.lower():
        language = "uz"
    elif "🇷🇺" in text or "рус" in text.lower():
        language = "ru"
    elif "🇺🇸" in text or "english" in text.lower():
        language = "en"
    else:
        language = "uz"  # Default to Uzbek
    
    logger.info(f"Selected language: {language}")
    
    try:
        # Save language to DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if user exists in user_settings
        c.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
        exists = c.fetchone()
        
        if exists:
            # Update existing user
            c.execute("UPDATE user_settings SET language = ? WHERE user_id = ?", (language, user_id))
            logger.info(f"Updated user {user_id} with language {language}")
        else:
            # Insert new user
            c.execute("INSERT INTO user_settings (user_id, language, onboarding_done) VALUES (?, ?, 0)", (user_id, language))
            logger.info(f"Inserted new user {user_id} with language {language}")
        
        conn.commit()
        conn.close()
        
        # Save language to context for next steps
        context.user_data['language'] = language
        
        logger.info(f"Sending currency selection message to user {user_id}")
        from main import get_message
        currency_text = get_message("currency_select", user_id)
        await update.message.reply_text(
            currency_text,
            reply_markup=ReplyKeyboardMarkup([
                ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        logger.info(f"Returning ONBOARDING_CURRENCY state: {ONBOARDING_CURRENCY}")
        return ONBOARDING_CURRENCY
    except sqlite3.Error as e:
        logger.exception(f"Database error in onboarding_language: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
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
        from main import MESSAGES
        language = get_user_language(user_id)
        income_text = MESSAGES.get(language, MESSAGES["uz"]).get("income_input", "3️⃣ Oylik taxminiy daromadingizni kiriting yoki o'tkazib yuboring:")
        skip_option = MESSAGES.get(language, MESSAGES["uz"]).get("skip_option", "⏭ O'tkazib yuborish")
        await update.message.reply_text(
            income_text,
            reply_markup=ReplyKeyboardMarkup([
                [skip_option]
            ], resize_keyboard=True, one_time_keyboard=True)
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
    from main import MESSAGES
    language = get_user_language(user_id)
    skip_option = MESSAGES.get(language, MESSAGES["uz"]).get("skip_option", "⏭ O'tkazib yuborish")
    
    if text == skip_option:
        goal_text = MESSAGES.get(language, MESSAGES["uz"]).get("goal_input", "4️⃣ Maqsad qo'yish yoki o'tkazib yuboring:")
        await update.message.reply_text(
            goal_text,
            reply_markup=ReplyKeyboardMarkup([
                [skip_option]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ONBOARDING_GOAL
    
    # Process income input
    try:
        income = int(text.replace(' ', ''))
        if income <= 0:
            raise ValueError
    except ValueError:
        error_text = MESSAGES.get(language, MESSAGES["uz"]).get("error_format", "❌ Noto'g'ri format! Masalan: 3 000 000 yoki 5000000.")
        await update.message.reply_text(
            error_text,
            reply_markup=ReplyKeyboardMarkup([
                [skip_option]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return ONBOARDING_INCOME
    
    # Save income to context
    context.user_data['onboarding_income'] = income
    
    goal_text = get_message("goal_input", user_id)
    await update.message.reply_text(
        goal_text,
        reply_markup=ReplyKeyboardMarkup([
            [skip_option]
        ], resize_keyboard=True, one_time_keyboard=True)
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
    
    # Check if user wants to skip
    from utils import get_user_language
    from main import MESSAGES
    language = get_user_language(user_id)
    skip_option = MESSAGES.get(language, MESSAGES["uz"]).get("skip_option", "⏭ O'tkazib yuborish")
    
    if text == skip_option:
        # Mark onboarding as done without goal
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            completion_text = MESSAGES.get(language, MESSAGES["uz"]).get("completion_minimal", "🎉 Onboarding yakunlandi!")
            await update.message.reply_text(completion_text, reply_markup=ReplyKeyboardRemove())
            return await show_main_menu(update)
        except sqlite3.Error as e:
            logger.exception(f"Database error in onboarding_goal: {e}")
            await update.message.reply_text(MESSAGES.get(language, MESSAGES["uz"]).get("error_general", "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring."))
            return ConversationHandler.END
    
    # Process goal input
    user_data = getattr(context, 'user_data', {})
    if not isinstance(user_data, dict):
        user_data = {}
    income = user_data.get('onboarding_income', 0)
    
    try:
        # Save goal to DB (goals table) and mark onboarding as done
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Save goal if provided
        if text and text != "⏭ O'tkazib yuborish":
            c.execute("INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)",
                      (user_id, text, income, None))
        
        # Mark onboarding as done
        c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Show completion message based on what was completed
        if income > 0:
            completion_text = (
                "🎉 Onboarding yakunlandi!\n\n"
                "✅ Til va valyuta sozlandi\n"
                "✅ Daromad kiritildi\n"
                "✅ Maqsad qo'yildi\n\n"
                "🤖 AI byudjet tavsiyalari mavjud!\n"
                "🏠 Asosiy menyudan foydalanishingiz mumkin!"
            )
        else:
            completion_text = (
                "🎉 Onboarding yakunlandi!\n\n"
                "✅ Til va valyuta sozlandi\n"
                "✅ Maqsad qo'yildi\n\n"
                "🏠 Asosiy menyudan foydalanishingiz mumkin!"
            )
        
        await update.message.reply_text(completion_text, reply_markup=ReplyKeyboardRemove())
        return await show_main_menu(update)
    except sqlite3.Error as e:
        logger.exception(f"Database error in onboarding_goal: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def show_main_menu(update):
    """Show main menu with reply keyboard"""
    from main import MAIN_MODULES_KEYBOARD
    from utils import get_user_language
    
    user_id = getattr(update.message.from_user, 'id', None)
    language = get_user_language(user_id) if user_id else "uz"
    keyboard = MAIN_MODULES_KEYBOARD.get(language, MAIN_MODULES_KEYBOARD["uz"])
    
    welcome_text = (
        "🎉 Tabriklaymiz! Onboarding yakunlandi!\n\n"
        "🏠 Asosiy menyudan foydalanishingiz mumkin:\n\n"
        "💰 <b>Kirim/Chiqim</b> - moliyaviy harakatlarni qo'shish\n"
        "📊 <b>Balans/Tahlil</b> - moliyaviy holatni ko'rish\n"
        "🤖 <b>AI vositalar</b> - sun'iy intellekt yordamida\n"
        "⚙️ <b>Sozlamalar/Yordam</b> - bot sozlamalari"
    )
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="HTML"
    )
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
        ONBOARDING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_language)],
        ONBOARDING_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_currency)],
        ONBOARDING_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_income)],
        ONBOARDING_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_goal)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
) 