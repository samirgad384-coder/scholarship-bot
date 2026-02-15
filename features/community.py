from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters
import sqlite3
import time


# ============================================
# ⚙️ إعدادات
# ============================================

GROUP_LINK = "https://t.me/+sqpOtr5zsathM2Vk"

SPAM_LIMIT = 5
SPAM_WINDOW = 10


# ============================================
# 🗄️ Database
# ============================================

def init_community_db():
    conn = sqlite3.connect("scholarship_bot.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS community_users(
        user_id INTEGER PRIMARY KEY,
        reputation INTEGER DEFAULT 0,
        messages INTEGER DEFAULT 0,
        badge TEXT DEFAULT "Member"
    )
    """)

    conn.commit()
    conn.close()


# ============================================
# 👥 صفحة المجتمع
# ============================================

async def show_community(update, context):
    query = update.callback_query
    await query.answer()

    text = """
🌍 مجتمع الطلاب العالمي

🚀 نظام مجتمع متطور:

⭐ نظام سمعة للمستخدمين
🏆 ترتيب أفضل الأعضاء
🎯 سؤال وجواب
🛡️ حماية من السبام
🎓 نظام Mentors
🏅 Badges للمستخدمين

انضم للمجتمع 👇
"""

    keyboard = [
        [InlineKeyboardButton("🚀 دخول الجروب", url=GROUP_LINK)],
        [InlineKeyboardButton("🏆 أفضل الأعضاء", callback_data="leaderboard")],
        [InlineKeyboardButton("⭐ نقاطي", callback_data="my_rep")],
        [InlineKeyboardButton("❓ اسأل سؤال", callback_data="ask_question")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="back_to_main")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================
# ⭐ Reputation System
# ============================================

def add_reputation(user_id, amount=1):
    conn = sqlite3.connect("scholarship_bot.db")
    cur = conn.cursor()

    cur.execute("INSERT OR IGNORE INTO community_users(user_id) VALUES(?)", (user_id,))
    cur.execute(
        "UPDATE community_users SET reputation = reputation + ? WHERE user_id=?",
        (amount, user_id)
    )

    conn.commit()
    conn.close()


async def my_reputation(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    conn = sqlite3.connect("scholarship_bot.db")
    cur = conn.cursor()

    cur.execute("SELECT reputation, badge FROM community_users WHERE user_id=?", (user_id,))
    data = cur.fetchone()
    conn.close()

    if not data:
        rep = 0
        badge = "Member"
    else:
        rep, badge = data

    await query.answer(
        f"⭐ نقاطك: {rep}\n🏅 رتبتك: {badge}",
        show_alert=True
    )


# ============================================
# 🏆 Leaderboard
# ============================================

async def leaderboard(update, context):
    query = update.callback_query
    await query.answer()

    conn = sqlite3.connect("scholarship_bot.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT user_id, reputation
    FROM community_users
    ORDER BY reputation DESC
    LIMIT 10
    """)

    users = cur.fetchall()
    conn.close()

    text = "🏆 أفضل أعضاء المجتمع\n\n"

    for i, (uid, rep) in enumerate(users, 1):
        text += f"{i}. 👤 {uid} — ⭐ {rep}\n"

    await query.edit_message_text(text)


# ============================================
# ❓ Q&A System
# ============================================

async def ask_question(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["ask_mode"] = True

    await query.edit_message_text(
        "❓ اكتب سؤالك الآن وسيرد عليك المجتمع."
    )


async def handle_question(update, context):
    if not context.user_data.get("ask_mode"):
        return

    context.user_data["ask_mode"] = False

    user = update.effective_user
    text = update.message.text

    add_reputation(user.id, 2)

    await update.message.reply_text(
        "✅ تم نشر سؤالك للمجتمع.\n⭐ حصلت على نقاط."
    )

    print(f"سؤال من {user.id}: {text}")


# ============================================
# 🛡️ Anti-Spam
# ============================================

user_messages = {}

def is_spam(user_id):
    now = time.time()

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id] = [
        t for t in user_messages[user_id] if now - t < SPAM_WINDOW
    ]

    user_messages[user_id].append(now)

    return len(user_messages[user_id]) > SPAM_LIMIT


async def anti_spam(update, context):
    user_id = update.effective_user.id

    if is_spam(user_id):
        await update.message.reply_text("⚠️ لا ترسل رسائل بسرعة كبيرة.")


# ============================================
# 🤖 Auto Replies
# ============================================

async def auto_reply(update, context):
    text = update.message.text.lower()

    if "منحة" in text:
        await update.message.reply_text("🎓 استخدم البحث الذكي لإيجاد المنح.")

    if "مساعدة" in text:
        await update.message.reply_text("📞 تواصل مع الدعم من القائمة.")


# ============================================
# 🎖️ Badge System
# ============================================

def update_badge(user_id):
    conn = sqlite3.connect("scholarship_bot.db")
    cur = conn.cursor()

    cur.execute("SELECT reputation FROM community_users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    if not data:
        return

    rep = data[0]

    badge = "Member"

    if rep > 100:
        badge = "Expert"
    elif rep > 50:
        badge = "Advanced"
    elif rep > 20:
        badge = "Active"

    cur.execute("UPDATE community_users SET badge=? WHERE user_id=?", (badge, user_id))
    conn.commit()
    conn.close()


# ============================================
# 📦 Register
# ============================================

def register(application):
    init_community_db()

    application.add_handler(
        CallbackQueryHandler(show_community, pattern="community")
    )

    application.add_handler(
        CallbackQueryHandler(my_reputation, pattern="my_rep")
    )

    application.add_handler(
        CallbackQueryHandler(leaderboard, pattern="leaderboard")
    )

    application.add_handler(
        CallbackQueryHandler(ask_question, pattern="ask_question")
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, anti_spam)
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply)
    )
