import sqlite3
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler

ADMIN_ID = 123456789  # غيرها لرقمك

DB_NAME = "scholarship_bot.db"


def is_admin(user_id):
    return user_id == ADMIN_ID


# ============================================
# ADMIN MENU
# ============================================

async def admin_menu(update, context):
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Analytics", callback_data="admin_stats")],
        [InlineKeyboardButton("👑 تفعيل Premium", callback_data="admin_add_premium")]
    ]

    await update.message.reply_text(
        "⚙️ لوحة تحكم الأدمن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================
# BROADCAST
# ============================================

async def start_broadcast(update, context):
    context.user_data["broadcast"] = True
    await update.callback_query.edit_message_text("اكتب الرسالة للإرسال للجميع")


async def broadcast_message(update, context):
    if "broadcast" not in context.user_data:
        return

    msg = update.message.text
    context.user_data.pop("broadcast")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            await context.bot.send_message(u[0], msg)
        except:
            pass

    await update.message.reply_text("✅ تم الإرسال")


# ============================================
# ANALYTICS
# ============================================

async def show_stats(update, context):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM premium_users")
    premium = cursor.fetchone()[0]

    conn.close()

    await update.callback_query.edit_message_text(
        f"📊 الإحصائيات:\n\n"
        f"👥 المستخدمين: {users}\n"
        f"💎 Premium: {premium}"
    )


# ============================================
# ADD PREMIUM USER
# ============================================

async def add_premium(update, context):
    context.user_data["add_premium"] = True
    await update.callback_query.edit_message_text("أرسل ID المستخدم")


async def save_premium(update, context):
    if "add_premium" not in context.user_data:
        return

    uid = int(update.message.text)
    context.user_data.pop("add_premium")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO premium_users VALUES (?)", (uid,))
    conn.commit()
    conn.close()

    await update.message.reply_text("تم التفعيل")


# ============================================
# REGISTER
# ============================================

def register(application):
    application.add_handler(CommandHandler("admin", admin_menu))

    application.add_handler(
        CallbackQueryHandler(start_broadcast, pattern="admin_broadcast")
    )

    application.add_handler(
        CallbackQueryHandler(show_stats, pattern="admin_stats")
    )

    application.add_handler(
        CallbackQueryHandler(add_premium, pattern="admin_add_premium")
    )

    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_premium))
