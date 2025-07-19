# utils.py
# Shared utility functions for FinBot AI

import sqlite3
from db import get_db_connection

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

def get_navigation_keyboard(extra_buttons=None):
    """Return a keyboard with extra buttons and navigation buttons."""
    base = ["🔙 Orqaga", "🏠 Bosh menyu"]
    if extra_buttons:
        return [extra_buttons] + [base]
    return [base] 