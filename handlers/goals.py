"""
handlers/goals.py
Handles AI goal (maqsad) logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from ai_service import ai_service
from datetime import datetime
from loguru import logger

# AI Goal states
AI_GOAL_NAME, AI_GOAL_AMOUNT, AI_GOAL_DEADLINE, AI_GOAL_MONITOR = 501, 502, 503, 504

async def ai_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start AI goal creation process"""
    if not update.message:
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🎯 AI Maqsad yaratish\n\n"
        "Maqsad nomini kiriting (masalan: telefon, o'qish, safar):",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return AI_GOAL_NAME

async def ai_goal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal name input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Maqsad yaratish bekor qilindi.")
        return ConversationHandler.END
    
    if len(text) < 3:
        await update.message.reply_text("❌ Maqsad nomi juda qisqa. Kamida 3 harf kiriting.")
        return AI_GOAL_NAME
    
    context.user_data['goal_name'] = text
    await update.message.reply_text(
        f"✅ Maqsad: {text}\n\n"
        "Maqsad uchun kerakli miqdorni kiriting (masalan: 5 000 000):",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return AI_GOAL_AMOUNT

async def ai_goal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal amount input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Maqsad yaratish bekor qilindi.")
        return ConversationHandler.END
    
    try:
        # Remove spaces and parse amount
        cleaned = text.replace(' ', '').replace(',', '').replace('.', '')
        amount = int(cleaned)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri miqdor! Masalan: 5 000 000")
        return AI_GOAL_AMOUNT
    
    context.user_data['goal_amount'] = amount
    await update.message.reply_text(
        f"✅ Miqdor: {amount:,} so'm\n\n"
        "Maqsad muddatini kiriting (masalan: 2024-12-31 yoki 6 oy):",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return AI_GOAL_DEADLINE

async def ai_goal_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal deadline input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Maqsad yaratish bekor qilindi.")
        return ConversationHandler.END
    
    # Simple deadline parsing (can be improved)
    deadline = text
    context.user_data['goal_deadline'] = deadline
    
    goal_name = context.user_data.get('goal_name', '')
    goal_amount = context.user_data.get('goal_amount', 0)
    
    await update.message.reply_text(
        f"🎯 <b>Maqsad ma'lumotlari:</b>\n\n"
        f"📝 Nomi: {goal_name}\n"
        f"💰 Miqdor: {goal_amount:,} so'm\n"
        f"📅 Muddat: {deadline}\n\n"
        "Maqsadni saqlashni tasdiqlaysizmi?",
        reply_markup=ReplyKeyboardMarkup([
            ["✅ Ha, saqla"],
            ["❌ Yo'q, bekor qil"]
        ], resize_keyboard=True, one_time_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    return AI_GOAL_MONITOR

async def ai_goal_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal confirmation and save"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    if text == "❌ Yo'q, bekor qil":
        await update.message.reply_text("❌ Maqsad yaratish bekor qilindi.")
        return ConversationHandler.END
    
    if text == "✅ Ha, saqla":
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if user_id is None:
            await update.message.reply_text("❌ Foydalanuvchi aniqlanmadi.")
            return ConversationHandler.END
        
        goal_name = context.user_data.get('goal_name', '')
        goal_amount = context.user_data.get('goal_amount', 0)
        goal_deadline = context.user_data.get('goal_deadline', '')
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO goals (user_id, goal_name, target_amount, deadline) 
                VALUES (?, ?, ?, ?)
            """, (user_id, goal_name, goal_amount, goal_deadline))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ <b>Maqsad saqlandi!</b>\n\n"
                f"🎯 {goal_name}\n"
                f"💰 {goal_amount:,} so'm\n"
                f"📅 {goal_deadline}\n\n"
                "Maqsadga erishish uchun har kuni kichik qadamlar tashlang!",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        except sqlite3.Error as e:
            logger.exception(f"Goal save error: {e}")
            await update.message.reply_text("❌ Maqsadni saqlashda xatolik yuz berdi.")
            return ConversationHandler.END
    
    await update.message.reply_text("❌ Noto'g'ri tanlov.")
    return AI_GOAL_MONITOR

# AI GOAL CONV HANDLER
ai_goal_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("ai_maqsad", ai_goal_start)],
    states={
        AI_GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_name)],
        AI_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_amount)],
        AI_GOAL_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_deadline)],
        AI_GOAL_MONITOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_monitor)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
) 