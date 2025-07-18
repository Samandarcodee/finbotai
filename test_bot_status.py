#!/usr/bin/env python3
"""
Test script to check if the FinBot is working properly
"""

import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError

async def test_bot():
    """Test if the bot is working"""
    BOT_TOKEN = "7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE"
    
    try:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Bot is working!")
        print(f"🤖 Bot name: {me.first_name}")
        print(f"👤 Username: @{me.username}")
        print(f"�� Bot ID: {me.id}")
        
        # Test if bot can receive updates
        updates = await bot.get_updates()
        print(f"📨 Updates available: {len(updates)}")
        
        return True
        
    except TelegramError as e:
        print(f"❌ Bot error: {e}")
        return False
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing FinBot status...")
    print("=" * 40)
    
    # Set environment variable
    os.environ['BOT_TOKEN'] = "7191355398:AAGRnK1CKSdZi5sxM0Slvgq0_SJHqIRB2nE"
    
    # Run the test
    result = asyncio.run(test_bot())
    
    print("=" * 40)
    if result:
        print("✅ Bot is ready to use!")
        print("📱 Telegram da botni topish uchun: @Finbotaii_bot")
        print("🚀 Bot ishga tushgan va xabarlarni kutmoqda...")
    else:
        print("❌ Bot da muammo bor!") 