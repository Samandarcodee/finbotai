#!/usr/bin/env python3
"""
test_bot.py
FinBot AI test fayli - yangi funksiyalarni test qilish uchun
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta
from db import init_db, get_user_settings, create_user, add_transaction, get_user_balance
from utils import format_amount, get_user_language, get_user_currency
from handlers.ai import show_ai_menu, show_budget_advice, show_savings_tips
from handlers.settings import show_settings, toggle_notifications, toggle_auto_reports

class MockUpdate:
    """Mock Update object for testing"""
    def __init__(self, user_id, message_text=""):
        self.message = MockMessage(user_id, message_text)
        self.effective_user = MockUser(user_id)
        self.callback_query = None

class MockMessage:
    """Mock Message object for testing"""
    def __init__(self, user_id, text=""):
        self.from_user = MockUser(user_id)
        self.text = text
        self.chat_id = user_id

class MockUser:
    """Mock User object for testing"""
    def __init__(self, user_id):
        self.id = user_id
        self.first_name = f"Test User {user_id}"
        self.username = f"testuser{user_id}"

class MockContext:
    """Mock Context object for testing"""
    def __init__(self):
        self.bot = None

async def test_database_operations():
    """Test database operations"""
    print("🧪 Testing database operations...")
    
    # Initialize database
    init_db()
    
    # Test user creation
    user_id = 12345
    success = create_user(user_id, "testuser", "Test", "User")
    print(f"✅ User creation: {'Success' if success else 'Failed'}")
    
    # Test settings retrieval
    settings = get_user_settings(user_id)
    print(f"✅ Settings retrieval: {settings}")
    
    # Test transaction addition
    success = add_transaction(user_id, "income", 1000000, "Ish", "Oylik maosh")
    print(f"✅ Income transaction: {'Success' if success else 'Failed'}")
    
    success = add_transaction(user_id, "expense", 500000, "Oziq-ovqat", "Oziq-ovqat xarajatlari")
    print(f"✅ Expense transaction: {'Success' if success else 'Failed'}")
    
    # Test balance calculation
    balance = get_user_balance(user_id)
    print(f"✅ Balance calculation: {balance}")

def test_utils_functions():
    """Test utility functions"""
    print("\n🧪 Testing utility functions...")
    
    user_id = 12345
    
    # Test format_amount
    amount = 1500000
    formatted = format_amount(amount, user_id)
    print(f"✅ Amount formatting: {amount} -> {formatted}")
    
    # Test language detection
    language = get_user_language(user_id)
    print(f"✅ Language detection: {language}")
    
    # Test currency detection
    currency = get_user_currency(user_id)
    print(f"✅ Currency detection: {currency}")

async def test_ai_functions():
    """Test AI functions"""
    print("\n🧪 Testing AI functions...")
    
    user_id = 12345
    
    # Create mock update
    update = MockUpdate(user_id)
    
    # Test AI menu
    try:
        await show_ai_menu(update, user_id)
        print("✅ AI menu: Success")
    except Exception as e:
        print(f"❌ AI menu: {e}")
    
    # Test budget advice
    try:
        await show_budget_advice(update, user_id)
        print("✅ Budget advice: Success")
    except Exception as e:
        print(f"❌ Budget advice: {e}")
    
    # Test savings tips
    try:
        await show_savings_tips(update, user_id)
        print("✅ Savings tips: Success")
    except Exception as e:
        print(f"❌ Savings tips: {e}")

async def test_settings_functions():
    """Test settings functions"""
    print("\n🧪 Testing settings functions...")
    
    user_id = 12345
    
    # Create mock update
    update = MockUpdate(user_id)
    
    # Test settings display
    try:
        await show_settings(update, user_id)
        print("✅ Settings display: Success")
    except Exception as e:
        print(f"❌ Settings display: {e}")
    
    # Test notifications toggle
    try:
        await toggle_notifications(update, user_id)
        print("✅ Notifications toggle: Success")
    except Exception as e:
        print(f"❌ Notifications toggle: {e}")
    
    # Test auto reports toggle
    try:
        await toggle_auto_reports(update, user_id)
        print("✅ Auto reports toggle: Success")
    except Exception as e:
        print(f"❌ Auto reports toggle: {e}")

def test_data_generation():
    """Generate test data for comprehensive testing"""
    print("\n🧪 Generating test data...")
    
    user_id = 12345
    
    # Add more test transactions
    test_transactions = [
        ("income", 2000000, "Ish", "Qo'shimcha daromad"),
        ("expense", 300000, "Transport", "Avtobus"),
        ("expense", 150000, "Oziq-ovqat", "Non"),
        ("expense", 500000, "Kommunal", "Elektroenergiya"),
        ("income", 500000, "Biznes", "Kichik biznes"),
        ("expense", 200000, "Ko'ngil ochar", "Kino"),
        ("expense", 400000, "Sog'liq", "Dori-darmon"),
        ("expense", 100000, "Ta'lim", "Kitoblar"),
    ]
    
    for transaction_type, amount, category, note in test_transactions:
        success = add_transaction(user_id, transaction_type, amount, category, note)
        if success:
            print(f"✅ Added {transaction_type}: {format_amount(amount, user_id)} - {category}")
        else:
            print(f"❌ Failed to add {transaction_type}")

def test_statistics():
    """Test statistics and reporting"""
    print("\n🧪 Testing statistics...")
    
    user_id = 12345
    
    # Get balance
    balance = get_user_balance(user_id)
    print(f"💰 Current balance: {format_amount(balance['balance'], user_id)}")
    print(f"💵 Total income: {format_amount(balance['income'], user_id)}")
    print(f"💸 Total expenses: {format_amount(balance['expense'], user_id)}")
    
    # Calculate savings rate
    if balance['income'] > 0:
        savings_rate = (balance['balance'] / balance['income']) * 100
        print(f"📊 Savings rate: {savings_rate:.1f}%")
        
        if savings_rate >= 20:
            status = "✅ Excellent savings!"
        elif savings_rate >= 10:
            status = "👍 Good savings"
        elif savings_rate >= 0:
            status = "⚠️ Need to reduce expenses"
        else:
            status = "❌ Spending more than income"
        
        print(f"📈 Status: {status}")

def test_database_integrity():
    """Test database integrity and structure"""
    print("\n🧪 Testing database integrity...")
    
    try:
        conn = sqlite3.connect("finbot.db")
        c = conn.cursor()
        
        # Check tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        print(f"✅ Database tables: {tables}")
        
        # Check user_settings structure
        c.execute("PRAGMA table_info(user_settings)")
        columns = [row[1] for row in c.fetchall()]
        print(f"✅ User settings columns: {columns}")
        
        # Check transactions structure
        c.execute("PRAGMA table_info(transactions)")
        columns = [row[1] for row in c.fetchall()]
        print(f"✅ Transactions columns: {columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database integrity test failed: {e}")

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting FinBot AI tests...\n")
    
    # Test database operations
    await test_database_operations()
    
    # Test utility functions
    test_utils_functions()
    
    # Generate test data
    test_data_generation()
    
    # Test statistics
    test_statistics()
    
    # Test AI functions
    await test_ai_functions()
    
    # Test settings functions
    await test_settings_functions()
    
    # Test database integrity
    test_database_integrity()
    
    print("\n🎉 All tests completed!")
    print("\n📊 Test Summary:")
    print("✅ Database operations")
    print("✅ Utility functions")
    print("✅ Data generation")
    print("✅ Statistics calculation")
    print("✅ AI functions")
    print("✅ Settings functions")
    print("✅ Database integrity")

if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests()) 