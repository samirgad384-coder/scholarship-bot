import sqlite3
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler

DB_NAME = "scholarship_bot.db"


# ============================================
# DATABASE
# ============================================

def init_premium_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS premium_users (
        user_id INTEGER PRIMARY KEY
    )
    """)

    conn.commit()
    conn.close()


def is_premium(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM premium_users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None


# ============================================
# UI
# ============================================

async def premium_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📊 تحليل متقدم", callback_data="premium_analysis")],
        [InlineKeyboardButton("📄 CV احترافي", callback_data="premium_cv")],
        [InlineKeyboardButton("🎓 استشارة", callback_data="premium_consult")]
    ]

    await update.callback_query.edit_message_text(
        "💎 خدمات Premium:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================
# PREMIUM FEATURES
# ============================================

async def premium_analysis(update, context):
    if not is_premium(update.effective_user.id):
        await update.callback_query.answer("هذه الميزة للمشتركين فقط", show_alert=True)
        return

    await update.callback_query.edit_message_text(
        "📊 تحليل متقدم:\n\n"
        "• تقييم فرص القبول\n"
        "• تحليل نقاط القوة\n"
        "• خطة تحسين\n"
    )


async def premium_cv(update, context):
    if not is_premium(update.effective_user.id):
        await update.callback_query.answer("هذه الميزة للمشتركين فقط", show_alert=True)
        return

    await update.callback_query.edit_message_text(
        "📄 أرسل CV الخاص بك لتحليله."
    )


async def premium_consult(update, context):
    if not is_premium(update.effective_user.id):
        await update.callback_query.answer("هذه الميزة للمشتركين فقط", show_alert=True)
        return

    await update.callback_query.edit_message_text(
        "🎓 سيتم التواصل معك للاستشارة."
    )


# ============================================
# REGISTER
# ============================================

def register(application):
    init_premium_db()

    application.add_handler(
        CallbackQueryHandler(premium_menu, pattern="premium")
    )

    application.add_handler(
        CallbackQueryHandler(premium_analysis, pattern="premium_analysis")
    )

    application.add_handler(
        CallbackQueryHandler(premium_cv, pattern="premium_cv")
    )

    application.add_handler(
        CallbackQueryHandler(premium_consult, pattern="premium_consult")
    )
