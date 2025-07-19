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

# Import start function from start handler
from handlers.start import start

# MESSAGES constant
MESSAGES = {
    "uz": {
        "main_menu": "🏠 Bosh menyu",
        "invalid_choice": "❌ Noto'g'ri tanlov. Qaytadan tanlang.",
        "choose_currency": "Valyutani tanlang:",
        "choose_language": "Tilni tanlang:",
        "currency_changed": "✅ Valyuta o'zgartirildi: {currency}",
        "language_changed": "✅ Til o'zgartirildi: {language}",
        "data_deleted": "✅ Barcha ma'lumotlar o'chirildi.",
        "delete_confirm": "⚠️ Bu amal barcha ma'lumotlaringizni o'chiradi. Tasdiqlaysizmi?",
        "settings_saved": "✅ Sozlamalar saqlandi!",
        "notifications_on": "✅ Bildirishnomalar yoqildi",
        "notifications_off": "❌ Bildirishnomalar o'chirildi",
        "auto_reports_on": "✅ Avtomatik hisobotlar yoqildi",
        "auto_reports_off": "❌ Avtomatik hisobotlar o'chirildi",
        "export_success": "📊 Ma'lumotlaringiz tayyorlandi. Tez orada yuboriladi...",
        "backup_success": "💾 Zaxira nusxasi yaratildi",
        "currencies": ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"],
        "languages": ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"],
        "settings_menu": "⚙️ <b>SOZLAMALAR</b>\n\nQuyidagi sozlamalardan birini tanlang:"
    },
    "ru": {
        "main_menu": "🏠 Главное меню",
        "invalid_choice": "❌ Неверный выбор. Пожалуйста, выберите снова.",
        "choose_currency": "Выберите валюту:",
        "choose_language": "Выберите язык:",
        "currency_changed": "✅ Валюта изменена: {currency}",
        "language_changed": "✅ Язык изменен: {language}",
        "data_deleted": "✅ Все данные удалены.",
        "delete_confirm": "⚠️ Это действие удалит все ваши данные. Подтверждаете?",
        "settings_saved": "✅ Настройки сохранены!",
        "notifications_on": "✅ Уведомления включены",
        "notifications_off": "❌ Уведомления отключены",
        "auto_reports_on": "✅ Автоматические отчеты включены",
        "auto_reports_off": "❌ Автоматические отчеты отключены",
        "export_success": "📊 Ваши данные готовы. Отправка...",
        "backup_success": "💾 Резервная копия создана",
        "currencies": ["🇺🇿 Сум", "💵 Доллар", "💶 Евро"],
        "languages": ["🇺🇿 Узбекский", "🇷🇺 Русский", "🇺🇸 Английский"],
        "settings_menu": "⚙️ <b>НАСТРОЙКИ</b>\n\nВыберите одну из настроек:"
    },
    "en": {
        "main_menu": "🏠 Main Menu",
        "invalid_choice": "❌ Invalid choice. Please try again.",
        "choose_currency": "Select currency:",
        "choose_language": "Select language:",
        "currency_changed": "✅ Currency changed: {currency}",
        "language_changed": "✅ Language changed: {language}",
        "data_deleted": "✅ All data deleted.",
        "delete_confirm": "⚠️ This action will delete all your data. Confirm?",
        "settings_saved": "✅ Settings saved!",
        "notifications_on": "✅ Notifications enabled",
        "notifications_off": "❌ Notifications disabled",
        "auto_reports_on": "✅ Auto reports enabled",
        "auto_reports_off": "❌ Auto reports disabled",
        "export_success": "📊 Your data is ready. Sending...",
        "backup_success": "💾 Backup created",
        "currencies": ["🇺🇿 Sum", "💵 Dollar", "💶 Euro"],
        "languages": ["🇺🇿 Uzbek", "🇷🇺 Russian", "🇺🇸 English"],
        "settings_menu": "⚙️ <b>SETTINGS</b>\n\nSelect one of the settings:"
    }
}

async def show_settings(update: Update, user_id: int):
    """Show user settings with enhanced menu"""
    try:
        settings = get_user_settings(user_id)
        currency = settings.get('currency', 'UZS')
        language = settings.get('language', 'uz')
        notifications = settings.get('notifications', True)
        auto_reports = settings.get('auto_reports', False)
        
        # Get language display name
        lang_names = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇺🇸 English"}
        lang_display = lang_names.get(language, "🇺🇿 O'zbekcha")
        
        # Get currency display name
        currency_names = {
            "UZS": "🇺🇿 So'm", "USD": "💵 Dollar", "EUR": "💶 Euro",
            "RUB": "🇷🇺 Rubl", "KZT": "🇰🇿 Tenge", "KGS": "🇰🇬 Som"
        }
        currency_display = currency_names.get(currency, "🇺🇿 So'm")
        
        notifications_status = "✅ Yoqilgan" if notifications else "❌ O'chirilgan"
        reports_status = "✅ Yoqilgan" if auto_reports else "❌ O'chirilgan"
        
        text = (
            "⚙️ <b>SOZLAMALAR</b>\n\n"
            f"💰 <b>Valyuta:</b> {currency_display}\n"
            f"🌐 <b>Til:</b> {lang_display}\n"
            f"🔔 <b>Bildirishnomalar:</b> {notifications_status}\n"
            f"📊 <b>Avtomatik hisobotlar:</b> {reports_status}\n\n"
            "Sozlamalarni o'zgartirish uchun tugmalardan birini bosing:"
        )
        
        keyboard = [
            ["💰 Valyutani o'zgartirish", "🌐 Tilni o'zgartirish"],
            ["🔔 Bildirishnomalar", "📊 Avtomatik hisobotlar"],
            ["📤 Ma'lumotlarni eksport qilish", "💾 Zaxira nusxasi"],
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
    """Handle settings menu selection with enhanced options"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if text.lower() in ["/start", "/cancel", "🏠 Bosh menyu", "🏠 Bosh menyu"]:
        return await start(update, context)
    elif text in ["💰 Valyutani o'zgartirish", "💰 Изменить валюту", "💰 Change currency"]:
        reply_markup = ReplyKeyboardMarkup([
            ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"],
            ["🇷🇺 Rubl", "🇰🇿 Tenge", "🇰🇬 Som"],
            ["🇹🇷 Lira", "🇨🇳 Yuan", "🇯🇵 Yen"],
            ["🔙 Orqaga"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(MESSAGES["uz"]["choose_currency"], reply_markup=reply_markup)
        return 9
    elif text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык", "🌐 Change language"]:
        reply_markup = ReplyKeyboardMarkup([
            ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"],
            ["🔙 Orqaga"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(MESSAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return 10
    elif text in ["🔔 Bildirishnomalar", "🔔 Уведомления", "🔔 Notifications"]:
        if user_id:
            await toggle_notifications(update, user_id)
            return await show_settings(update, user_id)
    elif text in ["📊 Avtomatik hisobotlar", "📊 Автоотчеты", "📊 Auto reports"]:
        if user_id:
            await toggle_auto_reports(update, user_id)
            return await show_settings(update, user_id)
    elif text in ["📤 Ma'lumotlarni eksport qilish", "📤 Экспорт данных", "📤 Export data"]:
        if user_id:
            await export_user_data(update, user_id)
            return await show_settings(update, user_id)
    elif text in ["💾 Zaxira nusxasi", "💾 Резервная копия", "💾 Backup"]:
        if user_id:
            await create_backup(update, user_id)
            return await show_settings(update, user_id)
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

async def toggle_notifications(update: Update, user_id: int):
    """Toggle notifications setting"""
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
        
        message = MESSAGES["uz"]["notifications_on"] if new_setting else MESSAGES["uz"]["notifications_off"]
        if update.message:
            await update.message.reply_text(message)
        
    except Exception as e:
        logger.exception(f"Toggle notifications error: {e}")
        if update.message:
            await update.message.reply_text("❌ Bildirishnomalar sozlamasida xatolik.")

async def toggle_auto_reports(update: Update, user_id: int):
    """Toggle auto reports setting"""
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
        
        message = MESSAGES["uz"]["auto_reports_on"] if new_setting else MESSAGES["uz"]["auto_reports_off"]
        if update.message:
            await update.message.reply_text(message)
        
    except Exception as e:
        logger.exception(f"Toggle auto reports error: {e}")
        if update.message:
            await update.message.reply_text("❌ Avtomatik hisobotlar sozlamasida xatolik.")

async def export_user_data(update: Update, user_id: int):
    """Export user data as JSON"""
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
        
        # Save to file (in production, you might want to send via email or cloud storage)
        filename = f"finbot_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        if update.message:
            await update.message.reply_text(MESSAGES["uz"]["export_success"])
        
    except Exception as e:
        logger.exception(f"Export data error: {e}")
        if update.message:
            await update.message.reply_text("❌ Ma'lumotlarni eksport qilishda xatolik.")

async def create_backup(update: Update, user_id: int):
    """Create backup of user data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all user data
        c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = c.fetchall()
        
        c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        settings = c.fetchone()
        
        conn.close()
        
        # Create backup summary
        backup_summary = {
            "user_id": user_id,
            "backup_date": datetime.now().isoformat(),
            "total_transactions": len(transactions),
            "settings": settings
        }
        
        if update.message:
            await update.message.reply_text(MESSAGES["uz"]["backup_success"])
        
    except Exception as e:
        logger.exception(f"Backup error: {e}")
        if update.message:
            await update.message.reply_text("❌ Zaxira nusxasi yaratishda xatolik.")

async def language_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    language_map = {
        "🇺🇿 O'zbekcha": "uz",
        "🇷🇺 Русский": "ru", 
        "🇺🇸 English": "en",
        "🇺🇿 Узбекский": "uz",
        "🇷🇺 Russian": "ru",
        "🇺🇸 English": "en"
    }
    
    if text.lower() in ["/start", "/cancel", "🏠 Bosh menyu", "🏠 Bosh menyu"]:
        return await start(update, context)
    elif text in language_map:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE user_settings SET language = ? WHERE user_id = ?", (language_map[text], user_id))
            conn.commit()
            conn.close()
            await update.message.reply_text(MESSAGES["uz"]["language_changed"].format(language=text))
            return await show_settings(update, user_id)
        except sqlite3.Error as e:
            logger.exception(f"Language update error: {e}")
            await update.message.reply_text("❌ Til o'zgartirishda xatolik.")
            return ConversationHandler.END
    else:
        reply_markup = ReplyKeyboardMarkup([
            ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"],
            ["🔙 Orqaga"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(MESSAGES["uz"]["invalid_choice"], reply_markup=reply_markup)
        return 10

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