import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
import logging
import random

logger = logging.getLogger(__name__)
DB_NAME = "scholarship_bot.db"


def init_daily_tips_db():
    """تهيئة جدول النصائح اليومية"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_tips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tip_text TEXT,
        tip_category TEXT,
        difficulty_level TEXT,
        created_at TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_tip_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tip_id INTEGER,
        viewed_at TEXT,
        is_helpful INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (tip_id) REFERENCES daily_tips(id)
    )
    """)
    
    # إضافة نصائح أولية
    seed_initial_tips(cursor)
    
    conn.commit()
    conn.close()


def seed_initial_tips(cursor):
    """إضافة نصائح أولية للنظام"""
    
    tips = [
        # نصائح عامة
        ("ابدأ بالتحضير للمنح قبل 6 أشهر على الأقل من موعد التقديم", "general", "beginner"),
        ("حافظ على معدل تراكمي عالي - معظم المنح تتطلب 3.5/4.0 أو أعلى", "general", "beginner"),
        ("تعلم لغة إضافية غير الإنجليزية يزيد فرصك بنسبة 30%", "general", "intermediate"),
        
        # نصائح CV
        ("اجعل CV في صفحة واحدة فقط unless لديك خبرات كثيرة", "cv", "beginner"),
        ("استخدم أفعال فعلية مثل: حققت، طورت، قمت بـ...", "cv", "intermediate"),
        ("أضف روابط لمشاريعك على GitHub أو Portfolio", "cv", "advanced"),
        ("خصص CV لكل منحة تقدم عليها", "cv", "intermediate"),
        
        # نصائح خطاب التحفيز
        ("ابدأ خطابك بقصة شخصية توضح شغفك بالتخصص", "motivation_letter", "intermediate"),
        ("اربط أهدافك الدراسية بأهداف المنحة والجامعة", "motivation_letter", "advanced"),
        ("تجنب العبارات العامة - كن محدداً ودقيقاً", "motivation_letter", "beginner"),
        
        # نصائح المقابلات
        ("تدرب على الإجابة عن سؤال: Tell me about yourself", "interview", "beginner"),
        ("استعد لأسئلة عن خططك المستقبلية بعد التخرج", "interview", "intermediate"),
        ("اسأل أنت أيضاً أسئلة ذكية عن البرنامج", "interview", "advanced"),
        
        # نصائح البحث
        ("استخدم Keywords دقيقة عند البحث عن منح", "search", "beginner"),
        ("تابع مواقع الجامعات الرسمية مباشرة", "search", "intermediate"),
        ("اشترك في newsletters متخصصة في المنح", "search", "beginner"),
        
        # نصائح التمويل
        ("قدم على أكثر من منحة لزيادة فرصك", "funding", "beginner"),
        ("بعض المنح تغطي فقط الرسوم - ابحث عن fully funded", "funding", "intermediate"),
        ("تحقق من شروط التجديد السنوي للمنحة", "funding", "advanced"),
        
        # نصائح اللغة
        ("IELTS Academic مطلوب لمعظم المنح الدراسية", "language", "beginner"),
        ("درجة 6.5+ في IELTS تعتبر جيدة لمعظم البرامج", "language", "intermediate"),
        ("TOEFL مقبول في أمريكا أكثر من أوروبا", "language", "intermediate"),
        
        # نصائح التوقيت
        ("معظم مواعيد المنح تكون بين سبتمبر ويناير", "timing", "beginner"),
        ("لا تنتظر آخر يوم للتقديم - قد يكون هناك ضغط على الموقع", "timing", "beginner"),
        ("جهز المستندات قبل فتح باب التقديم بشهر", "timing", "intermediate"),
    ]
    
    for tip_text, category, level in tips:
        cursor.execute("""
        INSERT OR IGNORE INTO daily_tips (tip_text, tip_category, difficulty_level, created_at)
        VALUES (?, ?, ?, ?)
        """, (tip_text, category, level, datetime.now().strftime("%Y-%m-%d")))


def get_daily_tip(user_id, preferred_category=None):
    """الحصول على نصيحة يومية مخصصة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # التحقق مما إذا كان المستخدم قد شاهد نصيحة اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
    SELECT tip_id FROM user_tip_history
    WHERE user_id = ? AND DATE(viewed_at) = ?
    """, (user_id, today))
    
    already_viewed = cursor.fetchone()
    
    if already_viewed:
        conn.close()
        return None
    
    # اختيار نصيحة عشوائية
    if preferred_category:
        cursor.execute("""
        SELECT id, tip_text, tip_category, difficulty_level
        FROM daily_tips
        WHERE tip_category = ?
        ORDER BY RANDOM()
        LIMIT 1
        """, (preferred_category,))
    else:
        cursor.execute("""
        SELECT id, tip_text, tip_category, difficulty_level
        FROM daily_tips
        ORDER BY RANDOM()
        LIMIT 1
        """)
    
    tip = cursor.fetchone()
    conn.close()
    
    if tip:
        return {
            "id": tip[0],
            "text": tip[1],
            "category": tip[2],
            "level": tip[3]
        }
    
    return None


def mark_tip_viewed(user_id, tip_id, is_helpful=False):
    """وضع علامة على النصيحة كم مشاهدة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO user_tip_history (user_id, tip_id, viewed_at, is_helpful)
    VALUES (?, ?, ?, ?)
    """, (user_id, tip_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1 if is_helpful else 0))
    
    conn.commit()
    conn.close()


def get_tip_statistics(user_id):
    """إحصائيات النصائح للمستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT COUNT(*), SUM(is_helpful)
    FROM user_tip_history
    WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        total = result[0] or 0
        helpful = result[1] or 0
        return {"total": total, "helpful": helpful}
    
    return {"total": 0, "helpful": 0}


# ============================================
# 📱 UI HANDLERS
# ============================================

async def daily_tip_menu(update, context):
    """عرض النصيحة اليومية"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    tip = get_daily_tip(user_id)
    
    if not tip:
        await query.edit_message_text(
            "✅你已经看过今天的提示了！\n\n"
            "明天再来获取新的提示。",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 العودة", callback_data="back_to_main")
            ]])
        )
        return
    
    # حفظ النصيحة كمشاهدة
    mark_tip_viewed(user_id, tip["id"])
    
    category_emoji = {
        "general": "💡",
        "cv": "📄",
        "motivation_letter": "✉️",
        "interview": "🎤",
        "search": "🔍",
        "funding": "💰",
        "language": "🗣️",
        "timing": "⏰"
    }
    
    emoji = category_emoji.get(tip["category"], "📌")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ مفيدة", callback_data=f"tip_helpful_{tip['id']}"),
            InlineKeyboardButton("❌ غير مفيدة", callback_data=f"tip_not_helpful_{tip['id']}")
        ],
        [InlineKeyboardButton("💡 نصيحة أخرى", callback_data="another_tip")],
        [InlineKeyboardButton("🏠 العودة", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        f"{emoji} نصيحة اليوم:\n\n"
        f"\"{tip['text']}\"\n\n"
        f"المستوى: {'مبتدئ' if tip['level'] == 'beginner' else 'متوسط' if tip['level'] == 'intermediate' else 'متقدم'}\n"
        f"التصنيف: {tip['category']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def another_tip(update, context):
    """عرض نصيحة أخرى"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    tip = get_daily_tip(user_id)
    
    if not tip:
        await query.answer("لا توجد نصائح إضافية", show_alert=True)
        return
    
    mark_tip_viewed(user_id, tip["id"])
    
    await query.edit_message_text(
        f"💡 نصيحة إضافية:\n\n"
        f"\"{tip['text']}\"",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 العودة", callback_data="back_to_main")
        ]])
    )


async def rate_tip(update, context):
    """تقييم النصيحة"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    tip_id = int(data.split("_")[-1])
    is_helpful = "helpful" in data
    
    user_id = update.effective_user.id
    
    # تحديث التقييم
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE user_tip_history
    SET is_helpful = ?
    WHERE user_id = ? AND tip_id = ?
    ORDER BY id DESC
    LIMIT 1
    """, (1 if is_helpful else 0, user_id, tip_id))
    
    conn.commit()
    conn.close()
    
    feedback = "شكراً لتقييمك! 🙏" if is_helpful else "سنحسن النصائح القادمة 💪"
    
    await query.edit_message_text(feedback)


async def tip_stats(update, context):
    """عرض إحصائيات النصائح"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    stats = get_tip_statistics(user_id)
    
    await query.answer(
        f"📊 إحصائياتك:\n"
        f"• نصائح مشاهدتها: {stats['total']}\n"
        f"• نصائح مفيدة: {stats['helpful']}",
        show_alert=True
    )


# ============================================
# 📦 REGISTER
# ============================================

def register(application):
    """تسجيل ميزة النصائح اليومية"""
    init_daily_tips_db()
    
    application.add_handler(
        CallbackQueryHandler(daily_tip_menu, pattern="daily_tip")
    )
    
    application.add_handler(
        CallbackQueryHandler(another_tip, pattern="another_tip")
    )
    
    application.add_handler(
        CallbackQueryHandler(rate_tip, pattern="tip_")
    )
    
    application.add_handler(
        CallbackQueryHandler(tip_stats, pattern="tip_stats")
    )
    
    logger.info("✅ Daily Tips feature loaded")
