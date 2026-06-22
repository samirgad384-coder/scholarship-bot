import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)
DB_NAME = "scholarship_bot.db"


def init_ranking_db():
    """تهيئة نظام الترتيب"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ranking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        rank_score INTEGER DEFAULT 0,
        rank_position INTEGER,
        badges TEXT,
        achievements TEXT,
        last_updated TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    
    conn.commit()
    conn.close()


def get_user_rank_data(user_id):
    """جلب بيانات ترتيب المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT rank_score, rank_position, badges, achievements
    FROM ranking
    WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "score": result[0],
            "position": result[1],
            "badges": result[2] or "",
            "achievements": result[3] or ""
        }
    
    return None


def create_user_rank(user_id):
    """إنشاء سجل ترتيب جديد للمستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT OR IGNORE INTO ranking (user_id, rank_score, rank_position, badges, achievements, last_updated)
    VALUES (?, 0, 0, '', '', ?)
    """, (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()


def update_rank_score(user_id, points):
    """تحديث نقاط الترتيب"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # زيادة النقاط
    cursor.execute("""
    UPDATE ranking
    SET rank_score = rank_score + ?, last_updated = ?
    WHERE user_id = ?
    """, (points, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    
    # تحديث الترتيب العام
    update_rank_positions(cursor)
    
    conn.commit()
    conn.close()


def update_rank_positions(cursor):
    """تحديث مراكز جميع المستخدمين"""
    cursor.execute("""
    SELECT user_id, rank_score FROM ranking ORDER BY rank_score DESC
    """)
    
    users = cursor.fetchall()
    
    for position, (user_id, score) in enumerate(users, 1):
        cursor.execute("""
        UPDATE ranking SET rank_position = ? WHERE user_id = ?
        """, (position, user_id))


def add_badge(user_id, badge_name):
    """إضافة شارة للمستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT badges FROM ranking WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    current_badges = result[0] if result and result[0] else ""
    
    if badge_name not in current_badges:
        new_badges = f"{current_badges},{badge_name}" if current_badges else badge_name
        
        cursor.execute("""
        UPDATE ranking SET badges = ? WHERE user_id = ?
        """, (new_badges, user_id))
        
        conn.commit()
    
    conn.close()


def add_achievement(user_id, achievement_name):
    """إضافة إنجاز للمستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT achievements FROM ranking WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    current_achievements = result[0] if result and result[0] else ""
    
    if achievement_name not in current_achievements:
        new_achievements = f"{current_achievements},{achievement_name}" if current_achievements else achievement_name
        
        cursor.execute("""
        UPDATE ranking SET achievements = ? WHERE user_id = ?
        """, (new_achievements, user_id))
        
        conn.commit()
    
    conn.close()


# ============================================
# 🏆 POINTS SYSTEM
# ============================================

POINTS = {
    "daily_login": 5,
    "complete_profile": 50,
    "save_scholarship": 10,
    "apply_scholarship": 100,
    "share_bot": 25,
    "invite_friend": 75,
    "helpful_tip": 15,
    "acceptance_letter": 500,
    "weekly_streak": 30
}


def award_points(user_id, action):
    """منح نقاط للمستخدم"""
    points = POINTS.get(action, 0)
    
    if points > 0:
        update_rank_score(user_id, points)
        
        # التحقق من الشارات
        check_badges(user_id)
        
        logger.info(f"🏆 Awarded {points} points to user {user_id} for {action}")


def check_badges(user_id):
    """التحقق من استحقاق الشارات"""
    rank_data = get_user_rank_data(user_id)
    
    if not rank_data:
        return
    
    score = rank_data["score"]
    
    # شارات حسب النقاط
    if score >= 1000:
        add_badge(user_id, "🥇 Legend")
    elif score >= 500:
        add_badge(user_id, "🥈 Master")
    elif score >= 200:
        add_badge(user_id, "🥉 Expert")
    elif score >= 100:
        add_badge(user_id, "⭐ Active")
    elif score >= 50:
        add_badge(user_id, "🌟 Starter")


# ============================================
# 📊 LEADERBOARD
# ============================================

def get_leaderboard(limit=10):
    """جلب لوحة المتصدرين"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT r.user_id, r.rank_score, r.rank_position, u.username, u.full_name
    FROM ranking r
    LEFT JOIN users u ON r.user_id = u.user_id
    ORDER BY r.rank_score DESC
    LIMIT ?
    """, (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    leaderboard = []
    for row in results:
        leaderboard.append({
            "user_id": row[0],
            "score": row[1],
            "position": row[2],
            "username": row[3],
            "full_name": row[4]
        })
    
    return leaderboard


def get_user_position(user_id):
    """جلب مركز المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT rank_position, rank_score FROM ranking WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"position": result[0], "score": result[1]}
    
    return {"position": 0, "score": 0}


# ============================================
# 🎖️ ACHIEVEMENTS
# ============================================

ACHIEVEMENTS = {
    "first_search": "أول بحث عن منحة",
    "first_save": "أول منحة محفوظة",
    "profile_complete": "ملف شخصي مكتمل",
    "daily_streak_7": "أسبوع متواصل",
    "daily_streak_30": "شهر متواصل",
    "top_10": "من أفضل 10",
    "top_100": "من أفضل 100",
    "scholarship_winner": "فائز بمنحة"
}


def unlock_achievement(user_id, achievement_key):
    """فتح إنجاز جديد"""
    achievement_name = ACHIEVEMENTS.get(achievement_key, achievement_key)
    add_achievement(user_id, achievement_name)
    
    # منح نقاط إضافية
    award_points(user_id, "unlock_achievement")


# ============================================
# 📱 UI HANDLERS
# ============================================

async def ranking_menu(update, context):
    """عرض قائمة الترتيب"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # التأكد من وجود سجل للمستخدم
    create_user_rank(user_id)
    
    user_pos = get_user_position(user_id)
    leaderboard = get_leaderboard(10)
    
    text = "🏆 لوحة المتصدرين\n\n"
    text += "أفضل 10 طلاب:\n\n"
    
    for i, entry in enumerate(leaderboard, 1):
        name = entry.get("username") or entry.get("full_name") or f"User {entry['user_id']}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {name} - {entry['score']} نقطة\n"
    
    text += f"\n━━━━━━━━━━\n"
    text += f"📊 ترتيبك: #{user_pos['position']}\n"
    text += f"💯 نقاطك: {user_pos['score']}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_ranking")],
        [InlineKeyboardButton("🏅 إنجازاتي", callback_data="my_achievements")],
        [InlineKeyboardButton("🏠 العودة", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def my_achievements(update, context):
    """عرض إنجازات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    rank_data = get_user_rank_data(user_id)
    
    if not rank_data:
        create_user_rank(user_id)
        rank_data = get_user_rank_data(user_id)
    
    badges = rank_data.get("badges", "").split(",") if rank_data.get("badges") else []
    achievements = rank_data.get("achievements", "").split(",") if rank_data.get("achievements") else []
    
    text = "🏅 إنجازاتك:\n\n"
    
    if badges:
        text += "الشارات:\n"
        for badge in badges:
            if badge.strip():
                text += f"• {badge}\n"
        text += "\n"
    
    if achievements:
        text += "الإنجازات:\n"
        for ach in achievements:
            if ach.strip():
                text += f"• {ach}\n"
    
    if not badges and not achievements:
        text += "لا توجد إنجازات بعد. واصل النشاط لفتح الإنجازات!"
    
    keyboard = [
        [InlineKeyboardButton("🏠 العودة", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================
# 📦 REGISTER
# ============================================

def register(application):
    """تسجيل ميزة الترتيب"""
    init_ranking_db()
    
    application.add_handler(
        CallbackQueryHandler(ranking_menu, pattern="ranking")
    )
    
    application.add_handler(
        CallbackQueryHandler(my_achievements, pattern="my_achievements")
    )
    
    application.add_handler(
        CallbackQueryHandler(ranking_menu, pattern="refresh_ranking")
    )
    
    logger.info("✅ Ranking feature loaded")
