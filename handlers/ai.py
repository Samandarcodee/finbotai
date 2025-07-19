"""
handlers/ai.py
Handles AI advice and AI analysis for FinBot AI Telegram bot.
"""

import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from db import get_db_connection, get_user_settings, DB_PATH
from utils import format_amount
from ai_service import ai_service
from loguru import logger
import sqlite3
from datetime import datetime, timedelta
import json
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler

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

async def show_ai_menu(update: Update, user_id: int):
    """Show AI tools menu"""
    try:
        keyboard = [
            ["💰 AI Byudjet Tavsiyasi", "📊 AI Xarajatlar Tahlili"],
            ["🎯 AI Maqsad Monitoring", "💡 AI Moliyaviy Maslahat"],
            ["💎 AI Tejash Maslahatlari", "📈 AI Investitsiya Maslahati"],
            ["🔙 Orqaga"]
        ]
        
        if update.message:
            await update.message.reply_text(
                MESSAGES["uz"]["ai_menu"],
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.exception(f"AI menu error: {e}")

async def show_ai_analysis(update: Update, user_id: int):
    """Show AI-powered spending analysis with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
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
                await loading_msg.edit_text(MESSAGES["uz"]["no_data"])
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
            ai_analysis = MESSAGES["uz"]["ai_error"]
        
        if loading_msg:
            await loading_msg.edit_text(f"{MESSAGES['uz']['spending_analysis']}\n\n{ai_analysis}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f"AI analysis error: {e}")
        if loading_msg:
            await loading_msg.edit_text(MESSAGES["uz"]["ai_error"])

async def show_ai_advice(update: Update, user_id: int):
    """Show AI financial advice with loading and HTML/emoji formatting."""
    loading_msg = None
    try:
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

async def show_budget_advice(update: Update, user_id: int):
    """Show AI budget advice"""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current month data
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense,
                category, SUM(amount) as category_total
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ? AND type = 'expense'
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """, (user_id, current_month))
        category_data = c.fetchall()
        
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        conn.close()
        
        month_income = month_data[0] or 0
        month_expense = month_data[1] or 0
        
        # Generate budget advice
        if month_income == 0:
            advice = "💰 <b>Byudjet tavsiyasi:</b>\n\n❌ Oylik daromad ma'lumotlari yo'q. Avval daromadlaringizni kiritib, keyin qayta urinib ko'ring."
        else:
            savings_rate = ((month_income - month_expense) / month_income) * 100 if month_income > 0 else 0
            
            if savings_rate >= 20:
                status = "✅ Ajoyib! Siz yaxshi tejayapsiz."
            elif savings_rate >= 10:
                status = "👍 Yaxshi! Tejash darajangiz yaxshi."
            elif savings_rate >= 0:
                status = "⚠️ Ehtiyot! Xarajatlaringizni kamaytiring."
            else:
                status = "❌ Xavfli! Daromadlaringizdan ko'p xarajat qilyapsiz."
            
            advice = f"""💰 <b>AI Byudjet Tavsiyasi:</b>

📊 <b>Oylik hisobot:</b>
• Daromad: {format_amount(month_income, user_id)}
• Xarajat: {format_amount(month_expense, user_id)}
• Tejash: {format_amount(month_income - month_expense, user_id)}
• Tejash foizi: {savings_rate:.1f}%

{status}

💡 <b>Tavsiyalar:</b>"""
            
            if savings_rate < 10:
                advice += "\n• Xarajatlaringizni 20% kamaytiring"
                advice += "\n• Ortiqcha xarajatlarni aniqlang"
                advice += "\n• Daromadlaringizni oshiring"
            else:
                advice += "\n• Yaxshi ishlayapsiz!"
                advice += "\n• Investitsiya qilishni o'ylang"
                advice += "\n• Zaxira pul yig'ing"
        
        if loading_msg:
            await loading_msg.edit_text(advice, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.exception(f"Budget advice error: {e}")
        if loading_msg:
            await loading_msg.edit_text(MESSAGES["uz"]["ai_error"])

async def show_savings_tips(update: Update, user_id: int):
    """Show AI savings tips"""
    loading_msg = None
    try:
        if update.message:
            loading_msg = await update.message.reply_text(MESSAGES["uz"]["loading"])
        
        # Get user spending patterns
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 5
        """, (user_id,))
        top_categories = c.fetchall()
        conn.close()
        
        tips = f"""💎 <b>AI Tejash Maslahatlari:</b>

🎯 <b>Asosiy tavsiyalar:</b>
• Xarajatlaringizni kuzatib boring
• Ortiqcha xarajatlarni kamaytiring
• Daromadlaringizni oshiring
• Zaxira pul yig'ing

📊 <b>Eng ko'p xarajat qiladigan kategoriyalar:</b>"""

        for i, (category, amount) in enumerate(top_categories, 1):
            tips += f"\n{i}. {category}: {format_amount(amount, user_id)}"
        
        tips += """

💡 <b>Tejash usullari:</b>
• 50/30/20 qoidasi: 50% - asosiy xarajatlar, 30% - xohishlar, 20% - tejash
• Avtomatik tejash o'rnating
• Ortiqcha xarajatlarni aniqlang
• Daromadlaringizni diversifikatsiya qiling

🎯 <b>Maqsadlar:</b>
• Oylik daromadlaringizning 20%ini tejang
• 3-6 oylik xarajatlaringiz miqdorida zaxira pul yig'ing
• Uzoq muddatli maqsadlar uchun alohida hisob oching"""

        if loading_msg:
            await loading_msg.edit_text(tips, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.exception(f"Savings tips error: {e}")
        if loading_msg:
            await loading_msg.edit_text(MESSAGES["uz"]["ai_error"])

async def show_investment_advice(update: Update, user_id: int):
    """Show AI investment advice"""
    loading_msg = None
    try:
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

async def show_goal_monitoring(update: Update, user_id: int):
    """Show AI goal monitoring"""
    loading_msg = None
    try:
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

async def handle_ai_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI menu selections"""
    if not update.message or not update.message.text or not hasattr(update.message, 'from_user'):
        return ConversationHandler.END
    
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    
    if not user_id:
        return ConversationHandler.END
    
    if text == "💰 AI Byudjet Tavsiyasi":
        await show_budget_advice(update, user_id)
    elif text == "📊 AI Xarajatlar Tahlili":
        await show_ai_analysis(update, user_id)
    elif text == "🎯 AI Maqsad Monitoring":
        await show_goal_monitoring(update, user_id)
    elif text == "💡 AI Moliyaviy Maslahat":
        await show_ai_advice(update, user_id)
    elif text == "💎 AI Tejash Maslahatlari":
        await show_savings_tips(update, user_id)
    elif text == "📈 AI Investitsiya Maslahati":
        await show_investment_advice(update, user_id)
    elif text == "🔙 Orqaga":
        from handlers.start import start
        return await start(update, context)
    else:
        await update.message.reply_text("❌ Noto'g'ri tanlov. Qaytadan tanlang.")
    
    return ConversationHandler.END 