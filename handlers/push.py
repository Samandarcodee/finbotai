"""
handlers/push.py
Handles push notification logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from db import get_all_user_ids, is_onboarded, get_user_settings, get_weekly_stats, DB_PATH
from utils import format_amount
from ai_service import ai_service
import asyncio
from loguru import logger
from datetime import datetime, timedelta
import os

# Push states
PUSH_TOPIC, PUSH_CONFIRM = 401, 402

# MESSAGES for push notifications
MESSAGES = {
    "uz": {
        "push_daily": "🌞 Yangi kun yangi imkoniyatlar bilan keldi! Bugun moliyaviy odatingizni davom ettiring: xarajatlaringizni yozishni unutmang!\n\n💡 Bugun hech bo'lmasa bitta xarajatingizni yozib qo'ydingizmi?",
        "push_weekly": "📊 Haftalik yakun:\n– Kirim: {income} so'm\n– Chiqim: {expense} so'm\n– Tejaganingiz: {saved} so'm 👏\n\n💰 Tejamkorlik odatingizni davom ettirasizmi? Shunday qiling, kelajakdagi siz minnatdor bo'ladi.",
        "feedback_push": "🙏 FinBot AI sizga yordam berayaptimi? Takliflaringiz bormi?"
    }
}

async def push_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle push notification command"""
    if not update.message:
        return ConversationHandler.END
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    
    # Check if user is admin
    if user_id != int(os.getenv("ADMIN_ID", "786171158")):
        await update.message.reply_text("❌ Sizda ruxsat yo'q.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📢 Push xabar yuborish\n\n"
        "Xabar turini tanlang:",
        reply_markup=ReplyKeyboardMarkup([
            ["🌞 Kunlik eslatma"],
            ["📊 Haftalik hisobot"],
            ["🎯 Oylik maqsad"],
            ["🙏 Fikr so'rash"],
            ["❌ Bekor qilish"]
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return PUSH_TOPIC

async def push_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle push topic selection"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    if text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Push xabar bekor qilindi.")
        return ConversationHandler.END
    
    context.user_data['push_topic'] = text
    await update.message.reply_text(
        f"✅ Tanlangan: {text}\n\n"
        "Push xabarni yuborishni tasdiqlaysizmi?",
        reply_markup=ReplyKeyboardMarkup([
            ["✅ Ha, yubor"],
            ["❌ Yo'q, bekor qil"]
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return PUSH_CONFIRM

async def push_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle push confirmation"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    text = update.message.text
    if text == "❌ Yo'q, bekor qil":
        await update.message.reply_text("❌ Push xabar bekor qilindi.")
        return ConversationHandler.END
    
    if text == "✅ Ha, yubor":
        topic = context.user_data.get('push_topic', '')
        success_count = 0
        error_count = 0
        
        try:
            if topic == "🌞 Kunlik eslatma":
                success_count, error_count = await send_daily_push_to_all(context)
            elif topic == "📊 Haftalik hisobot":
                success_count, error_count = await send_weekly_push_to_all(context)
            elif topic == "🎯 Oylik maqsad":
                success_count, error_count = await send_monthly_goal_push_to_all(context)
            elif topic == "🙏 Fikr so'rash":
                success_count, error_count = await send_monthly_feedback_push_to_all(context)
            
            await update.message.reply_text(
                f"✅ Push xabar yuborildi!\n\n"
                f"✅ Muvaffaqiyatli: {success_count}\n"
                f"❌ Xatolik: {error_count}"
            )
        except Exception as e:
            logger.exception(f"Push error: {e}")
            await update.message.reply_text("❌ Push xabar yuborishda xatolik yuz berdi.")
        
        return ConversationHandler.END
    
    return ConversationHandler.END

async def send_daily_push_to_all(context):
    """Send daily push to all onboarded users"""
    success_count = 0
    error_count = 0
    
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=MESSAGES["uz"]["push_daily"]
            )
            success_count += 1
        except Exception as e:
            logger.exception(f"Daily push error for user {user_id}: {e}")
            error_count += 1
    
    return success_count, error_count

async def send_weekly_push_to_all(context):
    """Send weekly push to all onboarded users"""
    success_count = 0
    error_count = 0
    
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            kirim, chiqim = get_weekly_stats(user_id)
            tejagan = kirim - chiqim
            await context.bot.send_message(
                chat_id=user_id,
                text=MESSAGES["uz"]["push_weekly"].format(
                    income=format_amount(kirim, user_id), 
                    expense=format_amount(chiqim, user_id), 
                    saved=format_amount(tejagan, user_id)
                ),
                parse_mode=ParseMode.HTML
            )
            success_count += 1
        except Exception as e:
            logger.exception(f"Weekly push error for user {user_id}: {e}")
            error_count += 1
    
    return success_count, error_count

async def send_monthly_goal_push_to_all(context):
    """Send monthly goal push to all onboarded users"""
    success_count = 0
    error_count = 0
    
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎯 Yangi oy keldi! Shu oy uchun yangi moliyaviy maqsad qo'yishga tayyormisiz?"
            )
            success_count += 1
        except Exception as e:
            logger.exception(f"Monthly goal push error for user {user_id}: {e}")
            error_count += 1
    
    return success_count, error_count

async def send_monthly_feedback_push_to_all(context):
    """Send monthly feedback push to all onboarded users"""
    success_count = 0
    error_count = 0
    
    for user_id in get_all_user_ids():
        if not is_onboarded(user_id):
            continue
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=MESSAGES["uz"]["feedback_push"]
            )
            success_count += 1
        except Exception as e:
            logger.exception(f"Monthly feedback push error for user {user_id}: {e}")
            error_count += 1
    
    return success_count, error_count

async def send_daily_push(context):
    """Scheduled daily push for all users"""
    await send_daily_push_to_all(context)

async def send_weekly_push(context):
    """Scheduled weekly push for all users"""
    await send_weekly_push_to_all(context)

async def send_monthly_goal_push(context):
    """Scheduled monthly goal push for all users"""
    await send_monthly_goal_push_to_all(context)

async def send_monthly_feedback_push(context):
    """Scheduled monthly feedback push for all users"""
    await send_monthly_feedback_push_to_all(context)

async def cancel_push(update, context):
    """Cancel push operation"""
    return ConversationHandler.END

# PUSH CONV HANDLER
push_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("push", push_command)],
    states={
        PUSH_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_topic_handler)],
        PUSH_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_confirm_handler)],
    },
    fallbacks=[CommandHandler("cancel", cancel_push)]
) 