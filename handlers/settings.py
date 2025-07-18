"""
handlers/settings.py
Handles user settings logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_db_connection, get_user_settings, DB_PATH
from loguru import logger
from telegram.constants import ParseMode

# Import start function from start handler
from handlers.start import start

# MESSAGES constant
MESSAGES = {
    "uz": {
        "main_menu": "🏠 Bosh menyu",
        "invalid_choice": "❌ Noto'g'ri tanlov. Qaytadan tanlang.",
        "choose_currency": "Valyutani tanlang:",
        "currency_changed": "✅ Valyuta o'zgartirildi: {currency}",
        "data_deleted": "✅ Barcha ma'lumotlar o'chirildi.",
        "delete_confirm": "⚠️ Bu amal barcha ma'lumotlaringizni o'chiradi. Tasdiqlaysizmi?",
        "currencies": ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"]
    },
    "ru": {
        "main_menu": "🏠 Главное меню",
        "invalid_choice": "❌ Неверный выбор. Пожалуйста, выберите снова.",
        "currencies": ["💰 Изменить валюту", "💰 Change currency"]
    },
    "en": {
        "main_menu": "🏠 Main menu",
        "invalid_choice": "❌ Invalid choice. Please try again.",
        "currencies": ["💰 Change currency"]
    }
}

async def show_settings(update: Update, user_id: int):
    """Show user settings"""
    try:
        settings = get_user_settings(user_id)
        currency = settings['currency']
        language = settings['language']
        
        text = (
            "⚙️ <b>SOZLAMALAR</b>\n\n"
            f"💰 <b>Valyuta:</b> {currency}\n"
            f"🌐 <b>Til:</b> {language}\n\n"
            "Sozlamalarni o'zgartirish uchun tugmalardan birini bosing:"
        )
        
        keyboard = [
            ["💰 Valyutani o'zgartirish"],
            ["🗑️ Ma'lumotlarni o'chirish"],
            ["🔙 Orqaga"]
        ]
        
        if update.message:
            await update.message.reply_text(
                text, 
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.exception(f"Settings error: {e}")
        if update.message:
            await update.message.reply_text("❌ Sozlamalarni ko'rishda xatolik.")

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu selection"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if text.lower() in ["/start", "/cancel", "🏠 Bosh menyu", "🏠 Bosh menyu"]:
        return await start(update, context)
    elif text in ["💰 Valyutani o'zgartirish", "💰 Изменить валюту", "💰 Change currency"]:
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in MESSAGES["uz"]["currencies"]] + [[MESSAGES["uz"]["main_menu"]]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(MESSAGES["uz"]["choose_currency"], reply_markup=reply_markup)
        return 9
    elif text == "🗑️ Ma'lumotlarni o'chirish":
        await update.message.reply_text(
            MESSAGES["uz"]["delete_confirm"],
            reply_markup=ReplyKeyboardMarkup([
                ["✅ Ha, o'chir"],
                ["❌ Yo'q, bekor qil"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return 7
    else:
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"])
        return 5

async def currency_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    currency_map = {
        "🇺🇿 So'm": "so'm",
        "💵 Dollar": "USD",
        "💶 Euro": "EUR",
        "🇺🇿 Сум": "so'm",
        "💵 Доллар": "USD",
        "💶 Евро": "EUR",
        "🇺🇿 So'm": "so'm",
        "💵 Dollar": "USD",
        "💶 Euro": "EUR"
    }
    
    if text.lower() in ["/start", "/cancel", "🏠 Bosh menyu", "🏠 Bosh menyu"]:
        return await start(update, context)
    elif text in currency_map:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE user_settings SET currency = ? WHERE user_id = ?", (currency_map[text], user_id))
            conn.commit()
            conn.close()
            await update.message.reply_text(MESSAGES["uz"]["currency_changed"].format(currency=text))
            return await show_settings(update, user_id)
        except sqlite3.Error as e:
            logger.exception(f"Currency update error: {e}")
            await update.message.reply_text("❌ Valyuta o'zgartirishda xatolik.")
            return ConversationHandler.END
    else:
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in MESSAGES["uz"]["currencies"]] + [[MESSAGES["uz"]["main_menu"]]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"], reply_markup=reply_markup)
        return 9

async def delete_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data deletion confirmation"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    if text == "✅ Ha, o'chir":
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Delete all user data
            c.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(MESSAGES["uz"]["data_deleted"])
            return ConversationHandler.END
        except sqlite3.Error as e:
            logger.exception(f"Data deletion error: {e}")
            await update.message.reply_text("❌ Ma'lumotlarni o'chirishda xatolik.")
            return ConversationHandler.END
    elif text == "❌ Yo'q, bekor qil":
        await update.message.reply_text("❌ Ma'lumotlarni o'chirish bekor qilindi.")
        return await show_settings(update, user_id)
    else:
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"])
        return 7 