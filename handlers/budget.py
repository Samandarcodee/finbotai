"""
handlers/budget.py
Handles AI budget (byudjet) logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from utils import format_amount, get_navigation_keyboard, build_reply_keyboard, validate_amount
from ai_service import ai_service
from datetime import datetime
from loguru import logger

# AI Budget states
AI_BUDGET_INCOME, AI_BUDGET_CONFIRM = 601, 602

async def ai_budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start AI budget creation with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if user_id is None:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    
    # Handle budget creation
    if text == "💰 AI Byudjet yaratish":
        keyboard = [
            ["📝 Oylik daromadni kiriting"],
            ["💡 Daromad tavsiyalari"]
        ]
        await update.message.reply_text(
            "💰 <b>AI Byudjet yaratish</b>\n\n"
            "Oylik daromadingizni kiriting (masalan: 3 000 000):",
            reply_markup=build_reply_keyboard(keyboard, resize=True),
            parse_mode="HTML"
        )
        return 1  # Budget income state
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return ConversationHandler.END

async def ai_budget_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle budget income input with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if user_id is None:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await ai_budget_start(update, context)
    
    # Validate amount
    amount, error = validate_amount(text)
    if error:
        keyboard = [
            ["💰 Daromadni qayta kiriting"],
            ["💡 Daromad tavsiyalari"]
        ]
        await update.message.reply_text(
            f"❌ {error}\n\nQaytadan kiriting:",
            reply_markup=build_reply_keyboard(keyboard, resize=True)
        )
        return 1  # Stay in income state
    
    # Save budget income
    context.user_data['budget_income'] = amount
    
    # Generate AI budget recommendations
    budget_recommendations = generate_budget_recommendations(amount, user_id)
    
    keyboard = [
        ["✅ Byudjetni saqlash"],
        ["❌ Bekor qilish"]
    ]
    await update.message.reply_text(
        f"💰 <b>AI Byudjet tavsiyalari</b>\n\n"
        f"📊 Oylik daromad: <b>{format_amount(amount, user_id)}</b>\n\n"
        f"{budget_recommendations}\n\n"
        "Byudjetni saqlashni xohlaysizmi?",
        reply_markup=build_reply_keyboard(keyboard, resize=True),
        parse_mode="HTML"
    )
    return 2  # Budget confirmation state

async def ai_budget_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle budget confirmation with navigation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if user_id is None:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await ai_budget_income(update, context)
    
    # Handle budget confirmation
    if text == "✅ Byudjetni saqlash":
        budget_income = 0
        if hasattr(context, 'user_data') and context.user_data and isinstance(context.user_data, dict):
            budget_income = context.user_data.get('budget_income', 0)
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO budgets (user_id, monthly_income, created_at)
                VALUES (?, ?, ?)
            """, (user_id, budget_income, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            
            keyboard = [
                ["📊 Byudjet holati"],
                ["💰 AI Byudjet tavsiyasi"]
            ]
            await update.message.reply_text(
                f"✅ <b>Byudjet saqlandi!</b>\n\n"
                f"💰 Oylik daromad: <b>{format_amount(budget_income, user_id)}</b>\n\n"
                "Byudjetingizni kuzatib boring!",
                reply_markup=build_reply_keyboard(keyboard, resize=True),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception(f"Budget save error: {e}")
            await update.message.reply_text("❌ Byudjetni saqlashda xatolik.")
        
        return ConversationHandler.END
        
    elif text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Byudjet yaratish bekor qilindi.")
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return 2  # Stay in confirmation state

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

def generate_budget_recommendations(income, user_id):
    """Generate AI budget recommendations based on income"""
    # 50/30/20 rule: 50% needs, 30% wants, 20% savings
    needs = income * 0.5
    wants = income * 0.3
    savings = income * 0.2
    
    recommendations = (
        f"🎯 <b>50/30/20 qoidasi:</b>\n"
        f"• Asosiy xarajatlar (50%): {format_amount(needs, user_id)}\n"
        f"• Xohishlar (30%): {format_amount(wants, user_id)}\n"
        f"• Tejash (20%): {format_amount(savings, user_id)}\n\n"
        f"💡 <b>Kategoriyalar bo'yicha:</b>\n"
        f"• 🏠 Uy: {format_amount(income * 0.25, user_id)}\n"
        f"• 🍔 Oziq-ovqat: {format_amount(income * 0.15, user_id)}\n"
        f"• 🚗 Transport: {format_amount(income * 0.10, user_id)}\n"
        f"• 💊 Sog'liq: {format_amount(income * 0.05, user_id)}\n"
        f"• 🎮 Ko'ngil ochar: {format_amount(income * 0.15, user_id)}\n"
        f"• 💰 Tejash: {format_amount(income * 0.20, user_id)}\n"
        f"• 🎯 Qo'shimcha: {format_amount(income * 0.10, user_id)}"
    )
    
    return recommendations 