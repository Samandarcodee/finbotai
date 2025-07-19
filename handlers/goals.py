"""
handlers/goals.py
Handles AI goal (maqsad) logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from utils import format_amount, validate_amount, get_navigation_keyboard
from ai_service import ai_service
from datetime import datetime
from loguru import logger

# AI Goal states
AI_GOAL_NAME, AI_GOAL_AMOUNT, AI_GOAL_DEADLINE, AI_GOAL_MONITOR = 501, 502, 503, 504

async def ai_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start goal creation with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    
    # Handle goal creation
    if text == "🎯 Maqsad qo'yish":
        keyboard = [
            ["📝 Maqsad nomini kiriting"],
            ["💡 Maqsad tavsiyalari"]
        ] + get_navigation_keyboard()
        
        await update.message.reply_text(
            "🎯 <b>Maqsad qo'yish</b>\n\n"
            "Maqsad nomini kiriting (masalan: iPhone 15 Pro, O'qish, Safar):",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="HTML"
        )
        return 1  # Goal name state
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return ConversationHandler.END

async def ai_goal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal name input with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await ai_goal_start(update, context)
    
    # Save goal name
    context.user_data['goal_name'] = text
    
    keyboard = [
        ["💰 Miqdorni kiriting"],
        ["💡 Miqdor tavsiyalari"]
    ] + get_navigation_keyboard()
    
    await update.message.reply_text(
        f"✅ Maqsad nomi: <b>{text}</b>\n\n"
        "Endi maqsad miqdorini kiriting (masalan: 5 000 000):",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="HTML"
    )
    return 2  # Goal amount state

async def ai_goal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal amount input with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await ai_goal_name(update, context)
    
    # Validate amount
    amount, error = validate_amount(text)
    if error:
        keyboard = [
            ["💰 Miqdorni qayta kiriting"],
            ["💡 Miqdor tavsiyalari"]
        ] + get_navigation_keyboard()
        
        await update.message.reply_text(
            f"❌ {error}\n\nQaytadan kiriting:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return 2  # Stay in amount state
    
    # Save goal amount
    context.user_data['goal_amount'] = amount
    
    keyboard = [
        ["📅 Muddatni kiriting"],
        ["💡 Muddat tavsiyalari"]
    ] + get_navigation_keyboard()
    
    await update.message.reply_text(
        f"✅ Maqsad miqdori: <b>{format_amount(amount, user_id)}</b>\n\n"
        "Endi maqsad muddatini kiriting (masalan: 2024-12-31):",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="HTML"
    )
    return 3  # Goal deadline state

async def ai_goal_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal deadline input with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await ai_goal_amount(update, context)
    
    # Validate date format
    try:
        deadline = datetime.strptime(text, "%Y-%m-%d")
        if deadline <= datetime.now():
            keyboard = [
                ["📅 Muddatni qayta kiriting"],
                ["💡 Muddat tavsiyalari"]
            ] + get_navigation_keyboard()
            
            await update.message.reply_text(
                "❌ Muddat o'tgan bo'lishi mumkin emas!\n\nQaytadan kiriting:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return 3  # Stay in deadline state
    except ValueError:
        keyboard = [
            ["📅 Muddatni qayta kiriting"],
            ["💡 Muddat tavsiyalari"]
        ] + get_navigation_keyboard()
        
        await update.message.reply_text(
            "❌ Noto'g'ri format! YYYY-MM-DD formatida kiriting.\n\nQaytadan kiriting:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return 3  # Stay in deadline state
    
    # Save goal deadline
    context.user_data['goal_deadline'] = text
    
    # Show goal summary
    goal_name = context.user_data.get('goal_name', 'N/A')
    goal_amount = context.user_data.get('goal_amount', 0)
    
    keyboard = [
        ["✅ Maqsadni saqlash"],
        ["❌ Bekor qilish"]
    ] + get_navigation_keyboard()
    
    await update.message.reply_text(
        f"🎯 <b>Maqsad ma'lumotlari:</b>\n\n"
        f"📝 Nomi: <b>{goal_name}</b>\n"
        f"💰 Miqdori: <b>{format_amount(goal_amount, user_id)}</b>\n"
        f"📅 Muddati: <b>{text}</b>\n\n"
        "Maqsadni saqlashni xohlaysizmi?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="HTML"
    )
    return 4  # Goal confirmation state

async def ai_goal_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal monitoring with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(update.message.from_user, 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    
    # Handle goal confirmation
    if text == "✅ Maqsadni saqlash":
        goal_name = context.user_data.get('goal_name', 'N/A')
        goal_amount = context.user_data.get('goal_amount', 0)
        goal_deadline = context.user_data.get('goal_deadline', 'N/A')
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO goals (user_id, name, target_amount, deadline, current_amount, status, created_at)
                VALUES (?, ?, ?, ?, 0, 'active', ?)
            """, (user_id, goal_name, goal_amount, goal_deadline, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            
            keyboard = [
                ["🎯 Maqsadlar ro'yxati"],
                ["📊 Maqsad monitoring"]
            ] + get_navigation_keyboard()
            
            await update.message.reply_text(
                f"✅ <b>Maqsad saqlandi!</b>\n\n"
                f"📝 Nomi: <b>{goal_name}</b>\n"
                f"💰 Miqdori: <b>{format_amount(goal_amount, user_id)}</b>\n"
                f"📅 Muddati: <b>{goal_deadline}</b>\n\n"
                "Maqsadlaringizni kuzatib boring!",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception(f"Goal save error: {e}")
            await update.message.reply_text("❌ Maqsadni saqlashda xatolik.")
        
        return ConversationHandler.END
        
    elif text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Maqsad qo'yish bekor qilindi.")
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return 4  # Stay in confirmation state

async def cancel_goal(update, context):
    """Cancel goal operation"""
    return ConversationHandler.END

# AI GOAL CONV HANDLER
ai_goal_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("ai_maqsad", ai_goal_start)],
    states={
        AI_GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_name)],
        AI_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_amount)],
        AI_GOAL_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_deadline)],
        AI_GOAL_MONITOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_goal_monitor)],
    },
    fallbacks=[CommandHandler("cancel", cancel_goal)]
) 