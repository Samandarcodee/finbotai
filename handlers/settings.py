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

# Import start function from start handler
from handlers.start import start

# Define constants locally to avoid circular import
SETTINGS_CURRENCY = 9
SETTINGS_LANGUAGE = 10
SETTINGS_DELETE = 7
# State constants for ConversationHandler
SETTINGS_MENU = 5

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

async def show_settings(update, context):
    """Show settings menu with improved navigation"""
    try:
        from constants import MESSAGES
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            await update.message.reply_text(MESSAGES["uz"]["user_not_found"])
            return ConversationHandler.END
            
        # Get fresh settings from database
        settings = get_user_settings(user_id)
        if not settings:
            await update.message.reply_text(MESSAGES["uz"]["user_not_found"])
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
            return SETTINGS_MENU  # Return the correct state
    except Exception as e:
        logger.exception(f"Settings error: {e}")
        if update.message:
            await update.message.reply_text("❌ Sozlamalarni ko'rishda xatolik.")

async def settings_handler(update, context):
    """Handle settings menu selection with enhanced options and navigation"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
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
        await update.message.reply_text("Valyutani tanlang:", reply_markup=reply_markup)
        return SETTINGS_CURRENCY
        
    elif text == "🌐 Tilni o'zgartirish":
        reply_markup = build_reply_keyboard([
            ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"]
        ], resize=True, one_time=True)
        await update.message.reply_text("Tilni tanlang:", reply_markup=reply_markup)
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
            "⚠️ <b>Eslatma:</b> Bu amal barcha ma'lumotlaringizni o'chiradi va qayta tiklanmaydi.\n\n"
            "Haqiqatan ham ma'lumotlaringizni o'chirmoqchimisiz?",
            reply_markup=build_reply_keyboard([
                ["✅ Ha, o'chir"],
                ["❌ Yo'q, bekor qil"]
            ], resize=True, one_time=True),
            parse_mode="HTML"
        )
        return SETTINGS_DELETE
        
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
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
        
        message = MESSAGES["uz"]["notifications_on"] if new_setting else MESSAGES["uz"]["notifications_off"]
        if update.message:
            await update.message.reply_text(message)
        
    except Exception as e:
        logger.exception(f"Toggle notifications error: {e}")
        if update.message:
            await update.message.reply_text("❌ Bildirishnomalar sozlamasida xatolik.")

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
        
        message = MESSAGES["uz"]["auto_reports_on"] if new_setting else MESSAGES["uz"]["auto_reports_off"]
        if update.message:
            await update.message.reply_text(message)
        
    except Exception as e:
        logger.exception(f"Toggle auto reports error: {e}")
        if update.message:
            await update.message.reply_text("❌ Avtomatik hisobotlar sozlamasida xatolik.")

async def export_user_data(update, context):
    """Export user data as JSON"""
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

async def create_backup(update, context):
    """Create backup of user data"""
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
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
    """Handle language selection with improved error handling"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text.strip()
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if not user_id:
        return ConversationHandler.END
    
    # Handle navigation commands first
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await show_settings(update, context)
    
    # Tilni aniqlash - to'g'ri matnlar bilan
    language = None
    if text == "🇺🇿 O'zbekcha":
        language = "uz"
    elif text == "🇷🇺 Русский":
        language = "ru"
    elif text == "🇺🇸 English":
        language = "en"
    
    if language is None:
        # Show language options again with better error message
        reply_markup = build_reply_keyboard([
            ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"],
            ["🔙 Orqaga", "🏠 Bosh menyu"]
        ], resize=True, one_time=True)
        await update.message.reply_text(
            "❌ Noto'g'ri tanlov. Faqat tilni tanlang:",
            reply_markup=reply_markup
        )
        return SETTINGS_LANGUAGE
    
    # DB ga saqlash
    try:
        logger.info(f"Starting language change for user {user_id} to {language}")
        
        conn = get_db_connection()
        if conn is None:
            logger.error(f"Database connection failed for user {user_id}")
            reply_markup = build_reply_keyboard([
                ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"],
                ["🔙 Orqaga", "🏠 Bosh menyu"]
            ], resize=True, one_time=True)
            await update.message.reply_text(
                "❌ Baza bilan ulanishda xatolik. Keyinroq urinib ko'ring.",
                reply_markup=reply_markup
            )
            return SETTINGS_LANGUAGE
        
        c = conn.cursor()
        logger.info(f"Database connection successful for user {user_id}")
        
        # Check if user exists in user_settings
        c.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
        user_exists = c.fetchone()
        logger.info(f"User exists check: {user_exists is not None}")
        
        if user_exists:
            # Update existing user settings
            logger.info(f"Updating existing user settings for user {user_id}")
            c.execute("UPDATE user_settings SET language = ? WHERE user_id = ?", (language, user_id))
        else:
            # Create new user settings record
            logger.info(f"Creating new user settings for user {user_id}")
            c.execute("""
                INSERT INTO user_settings (user_id, language, currency, notifications, auto_reports) 
                VALUES (?, ?, 'UZS', 1, 0)
            """, (user_id, language))
        
        conn.commit()
        conn.close()
        logger.info(f"Language change successful for user {user_id}")
        
        # Yangi tilda xabar yuborish
        from constants import MESSAGES
        msg = MESSAGES[language]["language_changed"].format(language=text)
        await update.message.reply_text(msg)
        # Bosh menyuni yangi til bilan ko'rsatish
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
        
    except Exception as e:
        logger.exception(f"Language change error for user {user_id}: {e}")
        reply_markup = build_reply_keyboard([
            ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"],
            ["🔙 Orqaga", "🏠 Bosh menyu"]
        ], resize=True, one_time=True)
        await update.message.reply_text(
            "❌ Tilni o'zgartirishda xatolik. Qayta urinib ko'ring:",
            reply_markup=reply_markup
        )
        return SETTINGS_LANGUAGE

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
            return await show_settings(update, context)
        except sqlite3.Error as e:
            logger.exception(f"Currency update error: {e}")
            await update.message.reply_text("❌ Valyuta o'zgartirishda xatolik.")
            return ConversationHandler.END
    else:
        # Show currency options again with better error message
        reply_markup = build_reply_keyboard([
            ["🇺🇿 So'm", "💵 Dollar", "💶 Euro"],
            ["🇷🇺 Rubl", "🇰🇿 Tenge", "🇰🇬 Som"],
            ["🇹🇷 Lira", "🇨🇳 Yuan", "🇯🇵 Yen"],
            ["🔙 Orqaga", "🏠 Bosh menyu"]
        ], resize=True, one_time=True)
        await update.message.reply_text(
            "❌ Noto'g'ri tanlov. Faqat valyutani tanlang:",
            reply_markup=reply_markup
        )
        return SETTINGS_CURRENCY

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
        return await show_settings(update, context)
    else:
        # Show deletion confirmation options again with better error message
        await update.message.reply_text(
            "❌ Noto'g'ri tanlov. Faqat quyidagilardan birini tanlang:",
            reply_markup=build_reply_keyboard([
                ["✅ Ha, o'chir"],
                ["❌ Yo'q, bekor qil"]
            ], resize=True, one_time=True)
        )
        return SETTINGS_DELETE 