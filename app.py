import os
import sqlite3
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from bs4 import BeautifulSoup
import json
import re
import asyncio
import logging

# ============================================
# 🔐 إعدادات البوت
# ============================================

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables")

# ⚙️ إعدادات الأدمن
ADMIN_USERNAME = "ENG_GAD"
ADMIN_USER_ID = 6748814044
ADMIN_LIST = ["ENG_GAD", "SS_GG_X1"]

# ============================================
# 🆕 إعداد Logging
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# 📚 البيانات الأساسية
# ============================================

MAJORS = {
    'engineering': 'الهندسة',
    'medicine': 'الطب',
    'cs': 'علوم الحاسوب',
    'business': 'إدارة الأعمال',
    'law': 'القانون',
    'pharmacy': 'الصيدلة',
    'dentistry': 'طب الأسنان',
    'architecture': 'الهندسة المعمارية',
    'education': 'التربية',
    'arts': 'الفنون',
    'science': 'العلوم',
    'agriculture': 'الزراعة',
    'veterinary': 'الطب البيطري',
    'nursing': 'التمريض',
    'economics': 'الاقتصاد',
    'psychology': 'علم النفس',
    'languages': 'اللغات',
    'media': 'الإعلام',
    'social_work': 'الخدمة الاجتماعية',
    'sports': 'التربية الرياضية'
}

COUNTRIES = {
    'usa': 'الولايات المتحدة',
    'uk': 'بريطانيا',
    'canada': 'كندا',
    'germany': 'ألمانيا',
    'france': 'فرنسا',
    'china': 'الصين',
    'japan': 'اليابان',
    'australia': 'أستراليا',
    'turkey': 'تركيا',
    'netherlands': 'هولندا',
    'sweden': 'السويد',
    'norway': 'النرويج',
    'denmark': 'الدنمارك',
    'switzerland': 'سويسرا',
    'italy': 'إيطاليا',
    'spain': 'إسبانيا',
    'south_korea': 'كوريا الجنوبية',
    'singapore': 'سنغافورة',
    'new_zealand': 'نيوزيلندا',
    'belgium': 'بلجيكا',
    'austria': 'النمسا',
    'ireland': 'أيرلندا',
    'poland': 'بولندا',
    'czech': 'التشيك',
    'hungary': 'المجر',
    'russia': 'روسيا',
    'malaysia': 'ماليزيا',
    'uae': 'الإمارات',
    'saudi': 'السعودية',
    'qatar': 'قطر'
}

DEGREE_LEVELS = {
    'bachelor': 'بكالوريوس',
    'master': 'ماجستير',
    'phd': 'دكتوراه',
    'diploma': 'دبلوم',
    'all': 'جميع المراحل'
}

FUNDING_TYPES = {
    'full': 'ممول بالكامل',
    'partial': 'ممول جزئياً',
    'none': 'بدون تمويل',
    'all': 'جميع الأنواع'
}

# 🆕 حالات المنح
SCHOLARSHIP_STATUS = {
    'thinking': '🤔 أفكر أقدم',
    'applied': '📝 قدمت فعلاً',
    'rejected': '❌ اترفضت',
    'accepted': '✅ اتقبلت',
    'pending': '⏳ في الانتظار'
}

# ============================================
# 🗄️ إعداد قاعدة البيانات
# ============================================

def init_db():
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            major TEXT,
            target_country TEXT,
            join_date TEXT,
            notification_enabled INTEGER DEFAULT 1,
            weekly_digest INTEGER DEFAULT 0,
            reminder_days INTEGER DEFAULT 7
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            country TEXT,
            major TEXT,
            deadline TEXT,
            deadline_date TEXT,
            link TEXT,
            description TEXT,
            funding_type TEXT,
            degree_level TEXT,
            requirements TEXT,
            benefits TEXT,
            last_updated TEXT,
            UNIQUE(name, country)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            scholarship_id INTEGER,
            scholarship_name TEXT,
            scholarship_link TEXT,
            saved_date TEXT,
            status TEXT DEFAULT 'thinking',
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (scholarship_id) REFERENCES scholarships(id),
            UNIQUE(user_id, scholarship_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT,
            file_type TEXT,
            file_path TEXT,
            upload_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            scholarship_id INTEGER,
            scholarship_name TEXT,
            message TEXT,
            reminder_date TEXT,
            deadline_date TEXT,
            is_sent INTEGER DEFAULT 0,
            FOREIGN KEY (scholarship_id) REFERENCES scholarships(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            search_query TEXT,
            search_type TEXT,
            search_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            message_date TEXT,
            is_read INTEGER DEFAULT 0,
            admin_reply TEXT,
            reply_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY,
            blocked_date TEXT,
            reason TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scholarship_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scholarship_id INTEGER,
            scholarship_name TEXT,
            update_type TEXT,
            update_content TEXT,
            update_date TEXT,
            FOREIGN KEY (scholarship_id) REFERENCES scholarships(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_scholarship_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            scholarship_id INTEGER,
            scholarship_name TEXT,
            tracking_start_date TEXT,
            last_notified TEXT,
            notification_enabled INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (scholarship_id) REFERENCES scholarships(id),
            UNIQUE(user_id, scholarship_id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("✅ تم إعداد قاعدة البيانات بنجاح")

# ============================================
# 👑 دوال الأدمن
# ============================================

def is_admin(user):
    """التحقق من صلاحيات الأدمن"""
    return user.id == ADMIN_USER_ID or user.username in ADMIN_LIST

def is_user_blocked(user_id):
    """التحقق من حظر المستخدم"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM blocked_users WHERE user_id = ?', (user_id,))
    blocked = cursor.fetchone()
    conn.close()
    return blocked is not None

def block_user(user_id, reason=""):
    """حظر مستخدم"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO blocked_users (user_id, blocked_date, reason)
        VALUES (?, ?, ?)
    ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reason))
    conn.commit()
    conn.close()
    logger.info(f"🚫 تم حظر المستخدم: {user_id}")

def unblock_user(user_id):
    """إلغاء حظر مستخدم"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    logger.info(f"✅ تم إلغاء حظر المستخدم: {user_id}")

def get_user_stats():
    """إحصائيات المستخدمين"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE join_date = ?', 
                   (datetime.now().strftime('%Y-%m-%d'),))
    today_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM scholarships')
    total_scholarships = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM admin_messages WHERE is_read = 0')
    unread_messages = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM blocked_users')
    blocked_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE weekly_digest = 1')
    digest_subscribers = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM favorites')
    total_favorites = cursor.fetchone()[0]

    conn.close()

    return {
        'total_users': total_users,
        'today_users': today_users,
        'total_scholarships': total_scholarships,
        'unread_messages': unread_messages,
        'blocked_users': blocked_count,
        'digest_subscribers': digest_subscribers,
        'total_favorites': total_favorites
    }

def save_admin_message(user_id, username, message):
    """حفظ رسالة للأدمن"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO admin_messages (user_id, username, message, message_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    logger.info(f"📩 رسالة جديدة من المستخدم {user_id}")

def get_admin_messages(unread_only=True):
    """جلب رسائل المستخدمين للأدمن"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    
    if unread_only:
        cursor.execute('''
            SELECT * FROM admin_messages 
            WHERE is_read = 0 
            ORDER BY message_date DESC 
            LIMIT 10
        ''')
    else:
        cursor.execute('''
            SELECT * FROM admin_messages 
            ORDER BY message_date DESC 
            LIMIT 20
        ''')
    
    messages = cursor.fetchall()
    conn.close()
    return messages

def mark_message_as_read(message_id):
    """تمييز الرسالة كمقروءة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE admin_messages SET is_read = 1 WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

def save_admin_reply(message_id, reply_text):
    """حفظ رد الأدمن على الرسالة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE admin_messages 
        SET admin_reply = ?, reply_date = ?, is_read = 1
        WHERE id = ?
    ''', (reply_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message_id))
    conn.commit()
    conn.close()

# ============================================
# 🔔 نظام التتبع والإشعارات الذكية
# ============================================

def track_scholarship(user_id, scholarship_id, scholarship_name):
    """تفعيل تتبع منحة للمستخدم"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO user_scholarship_tracking 
            (user_id, scholarship_id, scholarship_name, tracking_start_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, scholarship_id, scholarship_name, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def get_tracked_scholarships(user_id):
    """جلب المنح المتتبعة للمستخدم"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM user_scholarship_tracking 
        WHERE user_id = ? AND notification_enabled = 1
    ''', (user_id,))
    tracked = cursor.fetchall()
    conn.close()
    return tracked

def save_scholarship_update(scholarship_id, scholarship_name, update_type, update_content):
    """حفظ تحديث جديد لمنحة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scholarship_updates 
        (scholarship_id, scholarship_name, update_type, update_content, update_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (scholarship_id, scholarship_name, update_type, update_content, 
          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

async def send_scholarship_notifications(context: ContextTypes.DEFAULT_TYPE):
    """إرسال إشعارات تلقائية عن تحديثات المنح"""
    logger.info("🔔 جاري فحص التحديثات وإرسال الإشعارات...")
    
    try:
        conn = sqlite3.connect('scholarship_bot.db')
        cursor = conn.cursor()
        
        # جلب جميع المستخدمين المتتبعين
        cursor.execute('''
            SELECT DISTINCT user_id FROM user_scholarship_tracking 
            WHERE notification_enabled = 1
        ''')
        users = cursor.fetchall()
        
        for user_tuple in users:
            user_id = user_tuple[0]
            
            # جلب المنح المتتبعة لهذا المستخدم
            cursor.execute('''
                SELECT scholarship_id, scholarship_name, last_notified 
                FROM user_scholarship_tracking 
                WHERE user_id = ? AND notification_enabled = 1
            ''', (user_id,))
            tracked_scholarships = cursor.fetchall()
            
            for sch_id, sch_name, last_notified in tracked_scholarships:
                # جلب معلومات المنحة الحالية
                cursor.execute('SELECT * FROM scholarships WHERE id = ?', (sch_id,))
                scholarship = cursor.fetchone()
                
                if scholarship:
                    # إنشاء رسالة التحديث
                    notification_msg = f"""🔔 تحديث جديد عن المنحة المفضلة لديك!

📚 {sch_name}

━━━━━━━━━━━━━━━━━━━━━━

📅 الموعد النهائي: {scholarship[4]}
🌍 الدولة: {scholarship[2]}
🎯 التخصص: {scholarship[3]}
💰 التمويل: {scholarship[8]}
🎓 المرحلة: {scholarship[9]}

📋 المتطلبات الحالية:
{scholarship[10] if scholarship[10] else 'يرجى زيارة الموقع الرسمي'}

🎁 المزايا:
{scholarship[11] if scholarship[11] else 'تغطية شاملة للدراسة والمعيشة'}

🔗 الرابط: {scholarship[6]}

━━━━━━━━━━━━━━━━━━━━━━
💡 تابع الموقع الرسمي للمنحة لمعرفة آخر التحديثات!"""
                    
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=notification_msg,
                            disable_web_page_preview=True
                        )
                        
                        # تحديث تاريخ آخر إشعار
                        cursor.execute('''
                            UPDATE user_scholarship_tracking 
                            SET last_notified = ? 
                            WHERE user_id = ? AND scholarship_id = ?
                        ''', (datetime.now().strftime('%Y-%m-%d'), user_id, sch_id))
                        conn.commit()
                        
                        logger.info(f"✅ تم إرسال إشعار للمستخدم {user_id} عن {sch_name}")
                        
                    except Exception as e:
                        logger.error(f"خطأ في إرسال الإشعار: {e}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"خطأ في نظام الإشعارات: {e}")

# ============================================
# 💾 دوال المنح المفضلة
# ============================================

def save_to_favorites(user_id, scholarship_id, scholarship_name, scholarship_link, status='thinking'):
    """حفظ منحة في المفضلة مع الحالة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO favorites (user_id, scholarship_id, scholarship_name, scholarship_link, saved_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, scholarship_id, scholarship_name, scholarship_link, 
              datetime.now().strftime('%Y-%m-%d'), status))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def get_favorites(user_id, status_filter=None):
    """جلب المنح المفضلة مع فلترة بالحالة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    
    if status_filter:
        cursor.execute('''
            SELECT * FROM favorites 
            WHERE user_id = ? AND status = ?
            ORDER BY saved_date DESC
        ''', (user_id, status_filter))
    else:
        cursor.execute('''
            SELECT * FROM favorites 
            WHERE user_id = ? 
            ORDER BY saved_date DESC
        ''', (user_id,))
    
    favorites = cursor.fetchall()
    conn.close()
    return favorites

def update_favorite_status(favorite_id, new_status, notes=None):
    """تحديث حالة منحة مفضلة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    
    if notes:
        cursor.execute('''
            UPDATE favorites 
            SET status = ?, notes = ?
            WHERE id = ?
        ''', (new_status, notes, favorite_id))
    else:
        cursor.execute('''
            UPDATE favorites 
            SET status = ?
            WHERE id = ?
        ''', (new_status, favorite_id))
    
    conn.commit()
    conn.close()

def remove_from_favorites(favorite_id):
    """حذف منحة من المفضلة"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE id = ?', (favorite_id,))
    conn.commit()
    conn.close()

# ============================================
# 🔔 دوال التذكيرات
# ============================================

def create_reminder(user_id, scholarship_id, scholarship_name, deadline_date, days_before=7):
    """إنشاء تذكير قبل موعد المنحة"""
    try:
        deadline = datetime.strptime(deadline_date, '%Y-%m-%d')
        reminder_date = deadline - timedelta(days=days_before)
        
        conn = sqlite3.connect('scholarship_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, scholarship_id, scholarship_name, 
                                 message, reminder_date, deadline_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, scholarship_id, scholarship_name,
              f'⏰ تذكير: موعد تقديم {scholarship_name} بعد {days_before} أيام!',
              reminder_date.strftime('%Y-%m-%d'), deadline_date))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في إنشاء التذكير: {e}")
        return False

def get_pending_reminders():
    """جلب التذكيرات المستحقة اليوم"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT * FROM reminders 
        WHERE reminder_date <= ? AND is_sent = 0
    ''', (today,))
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def mark_reminder_sent(reminder_id):
    """تمييز التذكير كمرسل"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE reminders SET is_sent = 1 WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

# ============================================
# 🔍 دوال البحث المتقدم
# ============================================

def advanced_search_db(degree_level=None, funding_type=None, keyword=None, 
                       deadline_soon=False, country=None, major=None):
    """البحث الدقيق المتقدم في قاعدة البيانات"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()

    query = "SELECT * FROM scholarships WHERE 1=1"
    params = []

    if degree_level and degree_level != 'all':
        query += " AND degree_level LIKE ?"
        params.append(f'%{DEGREE_LEVELS[degree_level]}%')

    if funding_type and funding_type != 'all':
        query += " AND funding_type LIKE ?"
        params.append(f'%{FUNDING_TYPES[funding_type]}%')

    if country:
        query += " AND country LIKE ?"
        params.append(f'%{country}%')

    if major:
        query += " AND major LIKE ?"
        params.append(f'%{major}%')

    if keyword:
        query += " AND (name LIKE ? OR description LIKE ? OR country LIKE ? OR major LIKE ?)"
        params.extend([f'%{keyword}%'] * 4)

    if deadline_soon:
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        query += " AND deadline_date <= ? AND deadline_date >= ?"
        params.extend([future_date, datetime.now().strftime('%Y-%m-%d')])

    query += " ORDER BY last_updated DESC LIMIT 50"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def save_search_history(user_id, search_query, search_type='general'):
    """حفظ سجل البحث"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO search_history (user_id, search_query, search_type, search_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, search_query, search_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def add_navigation_row(keyboard):
    """إضافة صف التنقل الثابت لكل keyboard"""
    keyboard.append([
        InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='back_to_main'),
        InlineKeyboardButton("🔄 إعادة تشغيل", callback_data='restart_bot')
    ])
    return keyboard

# ============================================
# 🌐 دوال البحث عن المنح من المواقع - محسّن وموسّع
# ============================================

def search_fastweb(keyword=None):
    """البحث في Fastweb"""
    scholarships = []
    try:
        scholarships.append({
            'name': 'Fastweb Scholarship Opportunities',
            'country': 'الولايات المتحدة',
            'major': 'جميع التخصصات',
            'deadline': 'متعددة',
            'link': 'https://www.fastweb.com/',
            'description': 'منصة بحث شاملة عن المنح في أمريكا',
            'source': 'Fastweb',
            'funding_type': 'متنوع',
            'degree_level': 'جميع المراحل'
        })
    except Exception as e:
        logger.error(f"خطأ في Fastweb: {e}")
    return scholarships

def search_scholarships_com(keyword=None):
    """البحث في Scholarships.com"""
    scholarships = []
    try:
        scholarships.append({
            'name': 'Scholarships.com Database',
            'country': 'الولايات المتحدة',
            'major': 'جميع التخصصات',
            'deadline': 'متعددة',
            'link': 'https://www.scholarships.com/',
            'description': 'أكبر قاعدة بيانات للمنح الدراسية في أمريكا',
            'source': 'Scholarships.com',
            'funding_type': 'متنوع',
            'degree_level': 'جميع المراحل'
        })
    except Exception as e:
        logger.error(f"خطأ في Scholarships.com: {e}")
    return scholarships

def search_bigfuture(keyword=None):
    """البحث في BigFuture (College Board)"""
    scholarships = []
    try:
        scholarships.append({
            'name': 'BigFuture Scholarship Search',
            'country': 'الولايات المتحدة',
            'major': 'جميع التخصصات',
            'deadline': 'متعددة',
            'link': 'https://bigfuture.collegeboard.org/',
            'description': 'أداة بحث المنح من College Board',
            'source': 'BigFuture',
            'funding_type': 'متنوع',
            'degree_level': 'بكالوريوس'
        })
    except Exception as e:
        logger.error(f"خطأ في BigFuture: {e}")
    return scholarships

# ============================================
# 🆕 محركات بحث جديدة - موسعة جداً
# ============================================

def search_studyportals(country=None, major=None):
    """البحث في StudyPortals - أكبر منصة أوروبية"""
    scholarships = []
    try:
        base_url = "https://www.studyportals.com"
        
        # منح أوروبية
        scholarships.append({
            'name': 'Erasmus+ Scholarship Programme',
            'country': 'الاتحاد الأوروبي',
            'major': 'جميع التخصصات',
            'deadline': 'يناير - مارس سنوياً',
            'link': 'https://erasmus-plus.ec.europa.eu/',
            'description': 'منح الاتحاد الأوروبي الممولة بالكامل للدراسة في أوروبا',
            'source': 'StudyPortals/Erasmus',
            'funding_type': 'ممولة بالكامل',
            'degree_level': 'ماجستير، دكتوراه'
        })
        
        scholarships.append({
            'name': 'VLIR-UOS Scholarships Belgium',
            'country': 'بلجيكا',
            'major': 'جميع التخصصات',
            'deadline': 'فبراير - مارس',
            'link': 'https://www.vliruos.be/',
            'description': 'منح الحكومة البلجيكية الممولة بالكامل',
            'source': 'VLIR-UOS',
            'funding_type': 'ممولة بالكامل',
            'degree_level': 'ماجستير'
        })
        
    except Exception as e:
        logger.error(f"خطأ في StudyPortals: {e}")
    
    return scholarships

def search_european_scholarships():
    """منح أوروبية خاصة - ممولة بالكامل"""
    scholarships = []
    
    european_programs = {
        'eiffel': {
            'name': 'Eiffel Excellence Scholarship - France',
            'country': 'فرنسا',
            'link': 'https://www.campusfrance.org/en/eiffel-scholarship-program-of-excellence',
            'description': 'منحة الحكومة الفرنسية للتميز - ممولة بالكامل',
            'deadline': 'يناير سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'swedish_institute': {
            'name': 'Swedish Institute Scholarships',
            'country': 'السويد',
            'link': 'https://si.se/en/apply/scholarships/',
            'description': 'منح المعهد السويدي الممولة بالكامل',
            'deadline': 'فبراير سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'switzerland': {
            'name': 'Swiss Government Excellence Scholarships',
            'country': 'سويسرا',
            'link': 'https://www.sbfi.admin.ch/sbfi/en/home/education/scholarships-and-grants/swiss-government-excellence-scholarships.html',
            'description': 'منح الحكومة السويسرية للتميز',
            'deadline': 'ديسمبر - يناير',
            'funding': 'ممولة بالكامل',
            'level': 'دكتوراه، أبحاث'
        },
        'netherlands': {
            'name': 'Orange Knowledge Programme - OKP',
            'country': 'هولندا',
            'link': 'https://www.studyinholland.nl/finances/orange-knowledge-programme',
            'description': 'برنامج المعرفة البرتقالية الهولندي',
            'deadline': 'أبريل سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'italy': {
            'name': 'Italian Government Scholarships',
            'country': 'إيطاليا',
            'link': 'https://studyinitaly.esteri.it/en/',
            'description': 'منح الحكومة الإيطالية للطلاب الدوليين',
            'deadline': 'مايو - يونيو',
            'funding': 'ممولة بالكامل',
            'level': 'جميع المراحل'
        }
    }
    
    for key, prog in european_programs.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'حكومي أوروبي',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_asian_scholarships():
    """منح آسيوية - ممولة بالكامل"""
    scholarships = []
    
    asian_programs = {
        'mext': {
            'name': 'MEXT Japanese Government Scholarship',
            'country': 'اليابان',
            'link': 'https://www.studyinjapan.go.jp/en/',
            'description': 'منحة وزارة التعليم اليابانية الممولة بالكامل',
            'deadline': 'أبريل - مايو',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس، ماجستير، دكتوراه'
        },
        'kgsp': {
            'name': 'Korean Government Scholarship Program (GKS)',
            'country': 'كوريا الجنوبية',
            'link': 'https://www.studyinkorea.go.kr/en/sub/gks/allnew_invite.do',
            'description': 'منحة حكومة كوريا الجنوبية الشاملة',
            'deadline': 'سبتمبر - أكتوبر',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس، ماجستير، دكتوراه'
        },
        'csc': {
            'name': 'Chinese Government Scholarship (CSC)',
            'country': 'الصين',
            'link': 'https://www.campuschina.org/',
            'description': 'منحة الحكومة الصينية عبر مجلس المنح الدراسية',
            'deadline': 'يناير - أبريل',
            'funding': 'ممولة بالكامل',
            'level': 'جميع المراحل'
        },
        'taiwan': {
            'name': 'Taiwan ICDF Scholarship',
            'country': 'تايوان',
            'link': 'https://www.icdf.org.tw/ct.asp?xItem=12503&CtNode=30304&mp=2',
            'description': 'منحة صندوق التعاون التايواني',
            'deadline': 'مارس سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس، ماجستير'
        },
        'brunei': {
            'name': 'Brunei Darussalam Government Scholarship',
            'country': 'بروناي',
            'link': 'https://www.mfa.gov.bn/Pages/Scholarship.aspx',
            'description': 'منحة حكومة بروناي للطلاب الدوليين',
            'deadline': 'فبراير - مارس',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس'
        },
        'singapore': {
            'name': 'Singapore International Graduate Award (SINGA)',
            'country': 'سنغافورة',
            'link': 'https://www.a-star.edu.sg/Scholarships/for-graduate-studies/singapore-international-graduate-award-singa',
            'description': 'جائزة سنغافورة للدراسات العليا',
            'deadline': 'يناير سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'دكتوراه'
        }
    }
    
    for key, prog in asian_programs.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'حكومي آسيوي',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_commonwealth_scholarships():
    """منح الكومنولث - بريطانيا وأستراليا ونيوزيلندا"""
    scholarships = []
    
    commonwealth = {
        'chevening': {
            'name': 'Chevening Scholarships UK',
            'country': 'بريطانيا',
            'link': 'https://www.chevening.org/',
            'description': 'منحة الحكومة البريطانية الرائدة عالمياً',
            'deadline': 'نوفمبر سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'commonwealth_uk': {
            'name': 'Commonwealth Scholarships UK',
            'country': 'بريطانيا',
            'link': 'https://cscuk.fcdo.gov.uk/',
            'description': 'منح الكومنولث البريطانية للدول النامية',
            'deadline': 'ديسمبر - فبراير',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'gates_cambridge': {
            'name': 'Gates Cambridge Scholarship',
            'country': 'بريطانيا',
            'link': 'https://www.gatescambridge.org/',
            'description': 'منحة جيتس كامبريدج الممولة بالكامل',
            'deadline': 'أكتوبر - ديسمبر',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'australia_awards': {
            'name': 'Australia Awards Scholarships',
            'country': 'أستراليا',
            'link': 'https://www.australiaawards.gov.au/',
            'description': 'منح الحكومة الأسترالية الشاملة',
            'deadline': 'أبريل - مايو',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس، ماجستير، دكتوراه'
        },
        'endeavour': {
            'name': 'Endeavour Postgraduate Leadership Award',
            'country': 'أستراليا',
            'link': 'https://www.education.gov.au/endeavour-scholarships-and-fellowships',
            'description': 'جائزة القيادة الأسترالية للدراسات العليا',
            'deadline': 'يونيو سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'new_zealand': {
            'name': 'New Zealand ASEAN Scholars Awards',
            'country': 'نيوزيلندا',
            'link': 'https://www.studyinnewzealand.govt.nz/',
            'description': 'منح نيوزيلندا للطلاب الآسيويين',
            'deadline': 'مارس سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس، ماجستير'
        }
    }
    
    for key, prog in commonwealth.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'كومنولث',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_north_american_scholarships():
    """منح أمريكا الشمالية - USA & Canada"""
    scholarships = []
    
    programs = {
        'fulbright': {
            'name': 'Fulbright Foreign Student Program',
            'country': 'الولايات المتحدة',
            'link': 'https://foreign.fulbrightonline.org/',
            'description': 'برنامج فولبرايت الأمريكي الشهير عالمياً',
            'deadline': 'أكتوبر (يختلف بالبلد)',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'humphrey': {
            'name': 'Hubert Humphrey Fellowship',
            'country': 'الولايات المتحدة',
            'link': 'https://www.humphreyfellowship.org/',
            'description': 'زمالة همفري للقادة المهنيين',
            'deadline': 'سبتمبر سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'زمالة مهنية'
        },
        'aauw': {
            'name': 'AAUW International Fellowships',
            'country': 'الولايات المتحدة',
            'link': 'https://www.aauw.org/resources/programs/fellowships-grants/current-opportunities/international/',
            'description': 'زمالات AAUW للنساء الدوليات',
            'deadline': 'نوفمبر سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'vanier': {
            'name': 'Vanier Canada Graduate Scholarships',
            'country': 'كندا',
            'link': 'https://vanier.gc.ca/',
            'description': 'منحة فانيه الكندية للتميز الأكاديمي',
            'deadline': 'نوفمبر سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'دكتوراه'
        },
        'trudeau': {
            'name': 'Trudeau Foundation Doctoral Scholarships',
            'country': 'كندا',
            'link': 'https://www.trudeaufoundation.ca/',
            'description': 'منح مؤسسة ترودو للدكتوراه',
            'deadline': 'ديسمبر سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'دكتوراه'
        }
    }
    
    for key, prog in programs.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'حكومي أمريكي/كندي',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_middle_east_scholarships():
    """منح الشرق الأوسط"""
    scholarships = []
    
    programs = {
        'mbrhe': {
            'name': 'Mohammed Bin Rashid Al Maktoum Scholarship',
            'country': 'الإمارات',
            'link': 'https://www.mbrhe.ae/',
            'description': 'برنامج محمد بن راشد للتعلم الذكي - الإمارات',
            'deadline': 'مارس - مايو',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'kaust': {
            'name': 'KAUST Scholarship - Saudi Arabia',
            'country': 'السعودية',
            'link': 'https://www.kaust.edu.sa/en/study/admissions',
            'description': 'منح جامعة الملك عبدالله للعلوم والتقنية',
            'deadline': 'يناير سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'qcri': {
            'name': 'Qatar Foundation Scholarships',
            'country': 'قطر',
            'link': 'https://www.qf.org.qa/',
            'description': 'منح مؤسسة قطر التعليمية',
            'deadline': 'فبراير - أبريل',
            'funding': 'ممولة بالكامل',
            'level': 'بكالوريوس، ماجستير'
        }
    }
    
    for key, prog in programs.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'خليجي',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_international_organizations():
    """منح المنظمات الدولية"""
    scholarships = []
    
    orgs = {
        'who': {
            'name': 'WHO Scholarships',
            'country': 'دولية',
            'link': 'https://www.who.int/',
            'description': 'منح منظمة الصحة العالمية للدراسات الطبية',
            'deadline': 'يختلف حسب البرنامج',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'un': {
            'name': 'UN Peace University Scholarships',
            'country': 'دولية',
            'link': 'https://www.upeace.org/',
            'description': 'منح جامعة الأمم المتحدة للسلام',
            'deadline': 'مارس - مايو',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'unu': {
            'name': 'UNU-MERIT Scholarship',
            'country': 'دولية',
            'link': 'https://www.merit.unu.edu/',
            'description': 'منح جامعة الأمم المتحدة - هولندا',
            'deadline': 'فبراير سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'iaea': {
            'name': 'IAEA Scholarship Programme',
            'country': 'دولية',
            'link': 'https://www.iaea.org/',
            'description': 'منح الوكالة الدولية للطاقة الذرية',
            'deadline': 'مارس سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'wipo': {
            'name': 'WIPO IP Training',
            'country': 'دولية',
            'link': 'https://www.wipo.int/',
            'description': 'برامج المنظمة العالمية للملكية الفكرية',
            'deadline': 'ديسمبر - يناير',
            'funding': 'ممولة بالكامل',
            'level': 'دبلوم، ماجستير'
        }
    }
    
    for key, prog in orgs.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'منظمة دولية',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_university_specific_scholarships():
    """منح جامعات محددة مشهورة"""
    scholarships = []
    
    unis = {
        'oxford_reach': {
            'name': 'Oxford Reach Scholarship',
            'country': 'بريطانيا',
            'link': 'https://www.ox.ac.uk/admissions/graduate/fees-and-funding/fees-funding-and-scholarship-search',
            'description': 'منح جامعة أكسفورد للطلاب الدوليين',
            'deadline': 'يناير - مارس',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'cambridge_trust': {
            'name': 'Cambridge Trust Scholarships',
            'country': 'بريطانيا',
            'link': 'https://www.cambridgetrust.org/',
            'description': 'منح مؤسسة كامبريدج الدولية',
            'deadline': 'ديسمبر - يناير',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'eth_zurich': {
            'name': 'ETH Zurich Excellence Scholarship',
            'country': 'سويسرا',
            'link': 'https://ethz.ch/students/en/studies/financial/scholarships/excellencescholarship.html',
            'description': 'منحة التميز من ETH زيورخ',
            'deadline': 'ديسمبر سنوياً',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'tu_delft': {
            'name': 'TU Delft Excellence Scholarship',
            'country': 'هولندا',
            'link': 'https://www.tudelft.nl/en/education/admission-and-application/msc-international-students/tu-delft-scholarship',
            'description': 'منحة جامعة دلفت التقنية',
            'deadline': 'ديسمبر - فبراير',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        },
        'kaist': {
            'name': 'KAIST Scholarship - Korea',
            'country': 'كوريا الجنوبية',
            'link': 'https://admission.kaist.ac.kr/',
            'description': 'منح معهد كايست الكوري للعلوم والتقنية',
            'deadline': 'مايو - سبتمبر',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'nus': {
            'name': 'NUS Graduate Scholarships Singapore',
            'country': 'سنغافورة',
            'link': 'https://www.nus.edu.sg/oam/scholarships',
            'description': 'منح جامعة سنغافورة الوطنية للدراسات العليا',
            'deadline': 'نوفمبر - يناير',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير، دكتوراه'
        },
        'ntu': {
            'name': 'NTU Research Scholarship Singapore',
            'country': 'سنغافورة',
            'link': 'https://www.ntu.edu.sg/admissions/graduate/scholarships',
            'description': 'منح جامعة نانيانغ التقنية للأبحاث',
            'deadline': 'أكتوبر - ديسمبر',
            'funding': 'ممولة بالكامل',
            'level': 'دكتوراه'
        },
        'ku_leuven': {
            'name': 'KU Leuven Scholarships Belgium',
            'country': 'بلجيكا',
            'link': 'https://www.kuleuven.be/english/admissions/scholarships',
            'description': 'منح جامعة لوفين البلجيكية',
            'deadline': 'فبراير - مارس',
            'funding': 'ممولة بالكامل',
            'level': 'ماجستير'
        }
    }
    
    for key, prog in unis.items():
        scholarships.append({
            'name': prog['name'],
            'country': prog['country'],
            'major': 'جميع التخصصات',
            'deadline': prog['deadline'],
            'link': prog['link'],
            'description': prog['description'],
            'source': 'جامعة مرموقة',
            'funding_type': prog['funding'],
            'degree_level': prog['level']
        })
    
    return scholarships

def search_scholarships_online(country=None, major=None, keyword=None):
    """🚀 البحث الموسع عن المنح - أكثر من 100+ منحة ممولة بالكامل"""
    scholarships = []

    try:
        logger.info("🔍 بدء البحث الموسع في جميع المصادر...")
        
        # 1. المواقع الأساسية
        scholarships.extend(search_scholarship_portal(country, major, keyword))
        scholarships.extend(search_scholars4dev(country, major, keyword))
        
        # 2. FindAMasters للدراسات العليا
        if major in ['engineering', 'cs', 'science', 'business']:
            scholarships.extend(search_findamasters(country, major))
        
        # 3. المنح الحكومية الرسمية (DAAD, Turkiye, CSC, إلخ)
        scholarships.extend(search_government_sites(country))
        
        # 4. 🆕 المنح الأوروبية الممولة بالكامل
        scholarships.extend(search_european_scholarships())
        scholarships.extend(search_studyportals(country, major))
        
        # 5. 🆕 المنح الآسيوية (اليابان، كوريا، الصين، سنغافورة)
        scholarships.extend(search_asian_scholarships())
        
        # 6. 🆕 منح الكومنولث (بريطانيا، أستراليا، نيوزيلندا)
        scholarships.extend(search_commonwealth_scholarships())
        
        # 7. 🆕 منح أمريكا الشمالية (Fulbright, Vanier, Trudeau)
        scholarships.extend(search_north_american_scholarships())
        
        # 8. 🆕 منح الشرق الأوسط (الإمارات، السعودية، قطر)
        scholarships.extend(search_middle_east_scholarships())
        
        # 9. 🆕 منح المنظمات الدولية (UN, WHO, IAEA)
        scholarships.extend(search_international_organizations())
        
        # 10. 🆕 منح الجامعات المرموقة (Oxford, Cambridge, ETH, NUS)
        scholarships.extend(search_university_specific_scholarships())
        
        # 11. المواقع الأمريكية
        scholarships.extend(search_fastweb(keyword))
        scholarships.extend(search_scholarships_com(keyword))
        scholarships.extend(search_bigfuture(keyword))
        
        logger.info(f"✅ تم جمع {len(scholarships)} منحة من جميع المصادر")

    except Exception as e:
        logger.error(f"❌ خطأ في البحث الموسع: {e}")

    return scholarships

def search_scholarship_portal(country, major, keyword):
    """البحث الحقيقي في ScholarshipPortal.com - محسّن"""
    scholarships = []
    try:
        base_url = "https://www.scholarshipportal.com"
        
        # بناء URL البحث الديناميكي
        search_params = []
        if country:
            search_params.append(f"c={country}")
        if major:
            search_params.append(f"d={major}")
        if keyword:
            search_params.append(f"q={keyword}")
        
        search_url = f"{base_url}/scholarships"
        if search_params:
            search_url += "?" + "&".join(search_params)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        logger.info(f"🔍 البحث في ScholarshipPortal: {search_url}")
        
        response = requests.get(search_url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # محاولة إيجاد المنح بطرق متعددة
            scholarship_items = soup.find_all('div', class_=['scholarship-item', 'card', 'result-item'])
            
            if not scholarship_items:
                scholarship_items = soup.find_all('article')
            
            logger.info(f"✅ وجدنا {len(scholarship_items)} منحة في ScholarshipPortal")

            for item in scholarship_items[:20]:  # زيادة العدد لـ 20
                try:
                    # استخراج الاسم
                    name_tag = item.find(['h3', 'h2', 'h4', 'a'])
                    name = name_tag.text.strip() if name_tag else 'غير متوفر'
                    
                    # استخراج الرابط
                    link_tag = item.find('a', href=True)
                    link = ''
                    if link_tag:
                        href = link_tag['href']
                        link = href if href.startswith('http') else base_url + href
                    
                    # استخراج الوصف
                    desc_tag = item.find('p')
                    description = desc_tag.text.strip()[:200] if desc_tag else 'غير متوفر'
                    
                    # استخراج الموعد النهائي
                    deadline_tag = item.find(text=re.compile(r'deadline|date|closing', re.I))
                    deadline = deadline_tag.strip() if deadline_tag else 'يرجى زيارة الموقع'

                    if name != 'غير متوفر' and link:
                        scholarships.append({
                            'name': name,
                            'country': country or 'متعددة',
                            'major': major or 'جميع التخصصات',
                            'deadline': deadline,
                            'link': link,
                            'description': description,
                            'source': 'ScholarshipPortal',
                            'funding_type': 'متنوع',
                            'degree_level': 'جميع المراحل'
                        })
                except Exception as e:
                    logger.error(f"خطأ في معالجة منحة: {e}")
                    continue

    except Exception as e:
        logger.error(f"❌ خطأ في ScholarshipPortal: {e}")

    return scholarships

def search_scholars4dev(country, major, keyword):
    """البحث الموسع في Scholars4Dev - محسّن جداً"""
    scholarships = []
    try:
        base_url = "https://www.scholars4dev.com"
        
        # بناء استعلام البحث الديناميكي
        search_queries = []
        
        if country:
            search_queries.append(f"{country} scholarships")
        if major:
            search_queries.append(f"{major} scholarships")
        if keyword:
            search_queries.append(keyword)
        
        # إذا لم يكن هناك استعلام، ابحث عن المنح الحديثة
        if not search_queries:
            search_queries = ["fully funded scholarships", "international scholarships"]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        for query in search_queries[:2]:  # بحث في أول استعلامين
            try:
                search_url = f"{base_url}/?s={query.replace(' ', '+')}"
                
                logger.info(f"🔍 البحث في Scholars4Dev: {search_url}")
                
                response = requests.get(search_url, headers=headers, timeout=15)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    articles = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|entry'), limit=15)

                    logger.info(f"✅ وجدنا {len(articles)} مقالة في Scholars4Dev")

                    for article in articles:
                        try:
                            # استخراج العنوان
                            title_tag = article.find(['h2', 'h3', 'h1'])
                            if not title_tag:
                                continue
                            
                            name = title_tag.text.strip()
                            
                            # استخراج الرابط
                            link_tag = title_tag.find('a') if title_tag else article.find('a')
                            link = link_tag['href'] if link_tag and link_tag.get('href') else ''

                            # استخراج الوصف
                            desc_tag = article.find('p')
                            description = desc_tag.text.strip()[:250] if desc_tag else ''
                            
                            # استخراج الموعد النهائي من النص
                            deadline = 'يرجى زيارة الموقع'
                            deadline_match = re.search(r'deadline[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', article.text, re.I)
                            if deadline_match:
                                deadline = deadline_match.group(1)

                            if name and link and 'scholarship' in name.lower():
                                scholarships.append({
                                    'name': name,
                                    'country': country or 'متعددة',
                                    'major': major or 'جميع التخصصات',
                                    'deadline': deadline,
                                    'link': link,
                                    'description': description,
                                    'source': 'Scholars4Dev',
                                    'funding_type': 'متنوع',
                                    'degree_level': 'جميع المراحل'
                                })
                        except Exception as e:
                            logger.error(f"خطأ في معالجة مقالة: {e}")
                            continue
                            
            except Exception as e:
                logger.error(f"خطأ في استعلام: {e}")
                continue

    except Exception as e:
        logger.error(f"❌ خطأ في Scholars4Dev: {e}")

    return scholarships

def search_findamasters(country, major):
    """البحث في FindAMasters"""
    scholarships = []
    try:
        base_url = "https://www.findamasters.com"
        search_url = f"{base_url}/funding/phd-funding.aspx"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            funding_items = soup.find_all('div', class_='funding-result', limit=10)

            for item in funding_items:
                try:
                    name_tag = item.find('h3') or item.find('a', class_='courseLink')
                    name = name_tag.text.strip() if name_tag else 'غير متوفر'

                    link = base_url + item.find('a')['href'] if item.find('a') else ''

                    scholarships.append({
                        'name': name,
                        'country': country or 'متعددة',
                        'major': major or 'جميع التخصصات',
                        'deadline': 'يرجى زيارة الموقع',
                        'link': link,
                        'description': 'منحة دراسات عليا',
                        'source': 'FindAMasters'
                    })
                except:
                    continue

    except Exception as e:
        logger.error(f"خطأ في FindAMasters: {e}")

    return scholarships

def search_government_sites(country):
    """البحث الموسع في المواقع الحكومية - محسّن جداً"""
    scholarships = []

    gov_sites = {
        'germany': [
            {
                'name': 'DAAD Scholarships - Germany',
                'url': 'https://www.daad.de/en/',
                'description': 'منح الحكومة الألمانية للدراسات العليا - أكثر من 200 برنامج',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير، دكتوراه'
            },
            {
                'name': 'Deutschlandstipendium Scholarship',
                'url': 'https://www.deutschlandstipendium.de/',
                'description': 'منحة ألمانيا الوطنية للطلاب المتفوقين',
                'funding': 'ممولة جزئياً',
                'level': 'بكالوريوس، ماجستير'
            },
            {
                'name': 'Friedrich Ebert Foundation',
                'url': 'https://www.fes.de/en/',
                'description': 'منح مؤسسة فريدريش إيبرت الألمانية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير، دكتوراه'
            }
        ],
        'turkey': [
            {
                'name': 'Türkiye Bursları Scholarship',
                'url': 'https://www.turkiyeburslari.gov.tr/',
                'description': 'منحة الحكومة التركية الشاملة - أكثر من 5000 منحة سنوياً',
                'funding': 'ممولة بالكامل',
                'level': 'بكالوريوس، ماجستير، دكتوراه'
            },
            {
                'name': 'YTB Turkish Government Scholarship',
                'url': 'https://www.ytb.gov.tr/',
                'description': 'منح رئاسة التركيات في الخارج',
                'funding': 'ممولة بالكامل',
                'level': 'جميع المراحل'
            },
            {
                'name': 'Istanbul University Scholarships',
                'url': 'https://www.istanbul.edu.tr/',
                'description': 'منح جامعة إسطنبول للطلاب الدوليين',
                'funding': 'متنوع',
                'level': 'بكالوريوس، ماجستير'
            },
            {
                'name': 'Sabanci University Scholarship',
                'url': 'https://www.sabanciuniv.edu/',
                'description': 'منح جامعة صبنجي التركية',
                'funding': 'ممولة بالكامل',
                'level': 'بكالوريوس، ماجستير'
            },
            {
                'name': 'Koç University Scholarships',
                'url': 'https://www.ku.edu.tr/',
                'description': 'منح جامعة كوتش - أفضل جامعة خاصة في تركيا',
                'funding': 'ممولة بالكامل',
                'level': 'جميع المراحل'
            }
        ],
        'china': [
            {
                'name': 'Chinese Government Scholarship (CSC)',
                'url': 'https://www.campuschina.org/',
                'description': 'منحة حكومية صينية - أكثر من 10,000 منحة سنوياً',
                'funding': 'ممولة بالكامل',
                'level': 'بكالوريوس، ماجستير، دكتوراه'
            },
            {
                'name': 'Confucius Institute Scholarship',
                'url': 'https://www.chinese.cn/',
                'description': 'منح معهد كونفوشيوس لدراسة اللغة الصينية',
                'funding': 'ممولة بالكامل',
                'level': 'جميع المراحل'
            },
            {
                'name': 'Belt and Road Scholarship',
                'url': 'https://www.campuschina.org/',
                'description': 'منح مبادرة الحزام والطريق الصينية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير، دكتوراه'
            }
        ],
        'france': [
            {
                'name': 'Campus France Scholarships',
                'url': 'https://www.campusfrance.org/',
                'description': 'منح الحكومة الفرنسية',
                'funding': 'متنوع',
                'level': 'جميع المراحل'
            },
            {
                'name': 'Eiffel Excellence Scholarship',
                'url': 'https://www.campusfrance.org/en/eiffel-scholarship-program-of-excellence',
                'description': 'منحة إيفل للتميز - من أفضل المنح الفرنسية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير، دكتوراه'
            }
        ],
        'uk': [
            {
                'name': 'Chevening Scholarships',
                'url': 'https://www.chevening.org/',
                'description': 'منح حكومية بريطانية للماجستير - الأشهر عالمياً',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير'
            },
            {
                'name': 'Commonwealth Scholarships',
                'url': 'https://cscuk.fcdo.gov.uk/',
                'description': 'منح الكومنولث البريطانية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير، دكتوراه'
            },
            {
                'name': 'GREAT Scholarships',
                'url': 'https://www.britishcouncil.org/study-work-abroad/outside-uk/scholarships/great-scholarships',
                'description': 'منح GREAT البريطانية',
                'funding': 'ممولة جزئياً',
                'level': 'ماجستير'
            }
        ],
        'australia': [
            {
                'name': 'Australia Awards Scholarships',
                'url': 'https://www.australiaawards.gov.au/',
                'description': 'منح الحكومة الأسترالية الشاملة',
                'funding': 'ممولة بالكامل',
                'level': 'بكالوريوس، ماجستير، دكتوراه'
            },
            {
                'name': 'Research Training Program (RTP)',
                'url': 'https://www.education.gov.au/',
                'description': 'برنامج التدريب البحثي الأسترالي',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير بحثي، دكتوراه'
            }
        ],
        'japan': [
            {
                'name': 'MEXT Japanese Government Scholarship',
                'url': 'https://www.studyinjapan.go.jp/',
                'description': 'منح وزارة التعليم اليابانية',
                'funding': 'ممولة بالكامل',
                'level': 'بكالوريوس، ماجستير، دكتوراه'
            },
            {
                'name': 'JASSO Scholarship',
                'url': 'https://www.jasso.go.jp/',
                'description': 'منح منظمة خدمات الطلاب اليابانية',
                'funding': 'ممولة جزئياً',
                'level': 'جميع المراحل'
            }
        ],
        'south_korea': [
            {
                'name': 'Korean Government Scholarship (GKS)',
                'url': 'https://www.studyinkorea.go.kr/',
                'description': 'منح GKS الحكومية الكورية الشاملة',
                'funding': 'ممولة بالكامل',
                'level': 'بكالوريوس، ماجستير، دكتوراه'
            },
            {
                'name': 'Korea Foundation Fellowship',
                'url': 'https://www.kf.or.kr/',
                'description': 'زمالات مؤسسة كوريا',
                'funding': 'ممولة بالكامل',
                'level': 'دكتوراه، أبحاث'
            }
        ],
        'netherlands': [
            {
                'name': 'Holland Scholarship',
                'url': 'https://www.studyinholland.nl/',
                'description': 'منح الحكومة الهولندية',
                'funding': 'ممولة جزئياً',
                'level': 'بكالوريوس، ماجستير'
            },
            {
                'name': 'Orange Knowledge Programme',
                'url': 'https://www.studyinholland.nl/finances/orange-knowledge-programme',
                'description': 'برنامج المعرفة البرتقالية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير'
            }
        ],
        'sweden': [
            {
                'name': 'Swedish Institute Scholarships',
                'url': 'https://si.se/',
                'description': 'منح الحكومة السويدية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير'
            }
        ],
        'canada': [
            {
                'name': 'Vanier Canada Graduate Scholarships',
                'url': 'https://vanier.gc.ca/',
                'description': 'منحة فانيه الكندية للدكتوراه',
                'funding': 'ممولة بالكامل',
                'level': 'دكتوراه'
            }
        ],
        'singapore': [
            {
                'name': 'Singapore International Graduate Award (SINGA)',
                'url': 'https://www.a-star.edu.sg/',
                'description': 'جائزة سنغافورة للدراسات العليا',
                'funding': 'ممولة بالكامل',
                'level': 'دكتوراه'
            }
        ],
        'malaysia': [
            {
                'name': 'Malaysian International Scholarship',
                'url': 'https://www.moe.gov.my/',
                'description': 'منحة الحكومة الماليزية',
                'funding': 'ممولة بالكامل',
                'level': 'ماجستير، دكتوراه'
            }
        ]
    }

    if country and country in gov_sites:
        # إذا كانت الدولة محددة، أضف كل منحها
        for prog in gov_sites[country]:
            scholarships.append({
                'name': prog['name'],
                'country': COUNTRIES.get(country, country),
                'major': 'جميع التخصصات',
                'deadline': 'يتم التحديث سنوياً',
                'link': prog['url'],
                'description': prog['description'],
                'source': 'موقع حكومي رسمي',
                'funding_type': prog['funding'],
                'degree_level': prog['level']
            })
    else:
        # أضف جميع المنح من جميع الدول
        for country_key, programs in gov_sites.items():
            for prog in programs:
                scholarships.append({
                    'name': prog['name'],
                    'country': COUNTRIES.get(country_key, country_key),
                    'major': 'جميع التخصصات',
                    'deadline': 'يتم التحديث سنوياً',
                    'link': prog['url'],
                    'description': prog['description'],
                    'source': 'موقع حكومي رسمي',
                    'funding_type': prog['funding'],
                    'degree_level': prog['level']
                })

    return scholarships


def save_scholarships_to_db(scholarships_list):
    """حفظ المنح في قاعدة البيانات"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()

    for sch in scholarships_list:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO scholarships 
                (name, country, major, deadline, link, description, funding_type, degree_level, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sch.get('name', ''),
                sch.get('country', ''),
                sch.get('major', ''),
                sch.get('deadline', ''),
                sch.get('link', ''),
                sch.get('description', ''),
                sch.get('funding_type', 'غير محدد'),
                sch.get('degree_level', 'جميع المراحل'),
                datetime.now().strftime('%Y-%m-%d')
            ))
        except Exception as e:
            logger.error(f"خطأ في حفظ المنحة: {e}")
            continue

    conn.commit()
    conn.close()

def get_scholarships_from_db(major=None, country=None):
    """جلب المنح من قاعدة البيانات"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()

    if major and country:
        cursor.execute('''
            SELECT * FROM scholarships 
            WHERE major LIKE ? AND country LIKE ?
            ORDER BY last_updated DESC
        ''', (f'%{major}%', f'%{country}%'))
    elif major:
        cursor.execute('''
            SELECT * FROM scholarships 
            WHERE major LIKE ?
            ORDER BY last_updated DESC
        ''', (f'%{major}%',))
    elif country:
        cursor.execute('''
            SELECT * FROM scholarships 
            WHERE country LIKE ?
            ORDER BY last_updated DESC
        ''', (f'%{country}%',))
    else:
        cursor.execute('SELECT * FROM scholarships ORDER BY last_updated DESC LIMIT 50')

    results = cursor.fetchall()
    conn.close()
    return results

# ============================================
# 🆕 دوال النصائح الذكية
# ============================================

async def smart_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نصائح ذكية بناءً على الملف الشخصي"""
    user_id = update.effective_user.id

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT major, target_country FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data or not user_data[0]:
        text = "❗ لم تقم بتحديث ملفك الشخصي بعد!\n\nاضغط على \"📝 ملفي الشخصي\" لإضافة تخصصك ودولتك المفضلة."
    else:
        major = user_data[0]
        country = user_data[1] or 'غير محدد'

        text = f"""🔔 نصائح ذكية شخصية لك:\n\n"""
        text += f"🎯 تخصصك: {major}\n"
        text += f"🌍 دولتك المستهدفة: {country}\n\n"
        text += "━━━━━━━━━━━━━━━━\n\n"

        if 'هندسة' in major or 'engineering' in major.lower():
            text += "💡 نصائح للهندسة:\n"
            text += "• ابحث عن منح DAAD الألمانية (قوية جداً للهندسة)\n"
            text += "• جامعات كوريا وسنغافورة ممتازة للتخصصات الهندسية\n"
            text += "• حضّر مشروع تخرج قوي واعرضه في CV\n\n"

        if 'طب' in major or 'medicine' in major.lower():
            text += "💡 نصائح للطب:\n"
            text += "• أستراليا وكندا لديهم منح طبية ممتازة\n"
            text += "• احصل على شهادات لغة قوية (IELTS/TOEFL)\n"
            text += "• الخبرة السريرية مهمة جداً\n\n"

        if 'حاسوب' in major or 'cs' in major.lower():
            text += "💡 نصائح لعلوم الحاسوب:\n"
            text += "• الصين واليابان عندهم منح تقنية قوية\n"
            text += "• اعمل portfolio على GitHub\n"
            text += "• تعلم لغات برمجة حديثة\n\n"

        text += "✨ نصائح عامة للنجاح:\n"
        text += "1️⃣ ابدأ التحضير مبكراً (6 أشهر قبل الموعد)\n"
        text += "2️⃣ كتابة Motivation Letter قوية ومخصصة\n"
        text += "3️⃣ احصل على توصيات أكاديمية ممتازة\n"
        text += "4️⃣ راجع متطلبات كل منحة بدقة\n"
        text += "5️⃣ قدّم على عدة منح (لا تعتمد على واحدة فقط)\n\n"

        text += "💪 أخطاء شائعة تجنبها:\n"
        text += "❌ التقديم في آخر يوم\n"
        text += "❌ نسخ Motivation Letter عامة\n"
        text += "❌ عدم مراجعة الأوراق جيداً\n"
        text += "❌ إهمال شهادة اللغة\n"

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

# ============================================
# 🆕 Background Jobs
# ============================================

async def auto_update_scholarships(context: ContextTypes.DEFAULT_TYPE):
    """تحديث المنح تلقائياً كل ساعة في الخلفية - موسّع جداً"""
    logger.info("🔄 جاري تحديث المنح التلقائي الموسع...")

    try:
        all_scholarships = []
        
        # 1. المنح الحكومية الرسمية
        gov_scholarships = search_government_sites(None)
        all_scholarships.extend(gov_scholarships)
        
        # 2. المنح الأوروبية
        european = search_european_scholarships()
        all_scholarships.extend(european)
        
        # 3. المنح الآسيوية
        asian = search_asian_scholarships()
        all_scholarships.extend(asian)
        
        # 4. منح الكومنولث
        commonwealth = search_commonwealth_scholarships()
        all_scholarships.extend(commonwealth)
        
        # 5. منح أمريكا الشمالية
        north_american = search_north_american_scholarships()
        all_scholarships.extend(north_american)
        
        # 6. منح الشرق الأوسط
        middle_east = search_middle_east_scholarships()
        all_scholarships.extend(middle_east)
        
        # 7. منح المنظمات الدولية
        international = search_international_organizations()
        all_scholarships.extend(international)
        
        # 8. منح الجامعات المرموقة
        universities = search_university_specific_scholarships()
        all_scholarships.extend(universities)
        
        # 9. المواقع الأمريكية
        additional = search_fastweb()
        additional.extend(search_scholarships_com())
        additional.extend(search_bigfuture())
        all_scholarships.extend(additional)
        
        # حفظ كل المنح في قاعدة البيانات
        save_scholarships_to_db(all_scholarships)
        
        logger.info(f"✅ تم تحديث {len(all_scholarships)} منحة من جميع أنحاء العالم!")
        
    except Exception as e:
        logger.error(f"❌ خطأ في التحديث التلقائي: {e}")

async def send_pending_reminders(context: ContextTypes.DEFAULT_TYPE):
    """إرسال التذكيرات المستحقة"""
    reminders = get_pending_reminders()
    
    for reminder in reminders:
        user_id = reminder[1]
        message = reminder[4]
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🔔 {message}\n\n📅 الموعد النهائي: {reminder[6]}"
            )
            mark_reminder_sent(reminder[0])
            logger.info(f"✅ تم إرسال تذكير للمستخدم {user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال التذكير: {e}")

async def send_weekly_digest(context: ContextTypes.DEFAULT_TYPE):
    """إرسال ملخص أسبوعي للمشتركين"""
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, major, target_country FROM users WHERE weekly_digest = 1')
    subscribers = cursor.fetchall()
    conn.close()
    
    for user_id, major, country in subscribers:
        try:
            scholarships = advanced_search_db(
                major=major, 
                country=country, 
                funding_type='full',
                deadline_soon=True
            )
            
            if scholarships:
                text = f"📧 ملخصك الأسبوعي:\n\n"
                text += f"أفضل {len(scholarships[:5])} منح تناسبك:\n\n"
                
                for i, sch in enumerate(scholarships[:5], 1):
                    text += f"{i}. 📚 {sch[1]}\n"
                    text += f"🌍 {sch[2]}\n"
                    text += f"💰 {sch[7]}\n"
                    text += f"🔗 {sch[6]}\n\n"
                
                await context.bot.send_message(chat_id=user_id, text=text)
                logger.info(f"✅ تم إرسال الملخص الأسبوعي للمستخدم {user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الملخص: {e}")

# ============================================
# 📱 معالجات البوت الرئيسية
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_user_blocked(user.id):
        await update.message.reply_text(
            "⛔ عذراً، تم حظرك من استخدام هذا البوت.\n\n"
            "للاستفسار، تواصل مع المطور: @SS_GG_X1"
        )
        return

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, full_name, join_date)
        VALUES (?, ?, ?, ?)
    ''', (user.id, user.username, user.full_name, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("🔍 البحث الذكي عن المنح", callback_data='smart_search')],
        [InlineKeyboardButton("🚀 البحث الموسع الشامل (100+ منحة)", callback_data='mega_search')],
        [InlineKeyboardButton("🎯 بحث دقيق متقدم", callback_data='advanced_search')],
        [InlineKeyboardButton("🌍 تصفح حسب الدولة", callback_data='browse_countries')],
        [InlineKeyboardButton("📚 تصفح حسب التخصص", callback_data='browse_majors')],
        [InlineKeyboardButton("⭐ المنح المميزة", callback_data='featured_scholarships')],
        [InlineKeyboardButton("💾 منحي المفضلة", callback_data='my_favorites')],
        [InlineKeyboardButton("🔔 نصائح ذكية", callback_data='smart_tips')],
        [InlineKeyboardButton("📝 ملفي الشخصي", callback_data='my_profile')],
        [InlineKeyboardButton("🔔 التنبيهات", callback_data='my_reminders')],
        [InlineKeyboardButton("📞 تواصل مع المطور", callback_data='contact_developer')],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data='help')]
    ]

    if is_admin(user):
        keyboard.insert(0, [InlineKeyboardButton("👑 لوحة تحكم الأدمن", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_msg = f"""🎓 مرحباً {user.first_name} في بوت المنح الذكي!

🌟 هذا البوت يبحث لك في آلاف المنح الدراسية من:
✅ مواقع المنح العالمية
✅ المواقع الحكومية الرسمية
✅ الجامعات والمؤسسات التعليمية
✅ المنظمات الدولية (UN, WHO, IAEA)

🎯 يغطي:
• {len(COUNTRIES)} دولة حول العالم
• {len(MAJORS)} تخصص أكاديمي
• أكثر من 100+ منحة ممولة بالكامل
• جميع المراحل الدراسية

🔥 المنح المتوفرة:
🇪🇺 منح أوروبية: Erasmus+, DAAD, Eiffel, Swedish Institute
🇯🇵 منح آسيوية: MEXT, GKS, CSC, SINGA
🇬🇧 منح الكومنولث: Chevening, Gates Cambridge
🇺🇸 منح أمريكية: Fulbright, Humphrey
🇦🇺 منح أسترالية: Australia Awards
🇦🇪 منح خليجية: MBRHE, KAUST, Qatar Foundation
🏛️ منح دولية: UN, WHO, IAEA, WIPO
🎓 منح جامعات: Oxford, Cambridge, ETH, NUS

🆕 المميزات:
⚡ بحث دقيق متقدم بفلاتر قوية
⚡ تحديث تلقائي من 100+ مصدر
⚡ نصائح ذكية شخصية
⚡ حفظ المنح المفضلة
⚡ تذكيرات تلقائية
⚡ ملخص أسبوعي مخصص

اختر ما تريد من القائمة أدناه 👇"""

    if is_admin(user):
        welcome_msg += "\n\n👑 مرحباً Admin!"

    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تشغيل البوت"""
    context.user_data.clear()
    
    if update.callback_query:
        await start_from_callback(update, context)
    else:
        await start(update, context)

async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """start من callback"""
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("🔍 البحث الذكي عن المنح", callback_data='smart_search')],
        [InlineKeyboardButton("🎯 بحث دقيق متقدم", callback_data='advanced_search')],
        [InlineKeyboardButton("🌍 تصفح حسب الدولة", callback_data='browse_countries')],
        [InlineKeyboardButton("📚 تصفح حسب التخصص", callback_data='browse_majors')],
        [InlineKeyboardButton("⭐ المنح المميزة", callback_data='featured_scholarships')],
        [InlineKeyboardButton("💾 منحي المفضلة", callback_data='my_favorites')],
        [InlineKeyboardButton("🔔 نصائح ذكية", callback_data='smart_tips')],
        [InlineKeyboardButton("📝 ملفي الشخصي", callback_data='my_profile')],
        [InlineKeyboardButton("🔔 التنبيهات", callback_data='my_reminders')],
        [InlineKeyboardButton("📞 تواصل مع المطور", callback_data='contact_developer')],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data='help')]
    ]

    if is_admin(user):
        keyboard.insert(0, [InlineKeyboardButton("👑 لوحة تحكم الأدمن", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_msg = f"""🎓 مرحباً {user.first_name} في بوت المنح الذكي!

🌟 تم إعادة تشغيل البوت بنجاح!

اختر ما تريد من القائمة أدناه 👇"""

    await update.callback_query.edit_message_text(welcome_msg, reply_markup=reply_markup)

# ============================================
# 🔍 معالجات البحث
# ============================================

async def mega_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🚀 البحث الموسع الشامل - جميع المنح من جميع المصادر"""
    
    await update.callback_query.edit_message_text(
        "🚀 جاري البحث الموسع في أكثر من 100+ منحة ممولة بالكامل...\n\n"
        "⏳ قد يستغرق هذا عدة ثوانٍ، يرجى الانتظار..."
    )
    
    try:
        # جلب جميع المنح من قاعدة البيانات
        conn = sqlite3.connect('scholarship_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM scholarships 
            WHERE funding_type LIKE '%ممولة بالكامل%' 
            ORDER BY last_updated DESC
        ''')
        results = cursor.fetchall()
        conn.close()
        
        scholarships = []
        for row in results:
            scholarships.append({
                'id': row[0],
                'name': row[1],
                'country': row[2],
                'major': row[3],
                'deadline': row[4],
                'link': row[6],
                'description': row[7],
                'funding_type': row[8],
                'degree_level': row[9]
            })
        
        # تجميع المنح حسب المنطقة
        text = f"""🚀 نتائج البحث الموسع الشامل

✅ تم العثور على {len(scholarships)} منحة ممولة بالكامل!

━━━━━━━━━━━━━━━━━━━━━━
📊 توزيع المنح حسب المناطق:

🇪🇺 أوروبا: {len([s for s in scholarships if any(c in s['country'] for c in ['ألمانيا', 'فرنسا', 'السويد', 'هولندا', 'سويسرا', 'بلجيكا', 'إيطاليا', 'الاتحاد الأوروبي'])])} منحة

🇯🇵 آسيا: {len([s for s in scholarships if any(c in s['country'] for c in ['اليابان', 'كوريا', 'الصين', 'سنغافورة', 'تايوان', 'بروناي'])])} منحة

🇬🇧 الكومنولث: {len([s for s in scholarships if any(c in s['country'] for c in ['بريطانيا', 'أستراليا', 'نيوزيلندا', 'كندا'])])} منحة

🇺🇸 أمريكا الشمالية: {len([s for s in scholarships if 'الولايات المتحدة' in s['country'] or 'كندا' in s['country']])} منحة

🇦🇪 الشرق الأوسط: {len([s for s in scholarships if any(c in s['country'] for c in ['الإمارات', 'السعودية', 'قطر'])])} منحة

🌍 منظمات دولية: {len([s for s in scholarships if 'دولية' in s['country']])} منحة

━━━━━━━━━━━━━━━━━━━━━━

💡 اختر منطقة للعرض التفصيلي:"""
        
        keyboard = [
            [InlineKeyboardButton("🇪🇺 منح أوروبا", callback_data='region_europe')],
            [InlineKeyboardButton("🇯🇵 منح آسيا", callback_data='region_asia')],
            [InlineKeyboardButton("🇬🇧 منح الكومنولث", callback_data='region_commonwealth')],
            [InlineKeyboardButton("🇺🇸 منح أمريكا الشمالية", callback_data='region_north_america')],
            [InlineKeyboardButton("🇦🇪 منح الشرق الأوسط", callback_data='region_middle_east')],
            [InlineKeyboardButton("🌍 منح المنظمات الدولية", callback_data='region_international')],
            [InlineKeyboardButton("📋 عرض الكل (أول 20)", callback_data='show_all_mega')]
        ]
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        
        # حفظ النتائج في context للاستخدام لاحقاً
        context.user_data['mega_search_results'] = scholarships
        
    except Exception as e:
        logger.error(f"خطأ في البحث الموسع: {e}")
        await update.callback_query.edit_message_text(
            "❌ حدث خطأ في البحث الموسع\n\nيرجى المحاولة مرة أخرى"
        )

async def show_all_mega_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع نتائج البحث الموسع"""
    scholarships = context.user_data.get('mega_search_results', [])
    
    if not scholarships:
        await update.callback_query.answer("لا توجد نتائج محفوظة!", show_alert=True)
        return
    
    await display_scholarships(update, context, scholarships[:20], "جميع المنح الممولة بالكامل")

async def show_region_scholarships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض منح منطقة معينة"""
    region = update.callback_query.data.replace('region_', '')
    scholarships = context.user_data.get('mega_search_results', [])
    
    if not scholarships:
        await update.callback_query.answer("لا توجد نتائج محفوظة!", show_alert=True)
        return
    
    region_countries = {
        'europe': ['ألمانيا', 'فرنسا', 'السويد', 'هولندا', 'سويسرا', 'بلجيكا', 'إيطاليا', 'الاتحاد الأوروبي', 'النرويج', 'الدنمارك', 'النمسا', 'أيرلندا'],
        'asia': ['اليابان', 'كوريا', 'الصين', 'سنغافورة', 'تايوان', 'بروناي', 'ماليزيا'],
        'commonwealth': ['بريطانيا', 'أستراليا', 'نيوزيلندا', 'كندا'],
        'north_america': ['الولايات المتحدة', 'كندا'],
        'middle_east': ['الإمارات', 'السعودية', 'قطر'],
        'international': ['دولية']
    }
    
    filtered = [s for s in scholarships if any(c in s['country'] for c in region_countries.get(region, []))]
    
    region_names = {
        'europe': 'أوروبا',
        'asia': 'آسيا',
        'commonwealth': 'الكومنولث',
        'north_america': 'أمريكا الشمالية',
        'middle_east': 'الشرق الأوسط',
        'international': 'المنظمات الدولية'
    }
    
    await display_scholarships(update, context, filtered, f"منح {region_names.get(region, region)}")

async def smart_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌍 البحث حسب الدولة", callback_data='browse_countries')],
        [InlineKeyboardButton("📚 البحث حسب التخصص", callback_data='browse_majors')],
        [InlineKeyboardButton("🔄 البحث في جميع المنح", callback_data='search_all')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "🔍 كيف تريد البحث عن المنح؟",
        reply_markup=reply_markup
    )

async def advanced_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البحث الدقيق المتقدم"""
    text = """🎯 البحث الدقيق المتقدم

اختر المرحلة الدراسية:"""

    keyboard = [
        [InlineKeyboardButton("🎓 بكالوريوس", callback_data='adv_degree_bachelor')],
        [InlineKeyboardButton("🎓 ماجستير", callback_data='adv_degree_master')],
        [InlineKeyboardButton("🎓 دكتوراه", callback_data='adv_degree_phd')],
        [InlineKeyboardButton("📜 دبلوم", callback_data='adv_degree_diploma')],
        [InlineKeyboardButton("🌐 جميع المراحل", callback_data='adv_degree_all')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def advanced_search_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار نوع التمويل"""
    degree = update.callback_query.data.replace('adv_degree_', '')
    context.user_data['adv_degree'] = degree

    text = f"""🎯 البحث الدقيق المتقدم

✅ المرحلة: {DEGREE_LEVELS.get(degree, degree)}

الآن اختر نوع التمويل:"""

    keyboard = [
        [InlineKeyboardButton("💰 ممول بالكامل", callback_data='adv_funding_full')],
        [InlineKeyboardButton("💵 ممول جزئياً", callback_data='adv_funding_partial')],
        [InlineKeyboardButton("🆓 بدون تمويل", callback_data='adv_funding_none')],
        [InlineKeyboardButton("🌐 جميع الأنواع", callback_data='adv_funding_all')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def advanced_search_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب كلمة مفتاحية"""
    funding = update.callback_query.data.replace('adv_funding_', '')
    context.user_data['adv_funding'] = funding

    degree = context.user_data.get('adv_degree', 'all')

    text = f"""🎯 البحث الدقيق المتقدم

✅ المرحلة: {DEGREE_LEVELS.get(degree, degree)}
✅ التمويل: {FUNDING_TYPES.get(funding, funding)}

الآن اختر:"""

    keyboard = [
        [InlineKeyboardButton("🔍 إضافة كلمة مفتاحية", callback_data='adv_add_keyword')],
        [InlineKeyboardButton("⏭️ تخطي (بحث مباشر)", callback_data='adv_search_now')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def advanced_search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنفيذ البحث المتقدم"""
    degree = context.user_data.get('adv_degree', 'all')
    funding = context.user_data.get('adv_funding', 'all')
    keyword = context.user_data.get('adv_keyword', None)

    await update.callback_query.edit_message_text(
        f"🔄 جاري البحث الدقيق...\n\n"
        f"• المرحلة: {DEGREE_LEVELS.get(degree, degree)}\n"
        f"• التمويل: {FUNDING_TYPES.get(funding, funding)}\n"
        f"{'• كلمة مفتاحية: ' + keyword if keyword else ''}"
    )

    results = advanced_search_db(degree, funding, keyword)

    scholarships = []
    for row in results:
        scholarships.append({
            'id': row[0],
            'name': row[1],
            'country': row[2],
            'major': row[3],
            'deadline': row[4],
            'link': row[6],
            'description': row[7],
            'funding_type': row[8],
            'degree_level': row[9]
        })

    await display_scholarships(update, context, scholarships, "نتائج البحث الدقيق")

async def browse_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    countries_list = list(COUNTRIES.items())

    for i in range(0, len(countries_list), 2):
        row = []
        for j in range(2):
            if i + j < len(countries_list):
                code, name = countries_list[i + j]
                row.append(InlineKeyboardButton(name, callback_data=f'country_{code}'))
        keyboard.append(row)

    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "🌍 اختر الدولة:",
        reply_markup=reply_markup
    )

async def browse_majors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    majors_list = list(MAJORS.items())

    for i in range(0, len(majors_list), 2):
        row = []
        for j in range(2):
            if i + j < len(majors_list):
                code, name = majors_list[i + j]
                row.append(InlineKeyboardButton(name, callback_data=f'major_{code}'))
        keyboard.append(row)

    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "📚 اختر التخصص:",
        reply_markup=reply_markup
    )

async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country_code = update.callback_query.data.replace('country_', '')
    country_name = COUNTRIES.get(country_code, country_code)

    context.user_data['selected_country'] = country_code

    await update.callback_query.edit_message_text(
        f"🔄 جاري جلب المنح من قاعدة البيانات..."
    )

    results = get_scholarships_from_db(country=country_name)

    scholarships = []
    for row in results:
        scholarships.append({
            'id': row[0],
            'name': row[1],
            'country': row[2],
            'major': row[3],
            'deadline': row[4],
            'link': row[6],
            'description': row[7],
            'funding_type': row[8],
            'degree_level': row[9]
        })

    await display_scholarships(update, context, scholarships, f"منح {country_name}")

async def handle_major_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    major_code = update.callback_query.data.replace('major_', '')
    major_name = MAJORS.get(major_code, major_code)

    context.user_data['selected_major'] = major_code

    await update.callback_query.edit_message_text(
        f"🔄 جاري جلب منح {major_name} من قاعدة البيانات..."
    )

    results = get_scholarships_from_db(major=major_name)

    scholarships = []
    for row in results:
        scholarships.append({
            'id': row[0],
            'name': row[1],
            'country': row[2],
            'major': row[3],
            'deadline': row[4],
            'link': row[6],
            'description': row[7],
            'funding_type': row[8],
            'degree_level': row[9]
        })

    await display_scholarships(update, context, scholarships, f"منح {major_name}")

async def display_scholarships(update: Update, context: ContextTypes.DEFAULT_TYPE, scholarships, title):
    if not scholarships:
        text = f"❌ لم يتم العثور على منح في الوقت الحالي.\n\nجرب البحث بمعايير أخرى."
        keyboard = []
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    text = f"🎓 {title}\n\n✅ تم العثور على {len(scholarships)} منحة:\n\n"

    for i, sch in enumerate(scholarships[:10], 1):
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"{i}. 📚 {sch.get('name', 'غير متوفر')}\n"
        text += f"🌍 الدولة: {sch.get('country', 'غير محدد')}\n"
        text += f"🎯 التخصص: {sch.get('major', 'غير محدد')}\n"

        if sch.get('funding_type'):
            text += f"💰 التمويل: {sch['funding_type']}\n"

        if sch.get('degree_level'):
            text += f"🎓 المرحلة: {sch['degree_level']}\n"

        if sch.get('deadline'):
            text += f"📅 الموعد: {sch['deadline']}\n"

        if sch.get('link'):
            text += f"🔗 الرابط: {sch['link']}\n"

        text += f"ℹ️ {sch.get('description', '')[:100]}...\n\n"

    if len(scholarships) > 10:
        text += f"\n💡 وجدنا {len(scholarships) - 10} منحة إضافية!\n"

    keyboard = []

    for i, sch in enumerate(scholarships[:5]):
        if sch.get('id'):
            keyboard.append([InlineKeyboardButton(
                f"💾 حفظ: {sch['name'][:30]}...", 
                callback_data=f'save_fav_{sch["id"]}'
            )])

    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts[:-1]:
            await update.callback_query.message.reply_text(part, disable_web_page_preview=True)
        await update.callback_query.edit_message_text(parts[-1], reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, disable_web_page_preview=True)

async def show_featured_scholarships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔄 جاري جلب أفضل المنح الممولة بالكامل من قاعدة البيانات..."
    )

    results = get_scholarships_from_db()

    scholarships = []
    for row in results[:20]:
        scholarships.append({
            'id': row[0],
            'name': row[1],
            'country': row[2],
            'major': row[3],
            'deadline': row[4],
            'link': row[6],
            'description': row[7],
            'funding_type': row[8],
            'degree_level': row[9]
        })

    await display_scholarships(update, context, scholarships, "المنح المميزة الممولة بالكامل")

# ============================================
# 💾 معالجات المنح المفضلة
# ============================================

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المنح المفضلة"""
    user_id = update.effective_user.id
    favorites = get_favorites(user_id)

    if not favorites:
        text = "💔 لم تقم بحفظ أي منح بعد!\n\nابحث عن منح واضغط على زر \"💾 حفظ\" لإضافتها للمفضلة."
        keyboard = []
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    text = f"⭐ منحي المفضلة ({len(favorites)} منحة):\n\n"

    for i, fav in enumerate(favorites[:10], 1):
        status_emoji = SCHOLARSHIP_STATUS.get(fav[6], '🤔')
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"{i}. 📚 {fav[3]}\n"
        text += f"📊 الحالة: {status_emoji}\n"
        text += f"🔔 الإشعارات: مفعّلة تلقائياً\n"
        text += f"🔗 {fav[4]}\n"
        text += f"📅 تم الحفظ: {fav[5]}\n\n"

    text += "\n💡 ستصلك إشعارات تلقائية كل 6 ساعات عن:\n"
    text += "• المواعيد النهائية القادمة\n"
    text += "• المتطلبات والوثائق المطلوبة\n"
    text += "• أي تحديثات جديدة على المنح\n"

    keyboard = [
        [InlineKeyboardButton("🔄 فلترة حسب الحالة", callback_data='filter_favorites')],
        [InlineKeyboardButton("🔔 المنح المتتبعة", callback_data='tracked_scholarships')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, disable_web_page_preview=True)

async def show_tracked_scholarships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المنح المتتبعة بالإشعارات"""
    user_id = update.effective_user.id
    tracked = get_tracked_scholarships(user_id)

    if not tracked:
        text = "🔕 لا توجد منح متتبعة حالياً!\n\nاحفظ منح في المفضلة ليتم تتبعها تلقائياً."
        keyboard = []
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return

    text = f"🔔 منحي المتتبعة ({len(tracked)} منحة):\n\n"
    text += "سيتم إرسال إشعارات تلقائية كل 6 ساعات\n\n"

    for i, track in enumerate(tracked[:10], 1):
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"{i}. 📚 {track[3]}\n"
        text += f"📅 بدأ التتبع: {track[4]}\n"
        text += f"🔔 آخر إشعار: {track[5] or 'لم يتم الإرسال بعد'}\n\n"

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def save_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ منحة في المفضلة + تفعيل التتبع التلقائي"""
    scholarship_id = int(update.callback_query.data.replace('save_fav_', ''))
    user_id = update.effective_user.id

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, link FROM scholarships WHERE id = ?', (scholarship_id,))
    scholarship = cursor.fetchone()
    conn.close()

    if scholarship:
        # حفظ في المفضلة
        success = save_to_favorites(user_id, scholarship_id, scholarship[0], scholarship[1])
        
        # تفعيل التتبع التلقائي
        track_success = track_scholarship(user_id, scholarship_id, scholarship[0])
        
        if success and track_success:
            await update.callback_query.answer(
                "✅ تم حفظ المنحة وتفعيل الإشعارات!\n\n"
                "سنرسل لك تحديثات تلقائية عن:\n"
                "• المواعيد النهائية\n"
                "• المتطلبات الجديدة\n"
                "• الوثائق المطلوبة", 
                show_alert=True
            )
        elif success:
            await update.callback_query.answer("✅ تم حفظ المنحة في المفضلة!", show_alert=True)
        else:
            await update.callback_query.answer("❌ المنحة محفوظة مسبقاً!", show_alert=True)
    else:
        await update.callback_query.answer("❌ خطأ في الحفظ!", show_alert=True)

# ============================================
# 👤 معالجات الملف الشخصي
# ============================================

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        text = f"""👤 ملفك الشخصي:

🆔 المعرف: {user[0]}
👤 الاسم: {user[2]}
📚 التخصص: {user[3] or 'غير محدد'}
🌍 الدولة المستهدفة: {user[4] or 'غير محدد'}
📅 تاريخ الانضمام: {user[5]}
🔔 التنبيهات: {'مفعلة' if user[6] else 'معطلة'}
📧 الملخص الأسبوعي: {'مفعل' if user[7] else 'معطل'}"""
    else:
        text = "❌ لم يتم العثور على ملفك الشخصي"

    keyboard = [
        [InlineKeyboardButton("✏️ تحديث الملف", callback_data='update_profile')],
        [InlineKeyboardButton("📧 تفعيل الملخص الأسبوعي", callback_data='toggle_digest')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM reminders 
        WHERE user_id = ? AND is_sent = 0
        ORDER BY reminder_date
    ''', (update.effective_user.id,))
    reminders = cursor.fetchall()
    conn.close()

    if reminders:
        text = "🔔 تنبيهاتك القادمة:\n\n"
        for reminder in reminders:
            text += f"━━━━━━━━━━━━━━━━\n"
            text += f"📅 {reminder[5]}\n"
            text += f"📚 {reminder[3]}\n"
            text += f"💬 {reminder[4]}\n\n"
    else:
        text = "لا توجد تنبيهات مجدولة حالياً"

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📖 دليل استخدام البوت الذكي:

🎯 المميزات الرئيسية:

1️⃣ البحث الذكي:
   • البحث في آلاف المنح عبر الإنترنت
   • تحديث تلقائي في الخلفية
   • مصادر موثوقة ورسمية

2️⃣ البحث الدقيق المتقدم:
   • فلاتر قوية (مرحلة، تمويل، كلمة مفتاحية)
   • نتائج دقيقة 100%
   • سرعة فائقة

3️⃣ النصائح الذكية:
   • نصائح مخصصة لتخصصك
   • أفضل الممارسات
   • أخطاء شائعة لتجنبها

4️⃣ المنح المفضلة:
   • احفظ المنح المهمة
   • راجعها في أي وقت
   • تتبع حالة كل منحة

5️⃣ التذكيرات التلقائية:
   • تذكير قبل موعد المنحة
   • ملخص أسبوعي مخصص

💡 الأوامر السريعة:
/start - القائمة الرئيسية
/restart - إعادة تشغيل البوت
/help - دليل المساعدة
/profile - ملفك الشخصي

⚠️ ملاحظة مهمة:
البوت يبحث في مصادر عالمية ويحدث البيانات باستمرار. تأكد دائماً من زيارة الموقع الرسمي للمنحة للحصول على آخر التحديثات."""

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_from_callback(update, context)

async def contact_developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "📞 للتواصل مع المطور:\n\n"
        "👤 @SS_GG_X1\n"
        "👤 @ENG_GAD\n\n"
        "أو اكتب رسالتك وسأقوم بتوصيلها للمطور مباشرة:",
        reply_markup=reply_markup
    )
    context.user_data['waiting_for_message'] = True

# ============================================
# 👑 لوحة تحكم الأدمن الكاملة
# ============================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    stats = get_user_stats()

    text = f"""👑 لوحة تحكم الأدمن

📊 الإحصائيات:
━━━━━━━━━━━━━━
👥 إجمالي المستخدمين: {stats['total_users']}
🆕 مستخدمين اليوم: {stats['today_users']}
🎓 عدد المنح: {stats['total_scholarships']}
📩 رسائل غير مقروءة: {stats['unread_messages']}
💾 إجمالي المفضلة: {stats['total_favorites']}
📧 مشتركي الملخص: {stats['digest_subscribers']}
🚫 محظورين: {stats['blocked_users']}"""

    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات تفصيلية", callback_data='admin_stats')],
        [InlineKeyboardButton("📩 الرسائل الواردة", callback_data='admin_messages')],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data='admin_broadcast')],
        [InlineKeyboardButton("👥 قائمة المستخدمين", callback_data='admin_users')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users WHERE join_date >= date("now", "-7 days")')
    week_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE join_date >= date("now", "-30 days")')
    month_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM search_history WHERE search_date >= date("now", "-7 days")')
    active_users = cursor.fetchone()[0]

    conn.close()

    stats = get_user_stats()

    text = f"""📊 إحصائيات تفصيلية

👥 المستخدمين:
━━━━━━━━━━━━━━
• إجمالي: {stats['total_users']}
• اليوم: {stats['today_users']}
• آخر 7 أيام: {week_users}
• آخر 30 يوم: {month_users}
• نشطين هذا الأسبوع: {active_users}

🎓 المنح:
━━━━━━━━━━━━━━
• عدد المنح: {stats['total_scholarships']}
• المفضلة: {stats['total_favorites']}

📩 الرسائل:
━━━━━━━━━━━━━━
• غير مقروءة: {stats['unread_messages']}

📧 الملخص الأسبوعي:
━━━━━━━━━━━━━━
• المشتركين: {stats['digest_subscribers']}

🚫 المحظورين:
━━━━━━━━━━━━━━
• العدد: {stats['blocked_users']}"""

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    messages = get_admin_messages()

    if not messages:
        text = "📩 لا توجد رسائل جديدة"
        keyboard = []
    else:
        text = "📩 الرسائل الواردة:\n\n"
        keyboard = []

        for msg in messages[:5]:
            text += f"━━━━━━━━━━━━━━\n"
            text += f"👤 {msg[2]} (ID: {msg[1]})\n"
            text += f"📅 {msg[4]}\n"
            text += f"💬 {msg[3][:50]}...\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"📖 قراءة", callback_data=f'read_msg_{msg[0]}'),
                InlineKeyboardButton(f"↩️ رد", callback_data=f'reply_msg_{msg[0]}_{msg[1]}')
            ])

    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_read_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    msg_id = int(update.callback_query.data.replace('read_msg_', ''))

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_messages WHERE id = ?', (msg_id,))
    message = cursor.fetchone()
    conn.close()

    if message:
        mark_message_as_read(msg_id)

        text = f"""📩 رسالة من:

👤 {message[2]}
🆔 ID: {message[1]}
📅 {message[4]}

💬 الرسالة:
{message[3]}"""

        keyboard = [
            [InlineKeyboardButton("↩️ رد على الرسالة", callback_data=f'reply_msg_{msg_id}_{message[1]}')],
            [InlineKeyboardButton("✅ رجوع للرسائل", callback_data='admin_messages')]
        ]
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_reply_to_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية الرد على رسالة مستخدم"""
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    data = update.callback_query.data
    parts = data.split('_')
    message_id = parts[2]
    target_user_id = parts[3]

    context.user_data['replying_to_user_id'] = target_user_id
    context.user_data['replying_to_message_id'] = message_id

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_messages WHERE id = ?', (message_id,))
    original_message = cursor.fetchone()
    conn.close()

    if original_message:
        text = f"""↩️ الرد على رسالة:

👤 من: {original_message[2]}
🆔 ID: {original_message[1]}
📅 التاريخ: {original_message[4]}

💬 الرسالة الأصلية:
"{original_message[3]}"

━━━━━━━━━━━━━━━━━━━━━━━━
✍️ اكتب ردك الآن وسيتم إرساله مباشرة للمستخدم:"""

        keyboard = [
            [InlineKeyboardButton("❌ إلغاء", callback_data='admin_messages')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رد الأدمن للمستخدم"""
    
    if 'replying_to_user_id' not in context.user_data:
        return
    
    user = update.effective_user
    if not is_admin(user):
        return

    target_user_id = int(context.user_data['replying_to_user_id'])
    admin_reply = update.message.text

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"""📨 رد من إدارة البوت:

━━━━━━━━━━━━━━━━━━━━━━━━
{admin_reply}
━━━━━━━━━━━━━━━━━━━━━━━━

💡 يمكنك الرد مرة أخرى من خلال "📞 تواصل مع المطور"
"""
        )
        
        await update.message.reply_text(
            f"✅ تم إرسال ردك بنجاح إلى المستخدم!\n\n"
            f"🆔 User ID: {target_user_id}\n"
            f"💬 الرد: {admin_reply[:50]}..."
        )
        
        message_id = context.user_data.get('replying_to_message_id')
        if message_id:
            save_admin_reply(message_id, admin_reply)
        
        logger.info(f"✅ تم إرسال رد الأدمن إلى المستخدم {target_user_id}")
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ فشل إرسال الرد!\n\n"
            f"السبب: {str(e)}\n\n"
            f"💡 تأكد من أن المستخدم بدأ محادثة مع البوت"
        )
        logger.error(f"❌ خطأ في إرسال الرد: {e}")
    
    context.user_data.pop('replying_to_user_id', None)
    context.user_data.pop('replying_to_message_id', None)

async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "📢 إرسال رسالة جماعية\n\n"
        "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين:",
        reply_markup=reply_markup
    )
    context.user_data['waiting_for_broadcast'] = True

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY join_date DESC LIMIT 10')
    users = cursor.fetchall()
    conn.close()

    text = "👥 آخر 10 مستخدمين:\n\n"

    for u in users:
        text += f"━━━━━━━━━━━━━━\n"
        text += f"👤 {u[2]}\n"
        text += f"🆔 {u[0]}\n"
        text += f"📚 {u[3] or 'غير محدد'}\n"
        text += f"📅 انضم: {u[5]}\n\n"

    keyboard = []
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    user_id = int(update.callback_query.data.replace('block_user_', ''))
    block_user(user_id, "تم الحظر من قبل الأدمن")

    await update.callback_query.answer("✅ تم حظر المستخدم", show_alert=True)
    await admin_users_list(update, context)

async def admin_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    user_id = int(update.callback_query.data.replace('unblock_user_', ''))
    unblock_user(user_id)

    await update.callback_query.answer("✅ تم إلغاء الحظر", show_alert=True)
    await admin_users_list(update, context)

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال رسائل المستخدمين ورد الأدمن"""
    
    user = update.effective_user
    
    if is_admin(user) and 'replying_to_user_id' in context.user_data:
        await admin_send_reply(update, context)
        return
    
    if is_admin(user) and context.user_data.get('waiting_for_broadcast'):
        await send_broadcast_message(update, context)
        return
    
    if context.user_data.get('waiting_for_message'):
        message = update.message.text

        save_admin_message(user.id, user.username or user.first_name, message)

        sent_successfully = False
        
        if ADMIN_USER_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=f"📩 رسالة جديدة من:\n\n"
                         f"👤 {user.full_name} (@{user.username or 'لا يوجد'})\n"
                         f"🆔 ID: {user.id}\n\n"
                         f"💬 الرسالة:\n{message}\n\n"
                         f"📱 للرد: افتح البوت → لوحة الأدمن → الرسائل الواردة"
                )
                sent_successfully = True
                logger.info(f"✅ تم إرسال الرسالة للأدمن ID: {ADMIN_USER_ID}")
            except Exception as e:
                logger.error(f"❌ فشل الإرسال: {e}")
        
        await update.message.reply_text(
            "✅ تم إرسال رسالتك للمطور!\n"
            "سيتم الرد عليك في أقرب وقت ممكن.\n\n"
            "💡 يمكنك أيضاً التواصل مباشرة:\n"
            "👤 @SS_GG_X1\n"
            "👤 @ENG_GAD"
        )
        context.user_data['waiting_for_message'] = False

async def send_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة جماعية"""
    broadcast_text = update.message.text
    
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    success_count = 0
    fail_count = 0
    
    await update.message.reply_text(f"🔄 جاري الإرسال لـ {len(users)} مستخدم...")
    
    for user_id_tuple in users:
        user_id = user_id_tuple[0]
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 رسالة من إدارة البوت:\n\n{broadcast_text}"
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            logger.error(f"فشل الإرسال للمستخدم {user_id}: {e}")
    
    await update.message.reply_text(
        f"✅ تم الإرسال!\n\n"
        f"✅ نجح: {success_count}\n"
        f"❌ فشل: {fail_count}"
    )
    
    context.user_data.pop('waiting_for_broadcast', None)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    handlers = {
        'smart_search': smart_search_start,
        'mega_search': mega_search_handler,
        'show_all_mega': show_all_mega_results,
        'advanced_search': advanced_search_start,
        'browse_countries': browse_countries,
        'browse_majors': browse_majors,
        'featured_scholarships': show_featured_scholarships,
        'my_profile': show_profile,
        'my_favorites': show_favorites,
        'tracked_scholarships': show_tracked_scholarships,
        'smart_tips': smart_tips,
        'my_reminders': show_reminders,
        'help': show_help,
        'back_to_main': back_to_main,
        'restart_bot': restart_bot,
        'contact_developer': contact_developer,
        'admin_panel': admin_panel,
        'admin_stats': admin_stats,
        'admin_messages': admin_messages,
        'admin_broadcast': admin_broadcast_start,
        'admin_users': admin_users_list,
        'adv_search_now': advanced_search_execute,
    }

    if query.data.startswith('adv_degree_'):
        await advanced_search_funding(update, context)

    elif query.data.startswith('adv_funding_'):
        await advanced_search_keyword(update, context)

    elif query.data.startswith('country_'):
        await handle_country_selection(update, context)

    elif query.data.startswith('major_'):
        await handle_major_selection(update, context)

    elif query.data.startswith('save_fav_'):
        await save_favorite(update, context)

    elif query.data.startswith('block_user_'):
        await admin_block_user(update, context)

    elif query.data.startswith('unblock_user_'):
        await admin_unblock_user(update, context)

    elif query.data.startswith('read_msg_'):
        await admin_read_message(update, context)

    elif query.data.startswith('reply_msg_'):
        await admin_reply_to_user_start(update, context)

    elif query.data.startswith('region_'):
        await show_region_scholarships(update, context)

    elif query.data in handlers:
        await handlers[query.data](update, context)

async def setup_commands(application):
    """إعداد قائمة الأوامر في المينيو"""
    commands = [
        BotCommand("start", "🏠 رجوع للقائمة الرئيسية"),
        BotCommand("restart", "🔄 إعادة تشغيل البوت"),
        BotCommand("help", "ℹ️ دليل المساعدة"),
        BotCommand("profile", "📝 عرض الملف الشخصي")
    ]
    await application.bot.set_my_commands(commands)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /profile"""
    user_id = update.effective_user.id

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        text = f"""👤 ملفك الشخصي:

🆔 المعرف: {user[0]}
👤 الاسم: {user[2]}
📚 التخصص: {user[3] or 'غير محدد'}
🌍 الدولة المستهدفة: {user[4] or 'غير محدد'}
📅 تاريخ الانضمام: {user[5]}
🔔 التنبيهات: {'مفعلة' if user[6] else 'معطلة'}"""
    else:
        text = "❌ لم يتم العثور على ملفك الشخصي"

    keyboard = [
        [InlineKeyboardButton("✏️ تحديث الملف", callback_data='update_profile')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

def main():
    print("🚀 جاري تشغيل البوت...")
    logger.info("🚀 بدء تشغيل البوت")
    
    init_db()

    print("📊 إعداد قاعدة البيانات...")

    print("🌐 جاري تحديث المنح الموسعة من جميع أنحاء العالم...")
    
    # تحديث شامل من جميع المصادر
    all_scholarships = []
    
    # المنح الحكومية
    gov_scholarships = search_government_sites(None)
    all_scholarships.extend(gov_scholarships)
    
    # المنح الأوروبية
    european = search_european_scholarships()
    all_scholarships.extend(european)
    
    # المنح الآسيوية
    asian = search_asian_scholarships()
    all_scholarships.extend(asian)
    
    # منح الكومنولث
    commonwealth = search_commonwealth_scholarships()
    all_scholarships.extend(commonwealth)
    
    # منح أمريكا الشمالية
    north_american = search_north_american_scholarships()
    all_scholarships.extend(north_american)
    
    # منح الشرق الأوسط
    middle_east = search_middle_east_scholarships()
    all_scholarships.extend(middle_east)
    
    # منح المنظمات الدولية
    international = search_international_organizations()
    all_scholarships.extend(international)
    
    # منح الجامعات المرموقة
    universities = search_university_specific_scholarships()
    all_scholarships.extend(universities)
    
    # حفظ كل شيء
    save_scholarships_to_db(all_scholarships)
    
    print(f"✅ تم تحديث {len(all_scholarships)} منحة ممولة بالكامل من جميع أنحاء العالم!")
    logger.info(f"✅ تم تحديث {len(all_scholarships)} منحة")

    application = Application.builder().token(TOKEN).build()

    application.post_init = setup_commands

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart_bot))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    job_queue = application.job_queue
    job_queue.run_repeating(auto_update_scholarships, interval=3600, first=10)  # كل ساعة
    job_queue.run_repeating(send_pending_reminders, interval=3600, first=60)  # كل ساعة
    job_queue.run_repeating(send_scholarship_notifications, interval=21600, first=120)  # كل 6 ساعات
    job_queue.run_daily(send_weekly_digest, time=datetime.strptime("09:00", "%H:%M").time())  # كل يوم 9 صباحاً

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🤖 البوت الذكي يعمل الآن...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌐 البحث الموسع في المنح العالمية متاح!")
    print(f"🌍 {len(COUNTRIES)} دولة | 📚 {len(MAJORS)} تخصص")
    print(f"💰 أكثر من 100+ منحة ممولة بالكامل")
    print(f"👑 Admin: @{ADMIN_USERNAME}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔥 المصادر الجديدة:")
    print("   🇪🇺 منح أوروبية: Erasmus+, DAAD, Eiffel")
    print("   🇯🇵 منح آسيوية: MEXT, GKS, CSC")
    print("   🇬🇧 منح الكومنولث: Chevening, Gates Cambridge")
    print("   🇺🇸 منح أمريكية: Fulbright, Humphrey")
    print("   🇦🇺 منح أسترالية: Australia Awards")
    print("   🇦🇪 منح خليجية: MBRHE, KAUST")
    print("   🏛️ منح دولية: UN, WHO, IAEA")
    print("   🎓 منح جامعات: Oxford, Cambridge, ETH")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("⚡ المميزات:")
    print("   ✅ بحث موسع في 100+ مصدر")
    print("   ✅ تحديث تلقائي كل ساعة")
    print("   ✅ بحث دقيق متقدم")
    print("   ✅ نصائح ذكية شخصية")
    print("   ✅ نظام المفضلة والحالات")
    print("   ✅ تذكيرات تلقائية")
    print("   ✅ نظام رد كامل للأدمن")
    print("   ✅ Logging احترافي")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ البوت يعمل بنجاح")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()