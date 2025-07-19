#!/usr/bin/env python3
"""
Test script to verify settings menu functionality
"""

import asyncio
from handlers.settings import show_settings, settings_handler
from handlers.start import start
from db import init_db, create_user

class MockUpdate:
    def __init__(self, text, user_id=12345):
        self.message = MockMessage(text, user_id)
        self.effective_user = MockUser(user_id)

class MockMessage:
    def __init__(self, text, user_id):
        self.text = text
        self.from_user = MockUser(user_id)
    
    async def reply_text(self, text, **kwargs):
        print(f"Bot: {text}")
        return True

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockContext:
    pass

async def test_settings():
    """Test settings menu functionality"""
    print("🧪 Testing Settings Menu...")
    
    # Initialize database
    init_db()
    create_user(12345, "testuser", "Test", "User")
    
    # Test 1: Show settings menu
    print("\n1️⃣ Testing show_settings...")
    update = MockUpdate("⚙️ Sozlamalar/Yordam")
    await show_settings(update, 12345)
    
    # Test 2: Handle currency selection
    print("\n2️⃣ Testing currency selection...")
    update = MockUpdate("💰 Valyutani o'zgartirish")
    result = await settings_handler(update, MockContext())
    print(f"Result state: {result}")
    
    # Test 3: Handle language selection
    print("\n3️⃣ Testing language selection...")
    update = MockUpdate("🌐 Tilni o'zgartirish")
    result = await settings_handler(update, MockContext())
    print(f"Result state: {result}")
    
    # Test 4: Handle notifications toggle
    print("\n4️⃣ Testing notifications toggle...")
    update = MockUpdate("🔔 Bildirishnomalar")
    result = await settings_handler(update, MockContext())
    print(f"Result state: {result}")
    
    # Test 5: Handle auto reports toggle
    print("\n5️⃣ Testing auto reports toggle...")
    update = MockUpdate("📊 Avtomatik hisobotlar")
    result = await settings_handler(update, MockContext())
    print(f"Result state: {result}")
    
    # Test 6: Handle back button
    print("\n6️⃣ Testing back button...")
    update = MockUpdate("🔙 Orqaga")
    result = await settings_handler(update, MockContext())
    print(f"Result state: {result}")
    
    print("\n✅ Settings menu test completed!")

if __name__ == "__main__":
 