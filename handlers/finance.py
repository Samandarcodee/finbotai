"""
handlers/finance.py
Handles income/expense addition, balance, and analysis for FinBot AI Telegram bot.
"""

import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from datetime import datetime
from db import get_db_connection, get_user_settings, validate_amount, DB_PATH
from utils import format_amount, get_navigation_keyboard, build_reply_keyboard
from loguru import logger

# State constants
INCOME_AMOUNT, INCOME_NOTE = 101, 102
EXPENSE_AMOUNT, EXPENSE_NOTE = 201, 202

def get_category_keyboard(is_income=True):
    """Get category keyboard for income or expense with navigation"""
    if is_income:
        categories = [
            ["💵 Maosh", "🏦 Kredit/qarz"],
            ["🎁 Sovg'a/yordam", "💸 Qo'shimcha daromad"],
            ["💳 Boshqa daromad"]
        ]
    else:
        categories = [
            ["🍔 Oziq-ovqat", "🚗 Transport"],
            ["💊 Sog'liq", "📚 Ta'lim"],
            ["🎮 O'yin-kulgi", "👕 Kiyim"],
            ["🏠 Uy", "📱 Aloqa"],
            ["💳 Boshqa chiqim"]
        ]
    return build_reply_keyboard(categories, resize=True, one_time=True)

async def show_balance(update: Update, user_id: int):
    """Show user balance with improved formatting and navigation"""
    try:
        settings = get_user_settings(user_id)
        if not settings:
            await update.message.reply_text("❌ Foydalanuvchi sozlamalari topilmadi.")
            return
            
        currency = settings.get('currency', 'UZS')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        current_month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """, (user_id, current_month))
        month_data = c.fetchone()
        c.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
            FROM transactions 
            WHERE user_id = ?
        """, (user_id,))
        total_data = c.fetchone()
        conn.close()
        
        month_income = month_data[0] or 0
        month_expense = month_data[1] or 0
        month_balance = month_income - month_expense
        total_income = total_data[0] or 0
        total_expense = total_data[1] or 0
        total_balance = total_income - total_expense
        
        balance_text = (
            "📊 <b>BALANS HISOBOTI</b>\n\n"
            "🗓️ <b>Bu oy:</b>\n"
            f"💰 Kirim: {format_amount(month_income, user_id)}\n"
            f"💸 Chiqim: {format_amount(month_expense, user_id)}\n"
            f"💵 Balans: {format_amount(month_balance, user_id)}\n\n"
            "📈 <b>Jami:</b>\n"
            f"💰 Kirim: {format_amount(total_income, user_id)}\n"
            f"💸 Chiqim: {format_amount(total_expense, user_id)}\n"
            f"💵 Balans: {format_amount(total_balance, user_id)}\n\n"
            f"💡 <b>Maslahat:</b> {get_balance_advice(total_balance, month_balance)}"
        )
        
        # Add navigation buttons
        keyboard = [
            ["📈 Tahlil", "📊 Kategoriyalar"],
            ["💰 Kirim/Chiqim"]
        ]
        if update.message:
            await update.message.reply_text(
                balance_text, 
                parse_mode=ParseMode.HTML,
                reply_markup=build_reply_keyboard(keyboard, resize=True)
            )
    except sqlite3.Error as e:
        logger.exception(f"Balance error: {e}")
        if update.message:
            await update.message.reply_text("❌ Balansni ko'rishda xatolik. Qaytadan urinib ko'ring.")
    except Exception as e:
        logger.exception(f"Unexpected error in show_balance: {e}")
        if update.message:
            await update.message.reply_text("❌ Kutilmagan xatolik yuz berdi.")

def get_balance_advice(total_balance, month_balance):
    """Get personalized balance advice"""
    if total_balance < 0:
        return "Balansingiz salbiy. Tejash rejangizni ko'rib chiqing."
    elif month_balance < 0:
        return "Bu oy xarajatlar ko'p. Keyingi oyga reja tuzing."
    elif month_balance > total_balance * 0.3:
        return "Ajoyib! Bu oy yaxshi tejayapsiz."
    else:
        return "Balansingiz barqaror. Davom eting!"

async def show_analysis(update: Update, user_id: int):
    """Show transaction analysis with improved formatting and navigation"""
    try:
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
        
        # Get category statistics
        c.execute("""
            SELECT category, COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 5
        """, (user_id,))
        categories = c.fetchall()
        
        conn.close()
        
        if not transactions:
            keyboard = [
                ["💰 Kirim qo'shish", "💸 Chiqim qo'shish"]
            ]
            if update.message:
                await update.message.reply_text(
                    "📈 <b>TAHLIL</b>\n\n"
                    "Hali tranzaksiyalar yo'q. Avval kirim yoki chiqim qo'shing!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=build_reply_keyboard(keyboard, resize=True)
                )
            return
        
        analysis_text = "📈 <b>TAHLIL HISOBOTI</b>\n\n"
        
        # Recent transactions
        analysis_text += "🕐 <b>Oxirgi tranzaksiyalar:</b>\n"
        for t in transactions[:5]:
            emoji = "💰" if t[0] == "income" else "💸"
            # Safe date parsing
            try:
                date_obj = datetime.strptime(t[4], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%d.%m")
            except (ValueError, TypeError):
                date_str = "N/A"
            analysis_text += f"{emoji} {date_str} - {format_amount(t[1], user_id)} - {t[2]}\n"
        
        # Category analysis
        if categories:
            analysis_text += "\n🏷️ <b>Eng ko'p xarajat qilgan kategoriyalar:</b>\n"
            for cat, count, total in categories:
                analysis_text += f"• {cat}: {format_amount(total, user_id)} ({count} ta)\n"
        
        # Add navigation buttons
        keyboard = [
            ["📊 Balans", "📊 Kategoriyalar"],
            ["💰 Kirim/Chiqim"]
        ]
        if update.message:
            await update.message.reply_text(
                analysis_text,
                parse_mode=ParseMode.HTML,
                reply_markup=build_reply_keyboard(keyboard, resize=True)
            )
        
    except sqlite3.Error as e:
        logger.exception(f"Analysis error: {e}")
        if update.message:
            await update.message.reply_text("❌ Tahlilni ko'rishda xatolik. Qaytadan urinib ko'ring.")
    except Exception as e:
        logger.exception(f"Unexpected error in show_analysis: {e}")
        if update.message:
            await update.message.reply_text("❌ Kutilmagan xatolik yuz berdi.")

async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add income transaction"""
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END

    settings = get_user_settings(user_id)
    currency = settings['currency']
    text = update.message.text.strip()
    
    if text.lower() in ['/cancel', 'bekor', 'cancel', '❌ bekor qilish', '🏠 bosh menyu']:
        return await cancel(update, context)
    
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"❌ {error}\n\nQaytadan kiriting yoki 'Bekor qilish' tugmasini bosing.")
        return 1
    
    # Extract note from text
    parts = text.split(" ", 1)
    note = parts[1] if len(parts) > 1 else "Kirim"
    selected_category = context.user_data.get('selected_income_category', 'Boshqa daromad')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'income', ?, ?, ?)", 
                (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        
        success_text = f"""✅ KIRIM QO'SHILDI!

💰 Miqdor: {format_amount(amount, user_id)}
📂 Kategoriya: {selected_category}
📝 Izoh: {note}
📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 Davom eting - har bir kirim muhim!"""
        
        await update.message.reply_text(success_text)
        return ConversationHandler.END
        
    except sqlite3.Error as e:
        logger.exception(f"Income add error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def income_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle income category selection"""
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    if text in ["🔙 Orqaga", "❌ Bekor qilish", "🏠 Bosh menyu", "/start", "/cancel"]:
        return await cancel(update, context)
    
    income_category_map = {
        "💵 Maosh": "Maosh",
        "🏦 Kredit/qarz": "Kredit/qarz",
        "🎁 Sovg'a/yordam": "Sovg'a/yordam",
        "💸 Qo'shimcha daromad": "Qo'shimcha daromad",
        "💳 Boshqa daromad": "Boshqa daromad"
    }
    selected_category = income_category_map.get(text, "Boshqa daromad")
    context.user_data['selected_income_category'] = selected_category
    await update.message.reply_text(
        f"✅ Kategoriya: {selected_category}\n\nKirim miqdorini kiriting (masalan: 1 000 000):"
    )
    return INCOME_AMOUNT

async def income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle income amount input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text in ["🔙 Orqaga", "❌ Bekor qilish", "🏠 Bosh menyu", "/start", "/cancel"]:
        return await cancel(update, context)
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"❌ {error}\n\nQaytadan kiriting yoki 'Bekor qilish' tugmasini bosing.")
        return INCOME_AMOUNT
    context.user_data['income_amount'] = amount
    await update.message.reply_text(
        "Izoh qo'shmoqchimisiz? (Masalan: ish haqi, sovg'a, bonus)\n\nIzoh kiriting yoki 'Orqaga' tugmasini bosing."
    )
    return INCOME_NOTE

async def income_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle income note input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text in ["🔙 Orqaga"]:
        await update.message.reply_text(
            "Kirim miqdorini kiriting (masalan: 500000):"
        )
        return INCOME_AMOUNT
    if text in ["❌ Bekor qilish", "/cancel", "cancel", "🏠 Bosh menyu", "/start"]:
        return await cancel(update, context)
    
    note = text if text else "Kirim"
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    user_data = context.user_data if hasattr(context, 'user_data') and context.user_data is not None else {}
    selected_category = user_data.get('selected_income_category', 'Boshqa daromad')
    amount = user_data.get('income_amount', 0)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'income', ?, ?, ?)",
                  (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        
        success_text = f"""✅ KIRIM QO'SHILDI!

💰 Miqdor: {format_amount(amount, user_id)}
📂 Kategoriya: {selected_category}
📝 Izoh: {note}
📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 Davom eting - har bir kirim muhim!"""
        await update.message.reply_text(success_text)
        return ConversationHandler.END
    except sqlite3.Error as e:
        logger.exception(f"Income add error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def expense_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expense category selection"""
    if not update.message or not hasattr(update.message, 'from_user') or not update.message.text:
        return ConversationHandler.END
    text = update.message.text
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    if user_id is None:
        return ConversationHandler.END
    if text in ["🔙 Orqaga", "❌ Bekor qilish", "🏠 Bosh menyu", "/start", "/cancel"]:
        return await cancel(update, context)
    
    expense_category_map = {
        "🍔 Oziq-ovqat": "Oziq-ovqat",
        "🚗 Transport": "Transport",
        "💊 Sog'liq": "Sog'liq",
        "📚 Ta'lim": "Ta'lim",
        "🎮 O'yin-kulgi": "O'yin-kulgi",
        "👕 Kiyim": "Kiyim",
        "🏠 Uy": "Uy",
        "📱 Aloqa": "Aloqa",
        "💳 Boshqa chiqim": "Boshqa chiqim"
    }
    selected_category = expense_category_map.get(text, "Boshqa chiqim")
    context.user_data['selected_expense_category'] = selected_category
    await update.message.reply_text(
        f"✅ Kategoriya: {selected_category}\n\nChiqim miqdorini kiriting (masalan: 250 000):"
    )
    return EXPENSE_AMOUNT

async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expense amount input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text in ["🔙 Orqaga", "❌ Bekor qilish", "🏠 Bosh menyu", "/start", "/cancel"]:
        return await cancel(update, context)
    amount, error = validate_amount(text)
    if error:
        await update.message.reply_text(f"❌ {error}\n\nQaytadan kiriting yoki 'Bekor qilish' tugmasini bosing.")
        return EXPENSE_AMOUNT
    context.user_data['expense_amount'] = amount
    await update.message.reply_text(
        "Izoh qo'shmoqchimisiz? (Masalan: nonushta, yo'l puli)\n\nIzoh kiriting yoki 'Orqaga' tugmasini bosing."
    )
    return EXPENSE_NOTE

async def expense_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle expense note input"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    text = update.message.text.strip()
    if text in ["🔙 Orqaga"]:
        await update.message.reply_text(
            "Chiqim miqdorini kiriting (masalan: 250000):"
        )
        return EXPENSE_AMOUNT
    if text in ["❌ Bekor qilish", "/cancel", "cancel", "🏠 Bosh menyu", "/start"]:
        return await cancel(update, context)
    
    note = text if text else "Chiqim"
    user_id = getattr(getattr(update.message, 'from_user', None), 'id', None)
    user_data = context.user_data if hasattr(context, 'user_data') and context.user_data is not None else {}
    selected_category = user_data.get('selected_expense_category', 'Boshqa chiqim')
    amount = user_data.get('expense_amount', 0)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, note, category) VALUES (?, 'expense', ?, ?, ?)",
                  (user_id, amount, note, selected_category))
        conn.commit()
        conn.close()
        
        success_text = f"""✅ CHIQIM QO'SHILDI!

💸 Miqdor: {format_amount(amount, user_id)}
📂 Kategoriya: {selected_category}
📝 Izoh: {note}
📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 Xarajatlaringizni nazorat qiling!"""
        await update.message.reply_text(success_text)
        return ConversationHandler.END
    except sqlite3.Error as e:
        logger.exception(f"Expense add error: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return ConversationHandler.END

async def show_categories(update: Update, user_id: int):
    """Show category analysis"""
    try:
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT category, COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' 
            GROUP BY category 
            ORDER BY SUM(amount) DESC
        """, (user_id,))
        categories = c.fetchall()
        conn.close()
        
        if not categories:
            if update.message:
                await update.message.reply_text(
                    "📋 KATEGORIYALAR\n\n"
                    "Hali kategoriyalar yo'q. Chiqimlar qo'shing!"
                )
            return
        
        text = "📋 KATEGORIYALAR BO'YICHA XARAJAT:\n\n"
        total_expense = sum(cat[2] for cat in categories)
        
        for cat, count, total in categories:
            percentage = (total / total_expense * 100) if total_expense > 0 else 0
            text += f"🏷️ {cat}:\n"
            text += f"   💰 {format_amount(total, user_id)}\n"
            text += f"   📊 {percentage:.1f}% xarajat\n\n"
        
        if update.message:
            await update.message.reply_text(text)
        
    except sqlite3.Error as e:
        logger.exception(f"Categories error: {e}")
        if update.message:
            await update.message.reply_text("❌ Kategoriyalarni ko'rishda xatolik.")

async def show_budget_status(update: Update, user_id: int):
    """Show budget status"""
    try:
        current_month = datetime.now().strftime("%Y-%m")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT category, amount FROM budgets WHERE user_id = ? AND month = ?", (user_id, current_month))
        budgets = dict(c.fetchall())
        if not budgets:
            if update.message:
                await update.message.reply_text(
                    "🎯 Byudjet belgilanmagan. /setbudget orqali byudjet qo'shing."
                )
            return
        c.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
        """, (user_id, current_month))
        spending = dict(c.fetchall())
        conn.close()
        
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        text = f"🎯 <b>Byudjet holati ({current_month}):</b>\n\n"
        for category, budget_amount in budgets.items():
            spent = spending.get(category, 0)
            remaining = budget_amount - spent
            percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
            if percentage < 70:
                status = "🟢"
            elif percentage < 90:
                status = "🟡"
            else:
                status = "🔴"
            text += f"{status} <b>{category}</b>\nByudjet: {format_amount(budget_amount, user_id)}\nSarflangan: {format_amount(spent, user_id)} ({percentage:.1f}%)\nQolgan: {format_amount(remaining, user_id)}\n\n"
        if update.message:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except sqlite3.Error as e:
        logger.exception(f"Budget error: {e}")
        if update.message:
            await update.message.reply_text("❌ Byudjetni ko'rishda xatolik.")

async def export_data(update: Update, user_id: int):
    """Export user data"""
    try:
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
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
        
        if not transactions:
            if update.message:
                await update.message.reply_text(
                    "📤 EXPORT\n\n"
                    "Export qilish uchun ma'lumot yo'q."
                )
            return
        
        export_text = "📤 EXPORT HISOBOTI\n\n"
        export_text += f"Foydalanuvchi ID: {user_id}\n"
        export_text += f"Tranzaksiyalar soni: {len(transactions)}\n"
        export_text += f"Valyuta: {currency}\n\n"
        
        for t in transactions:
            emoji = "💰" if t[0] == "income" else "💸"
            # Safe date parsing
            try:
                date_obj = datetime.strptime(t[4], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%d.%m.%Y %H:%M")
            except (ValueError, TypeError):
                date_str = "N/A"
            export_text += f"{emoji} {date_str} - {format_amount(t[1], user_id)} - {t[2]} ({t[3]})\n"
        
        if update.message:
            await update.message.reply_text(export_text)
        
    except sqlite3.Error as e:
        logger.exception(f"Export error: {e}")
        if update.message:
            await update.message.reply_text("❌ Export qilishda xatolik.")

async def show_records(update: Update, user_id: int):
    """Show user records"""
    try:
        settings = get_user_settings(user_id)
        currency = settings['currency']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Biggest income and expense
        c.execute("SELECT MAX(amount), note FROM transactions WHERE user_id = ? AND type = 'income'", (user_id,))
        max_income = c.fetchone()
        
        c.execute("SELECT MAX(amount), note FROM transactions WHERE user_id = ? AND type = 'expense'", (user_id,))
        max_expense = c.fetchone()
        
        # Most active day
        c.execute("""
            SELECT DATE(date), COUNT(*) 
            FROM transactions 
            WHERE user_id = ? 
            GROUP BY DATE(date) 
            ORDER BY COUNT(*) DESC 
            LIMIT 1
        """, (user_id,))
        active_day = c.fetchone()
        
        # Total transactions
        c.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
        total_transactions = c.fetchone()[0]
        
        # Monthly average
        c.execute("""
            SELECT AVG(monthly_total) FROM (
                SELECT strftime('%Y-%m', date) as month, SUM(amount) as monthly_total
                FROM transactions 
                WHERE user_id = ? AND type = 'expense'
                GROUP BY strftime('%Y-%m', date)
            )
        """, (user_id,))
        avg_monthly = c.fetchone()[0] or 0
        
        conn.close()
        
        text = "🏆 REKORDLARINGIZ:\n\n"
        
        if max_income and max_income[0]:
            text += f"💰 Eng katta kirim: {format_amount(max_income[0], user_id)}\n"
            text += f"   📝 {max_income[1]}\n\n"
        
        if max_expense and max_expense[0]:
            text += f"💸 Eng katta chiqim: {format_amount(max_expense[0], user_id)}\n"
            text += f"   📝 {max_expense[1]}\n\n"
        
        if active_day and active_day[1]:
            try:
                date_obj = datetime.strptime(active_day[0], "%Y-%m-%d")
                date_str = date_obj.strftime("%d.%m.%Y")
            except (ValueError, TypeError):
                date_str = "N/A"
            text += f"📅 Eng faol kun: {date_str} ({active_day[1]} ta tranzaksiya)\n\n"
        
        text += f"📊 Jami tranzaksiyalar: {total_transactions} ta\n"
        text += f"📈 O'rtacha oylik xarajat: {format_amount(int(avg_monthly), user_id)}"
        
        if update.message:
            await update.message.reply_text(text)
        
    except sqlite3.Error as e:
        logger.exception(f"Records error: {e}")
        if update.message:
            await update.message.reply_text("❌ Rekordlarni ko'rishda xatolik.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation and return to main menu with navigation"""
    if not update.message:
        return ConversationHandler.END
    
    user_id = getattr(update.message.from_user, 'id', None)
    if not user_id:
        return ConversationHandler.END
    
    # Universal navigation
    if update.message.text in ["🏠 Bosh menyu", "/start"]:
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    elif update.message.text == "🔙 Orqaga":
        # Return to previous menu based on context
        from handlers.start import show_main_menu
        return await show_main_menu(update, context)
    else:
        # Default cancel behavior
        from handlers.start import show_main_menu
        return await show_main_menu(update, context) 