#!/usr/bin/env python3
"""
FinBot AI Test Script
Bu script botning to'g'ri ishlashini tekshirish uchun ishlatiladi
"""

import os
import asyncio
from telegram import Bot
from telegram.error import InvalidToken

async def test_bot():
    # Test token - bu noto'g'ri token
    test_token = "6884567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    
    try:
        bot = Bot(token=test_token)
        me = await bot.get_me()
        print(f"✅ Bot muvaffaqiyatli ulandi!")
        print(f"Bot nomi: {me.first_name}")
        print(f"Username: @{me.username}")
        return True
    except InvalidToken:
        print("❌ Bot token noto'g'ri!")
        print("Iltimos, haqiqiy bot token kiriting.")
        return False
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot()) 