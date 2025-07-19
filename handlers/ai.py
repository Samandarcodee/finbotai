"""
handlers/ai.py
Handles AI advice and AI analysis for FinBot AI Telegram bot.
"""

import asyncio
from telegram import Update
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from utils import format_amount
from ai_service import ai_service
from loguru import logger
import sqlite3
from datetime import datetime

async def show_ai_analysis(update: Update, user_id: int):
    """Show AI-powered spending analysis with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text("🧠 AI moliyaviy tahlil qilmoqda…")
        
        # Get user data for AI analysis
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT type, amount, note, category, date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 20
        """, (user_id,))
        transactions = c.fetchall()
        conn.close()
        
        if not transactions:
            if loading_msg:
                await loading_msg.edit_text("❌ AI tahlil uchun ma'lumot yetarli emas. Avval kirim/chiqim qo'shing!")
            return
        
        # Prepare data for AI
        transaction_data = []
        for t in transactions:
            try:
                date_obj = datetime.strptime(t[4], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%d.%m")
            except (ValueError, TypeError):
                date_str = "N/A"
            transaction_data.append({
                'type': t[0],
                'amount': t[1],
                'note': t[2],
                'category': t[3],
                'date': date_str
            })
        
        # Call AI service
        try:
            ai_analysis = await ai_service.analyze_spending_patterns(transaction_data)
        except Exception as e:
            logger.exception(f"AI analysis error: {e}")
            ai_analysis = "AI xizmatida muammo bor. Keyinroq urinib ko'ring."
        
        if loading_msg:
            await loading_msg.edit_text(f"📊 <b>AI tahlil natijasi:</b>\n\n{ai_analysis}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f"AI analysis error: {e}")
        if loading_msg:
            await loading_msg.edit_text("AI tahlil xatosi yoki ma'lumot yetarli emas.")

async def show_ai_advice(update: Update, user_id: int):
    """Show AI financial advice with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text("🧠 AI moliyaviy maslahatchi hisob-kitob qilmoqda…")
        
        # Get user data for AI advice
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current month data
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        
        # Get total data
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        total_data = c.fetchone()
        
        # Get top spending categories
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 3
        """, (user_id,))
        categories = [cat[0] for cat in c.fetchall()]
        conn.close()
        
        # Prepare user data for AI
        month_income = month_data[0] or 0
        month_expense = month_data[1] or 0
        total_income = total_data[0] or 0
        total_expense = total_data[1] or 0
        
        user_data = {
            'month_income': month_income,
            'month_expense': month_expense,
            'total_income': total_income,
            'total_expense': total_expense,
            'currency': currency,
            'top_categories': categories
        }
        
        # Call AI service
        try:
            ai_advice = await ai_service.get_financial_advice(user_data)
        except Exception as e:
            logger.exception(f"AI advice error: {e}")
            ai_advice = ai_service.get_default_advice()
        
        if loading_msg:
            await loading_msg.edit_text(f"🤖 <b>AI moliyaviy maslahat:</b>\n\n{ai_advice}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f"AI advice error: {e}")
        if loading_msg:
            await loading_msg.edit_text("AI maslahat xatosi yoki ma'lumot yetarli emas.") 