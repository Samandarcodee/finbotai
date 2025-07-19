"""
handlers/budget.py
Handles AI budget (byudjet) logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from utils import format_amount
from ai_service import ai_service
from datetime import datetime
from loguru import logger

# AI Budget states
AI_BUDGET_INCOME, AI_BUDGET_CONFIRM = 601, 602

async def ai_budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start AI budget creation process"""
    if not update.message:
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🤖 AI Byudjet yaratish\n\n"
        "Oylik taxminiy kirimingizni kiriting (masalan: 3 000 000):",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return AI_BUDGET_INCOME

async def ai_budget_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle income input for AI budget"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Byudjet yaratish bekor qilindi.")
        return ConversationHandler.END
    
    try:
        # Remove spaces and parse amount
        cleaned = text.replace(' ', '').replace(',', '').replace('.', '')
        income = int(cleaned)
        if income <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri miqdor! Masalan: 3 000 000")
        return AI_BUDGET_INCOME
    
    context.user_data['monthly_income'] = income
    
    # Get user's spending history for AI analysis
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        await update.message.reply_text("❌ Foydalanuvchi aniqlanmadi.")
        return ConversationHandler.END
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT type, amount, note, category, date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 50
        """, (user_id,))
        transactions = c.fetchall()
        conn.close()
        
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
        
        # Call AI service for budget plan
        try:
            user_data = {
                'monthly_income': income,
                'transactions': transaction_data
            }
            ai_budget_plan = await ai_service.generate_budget_plan(user_data, transaction_data)
        except Exception as e:
            logger.exception(f"AI budget error: {e}")
            ai_budget_plan = "AI xizmatida muammo bor. Keyinroq urinib ko'ring."
        
        context.user_data['ai_budget_plan'] = ai_budget_plan
        
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        await update.message.reply_text(
            f"✅ Oylik kirim: {format_amount(income, user_id)}\n\n"
            f"🤖 <b>AI Byudjet rejasi:</b>\n\n{ai_budget_plan}\n\n"
            "Bu rejani saqlashni xohlaysizmi?",
            reply_markup=ReplyKeyboardMarkup([
                ["✅ Ha, saqla"],
                ["❌ Yo'q, bekor qil"]
            ], resize_keyboard=True, one_time_keyboard=True),
            parse_mode=ParseMode.HTML
        )
        return AI_BUDGET_CONFIRM
        
    except sqlite3.Error as e:
        logger.exception(f"Database error in AI budget: {e}")
        await update.message.reply_text("❌ Ma'lumotlarni olishda xatolik.")
        return ConversationHandler.END

async def ai_budget_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI budget confirmation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    if text == "❌ Yo'q, bekor qil":
        await update.message.reply_text("❌ Byudjet yaratish bekor qilindi.")
        return ConversationHandler.END
    
    if text == "✅ Ha, saqla":
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if user_id is None:
            await update.message.reply_text("❌ Foydalanuvchi aniqlanmadi.")
            return ConversationHandler.END
        
        monthly_income = context.user_data.get('monthly_income', 0)
        ai_plan = context.user_data.get('ai_budget_plan', '')
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Save budget categories (simplified - can be improved)
            current_month = datetime.now().strftime("%Y-%m")
            budget_categories = [
                ("Oziq-ovqat", int(monthly_income * 0.3)),
                ("Transport", int(monthly_income * 0.15)),
                ("Sog'liq", int(monthly_income * 0.1)),
                ("Ta'lim", int(monthly_income * 0.1)),
                ("O'yin-kulgi", int(monthly_income * 0.1)),
                ("Kiyim", int(monthly_income * 0.05)),
                ("Uy", int(monthly_income * 0.1)),
                ("Aloqa", int(monthly_income * 0.05)),
                ("Boshqa", int(monthly_income * 0.05))
            ]
            
            for category, amount in budget_categories:
                c.execute("""
                    INSERT INTO budgets (user_id, category, amount, month) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, category, month) DO UPDATE SET amount = excluded.amount
                """, (user_id, category, amount, current_month))
            
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ <b>AI Byudjet saqlandi!</b>\n\n"
                f"💰 Oylik kirim: {format_amount(monthly_income, user_id)}\n"
                f"📅 Oy: {current_month}\n\n"
                "Byudjetni kuzatish uchun /budget buyrug'ini ishlating!",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
            
        except sqlite3.Error as e:
            logger.exception(f"Budget save error: {e}")
            await update.message.reply_text("❌ Byudjetni saqlashda xatolik yuz berdi.")
            return ConversationHandler.END
    
    await update.message.reply_text("❌ Noto'g'ri tanlov.")
    return AI_BUDGET_CONFIRM

async def cancel_budget(update, context):
    """Cancel budget operation"""
    return ConversationHandler.END

# AI BUDGET CONV HANDLER
ai_budget_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("ai_byudjet", ai_budget_start)],
    states={
        AI_BUDGET_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_budget_income)],
        AI_BUDGET_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_budget_confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel_budget)]
) 