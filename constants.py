"""
constants.py
Shared constants and functions for FinBot AI Telegram bot.
"""

# Constants
ASK_SUPPORT = 100
INCOME_AMOUNT, INCOME_NOTE = 101, 102
EXPENSE_AMOUNT, EXPENSE_NOTE = 201, 202

# Multi-language messages
MESSAGES = {
    "uz": {
        "start_text": "Assalomu alaykum! FinBot AI ga xush kelibsiz.",
        "settings_text": "⚙️ Sozlamalar bo'limiga xush kelibsiz.",
        "language_changed": "✅ Til muvaffaqiyatli {language} ga o'zgartirildi.",
        "currency_changed": "✅ Valyuta muvaffaqiyatli {currency} ga o'zgartirildi.",
        "invalid_choice": "❌ Noto'g'ri tanlov. Iltimos, ro'yxatdan tanlang:",
        "db_connection_error": "❌ Baza bilan ulanishda xatolik. Keyinroq urinib ko'ring.",
        "language_change_error": "❌ Tilni o'zgartirishda xatolik. Qayta urinib ko'ring:",
        "currency_change_error": "❌ Valyuta o'zgartirishda xatolik. Qayta urinib ko'ring:",
        "user_not_found": "❌ Foydalanuvchi topilmadi.",
        "settings_error": "❌ Sozlamalarni ko'rishda xatolik.",
        "notifications_on": "✅ Bildirishnomalar yoqildi.",
        "notifications_off": "❌ Bildirishnomalar o'chirildi.",
        "auto_reports_on": "✅ Avtomatik hisobotlar yoqildi.",
        "auto_reports_off": "❌ Avtomatik hisobotlar o'chirildi.",
        "export_success": "✅ Ma'lumotlar muvaffaqiyatli eksport qilindi.",
        "backup_success": "✅ Zaxira nusxasi muvaffaqiyatli yaratildi.",
        "data_deleted": "✅ Barcha ma'lumotlar o'chirildi.",
        "select_language": "Tilni tanlang:",
        "select_currency": "Valyutani tanlang:",
        "settings_title": "⚙️ SOZLAMALAR",
        "settings_description": "Sozlamalarni o'zgartirish uchun tugmalardan birini bosing:",
        "error_soft": "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
    },
    "ru": {
        "start_text": "Здравствуйте! Добро пожаловать в FinBot AI.",
        "settings_text": "⚙️ Добро пожаловать в настройки.",
        "language_changed": "✅ Язык успешно изменен на {language}.",
        "currency_changed": "✅ Валюта успешно изменена на {currency}.",
        "invalid_choice": "❌ Неверный выбор. Пожалуйста, выберите из списка:",
        "db_connection_error": "❌ Ошибка подключения к базе данных. Попробуйте позже.",
        "language_change_error": "❌ Ошибка изменения языка. Попробуйте еще раз:",
        "currency_change_error": "❌ Ошибка изменения валюты. Попробуйте еще раз:",
        "user_not_found": "❌ Пользователь не найден.",
        "settings_error": "❌ Ошибка просмотра настроек.",
        "notifications_on": "✅ Уведомления включены.",
        "notifications_off": "❌ Уведомления отключены.",
        "auto_reports_on": "✅ Автоматические отчеты включены.",
        "auto_reports_off": "❌ Автоматические отчеты отключены.",
        "export_success": "✅ Данные успешно экспортированы.",
        "backup_success": "✅ Резервная копия успешно создана.",
        "data_deleted": "✅ Все данные удалены.",
        "select_language": "Выберите язык:",
        "select_currency": "Выберите валюту:",
        "settings_title": "⚙️ НАСТРОЙКИ",
        "settings_description": "Нажмите одну из кнопок для изменения настроек:",
        "error_soft": "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
    },
    "en": {
        "start_text": "Hello! Welcome to FinBot AI.",
        "settings_text": "⚙️ Welcome to settings.",
        "language_changed": "✅ Language successfully changed to {language}.",
        "currency_changed": "✅ Currency successfully changed to {currency}.",
        "invalid_choice": "❌ Invalid choice. Please select from the list:",
        "db_connection_error": "❌ Database connection error. Please try again later.",
        "language_change_error": "❌ Language change error. Please try again:",
        "currency_change_error": "❌ Currency change error. Please try again:",
        "user_not_found": "❌ User not found.",
        "settings_error": "❌ Error viewing settings.",
        "notifications_on": "✅ Notifications enabled.",
        "notifications_off": "❌ Notifications disabled.",
        "auto_reports_on": "✅ Auto reports enabled.",
        "auto_reports_off": "❌ Auto reports disabled.",
        "export_success": "✅ Data successfully exported.",
        "backup_success": "✅ Backup successfully created.",
        "data_deleted": "✅ All data deleted.",
        "select_language": "Select language:",
        "select_currency": "Select currency:",
        "settings_title": "⚙️ SETTINGS",
        "settings_description": "Click one of the buttons to change settings:",
        "error_soft": "❌ An error occurred. Please try again."
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

# Universal navigation messages
NAVIGATION_MESSAGES = {
    "uz": {
        "back_button": "🔙 Orqaga",
        "main_menu_button": "🏠 Bosh menyu",
        "invalid_choice": "❌ Noto'g'ri tanlov. Qaytadan tanlang.",
        "navigation_error": "❌ Navigatsiya xatoligi. Bosh menyuga qaytamiz.",
        "loading": "⏳ Yuklanmoqda...",
        "error_occurred": "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring."
    },
    "ru": {
        "back_button": "🔙 Назад",
        "main_menu_button": "🏠 Главное меню",
        "invalid_choice": "❌ Неверный выбор. Выберите снова.",
        "navigation_error": "❌ Ошибка навигации. Возвращаемся в главное меню.",
        "loading": "⏳ Загрузка...",
        "error_occurred": "❌ Произошла ошибка. Попробуйте снова."
    },
    "en": {
        "back_button": "🔙 Back",
        "main_menu_button": "🏠 Main Menu",
        "invalid_choice": "❌ Invalid choice. Please select again.",
        "navigation_error": "❌ Navigation error. Returning to main menu.",
        "loading": "⏳ Loading...",
        "error_occurred": "❌ An error occurred. Please try again."
    }
}

NAV_COMMANDS = ["/start", "/cancel", "/help", "🏠 Bosh menyu", "🔙 Orqaga"]
SETTINGS_CURRENCY = 0
SETTINGS_LANGUAGE = 1
SETTINGS_DELETE = 2

# Language and Currency Options
LANGUAGE_OPTIONS = ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇺🇸 English"]
CURRENCY_OPTIONS = ["🇺🇿 So'm", "💵 Dollar", "💶 Euro", "🇷🇺 Rubl", "🇰🇿 Tenge", "🇰🇬 Som", "🇹🇷 Lira", "🇨🇳 Yuan", "🇯🇵 Yen"]

# Language and Currency mapping
LANGUAGE_MAP = {
    "🇺🇿 O'zbekcha": "uz",
    "🇷🇺 Русский": "ru", 
    "🇺🇸 English": "en"
}

CURRENCY_MAP = {
    "🇺🇿 So'm": "UZS",
    "💵 Dollar": "USD",
    "💶 Euro": "EUR",
    "🇷🇺 Rubl": "RUB",
    "🇰🇿 Tenge": "KZT",
    "🇰🇬 Som": "KGS",
    "🇹🇷 Lira": "TRY",
    "🇨🇳 Yuan": "CNY",
    "🇯🇵 Yen": "JPY"
}

def get_message(key, user_id=None, **kwargs):
    """Get message in user's language"""
    from utils import get_user_language
    language = get_user_language(user_id) if user_id else "uz"
    message = MESSAGES.get(language, MESSAGES["uz"]).get(key, MESSAGES["uz"].get(key, key))
    return message.format(**kwargs) if kwargs else message

def get_keyboard(user_id):
    """Get keyboard with navigation buttons"""
    from utils import get_user_language
    language = get_user_language(user_id)
    
    if language == "ru":
        return [
            ["💰 Доход/Расход", "📊 Баланс/Анализ"],
            ["🤖 AI инструменты", "⚙️ Настройки/Помощь"]
        ]
    elif language == "en":
        return [
            ["💰 Income/Expense", "📊 Balance/Analysis"],
            ["🤖 AI Tools", "⚙️ Settings/Help"]
        ]
    else:  # uz
        return [
            ["💰 Kirim/Chiqim", "📊 Balans/Tahlil"],
            ["🤖 AI vositalar", "⚙️ Sozlamalar/Yordam"]
        ]

def get_navigation_buttons(language="uz"):
    """Get universal navigation buttons"""
    return [
        NAVIGATION_MESSAGES[language]["back_button"],
        NAVIGATION_MESSAGES[language]["main_menu_button"]
    ] 