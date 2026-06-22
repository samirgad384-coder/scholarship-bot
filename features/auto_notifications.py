import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)
DB_NAME = "scholarship_bot.db"


def init_notifications_db():
    """تهيئة جدول الإشعارات التلقائية"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auto_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        notification_type TEXT,
        message TEXT,
        scheduled_time TEXT,
        is_sent INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    
    conn.commit()
    conn.close()


def schedule_notification(user_id, notification_type, message, delay_hours=24):
    """جدولة إشعار تلقائي"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    scheduled_time = (datetime.now() + timedelta(hours=delay_hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT INTO auto_notifications
    (user_id, notification_type, message, scheduled_time, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        notification_type,
        message,
        scheduled_time,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    conn.commit()
    conn.close()
    
    logger.info(f"📬 Notification scheduled for user {user_id}")


def get_pending_notifications():
    """جلب الإشعارات المعلقة للإرسال"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    SELECT id, user_id, notification_type, message
    FROM auto_notifications
    WHERE is_sent = 0 AND scheduled_time <= ?
    ORDER BY scheduled_time ASC
    """, (now,))
    
    notifications = cursor.fetchall()
    conn.close()
    
    return notifications


def mark_notification_sent(notification_id):
    """وضع علامة على الإشعار كمرسل"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE auto_notifications
    SET is_sent = 1
    WHERE id = ?
    """, (notification_id,))
    
    conn.commit()
    conn.close()


# ============================================
# 📱 NOTIFICATION TYPES
# ============================================

NOTIFICATION_TEMPLATES = {
    "deadline_reminder": "⏰ تذكير: موعد تقديم منحة {scholarship_name} يقترب!\nالمتبقي: {days_left} أيام",
    
    "new_scholarship": "🎓 منحة جديدة متاحة!\n{scholarship_name} في {country}\nالتخصص: {major}",
    
    "application_status": "📊 تحديث حالة طلبك:\n{scholarship_name}\nالحالة: {status}",
    
    "weekly_digest": "📈 ملخص الأسبوع:\n• عدد المنح الجديدة: {count}\n• المواعيد القادمة: {deadlines}",
    
    "profile_completion": "💡 ملفك غير مكتمل!\nأكمل معلوماتك لزيادة فرص القبول بنسبة 40%",
    
    "premium_expiry": "💎 اشتراك Premium سينتهي قريباً!\nجدد اشتراكك للاستمرار في استخدام الميزات الحصرية",
    
    "interview_prep": "🎯 مقابلة قريبة!\nابدأ التحضير لمقابلة {scholarship_name}",
    
    "document_checklist": "📋 مستندات ناقصة:\nتأكد من تجهيز: {documents}"
}


async def send_auto_notifications(application):
    """إرسال الإشعارات التلقائية المعلقة"""
    notifications = get_pending_notifications()
    
    sent_count = 0
    
    for notif in notifications:
        notif_id, user_id, notif_type, message = notif
        
        try:
            await application.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=get_notification_keyboard(notif_type)
            )
            
            mark_notification_sent(notif_id)
            sent_count += 1
            
            logger.info(f"✅ Sent notification {notif_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification to {user_id}: {e}")
    
    if sent_count > 0:
        logger.info(f"📬 Sent {sent_count} notifications")
    
    return sent_count


def get_notification_keyboard(notification_type):
    """إنشاء أزرار للإشعار"""
    
    keyboards = {
        "deadline_reminder": [
            [InlineKeyboardButton("📝 قدّم الآن", callback_data="apply_now")],
            [InlineKeyboardButton("🔕 إيقاف التذكير", callback_data="mute_reminder")]
        ],
        
        "new_scholarship": [
            [InlineKeyboardButton("👁️ عرض التفاصيل", callback_data="view_scholarship")],
            [InlineKeyboardButton("❤️ حفظ للمفضلة", callback_data="save_favorite")]
        ],
        
        "application_status": [
            [InlineKeyboardButton("📊 متابعة الحالة", callback_data="track_application")]
        ],
        
        "weekly_digest": [
            [InlineKeyboardButton("🔍 بحث مخصص", callback_data="custom_search")],
            [InlineKeyboardButton("📅 جدولة التقديم", callback_data="schedule_apply")]
        ],
        
        "profile_completion": [
            [InlineKeyboardButton("✏️ إكمال الملف", callback_data="complete_profile")]
        ],
        
        "premium_expiry": [
            [InlineKeyboardButton("💳 تجديد الاشتراك", callback_data="renew_premium")]
        ]
    }
    
    keyboard = keyboards.get(notification_type, [])
    
    if keyboard:
        return InlineKeyboardMarkup(keyboard)
    
    return None


# ============================================
# 🔔 USER PREFERENCES
# ============================================

def set_notification_preference(user_id, preference_type, enabled=True):
    """إعداد تفضيلات الإشعارات للمستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE users
    SET notification_enabled = ?
    WHERE user_id = ?
    """, (1 if enabled else 0, user_id))
    
    conn.commit()
    conn.close()


def get_user_notification_settings(user_id):
    """جلب إعدادات إشعارات المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT notification_enabled, weekly_digest, reminder_days
    FROM users
    WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "enabled": bool(result[0]),
            "weekly_digest": bool(result[1]),
            "reminder_days": result[2] or 7
        }
    
    return {"enabled": True, "weekly_digest": False, "reminder_days": 7}


# ============================================
# 🤖 AUTO TRIGGERS
# ============================================

def trigger_deadline_reminder(user_id, scholarship_name, days_left):
    """تشغيل تذكير بموعد نهائي"""
    message = NOTIFICATION_TEMPLATES["deadline_reminder"].format(
        scholarship_name=scholarship_name,
        days_left=days_left
    )
    
    schedule_notification(user_id, "deadline_reminder", message, delay_hours=days_left * 24)


def trigger_new_scholarship(user_id, scholarship_name, country, major):
    """إشعار بمنحة جديدة"""
    message = NOTIFICATION_TEMPLATES["new_scholarship"].format(
        scholarship_name=scholarship_name,
        country=country,
        major=major
    )
    
    schedule_notification(user_id, "new_scholarship", message, delay_hours=1)


def trigger_profile_incomplete(user_id):
    """تذكير بإكمال الملف"""
    message = NOTIFICATION_TEMPLATES["profile_completion"]
    schedule_notification(user_id, "profile_completion", message, delay_hours=2)


# ============================================
# 📦 REGISTER
# ============================================

async def notifications_menu(update, context):
    """قائمة إعدادات الإشعارات"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    settings = get_user_notification_settings(user_id)
    
    status = "مفعّلة ✅" if settings["enabled"] else "معطلة ❌"
    
    keyboard = [
        [InlineKeyboardButton("🔔 Toggle", callback_data="toggle_notifications")],
        [InlineKeyboardButton("📅 Digest أسبوعي", callback_data="toggle_digest")],
        [InlineKeyboardButton("⏰ فترة التذكير", callback_data="set_reminder_days")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        f"📬 إعدادات الإشعارات\n\n"
        f"الحالة: {status}\n"
        f"النشرة الأسبوعية: {'مفعّلة' if settings['weekly_digest'] else 'معطلة'}\n"
        f"أيام التذكير: {settings['reminder_days']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def register(application):
    """تسجيل ميزة الإشعارات التلقائية"""
    init_notifications_db()
    
    application.add_handler(
        CallbackQueryHandler(notifications_menu, pattern="notifications")
    )
    
    logger.info("✅ Auto Notifications feature loaded")
