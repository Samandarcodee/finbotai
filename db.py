"""
db.py
Database helper functions for FinBot AI Telegram bot.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from loguru import logger

DB_PATH = os.getenv("DATABASE_URL", "finbot.db")

def init_db():
    """Initialize database with all required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        user_id INTEGER,
                        type TEXT,
                        amount INTEGER,
                        note TEXT,
                        category TEXT,
                        date TEXT DEFAULT (datetime('now'))
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        username TEXT,
                        joined_at TEXT DEFAULT (datetime('now'))
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        language TEXT DEFAULT 'uz',
                        currency TEXT DEFAULT "so'm",
                        onboarding_done INTEGER DEFAULT 0
                    )''')
        # Add onboarding_done column if missing (for existing DB)
        try:
            c.execute("ALTER TABLE user_settings ADD COLUMN onboarding_done INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                        user_id INTEGER,
                        category TEXT,
                        amount INTEGER,
                        month TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS goals (
                        user_id INTEGER,
                        goal_name TEXT,
                        target_amount INTEGER,
                        deadline TEXT,
                        created_at TEXT DEFAULT (datetime('now'))
                    )''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.exception(f"Database initialization error: {e}")
        raise

def get_db_connection():
    """Database connection helper with error handling"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.exception(f"Database connection error: {e}")
        return None

def get_user_settings(user_id):
    """Get user settings (language, currency) with defaults"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT language, currency FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return {"language": row[0] or "uz", "currency": row[1] or "so'm"}
        else:
            return {"language": "uz", "currency": "so'm"}
    except sqlite3.Error as e:
        logger.exception(f"DB error in get_user_settings: {e}")
        return {"language": "uz", "currency": "so'm"}

def format_currency(amount, currency="so'm"):
    """Format currency with proper spacing"""
    return f"{amount:,} {currency}"

def validate_amount(amount_str):
    """Validate and parse amount string"""
    try:
        # Remove spaces and common separators
        cleaned = amount_str.replace(' ', '').replace(',', '').replace('.', '')
        amount = int(cleaned)
        if amount <= 0:
            return None, "Miqdor 0 dan katta bo'lishi kerak! Masalan: 1 000 000"
        if amount > 999999999:
            return None, "Miqdor juda katta! Iltimos, kichikroq miqdorni kiriting. Masalan: 1 000 000"
        return amount, None
    except ValueError:
        return None, "Noto'g'ri format! Masalan: 1 000 000 yoki 5000000."

def get_all_user_ids():
    """Get all user IDs from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in c.fetchall()]
        conn.close()
        return user_ids
    except sqlite3.Error as e:
        logger.exception(f"Error getting user IDs: {e}")
        return []

def get_weekly_stats(user_id):
    """Get weekly income and expense statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income' AND date >= ?", (user_id, week_ago))
        kirim = c.fetchone()[0] or 0
        c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense' AND date >= ?", (user_id, week_ago))
        chiqim = c.fetchone()[0] or 0
        conn.close()
        return kirim, chiqim
    except sqlite3.Error as e:
        logger.exception(f"Error getting weekly stats: {e}")
        return 0, 0

def is_onboarded(user_id):
    """Check if user has completed onboarding"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT onboarding_done FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row is None or not isinstance(row, (list, tuple)):
            return False
        return bool(row[0])
    except sqlite3.Error as e:
        logger.exception(f"Error checking onboarding status: {e}")
        return False

def set_onboarded(user_id):
    """Mark user as onboarded"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.exception(f"Error setting onboarding status: {e}")

def get_currency_code(text):
    """Extract currency code from text"""
    if text is None:
        return "so'm"
    
    text_lower = text.lower()
    if "so'm" in text_lower or "uz" in text_lower:
        return "so'm"
    elif "dollar" in text_lower or "$" in text or "usd" in text_lower():
        return "USD"
    elif "euro" in text_lower or "eur" in text_lower():
        return "EUR"
    return "so'm" 