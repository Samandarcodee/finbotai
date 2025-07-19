"""
db.py
Database helper functions for FinBot AI Telegram bot.
"""

import sqlite3
import os
from datetime import datetime, timedelta, timedelta
from loguru import logger

# Database file path
DB_PATH = "finbot.db"

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.exception(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize database with all tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User settings table with enhanced fields
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        language TEXT DEFAULT 'uz',
                currency TEXT DEFAULT 'UZS',
                notifications BOOLEAN DEFAULT 1,
                auto_reports BOOLEAN DEFAULT 0,
                daily_reminder BOOLEAN DEFAULT 0,
                weekly_report BOOLEAN DEFAULT 0,
                monthly_report BOOLEAN DEFAULT 0,
                onboarding_done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Transactions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT CHECK(type IN ('income', 'expense')),
                amount REAL,
                category TEXT,
                note TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Goals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                target_amount REAL,
                current_amount REAL DEFAULT 0,
                deadline DATE,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Budgets table
        c.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        category TEXT,
                amount REAL,
                spent REAL DEFAULT 0,
                period TEXT DEFAULT 'monthly',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Push notifications table
        c.execute('''
            CREATE TABLE IF NOT EXISTS push_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # AI analysis history table
        c.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                analysis_type TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Export history table
        c.execute('''
            CREATE TABLE IF NOT EXISTS export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                export_type TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create indexes for better performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_type ON transactions(user_id, type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_budgets_user_category ON budgets(user_id, category)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.exception(f"Database initialization error: {e}")

def get_user_settings(user_id):
    """Get user settings with defaults"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {
                'language': 'uz',
                'currency': 'UZS',
                'notifications': True,
                'auto_reports': False,
                'daily_reminder': False,
                'weekly_report': False,
                'monthly_report': False,
                'onboarding_done': False
            }
        
        c = conn.cursor()
        c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        else:
            # Return default settings if user not found
            return {
                'language': 'uz',
                'currency': 'UZS',
                'notifications': True,
                'auto_reports': False,
                'daily_reminder': False,
                'weekly_report': False,
                'monthly_report': False,
                'onboarding_done': False
            }
    except Exception as e:
        logger.exception(f"Get user settings error: {e}")
        return {
            'language': 'uz',
            'currency': 'UZS',
            'notifications': True,
            'auto_reports': False,
            'daily_reminder': False,
            'weekly_report': False,
            'monthly_report': False,
            'onboarding_done': False
        }

def create_user(user_id, username=None, first_name=None, last_name=None):
    """Create new user"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        
        # Check if user already exists
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone():
            conn.close()
            return True
        
        # Create user
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        
        # Create default settings
        c.execute("""
            INSERT INTO user_settings (user_id, language, currency, notifications, auto_reports, onboarding_done)
            VALUES (?, 'uz', 'UZS', 1, 0, 0)
        """, (user_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} created successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Create user error: {e}")
        return False

def add_transaction(user_id, transaction_type, amount, category, note=None):
    """Add new transaction"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        c.execute("""
            INSERT INTO transactions (user_id, type, amount, category, note)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, transaction_type, amount, category, note))
        
        conn.commit()
        conn.close()
        logger.info(f"Transaction added for user {user_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Add transaction error: {e}")
        return False

def get_user_transactions(user_id, limit=50, offset=0):
    """Get user transactions"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        
        c = conn.cursor()
        c.execute("""
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        
        transactions = c.fetchall()
        conn.close()
        return transactions
        
    except Exception as e:
        logger.exception(f"Get transactions error: {e}")
        return []

def get_user_balance(user_id):
    """Get user balance"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {'income': 0, 'expense': 0, 'balance': 0}
        
        c = conn.cursor()
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        income = result[0] or 0
        expense = result[1] or 0
        balance = income - expense
        
        return {
            'income': income,
            'expense': expense,
            'balance': balance
        }
        
    except Exception as e:
        logger.exception(f"Get balance error: {e}")
        return {'income': 0, 'expense': 0, 'balance': 0}

def get_monthly_stats(user_id, year=None, month=None):
    """Get monthly statistics"""
    try:
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        conn = get_db_connection()
        if conn is None:
            return {'income': 0, 'expense': 0, 'balance': 0}
        
        c = conn.cursor()
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, f"{year:04d}-{month:02d}"))
        
        result = c.fetchone()
        conn.close()
        
        income = result[0] or 0
        expense = result[1] or 0
        balance = income - expense
        
        return {
            'income': income,
            'expense': expense,
            'balance': balance
        }
        
    except Exception as e:
        logger.exception(f"Get monthly stats error: {e}")
        return {'income': 0, 'expense': 0, 'balance': 0}

def get_spending_categories(user_id, period='month'):
    """Get spending by categories"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        
        c = conn.cursor()
        
        if period == 'month':
            current_month = datetime.now().strftime("%Y-%m")
            c.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions 
                WHERE user_id = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
                GROUP BY category 
                ORDER BY total DESC
            """, (user_id, current_month))
        else:
            c.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions 
                WHERE user_id = ? AND type = 'expense'
                GROUP BY category 
                ORDER BY total DESC
            """, (user_id,))
        
        categories = c.fetchall()
        conn.close()
        return categories
        
    except Exception as e:
        logger.exception(f"Get spending categories error: {e}")
        return []

def create_goal(user_id, name, target_amount, deadline):
    """Create new goal"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        c.execute("""
            INSERT INTO goals (user_id, name, target_amount, deadline)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, target_amount, deadline))
        
        conn.commit()
        conn.close()
        logger.info(f"Goal created for user {user_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Create goal error: {e}")
        return False

def get_user_goals(user_id):
    """Get user goals"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        
        c = conn.cursor()
        c.execute("""
            SELECT * FROM goals 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        
        goals = c.fetchall()
        conn.close()
        return goals
        
    except Exception as e:
        logger.exception(f"Get goals error: {e}")
        return []

def update_goal_progress(user_id, goal_id, amount):
    """Update goal progress"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        c.execute("""
            UPDATE goals 
            SET current_amount = current_amount + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (amount, goal_id, user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Goal progress updated for user {user_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Update goal progress error: {e}")
        return False

def save_ai_analysis(user_id, analysis_type, result):
    """Save AI analysis result"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        c.execute("""
            INSERT INTO ai_analysis_history (user_id, analysis_type, result)
            VALUES (?, ?, ?)
        """, (user_id, analysis_type, result))
        
        conn.commit()
        conn.close()
        logger.info(f"AI analysis saved for user {user_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Save AI analysis error: {e}")
        return False

def get_users_with_notifications():
    """Get users with enabled notifications"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        
        c = conn.cursor()
        c.execute("""
            SELECT user_id FROM user_settings 
            WHERE notifications = 1
        """)
        
        users = [row[0] for row in c.fetchall()]
        conn.close()
        return users
        
    except Exception as e:
        logger.exception(f"Get users with notifications error: {e}")
        return []

def get_users_with_auto_reports():
    """Get users with enabled auto reports"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        
        c = conn.cursor()
        c.execute("""
            SELECT user_id FROM user_settings 
            WHERE auto_reports = 1
        """)
        
        users = [row[0] for row in c.fetchall()]
        conn.close()
        return users
        
    except Exception as e:
        logger.exception(f"Get users with auto reports error: {e}")
        return []

# Legacy functions for backward compatibility
def get_currency_code(text):
    """Extract currency code from text"""
    if text is None:
        return "UZS"
    
    text_lower = text.lower()
    if "so'm" in text_lower or "uz" in text_lower or "🇺🇿" in text:
        return "UZS"
    elif "dollar" in text_lower or "$" in text or "usd" in text_lower or "💵" in text:
        return "USD"
    elif "euro" in text_lower or "eur" in text_lower or "💶" in text:
        return "EUR"
    elif "rubl" in text_lower or "rub" in text_lower or "🇷🇺" in text:
        return "RUB"
    elif "tenge" in text_lower or "kzt" in text_lower or "🇰🇿" in text:
        return "KZT"
    elif "som" in text_lower or "kgs" in text_lower or "🇰🇬" in text:
        return "KGS"
    elif "lira" in text_lower or "try" in text_lower or "🇹🇷" in text:
        return "TRY"
    elif "yuan" in text_lower or "cny" in text_lower or "🇨🇳" in text:
        return "CNY"
    elif "yen" in text_lower or "jpy" in text_lower or "🇯🇵" in text:
        return "JPY"
    return "UZS" 

def is_onboarded(user_id):
    """Check if user has completed onboarding"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        c.execute("SELECT onboarding_done FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return bool(row[0])
        return False
    except Exception as e:
        logger.exception(f"Error checking onboarding status: {e}")
        return False

def set_onboarded(user_id):
    """Mark user as onboarded"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        c = conn.cursor()
        c.execute("UPDATE user_settings SET onboarding_done = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} marked as onboarded")
        return True
    except Exception as e:
        logger.exception(f"Error setting onboarding status: {e}")
        return False

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
        conn = get_db_connection()
        if conn is None:
            return []
        
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in c.fetchall()]
        conn.close()
        return user_ids
    except Exception as e:
        logger.exception(f"Error getting user IDs: {e}")
        return []

def get_weekly_stats(user_id):
    """Get weekly income and expense statistics"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 0, 0
        
        c = conn.cursor()
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income' AND date >= ?", (user_id, week_ago))
        kirim = c.fetchone()[0] or 0
        c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense' AND date >= ?", (user_id, week_ago))
        chiqim = c.fetchone()[0] or 0
        conn.close()
        return kirim, chiqim
    except Exception as e:
        logger.exception(f"Error getting weekly stats: {e}")
        return 0, 0 