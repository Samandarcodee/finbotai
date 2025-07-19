"""
handlers/push.py
Handles push notification logic for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.constants import ParseMode
from db import get_all_user_ids, is_onboarded, get_user_settings, get_weekly_stats, DB_PATH
from utils import format_amount, get_navigation_keyboard, build_reply_keyboard
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
        reply_markup=build_reply_keyboard([
            ["🌞 Kunlik eslatma"],
            ["📊 Haftalik hisobot"],
            ["🏆 Oylik maqsad"],
            ["🙏 Fikr so'rash"],
            ["🏠 Bosh menyu"]
        ], resize=True, one_time=True, add_navigation=False)
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
        reply_markup=build_reply_keyboard([
            ["✅ Ha, yubor"],
            ["❌ Yo'q, bekor qil"]
        ], resize=True, one_time=True)
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
            elif topic == "🏆 Oylik maqsad":
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

async def show_push_menu(update: Update, user_id: int):
    """Show push notifications menu with navigation"""
    try:
        settings = get_user_settings(user_id)
        if not settings:
            await update.message.reply_text("❌ Foydalanuvchi sozlamalari topilmadi.")
            return
            
        notifications = settings.get('notifications', True)
        auto_reports = settings.get('auto_reports', False)
        notif_status = "✅ Yoqilgan" if notifications else "❌ O'chirilgan"
        auto_status = "✅ Yoqilgan" if auto_reports else "❌ O'chirilgan"
        text = (
            "🔔 <b>BILDIRISHNOMALAR</b>\n\n"
            f"🔔 Push bildirishnomalar: {notif_status}\n"
            f"📊 Avtomatik hisobotlar: {auto_status}\n\n"
            "Bildirishnomalarni sozlash uchun tugmalardan birini bosing:"
        )
        
        keyboard = [
            ["🔔 Push bildirishnomalar", "📊 Avtomatik hisobotlar"],
            ["⏰ Eslatmalar", "📱 Test bildirishnoma"]
        ] + get_navigation_keyboard()
        
        if update.message:
            await update.message.reply_text(
                text,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.exception(f"Push menu error: {e}")
        if update.message:
            await update.message.reply_text("❌ Bildirishnomalar menyusini ko'rishda xatolik.")

async def handle_push_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle push notifications menu with navigation"""
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
    
    # Handle push menu options
    if text == "🔔 Push bildirishnomalar":
        await toggle_push_notifications(update, user_id)
        return await show_push_menu(update, user_id)
        
    elif text == "📊 Avtomatik hisobotlar":
        await toggle_auto_reports(update, user_id)
        return await show_push_menu(update, user_id)
        
    elif text == "⏰ Eslatmalar":
        keyboard = [
            ["🕐 Har kuni", "📅 Haftada bir marta"],
            ["📊 Oy oxirida", "🎯 Maqsad eslatmalari"]
        ] + get_navigation_keyboard()
        
        await update.message.reply_text(
            "⏰ <b>ESLATMALAR</b>\n\n"
            "Qanday eslatmalar kerak?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="HTML"
        )
        return 1  # Reminders state
        
    elif text == "📱 Test bildirishnoma":
        await send_test_notification(update, user_id)
        return await show_push_menu(update, user_id)
        
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return await show_push_menu(update, user_id)

async def handle_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reminder settings with navigation"""
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
        return await show_push_menu(update, user_id)
    
    # Handle reminder options
    if text == "🕐 Har kuni":
        await set_daily_reminders(update, user_id)
    elif text == "📅 Haftada bir marta":
        await set_weekly_reminders(update, user_id)
    elif text == "📊 Oy oxirida":
        await set_monthly_reminders(update, user_id)
    elif text == "🎯 Maqsad eslatmalari":
        await set_goal_reminders(update, user_id)
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return 1  # Stay in reminders state
    
    return await show_push_menu(update, user_id)

async def toggle_push_notifications(update: Update, user_id: int):
    """Toggle push notifications with navigation"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current setting
        c.execute("SELECT notifications FROM user_settings WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if result:
            current = result[0]
            new_setting = not current
            
            c.execute("UPDATE user_settings SET notifications = ? WHERE user_id = ?", (new_setting, user_id))
            conn.commit()
            
            status = "✅ Yoqildi" if new_setting else "❌ O'chirildi"
            await update.message.reply_text(f"🔔 Push bildirishnomalar {status}")
        else:
            await update.message.reply_text("❌ Foydalanuvchi sozlamalari topilmadi.")
            
        conn.close()
        
    except Exception as e:
        logger.exception(f"Toggle notifications error: {e}")
        await update.message.reply_text("❌ Bildirishnomalarni o'zgartirishda xatolik.")

async def toggle_auto_reports(update: Update, user_id: int):
    """Toggle auto reports with navigation"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current setting
        c.execute("SELECT auto_reports FROM user_settings WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if result:
            current = result[0]
            new_setting = not current
            
            c.execute("UPDATE user_settings SET auto_reports = ? WHERE user_id = ?", (new_setting, user_id))
            conn.commit()
            
            status = "✅ Yoqildi" if new_setting else "❌ O'chirildi"
            await update.message.reply_text(f"📊 Avtomatik hisobotlar {status}")
        else:
            await update.message.reply_text("❌ Foydalanuvchi sozlamalari topilmadi.")
            
        conn.close()
        
    except Exception as e:
        logger.exception(f"Toggle auto reports error: {e}")
        await update.message.reply_text("❌ Avtomatik hisobotlarni o'zgartirishda xatolik.")

async def send_test_notification(update: Update, user_id: int):
    """Send test notification with navigation"""
    try:
        await update.message.reply_text(
            "📱 <b>Test bildirishnoma</b>\n\n"
            "✅ Bu test bildirishnoma. Agar siz buni ko'rsangiz, "
            "bildirishnomalar to'g'ri ishlayapti!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.exception(f"Test notification error: {e}")
        await update.message.reply_text("❌ Test bildirishnomani yuborishda xatolik.")

# PUSH CONV HANDLER
push_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("push", push_command)],
    states={
        PUSH_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_topic_handler)],
        PUSH_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_confirm_handler)],
    },
    fallbacks=[CommandHandler("cancel", cancel_push)]
) 