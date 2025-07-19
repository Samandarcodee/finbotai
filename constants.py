"""
constants.py
Shared constants and functions for FinBot AI Telegram bot.
"""

# Constants
ASK_SUPPORT = 100
INCOME_AMOUNT, INCOME_NOTE = 101, 102
EXPENSE_AMOUNT, EXPENSE_NOTE = 201, 202

# MESSAGES constant
MESSAGES = {
    "uz": {
        "main_menu": "🏠 Bosh menyu",
        "main_menu_text": "🏠 <b>FinBot AI - Bosh menyu</b>\n\nQuyidagi funksiyalardan birini tanlang:\n\n💰 <b>Kirim/Chiqim</b> - Daromad va xarajatlarni kiritish\n📊 <b>Balans/Tahlil</b> - Moliyaviy holatni ko'rish\n🤖 <b>AI vositalar</b> - Aqlliroq moliyaviy maslahatlar\n⚙️ <b>Sozlamalar/Yordam</b> - Bot sozlamalari va yordam",
        "invalid_choice": "❌ Noto'g'ri tanlov. Qaytadan tanlang.",
        "error_soft": "🤖 Xatolik yuz berdi, lekin qo'rqmang, jamoamiz bu haqida xabardor.",
        "loading": "🧠 AI hisob-kitob qilmoqda...",
        "ai_error": "❌ AI xizmatida xatolik. Qaytadan urinib ko'ring.",
        "welcome": "👋 Assalomu alaykum, {name}!\n\n💡 Moliyaviy kelajagingizni o'zingiz nazorat qilmoqchimisiz?\nMen bu yo'lda sizga yordam beruvchi FinBot AI 🤖man.\n\n✅ Har bir so'mingizni to'g'ri boshqarish\n✅ Tejash imkoniyatlarini topish\n✅ Moliyaviy erkinlik sari odimlash – men bilan birga bo'ladi.\n\n🎯 Boshlang'ich sozlash (2-4 bosqich):\n1️⃣ Tilni tanlash (majburiy)\n2️⃣ Valyutani tanlash (majburiy)\n3️⃣ Oylik daromadingizni kiritish (ixtiyoriy)\n4️⃣ Tejash maqsadingizni qo'yish (ixtiyoriy)\n\n⚡️ Barchasi atigi 2 daqiqa vaqt oladi.",
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
        "main_menu_text": "🏠 <b>FinBot AI - Главное меню</b>\n\nВыберите одну из функций:\n\n💰 <b>Доходы/Расходы</b> - Ввод доходов и расходов\n📊 <b>Баланс/Анализ</b> - Просмотр финансового состояния\n🤖 <b>AI инструменты</b> - Умные финансовые советы\n⚙️ <b>Настройки/Помощь</b> - Настройки бота и помощь",
        "invalid_choice": "❌ Неправильный выбор. Выберите снова.",
        "error_soft": "🤖 Произошла ошибка, но не волнуйтесь, наша команда в курсе.",
        "loading": "🧠 AI вычисляет...",
        "ai_error": "❌ Ошибка в AI сервисе. Попробуйте снова.",
        "welcome": "👋 Здравствуйте, {name}!\n\n💡 Хотите контролировать свое финансовое будущее?\nЯ FinBot AI, который поможет вам в этом 🤖\n\n✅ Правильно управлять каждой копейкой\n✅ Находить возможности для экономии\n✅ Двигаться к финансовой свободе – вместе со мной.\n\n🎯 Начальная настройка (2-4 этапа):\n1️⃣ Выбор языка (обязательно)\n2️⃣ Выбор валюты (обязательно)\n3️⃣ Ввод месячного дохода (по желанию)\n4️⃣ Постановка цели экономии (по желанию)\n\n⚡️ Все займет всего 2 минуты.",
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
        "main_menu_text": "🏠 <b>FinBot AI - Main Menu</b>\n\nSelect one of the functions:\n\n💰 <b>Income/Expense</b> - Enter income and expenses\n📊 <b>Balance/Analysis</b> - View financial status\n🤖 <b>AI Tools</b> - Smart financial advice\n⚙️ <b>Settings/Help</b> - Bot settings and help",
        "invalid_choice": "❌ Invalid choice. Please select again.",
        "error_soft": "🤖 An error occurred, but don't worry, our team is aware.",
        "loading": "🧠 AI is calculating...",
        "ai_error": "❌ Error in AI service. Please try again.",
        "welcome": "👋 Hello, {name}!\n\n💡 Want to control your financial future?\nI'm FinBot AI who will help you with this 🤖\n\n✅ Manage every penny correctly\n✅ Find savings opportunities\n✅ Move towards financial freedom – together with me.\n\n🎯 Initial setup (2-4 steps):\n1️⃣ Language selection (required)\n2️⃣ Currency selection (required)\n3️⃣ Enter your monthly income (optional)\n4️⃣ Set your savings goal (optional)\n\n⚡️ Everything takes just 2 minutes.",
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