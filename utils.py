# utils.py
# Shared utility functions for FinBot AI

import sqlite3
from db import get_db_connection
from constants import NAV_COMMANDS

# Currency symbols
CURRENCY_SYMBOLS = {
    "UZS": "so'm",
    "USD": "$",
    "EUR": "€",
    "RUB": "₽",
    "KZT": "₸",
    "KGS": "с",
    "TRY": "₺",
    "CNY": "¥",
    "JPY": "¥"
}

def get_user_language(user_id):
    """Get user language from database"""
    try:
        conn = get_db_connection()
        if conn is None:
            return "uz"  # Default to Uzbek
        
        c = conn.cursor()
        c.execute("SELECT language FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return row[0]
        return "uz"  # Default to Uzbek
    except Exception:
        return "uz"  # Default to Uzbek

def get_user_currency(user_id):
    """Get user currency from database"""
    try:
        conn = get_db_connection()
        if conn is None:
            return "UZS"  # Default to Uzbek som
        
        c = conn.cursor()
        c.execute("SELECT currency FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return row[0]
        return "UZS"  # Default to Uzbek som
    except Exception:
        return "UZS"  # Default to Uzbek som

def format_amount(amount, user_id):
    """Format amount with user's currency symbol"""
    currency = get_user_currency(user_id)
    symbol = CURRENCY_SYMBOLS.get(currency, "so'm")
    
    # Format number with spaces for thousands
    formatted_amount = "{:,}".format(amount).replace(",", " ")
    
    if currency == "UZS":
        return f"{formatted_amount} {symbol}"
    elif currency == "RUB":
        return f"{formatted_amount} {symbol}"
    elif currency == "USD":
        return f"{symbol}{formatted_amount}"
    else:
        return f"{formatted_amount} {symbol}" 

def validate_amount(text):
    """Validate and parse an amount string. Returns (amount, error)."""
    try:
        cleaned = text.replace(' ', '').replace(',', '').replace("'", '').replace('so\'m', '').replace('сум', '').replace('UZS', '').replace('$', '').replace('USD', '').replace('€', '').replace('EUR', '').replace('₽', '').replace('RUB', '').replace('₸', '').replace('KZT', '').replace('с', '').replace('KGS', '').replace('₺', '').replace('TRY', '').replace('¥', '').replace('CNY', '').replace('JPY', '').strip()
        if not cleaned.isdigit():
            return None, "Noto'g'ri miqdor! Masalan: 5 000 000"
        amount = int(cleaned)
        if amount <= 0:
            return None, "Miqdor 0 dan katta bo'lishi kerak!"
        return amount, None
    except Exception:
        return None, "Noto'g'ri miqdor! Masalan: 5 000 000"

def get_navigation_keyboard():
    """Return navigation buttons as a single row."""
    return [["🔙 Orqaga", "🏠 Bosh menyu"]]


def build_reply_keyboard(buttons, resize=True, one_time=False, add_navigation=True):
    """Universal reply keyboard builder. Navigation tugmalari faqat bir marta va to'g'ri formatda chiqadi."""
    from telegram import ReplyKeyboardMarkup
    keyboard = []
    # buttons ni to'g'ri formatga keltiramiz
    if buttons:
        if isinstance(buttons[0], list):
            keyboard.extend(buttons)
        else:
            keyboard.append(buttons)
    if add_navigation:
        # Navigation tugmalari dublikat bo'lmasligi uchun tekshiramiz
        nav = ["🔙 Orqaga", "🏠 Bosh menyu"]
        if not any(set(nav) <= set(row) for row in keyboard):
            keyboard += get_navigation_keyboard()
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=resize, one_time_keyboard=one_time) 

def is_navigation_command(text):
    return text.strip() in NAV_COMMANDS 