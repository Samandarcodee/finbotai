"""
handlers/settings.py
Handles user settings logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_db_connection, get_user_settings, DB_PATH
from loguru import logger
from telegram.constants import ParseMode
import json
from datetime import datetime
from utils import get_navigation_keyboard, build_reply_keyboard
from constants import get_message, SETTINGS_CURRENCY, SETTINGS_LANGUAGE, SETTINGS_DELETE
# MESSAGES constant
# Define constants locally to avoid circular import

# Import start function from start handler
from handlers.start import start
import os

async def show_settings(update, context):
    """Show settings menu with improved navigation"""
    try:
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        settings = get_user_settings(user_id)
        if not settings:
            await update.message.reply_text(get_message("user_not_found", user_id))
            return ConversationHandler.END
        currency = settings.get('currency', 'UZS')
        language = settings.get('language', 'uz')
        notifications = settings.get('notifications', True)
        auto_reports = settings.get('auto_reports', False)
        notif_status = "✅ Yoqilgan" if notifications else "❌ O'chirilgan"
        auto_status = "✅ Yoqilgan" if auto_reports else "❌ O'chirilgan"
        text = (
            f"⚙️ <b>SOZLAMALAR</b>\n\n"
            f"💰 Valyuta: {currency}\n"
            f"🌐 Til: {language}\n"
            f"🔔 Bildirishnomalar: {notif_status}\n"
            f"📊 Avtomatik hisobotlar: {auto_status}\n\n"
            "Sozlamalarni o'zgartirish uchun tugmalardan birini bosing:"
        )
        keyboard = [
            ["💰 Valyutani o'zgartirish", "🌐 Tilni o'zgartirish"],
            ["🔔 Bildirishnomalar", "📊 Avtomatik hisobotlar"],
            ["📤 Ma'lumotlarni eksport qilish", "💾 Zaxira nusxasi"],
            ["🗑️ Ma'lumotlarni o'chirish"],
            ["🏠 Bosh menyu"]
        ]
        if update.message:
            await update.message.reply_text(
                text, 
                reply_markup=build_reply_keyboard(keyboard, resize=True, one_time=True, add_navigation=False),
                parse_mode=ParseMode.HTML
            )
            return 5  # Return the main settings menu state
    except Exception as e:
        logger.exception(f"Settings error: {e}")
        if update.message:
            await update.message.reply_text(get_message("error_general", user_id))

async def settings_handler(update, context):
    """Handle settings menu selection with enhanced options and navigation"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in [get_message("main_menu", user_id), "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await show_settings(update, context)
    
    # Handle settings options
    if text == "💰 Valyutani o'zgartirish":
        reply_markup = build_reply_keyboard([
            ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"],
            ["🇷🇺 Rubl", "🇰🇿 Tenge", "🇰🇬 Som"],
            ["🇹🇷 Lira", "🇨🇳 Yuan", "🇯🇵 Yen"]
        ], resize=True, one_time=True)
        await update.message.reply_text(get_message("currency_select", user_id), reply_markup=reply_markup)
        return SETTINGS_CURRENCY
        
    elif text == "🌐 Tilni o'zgartirish":
        reply_markup = build_reply_keyboard([
            ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"]
        ], resize=True, one_time=True)
        await update.message.reply_text(get_message("language_select", user_id), reply_markup=reply_markup)
        return SETTINGS_LANGUAGE
        
    elif text == "🔔 Bildirishnomalar":
        await toggle_notifications(update, context)
        return await show_settings(update, context)
        
    elif text == "📊 Avtomatik hisobotlar":
        await toggle_auto_reports(update, context)
        return await show_settings(update, context)
        
    elif text == "📤 Ma'lumotlarni eksport qilish":
        await export_user_data(update, context)
        return await show_settings(update, context)
        
    elif text == "💾 Zaxira nusxasi":
        await create_backup(update, context)
        return await show_settings(update, context)
        
    elif text == "🗑️ Ma'lumotlarni o'chirish":
        await update.message.reply_text(
            get_message("delete_confirm", user_id),
            reply_markup=build_reply_keyboard([
                ["✅ Ha, o'chir"],
                ["❌ Yo'q, bekor qil"]
            ], resize=True, one_time=True),
            parse_mode="HTML"
        )
        return SETTINGS_DELETE
        
    else:
        await update.message.reply_text(get_message("invalid_choice", user_id))
        return await show_settings(update, context)

async def toggle_notifications(update, context):
    """Toggle notifications setting"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current setting
        c.execute("SELECT notifications FROM user_settings WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        current_setting = result[0] if result else True
        
        # Toggle setting
        new_setting = not current_setting
        c.execute("UPDATE user_settings SET notifications = ? WHERE user_id = ?", (new_setting, user_id))
        conn.commit()
        conn.close()
        
        message = "Bildirishnomalar yoqildi." if new_setting else "Bildirishnomalar o'chirildi."
        if update.message:
            await update.message.reply_text(message)
        
    except Exception as e:
        logger.exception(f"Toggle notifications error: {e}")
        if update.message:
            await update.message.reply_text(get_message("error_general", user_id))

async def toggle_auto_reports(update, context):
    """Toggle auto reports setting"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current setting
        c.execute("SELECT auto_reports FROM user_settings WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        current_setting = result[0] if result else False
        
        # Toggle setting
        new_setting = not current_setting
        c.execute("UPDATE user_settings SET auto_reports = ? WHERE user_id = ?", (new_setting, user_id))
        conn.commit()
        conn.close()
        
        message = "Avtomatik hisobotlar yoqildi." if new_setting else "Avtomatik hisobotlar o'chirildi."
        if update.message:
            await update.message.reply_text(message)
        
    except Exception as e:
        logger.exception(f"Toggle auto reports error: {e}")
        if update.message:
            await update.message.reply_text(get_message("error_general", user_id))

async def export_user_data(update, context):
    """Export user data as JSON and send to user"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Get user data
        c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = c.fetchall()
        c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        settings = c.fetchone()
        c.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
        goals = c.fetchall()
        conn.close()
        # Prepare export data
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "transactions": transactions,
            "settings": settings,
            "goals": goals
        }
        filename = f"finbot_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        if update.message:
            await update.message.reply_text(get_message("data_exported", user_id))
            with open(filename, 'rb') as f:
                await update.message.reply_document(f, filename=filename)
        os.remove(filename)
    except Exception as e:
        logger.exception(f"Export data error: {e}")
        if update.message:
            await update.message.reply_text(get_message("error_export_data", user_id))

async def create_backup(update, context):
    """Create backup of user data and send to user"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = c.fetchall()
        c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        settings = c.fetchone()
        conn.close()
        backup_summary = {
            "user_id": user_id,
            "backup_date": datetime.now().isoformat(),
            "total_transactions": len(transactions),
            "settings": settings
        }
        filename = f"finbot_backup_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_summary, f, ensure_ascii=False, indent=2)
        if update.message:
            await update.message.reply_text(get_message("backup_created", user_id))
            with open(filename, 'rb') as f:
                await update.message.reply_document(f, filename=filename)
        os.remove(filename)
    except Exception as e:
        logger.exception(f"Backup error: {e}")
        if update.message:
            await update.message.reply_text(get_message("error_backup", user_id))

async def language_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if not user_id:
        return ConversationHandler.END
    # Tilni aniqlash
    if "O'zbek" in text or "🇺🇿" in text:
        language = "uz"
    elif "Русский" in text or "🇷🇺" in text:
        language = "ru"
    elif "English" in text or "🇺🇸" in text:
        language = "en"
    else:
        language = "uz"
    # DB ga saqlash
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE user_settings SET language = ? WHERE user_id = ?", (language, user_id))
        conn.commit()
        conn.close()
        # Yangi tilda xabar yuborish
        from constants import MESSAGES
        msg = MESSAGES[language]["language_changed"].format(language=text)
        await update.message.reply_text(msg)
        # Bosh menyuni yangi til bilan ko'rsatish
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    except Exception as e:
        logger.exception(f"Language change error: {e}")
        await update.message.reply_text(get_message("error_language_change", user_id))
        return ConversationHandler.END

async def currency_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    currency_map = {
        "🇺🇿 So'm": "UZS",
        "💵 Dollar": "USD",
        "💶 Euro": "EUR",
        "🇷🇺 Rubl": "RUB",
        "🇰🇿 Tenge": "KZT",
        "🇰🇬 Som": "KGS",
        "🇹🇷 Lira": "TRY",
        "🇨🇳 Yuan": "CNY",
        "🇯🇵 Yen": "JPY",
        "🇺🇿 Сум": "UZS",
        "💵 Доллар": "USD",
        "💶 Евро": "EUR",
        "🇷🇺 Рубль": "RUB",
        "🇰🇿 Тенге": "KZT",
        "🇰🇬 Сом": "KGS",
        "🇹🇷 Лира": "TRY",
        "🇨🇳 Юань": "CNY",
        "🇯🇵 Иена": "JPY"
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
            await update.message.reply_text(get_message("currency_changed", user_id))
            return await show_settings(update, context)
        except sqlite3.Error as e:
            logger.exception(f"Currency update error: {e}")
            await update.message.reply_text(get_message("error_currency_change", user_id))
            return ConversationHandler.END
    else:
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in ["🇺🇿 So'm", "💵 Dollar", "💶 Euro", "🇷🇺 Rubl", "🇰🇿 Tenge", "🇰🇬 Som", "🇹🇷 Lira", "🇨🇳 Yuan", "🇯🇵 Yen"]] + [[get_message("main_menu", user_id)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(get_message("incorrect_currency_selection", user_id), reply_markup=reply_markup)
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
            
            await update.message.reply_text(get_message("data_deleted", user_id))
            return ConversationHandler.END
        except sqlite3.Error as e:
            logger.exception(f"Data deletion error: {e}")
            await update.message.reply_text(get_message("error_delete_data", user_id))
            return ConversationHandler.END
    elif text == "❌ Yo'q, bekor qil":
        await update.message.reply_text(get_message("data_deletion_cancelled", user_id))
        return await show_settings(update, context)
    else:
        await update.message.reply_text(get_message("incorrect_delete_selection", user_id))
        return 7 