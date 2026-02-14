import sqlite3
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, MessageHandler, filters

DB_NAME = "scholarship_bot.db"


# ============================================
# DATABASE
# ============================================

def init_dream_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_dream_profile (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        age INTEGER,
        score REAL,
        current_country TEXT,
        target_country TEXT,
        major TEXT,
        stage TEXT,
        english_level TEXT,
        budget TEXT,
        experience TEXT,
        rating INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# ============================================
# ENTRY POINT
# ============================================

async def start_dream_search(update, context):
    context.user_data.clear()
    context.user_data["dream_step"] = "name"

    await update.callback_query.edit_message_text(
        "✨ مرحباً بك في نظام تحقيق حلم الدراسة بالخارج\n\n"
        "هذا النظام سيبحث لك عن أفضل المنح المناسبة لك بدقة عالية.\n\n"
        "لنبدأ 👇\n\n"
        "اكتب اسمك الكامل:"
    )


# ============================================
# FLOW ENGINE
# ============================================

async def dream_flow(update, context):
    if "dream_step" not in context.user_data:
        return

    step = context.user_data["dream_step"]
    text = update.message.text

    if step == "name":
        context.user_data["name"] = text
        context.user_data["dream_step"] = "age"
        await update.message.reply_text("كم عمرك؟")

    elif step == "age":
        context.user_data["age"] = text
        context.user_data["dream_step"] = "score"
        await update.message.reply_text("ما مجموعك أو معدلك الدراسي؟")

    elif step == "score":
        context.user_data["score"] = text
        context.user_data["dream_step"] = "current_country"
        await update.message.reply_text("ما بلدك الحالية؟")

    elif step == "current_country":
        context.user_data["current_country"] = text
        context.user_data["dream_step"] = "target_country"
        await update.message.reply_text("الدولة التي تريد الدراسة فيها (اكتب تخطي لو مش مهم)")

    elif step == "target_country":
        context.user_data["target_country"] = None if text == "تخطي" else text
        context.user_data["dream_step"] = "major"
        await update.message.reply_text("ما تخصصك؟")

    elif step == "major":
        context.user_data["major"] = text
        context.user_data["dream_step"] = "stage"
        await update.message.reply_text("المرحلة الدراسية؟ (بكالوريوس / ماجستير / دكتوراه)")

    elif step == "stage":
        context.user_data["stage"] = text
        context.user_data["dream_step"] = "english"
        await update.message.reply_text("مستوى اللغة الإنجليزية؟ (ضعيف / متوسط / قوي)")

    elif step == "english":
        context.user_data["english"] = text
        context.user_data["dream_step"] = "budget"
        await update.message.reply_text("هل تفضل منح ممولة بالكامل فقط؟ (نعم / لا)")

    elif step == "budget":
        context.user_data["budget"] = text
        context.user_data["dream_step"] = "experience"
        await update.message.reply_text("هل لديك خبرات أو شهادات إضافية؟")

    elif step == "experience":
        context.user_data["experience"] = text
        context.user_data.pop("dream_step")

        await save_profile(update, context)
        await run_matching(update, context)


# ============================================
# SAVE PROFILE
# ============================================

async def save_profile(update, context):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO user_dream_profile
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        update.effective_user.id,
        context.user_data.get("name"),
        context.user_data.get("age"),
        context.user_data.get("score"),
        context.user_data.get("current_country"),
        context.user_data.get("target_country"),
        context.user_data.get("major"),
        context.user_data.get("stage"),
        context.user_data.get("english"),
        context.user_data.get("budget"),
        context.user_data.get("experience"),
        None,
        datetime.now().strftime("%Y-%m-%d")
    ))

    conn.commit()
    conn.close()


# ============================================
# MATCHING ENGINE
# ============================================

def calculate_match_score(user_major, sch_major, target_country, sch_country):
    score = 0

    if user_major and sch_major and user_major.lower() in sch_major.lower():
        score += 40

    if target_country and sch_country and target_country.lower() in sch_country.lower():
        score += 40

    score += 20
    return score


async def run_matching(update, context):
    await update.message.reply_text("🔍 جاري تحليل فرصك واختيار أفضل المنح لك...")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scholarships")
    scholarships = cursor.fetchall()
    conn.close()

    if not scholarships:
        await update.message.reply_text("لا توجد منح حالياً.")
        return

    user_major = context.user_data.get("major")
    target_country = context.user_data.get("target_country")

    ranked = []

    for sch in scholarships:
        match = calculate_match_score(
            user_major,
            sch[3],
            target_country,
            sch[2]
        )
        ranked.append((match, sch))

    ranked.sort(reverse=True, key=lambda x: x[0])

    text = "🎯 أفضل المنح المناسبة لك:\n\n"

    for score, sch in ranked[:5]:
        text += f"📚 {sch[1]}\n"
        text += f"🌍 {sch[2]}\n"
        text += f"⭐ نسبة التوافق: {score}%\n"
        text += f"🔗 {sch[6]}\n\n"

    text += "\n📊 قيّم دقة النتائج:"

    keyboard = [[InlineKeyboardButton(f"{i}/10 ⭐", callback_data=f"dream_rate_{i}")]
                for i in range(1, 11)]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await show_acceptance_prediction(update, context)


# ============================================
# ACCEPTANCE PREDICTION
# ============================================

async def show_acceptance_prediction(update, context):
    score = float(context.user_data.get("score", 50))

    if score >= 90:
        chance = "🔥 فرصة قبول عالية جداً (90%)"
    elif score >= 75:
        chance = "✅ فرصة قبول جيدة (70%)"
    else:
        chance = "⚠️ تحتاج تحسين فرصك"

    await update.message.reply_text(
        f"📈 تحليل فرص قبولك:\n{chance}"
    )

    await suggest_improvements(update, context)


# ============================================
# IMPROVEMENT SUGGESTIONS
# ============================================

async def suggest_improvements(update, context):
    suggestions = (
        "💡 لزيادة فرص القبول:\n\n"
        "• تحسين مستوى اللغة الإنجليزية\n"
        "• الحصول على شهادات إضافية\n"
        "• كتابة Motivation Letter قوية\n"
        "• تقديم على أكثر من منحة\n"
        "• تحسين CV\n"
    )

    await update.message.reply_text(suggestions)


# ============================================
# SAVE RATING
# ============================================

async def save_rating(update, context):
    rating = int(update.callback_query.data.replace("dream_rate_", ""))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE user_dream_profile SET rating=? WHERE user_id=?
    """, (rating, update.effective_user.id))

    conn.commit()
    conn.close()

    await update.callback_query.edit_message_text("❤️ شكراً لتقييمك")


# ============================================
# REGISTER FEATURE
# ============================================

def register(application):
    init_dream_db()

    application.add_handler(
        CallbackQueryHandler(start_dream_search, pattern="dream_search")
    )

    application.add_handler(
        CallbackQueryHandler(save_rating, pattern="dream_rate_")
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, dream_flow)
    )
