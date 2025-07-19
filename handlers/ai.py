"""
handlers/ai.py
Handles AI advice and AI analysis for FinBot AI Telegram bot.
"""

import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from utils import format_amount, get_navigation_keyboard, build_reply_keyboard
from ai_service import ai_service
from loguru import logger
import sqlite3
from datetime import datetime, timedelta
import json
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from utils import get_navigation_keyboard

# MESSAGES constant
MESSAGES = {
    "uz": {
        "ai_menu": "🤖 <b>AI VOSITALAR</b>\n\nQuyidagi AI funksiyalaridan birini tanlang:",
        "loading": "🧠 AI hisob-kitob qilmoqda...",
        "no_data": "❌ AI tahlil uchun ma'lumot yetarli emas. Avval kirim/chiqim qo'shing!",
        "ai_error": "❌ AI xizmatida muammo bor. Keyinroq urinib ko'ring.",
        "budget_advice": "💰 <b>AI Byudjet Tavsiyasi:</b>",
        "spending_analysis": "📊 <b>AI Xarajatlar Tahlili:</b>",
        "goal_monitoring": "🎯 <b>AI Maqsad Monitoring:</b>",
        "financial_advice": "💡 <b>AI Moliyaviy Maslahat:</b>",
        "savings_tips": "💎 <b>AI Tejash Maslahatlari:</b>",
        "investment_advice": "📈 <b>AI Investitsiya Maslahati:</b>",
        "back_to_ai": "🔙 AI menyuga qaytish"
    },
    "ru": {
        "ai_menu": "🤖 <b>AI ИНСТРУМЕНТЫ</b>\n\nВыберите одну из AI функций:",
        "loading": "🧠 AI вычисляет...",
        "no_data": "❌ Недостаточно данных для AI анализа. Сначала добавьте доходы/расходы!",
        "ai_error": "❌ Проблема с AI сервисом. Попробуйте позже.",
        "budget_advice": "💰 <b>AI Рекомендации по бюджету:</b>",
        "spending_analysis": "📊 <b>AI Анализ расходов:</b>",
        "goal_monitoring": "🎯 <b>AI Мониторинг целей:</b>",
        "financial_advice": "💡 <b>AI Финансовый совет:</b>",
        "savings_tips": "💎 <b>AI Советы по экономии:</b>",
        "investment_advice": "📈 <b>AI Инвестиционный совет:</b>",
        "back_to_ai": "🔙 Вернуться в AI меню"
    },
    "en": {
        "ai_menu": "🤖 <b>AI TOOLS</b>\n\nSelect one of the AI functions:",
        "loading": "🧠 AI is calculating...",
        "no_data": "❌ Not enough data for AI analysis. Add income/expenses first!",
        "ai_error": "❌ AI service issue. Try again later.",
        "budget_advice": "💰 <b>AI Budget Advice:</b>",
        "spending_analysis": "📊 <b>AI Spending Analysis:</b>",
        "goal_monitoring": "🎯 <b>AI Goal Monitoring:</b>",
        "financial_advice": "💡 <b>AI Financial Advice:</b>",
        "savings_tips": "💎 <b>AI Savings Tips:</b>",
        "investment_advice": "📈 <b>AI Investment Advice:</b>",
        "back_to_ai": "🔙 Back to AI menu"
    }
}

async def show_ai_menu(update, context):
    """Show AI tools menu with improved error handling and navigation"""
    try:
        from constants import get_message
        from utils import get_user_language
        
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        language = get_user_language(user_id)
        ai_menu_text = get_message("ai_menu", user_id)
        
        # Create AI menu keyboard
        keyboard = [
            ["💡 AI Moliyaviy Maslahat", "📊 AI Xarajatlar Tahlili"],
            ["💰 AI Byudjet Tavsiyasi", "🏆 AI Maqsad Monitoring"],
            ["💡 AI Tejash Maslahatlari", "📈 AI Investitsiya Maslahati"],
            ["🏠 Bosh menyu"]
        ]
        if update.message:
            await update.message.reply_text(
                ai_menu_text,
                reply_markup=build_reply_keyboard(keyboard, resize=True, one_time=True, add_navigation=False),
                parse_mode="HTML"
            )
        return 100  # AI menu state
        
    except Exception as e:
        logger.exception(f"AI menu error: {e}")
        if update.message:
            await update.message.reply_text("❌ AI menyusini ko'rishda xatolik.")
        return ConversationHandler.END

async def show_ai_analysis(update, context):
    """Show AI-powered spending analysis with improved functionality"""
    try:
        from constants import MESSAGES
        from utils import get_user_language, format_amount
        
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        language = get_user_language(user_id)
        
        # Show loading message
        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        # Get user data for AI analysis
        settings = get_user_settings(user_id)
        if not settings:
            await update.message.reply_text("❌ Foydalanuvchi sozlamalari topilmadi.")
            return
            
        currency = settings.get('currency', 'UZS')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get recent transactions
        c.execute("""
            SELECT type, amount, note, category, date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 10
        """, (user_id,))
        transactions = c.fetchall()
        
        # Get spending patterns
        c.execute("""
            SELECT category, COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 5
        """, (user_id,))
        categories = c.fetchall()
        
        # Get monthly trends
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        
        conn.close()
        
        if not transactions:
            analysis_text = "📊 <b>AI XARAJATLAR TAHLILI</b>\n\n"
            analysis_text += "❌ <b>Hozircha tranzaksiyalar yo'q</b>\n\n"
            analysis_text += "💡 <b>Tavsiyalar:</b>\n"
            analysis_text += "• Avval kirim va chiqimlaringizni kiritib bosing\n"
            analysis_text += "• AI sizga xarajatlar patternlarini tahlil qiladi\n"
            analysis_text += "• Tejash imkoniyatlarini topadi\n"
        else:
            # Analyze the most recent transaction for demo
            latest_transaction = transactions[0]
            transaction_type = latest_transaction[0]
            amount = latest_transaction[1]
            note = latest_transaction[2]
            category = latest_transaction[3]
            
            # Parse date
            try:
                date_obj = datetime.strptime(latest_transaction[4], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%d-%B")
            except (ValueError, TypeError):
                date_str = "N/A"
            
            analysis_text = "📊 <b>AI XARAJATLAR TAHLILI</b>\n\n"
            analysis_text += "🔍 <b>So'nggi tranzaksiya tahlili:</b>\n\n"
            analysis_text += f"• <b>Daromad turi</b>: {'Kirim' if transaction_type == 'income' else 'Chiqim'}\n"
            analysis_text += f"• <b>Sana</b>: {date_str}\n"
            analysis_text += f"• <b>Miqdor</b>: {format_amount(amount, user_id)}\n"
            analysis_text += f"• <b>Izoh</b>: \"{note}\"\n"
            analysis_text += f"• <b>Kategoriya</b>: {category}\n\n"
            
            # Add spending patterns
            if categories:
                analysis_text += "📈 <b>Xarajatlar patternlari:</b>\n"
                for i, (cat, count, total) in enumerate(categories[:3], 1):
                    analysis_text += f"{i}. {cat}: {format_amount(total, user_id)} ({count} ta)\n"
                analysis_text += "\n"
            
            # Add monthly summary
            if month_data:
                month_income = month_data[0] or 0
                month_expense = month_data[1] or 0
                month_balance = month_income - month_expense
                
                analysis_text += "📅 <b>Bu oy statistikasi:</b>\n"
                analysis_text += f"💰 Kirim: {format_amount(month_income, user_id)}\n"
                analysis_text += f"💸 Chiqim: {format_amount(month_expense, user_id)}\n"
                analysis_text += f"💵 Balans: {format_amount(month_balance, user_id)}\n\n"
            
            # Add AI insights
            analysis_text += "🧠 <b>AI tushunchalari:</b>\n"
            if transaction_type == 'income':
                analysis_text += "✅ Yaxshi! Daromad qo'shdingiz\n"
                analysis_text += "💡 Daromadlaringizni diversifikatsiya qilishni o'ylang\n"
            else:
                analysis_text += "💸 Xarajat qildingiz\n"
                analysis_text += "💡 Xarajatlaringizni optimallashtirish imkoniyatlarini ko'rib chiqing\n"
            
            analysis_text += "\n📊 <b>Umumiy xulosa:</b>\n"
            analysis_text += f"{date_str}da \"{category}\" kategoriyasida {format_amount(amount, user_id)} miqdorida "
            analysis_text += f"{'kirim' if transaction_type == 'income' else 'chiqim'} amalga oshirilgan. "
            analysis_text += f"Operatsiyaga \"{note}\" degan izoh berilgan."
        
        # Add navigation buttons
        keyboard = [
            ["🧠 AI Maslahat", "💰 AI Byudjet"],
            ["🔙 Orqaga", "🏠 Bosh menyu"]
        ]
        
        if update.message:
            await update.message.reply_text(
                analysis_text,
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.exception(f"AI analysis error: {e}")
        if update.message:
            await update.message.reply_text("❌ AI tahlilini olishda xatolik.")

async def show_ai_advice(update, context):
    """Show AI financial advice with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
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
            await loading_msg.edit_text(f"{MESSAGES['uz']['financial_advice']}\n\n{ai_advice}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f"AI advice error: {e}")
        if loading_msg:
            await loading_msg.edit_text(MESSAGES["uz"]["ai_error"])

async def show_budget_advice(update, context):
    """Show AI budget advice with improved error handling"""
    try:
        from constants import MESSAGES
        from utils import get_user_language, format_amount
        
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        language = get_user_language(user_id)
        
        # Show loading message
        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        # Get user's financial data
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
        
        # Get category breakdown
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category 
            ORDER BY SUM(amount) DESC
        """, (user_id, current_month))
        categories = c.fetchall()
        
        conn.close()
        
        month_income = month_data[0] or 0
        month_expense = month_data[1] or 0
        month_balance = month_income - month_expense
        
        # Generate AI advice
        advice_text = "💰 <b>AI BYUDJET TAVSIYASI</b>\n\n"
        
        if month_income == 0:
            advice_text += "📝 <b>Hozircha ma'lumot yo'q</b>\n\n"
            advice_text += "💡 <b>Tavsiyalar:</b>\n"
            advice_text += "• Avval kirim va chiqimlaringizni kiritib bosing\n"
            advice_text += "• AI sizga shaxsiy byudjet tavsiyalari beradi\n"
            advice_text += "• Tejash imkoniyatlarini topadi\n"
        else:
            savings_rate = (month_balance / month_income * 100) if month_income > 0 else 0
            
            advice_text += f"📊 <b>Bu oy statistikasi:</b>\n"
            advice_text += f"💰 Kirim: {format_amount(month_income, user_id)}\n"
            advice_text += f"💸 Chiqim: {format_amount(month_expense, user_id)}\n"
            advice_text += f"💵 Balans: {format_amount(month_balance, user_id)}\n"
            advice_text += f"📈 Tejash: {savings_rate:.1f}%\n\n"
            
            # Category analysis
            if categories:
                advice_text += "🏷️ <b>Xarajatlar tuzilishi:</b>\n"
                for category, amount in categories[:5]:
                    percentage = (amount / month_expense * 100) if month_expense > 0 else 0
                    advice_text += f"• {category}: {format_amount(amount, user_id)} ({percentage:.1f}%)\n"
                advice_text += "\n"
            
            # AI recommendations
            advice_text += "🧠 <b>AI TAVSIYALARI:</b>\n"
            
            if savings_rate < 10:
                advice_text += "⚠️ Tejashingiz juda kam. Quyidagilarni ko'rib chiqing:\n"
                advice_text += "• Ortiqcha xarajatlarni kamaytiring\n"
                advice_text += "• Daromadlarni oshirish imkoniyatlarini qidiring\n"
                advice_text += "• Byudjet rejangizni qayta ko'rib chiqing\n"
            elif savings_rate < 30:
                advice_text += "✅ Tejashingiz yaxshi. Davom eting:\n"
                advice_text += "• Mavjud tejash darajasini saqlang\n"
                advice_text += "• Qo'shimcha tejash imkoniyatlarini qidiring\n"
                advice_text += "• Investitsiya imkoniyatlarini ko'rib chiqing\n"
            else:
                advice_text += "🎉 Ajoyib! Siz juda yaxshi tejayapsiz:\n"
                advice_text += "• Mavjud darajani saqlang\n"
                advice_text += "• Investitsiya imkoniyatlarini ko'rib chiqing\n"
                advice_text += "• Moliyaviy maqsadlaringizni oshiring\n"
        
        # Add navigation buttons
        keyboard = [
            ["🧠 AI Maslahat", "📊 AI Tahlil"],
            ["🔙 Orqaga", "🏠 Bosh menyu"]
        ]
        
        if update.message:
            await update.message.reply_text(
                advice_text,
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.exception(f"Budget advice error: {e}")
        if update.message:
            await update.message.reply_text("❌ Byudjet tavsiyasini olishda xatolik.")

async def show_savings_tips(update, context):
    """Show AI savings tips with improved error handling"""
    try:
        from constants import MESSAGES
        from utils import get_user_language
        
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        language = get_user_language(user_id)
        
        # Show loading message
        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        # Generate savings tips
        tips_text = "💡 <b>AI TEJASH MASLAHATLARI</b>\n\n"
        
        tips_text += "🎯 <b>Asosiy tamoyillar:</b>\n"
        tips_text += "• 50/30/20 qoidasi: 50% xarajatlar, 30% xohishlar, 20% tejash\n"
        tips_text += "• Avtomatik tejash: har oy ma'lum miqdorni ajrating\n"
        tips_text += "• Zavod qoidasi: har xarajatdan 10% tejash\n\n"
        
        tips_text += "💰 <b>Amaliy maslahatlar:</b>\n"
        tips_text += "• Kunlik xarajatlarni kuzatib boring\n"
        tips_text += "• Ortiqcha xarajatlarni aniqlang va kamaytiring\n"
        tips_text += "• Uy xarajatlarini optimallashtiring\n"
        tips_text += "• Transport xarajatlarini kamaytiring\n"
        tips_text += "• Oziq-ovqat xarajatlarini optimallashtiring\n\n"
        
        tips_text += "📱 <b>Zamonaviy usullar:</b>\n"
        tips_text += "• Tejash ilovalaridan foydalaning\n"
        tips_text += "• Karta cashback imkoniyatlaridan foydalaning\n"
        tips_text += "• Online xarid qilganda chegirmalarni qidiring\n"
        tips_text += "• Ortiqcha obunalarni bekor qiling\n\n"
        
        tips_text += "🎯 <b>Uzoq muddatli reja:</b>\n"
        tips_text += "• Favqulodda vaziyatlar uchun 3-6 oylik zaxira\n"
        tips_text += "• Pensiya uchun alohida tejash\n"
        tips_text += "• Investitsiya imkoniyatlarini ko'rib chiqing\n"
        
        # Add navigation buttons
        keyboard = [
            ["💰 AI Byudjet", "🧠 AI Maslahat"],
            ["🔙 Orqaga", "🏠 Bosh menyu"]
        ]
        
        if update.message:
            await update.message.reply_text(
                tips_text,
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.exception(f"Savings tips error: {e}")
        if update.message:
            await update.message.reply_text("❌ Tejash maslahatlarini olishda xatolik.")

async def show_investment_advice(update, context):
    """Show AI investment advice"""
    loading_msg = None
    try:
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get user financial data
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        financial_data = c.fetchone()
        conn.close()
        
        total_income = financial_data[0] or 0
        total_expense = financial_data[1] or 0
        savings = total_income - total_expense
        
        if savings <= 0:
            advice = """📈 <b>AI Investitsiya Maslahati:</b>

❌ <b>Hozircha investitsiya qilish uchun yetarli mablag' yo'q.</b>

💡 <b>Avval quyidagilarni amalga oshiring:</b>
• Xarajatlaringizni kamaytiring
• Daromadlaringizni oshiring
• 3-6 oylik zaxira pul yig'ing
• Qarzlaringizni to'lang

🎯 <b>Keyingi qadamlar:</b>
• Tejash darajangizni 20%ga yetkazing
• Zaxira pul yig'ing
• Moliyaviy maqsadlar qo'ying"""
        else:
            monthly_savings = savings / 12 if savings > 0 else 0
            
            advice = f"""📈 <b>AI Investitsiya Maslahati:</b>

💰 <b>Moliyaviy holat:</b>
• Jami daromad: {format_amount(total_income, user_id)}
• Jami xarajat: {format_amount(total_expense, user_id)}
• Tejash: {format_amount(savings, user_id)}
• O'rtacha oylik tejash: {format_amount(monthly_savings, user_id)}

💡 <b>Investitsiya tavsiyalari:</b>

🎯 <b>Boshlang'ich daraja:</b>
• Bank depozitlari (5-10% yillik)
• Davlat obligatsiyalari
• Pul bozor fondlari

📊 <b>O'rta daraja:</b>
• Aksiyalar (diversifikatsiya bilan)
• ETF fondlari
• Real estate investitsiyalari

🚀 <b>Yuqori daraja:</b>
• Kripto valyutalar (kichik miqdorda)
• Venture capital
• Xalqaro investitsiyalar

⚠️ <b>Eslatma:</b>
• Investitsiya qilishdan oldin moliyaviy maslahatchi bilan maslahatlashing
• Risk darajangizga mos investitsiya tanlang
• Diversifikatsiya qilishni unutmang"""

        if loading_msg:
            await loading_msg.edit_text(advice, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.exception(f"Investment advice error: {e}")
        if loading_msg:
            await loading_msg.edit_text(MESSAGES["uz"]["ai_error"])

async def show_goal_monitoring(update, context):
    """Show AI goal monitoring"""
    loading_msg = None
    try:
        user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
        if not user_id:
            return ConversationHandler.END

        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get user goals
        c.execute("""
            SELECT name, target_amount, current_amount, deadline, created_at
            FROM goals 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        goals = c.fetchall()
        conn.close()
        
        if not goals:
            advice = """🎯 <b>AI Maqsad Monitoring:</b>

❌ <b>Hozircha maqsadlar yo'q.</b>

💡 <b>Maqsad qo'yish tavsiyalari:</b>
• Qisqa muddatli maqsadlar (3-6 oy)
• O'rta muddatli maqsadlar (1-3 yil)
• Uzoq muddatli maqsadlar (5+ yil)

🎯 <b>Maqsad turlari:</b>
• Tejash maqsadlari
• Investitsiya maqsadlari
• Xarid maqsadlari
• Ta'lim maqsadlari

📊 <b>Maqsad qo'yish qoidalari:</b>
• Aniq va o'lchanadigan bo'lishi
• Vaqt chegarasi bo'lishi
• Realistik bo'lishi
• Yozib qo'yilgan bo'lishi"""
        else:
            advice = f"""🎯 <b>AI Maqsad Monitoring:</b>

📊 <b>Maqsadlar holati:</b>"""

            for i, (name, target, current, deadline, created) in enumerate(goals, 1):
                progress = (current / target * 100) if target > 0 else 0
                remaining = target - current
                
                # Calculate days remaining
                try:
                    deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                    days_remaining = (deadline_date - datetime.now()).days
                    deadline_status = f"⏰ {days_remaining} kun qoldi" if days_remaining > 0 else "⏰ Vaqt tugadi"
                except:
                    deadline_status = "⏰ Vaqt aniqlanmagan"
                
                status_emoji = "✅" if progress >= 100 else "🔄" if progress >= 50 else "⏳"
                
                advice += f"""

{i}. <b>{name}</b>
{status_emoji} Progress: {progress:.1f}%
💰 Joriy: {format_amount(current, user_id)} / {format_amount(target, user_id)}
💵 Qolgan: {format_amount(remaining, user_id)}
{deadline_status}"""

            advice += """

💡 <b>Monitoring tavsiyalari:</b>
• Maqsadlaringizni muntazam tekshiring
• Progressni kuzatib boring
• Kerak bo'lsa maqsadlarni o'zgartiring
• Muvaffaqiyatni nishonlang"""

        if loading_msg:
            await loading_msg.edit_text(advice, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.exception(f"Goal monitoring error: {e}")
        if loading_msg:
            await loading_msg.edit_text(MESSAGES["uz"]["ai_error"])

async def handle_ai_menu(update, context):
    """Handle AI menu selections with universal navigation"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    if text == "🔙 Orqaga":
        return await show_ai_menu(update, context)
    
    if text == "💰 AI Byudjet Tavsiyasi":
        await show_budget_advice(update, context)
    elif text == "📊 AI Xarajatlar Tahlili":
        await show_ai_analysis(update, context)
    elif text == "🎯 AI Maqsad Monitoring":
        await show_goal_monitoring(update, context)
    elif text == "💡 AI Moliyaviy Maslahat":
        await show_ai_advice(update, context)
    elif text == "💡 AI Tejash Maslahatlari":
        await show_savings_tips(update, context)
    elif text == "📈 AI Investitsiya Maslahati":
        await show_investment_advice(update, context)
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
        return 100  # Return to AI menu state
    
    return 100  # Return to AI menu state for other selections 