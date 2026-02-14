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
# 🌐 دوال البحث عن المنح من المواقع
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

def search_scholarships_online(country=None, major=None, keyword=None):
    """البحث عن المنح على الإنترنت من مصادر متعددة"""
    scholarships = []

    try:
        scholarships.extend(search_scholarship_portal(country, major, keyword))
        scholarships.extend(search_scholars4dev(country, major, keyword))

        if major in ['engineering', 'cs', 'science', 'business']:
            scholarships.extend(search_findamasters(country, major))

        scholarships.extend(search_government_sites(country))
        scholarships.extend(search_fastweb(keyword))
        scholarships.extend(search_scholarships_com(keyword))
        scholarships.extend(search_bigfuture(keyword))

    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")

    return scholarships

def search_scholarship_portal(country, major, keyword):
    """البحث في ScholarshipPortal.com"""
    scholarships = []
    try:
        base_url = "https://www.scholarshipportal.com"
        search_url = f"{base_url}/scholarships"

        params = {}
        if country:
            params['country'] = country
        if major:
            params['discipline'] = major

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            scholarship_items = soup.find_all('div', class_='scholarship-item')

            for item in scholarship_items[:10]:
                try:
                    name = item.find('h3').text.strip() if item.find('h3') else 'غير متوفر'
                    link = base_url + item.find('a')['href'] if item.find('a') else ''
                    description = item.find('p').text.strip() if item.find('p') else 'غير متوفر'

                    scholarships.append({
                        'name': name,
                        'country': country or 'متعددة',
                        'major': major or 'جميع التخصصات',
                        'deadline': 'يرجى زيارة الموقع',
                        'link': link,
                        'description': description,
                        'source': 'ScholarshipPortal'
                    })
                except:
                    continue

    except Exception as e:
        logger.error(f"خطأ في ScholarshipPortal: {e}")

    return scholarships

def search_scholars4dev(country, major, keyword):
    """البحث في Scholars4Dev"""
    scholarships = []
    try:
        base_url = "https://www.scholars4dev.com"

        if country:
            search_url = f"{base_url}/?s={country}+scholarships"
        elif major:
            search_url = f"{base_url}/?s={major}+scholarships"
        elif keyword:
            search_url = f"{base_url}/?s={keyword}"
        else:
            search_url = f"{base_url}/scholarships/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', limit=10)

            for article in articles:
                try:
                    title_tag = article.find('h2') or article.find('h3')
                    name = title_tag.text.strip() if title_tag else 'غير متوفر'

                    link_tag = title_tag.find('a') if title_tag else None
                    link = link_tag['href'] if link_tag else ''

                    desc_tag = article.find('p')
                    description = desc_tag.text.strip()[:200] if desc_tag else 'غير متوفر'

                    scholarships.append({
                        'name': name,
                        'country': country or 'متعددة',
                        'major': major or 'جميع التخصصات',
                        'deadline': 'يرجى زيارة الموقع',
                        'link': link,
                        'description': description,
                        'source': 'Scholars4Dev'
                    })
                except:
                    continue

    except Exception as e:
        logger.error(f"خطأ في Scholars4Dev: {e}")

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
    """البحث في المواقع الحكومية للمنح"""
    scholarships = []

    gov_sites = {
        'germany': {
            'name': 'منح DAAD الألمانية',
            'url': 'https://www.daad.de/en/',
            'description': 'منح الحكومة الألمانية للدراسات العليا'
        },
        'turkey': {
            'name': 'منحة تركيا Türkiye Bursları',
            'url': 'https://www.turkiyeburslari.gov.tr/',
            'description': 'منحة الحكومة التركية الممولة بالكامل'
        },
        'china': {
            'name': 'منحة الحكومة الصينية CSC',
            'url': 'https://www.campuschina.org/',
            'description': 'منحة حكومية صينية لجميع المراحل الدراسية'
        },
        'france': {
            'name': 'منح Campus France',
            'url': 'https://www.campusfrance.org/',
            'description': 'منح الحكومة الفرنسية'
        },
        'uk': {
            'name': 'منح Chevening البريطانية',
            'url': 'https://www.chevening.org/',
            'description': 'منح حكومية بريطانية للماجستير'
        },
        'australia': {
            'name': 'منح Australia Awards',
            'url': 'https://www.australiaawards.gov.au/',
            'description': 'منح الحكومة الأسترالية'
        },
        'japan': {
            'name': 'منح MEXT اليابانية',
            'url': 'https://www.studyinjapan.go.jp/',
            'description': 'منح وزارة التعليم اليابانية'
        },
        'south_korea': {
            'name': 'منح حكومة كوريا الجنوبية',
            'url': 'https://www.studyinkorea.go.kr/',
            'description': 'منح GKS الحكومية الكورية'
        },
        'netherlands': {
            'name': 'منح Holland Scholarship',
            'url': 'https://www.studyinholland.nl/',
            'description': 'منح الحكومة الهولندية'
        },
        'sweden': {
            'name': 'منح المعهد السويدي',
            'url': 'https://si.se/en/',
            'description': 'منح الحكومة السويدية'
        }
    }

    if country and country in gov_sites:
        site = gov_sites[country]
        scholarships.append({
            'name': site['name'],
            'country': COUNTRIES.get(country, country),
            'major': 'جميع التخصصات',
            'deadline': 'يتم التحديث سنوياً',
            'link': site['url'],
            'description': site['description'],
            'source': 'موقع حكومي رسمي',
            'funding_type': 'ممولة بالكامل',
            'degree_level': 'بكالوريوس، ماجستير، دكتوراه'
        })
    else:
        for key, site in gov_sites.items():
            scholarships.append({
                'name': site['name'],
                'country': COUNTRIES.get(key, key),
                'major': 'جميع التخصصات',
                'deadline': 'يتم التحديث سنوياً',
                'link': site['url'],
                'description': site['description'],
                'source': 'موقع حكومي رسمي',
                'funding_type': 'ممولة بالكامل'
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
    """تحديث المنح تلقائياً كل ساعة في الخلفية"""
    logger.info("🔄 جاري تحديث المنح التلقائي...")

    try:
        gov_scholarships = search_government_sites(None)
        save_scholarships_to_db(gov_scholarships)

        additional = search_fastweb()
        additional.extend(search_scholarships_com())
        additional.extend(search_bigfuture())
        save_scholarships_to_db(additional)

        logger.info(f"✅ تم تحديث {len(gov_scholarships) + len(additional)} منحة")
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
        [InlineKeyboardButton("🤖 المساعد الذكي AI", callback_data='ai_menu')],
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

🎯 يغطي:
• {len(COUNTRIES)} دولة حول العالم
• {len(MAJORS)} تخصص أكاديمي
• منح ممولة بالكامل وجزئياً
• جميع المراحل الدراسية

🆕 المميزات الجديدة:
⚡ بحث دقيق متقدم بفلاتر قوية
⚡ نصائح ذكية شخصية
⚡ حفظ المنح المفضلة
⚡ تذكيرات تلقائية قبل المواعيد
⚡ ملخص أسبوعي مخصص
⚡ نظام حالات للمنح

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
        text += f"🔗 {fav[4]}\n"
        text += f"📅 تم الحفظ: {fav[5]}\n\n"

    keyboard = [
        [InlineKeyboardButton("🔄 فلترة حسب الحالة", callback_data='filter_favorites')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, disable_web_page_preview=True)

async def save_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ منحة في المفضلة"""
    scholarship_id = int(update.callback_query.data.replace('save_fav_', ''))
    user_id = update.effective_user.id

    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, link FROM scholarships WHERE id = ?', (scholarship_id,))
    scholarship = cursor.fetchone()
    conn.close()

    if scholarship:
        success = save_to_favorites(user_id, scholarship_id, scholarship[0], scholarship[1])
        if success:
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
            
            # 🆕 زر القراءة والرد
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

# ============================================
# 🆕 نظام الرد على رسائل المستخدمين
# ============================================

async def admin_reply_to_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية الرد على رسالة مستخدم"""
    user = update.effective_user

    if not is_admin(user):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return

    # استخراج message_id و user_id من callback_data
    data = update.callback_query.data  # مثال: reply_msg_5_6748814044
    parts = data.split('_')
    message_id = parts[2]
    target_user_id = parts[3]

    # حفظ البيانات في context
    context.user_data['replying_to_user_id'] = target_user_id
    context.user_data['replying_to_message_id'] = message_id

    # جلب بيانات الرسالة الأصلية
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
    
    # التحقق من وجود رد قيد الإعداد
    if 'replying_to_user_id' not in context.user_data:
        return  # ليس رد على رسالة
    
    user = update.effective_user
    if not is_admin(user):
        return

    target_user_id = int(context.user_data['replying_to_user_id'])
    admin_reply = update.message.text

    # إرسال الرد للمستخدم
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
        
        # تأكيد للأدمن
        await update.message.reply_text(
            f"✅ تم إرسال ردك بنجاح إلى المستخدم!\n\n"
            f"🆔 User ID: {target_user_id}\n"
            f"💬 الرد: {admin_reply[:50]}..."
        )
        
        # حفظ الرد في قاعدة البيانات
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
    
    # مسح البيانات المؤقتة
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

# ============================================
# 💬 معالج رسائل المستخدمين (محسّن)
# ============================================

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال رسائل المستخدمين ورد الأدمن"""
    
    user = update.effective_user
    
    # 🆕 التحقق من وجود رد من الأدمن
    if is_admin(user) and 'replying_to_user_id' in context.user_data:
        await admin_send_reply(update, context)
        return
    
    # 🆕 معالج البث الجماعي
    if is_admin(user) and context.user_data.get('waiting_for_broadcast'):
        await send_broadcast_message(update, context)
        return
    
    # الكود الأصلي لاستقبال رسائل المستخدمين
    if context.user_data.get('waiting_for_message'):
        message = update.message.text

        save_admin_message(user.id, user.username or user.first_name, message)

        # محاولة الإرسال بالـ ID
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

# ============================================
# 🎮 معالج الأزرار الرئيسي
# ============================================
from ai_assistant import (
    ai_analyze_profile,
    ai_review_motivation_letter,
    ai_answer_question,
    ai_compare_scholarships,
    ai_generate_application_checklist,
    ai_career_path_advice,
    #ai_smart_search_suggestions,
    ai_interview_preparation,
    ai_scholarship_match_score,
    ai_quick_tip,
    save_ai_conversation,
    get_ai_usage_stats
)

# ============================================
# 🎯 معالجات المساعد الذكي
# ============================================

async def ai_assistant_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة المساعد الذكي"""
    
    text = """🤖 المساعد الذكي AI

اختر الخدمة التي تريدها:"""

    keyboard = [
        [InlineKeyboardButton("🔍 تحليل ملفي الشخصي", callback_data='ai_profile_analysis')],
        [InlineKeyboardButton("📝 مراجعة Motivation Letter", callback_data='ai_review_letter')],
        [InlineKeyboardButton("⚖️ مقارنة منحتين", callback_data='ai_compare_start')],
        [InlineKeyboardButton("✅ إنشاء Checklist", callback_data='ai_checklist')],
        [InlineKeyboardButton("💼 نصائح المسار المهني", callback_data='ai_career')],
        [InlineKeyboardButton("🎤 التحضير للمقابلة", callback_data='ai_interview_prep')],
        [InlineKeyboardButton("💡 نصيحة سريعة", callback_data='ai_quick_tips')],
        [InlineKeyboardButton("❓ اسأل المساعد", callback_data='ai_ask_question')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def ai_profile_analysis_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحليل الملف الشخصي بالـ AI"""
    user_id = update.effective_user.id
    
    await update.callback_query.edit_message_text("🔄 جاري تحليل ملفك الشخصي بواسطة AI...")
    
    # جلب بيانات المستخدم
    conn = sqlite3.connect('scholarship_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT major, target_country FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data or not user_data[0]:
        await update.callback_query.edit_message_text(
            "❗ يرجى تحديث ملفك الشخصي أولاً!\n\n"
            "اضغط 'ملفي الشخصي' من القائمة الرئيسية."
        )
        return
    
    user_profile = {
        'major': user_data[0],
        'target_country': user_data[1] or 'غير محدد'
    }
    
    # تحليل AI
    analysis = await ai_analyze_profile(user_profile)
    
    # حفظ المحادثة
    save_ai_conversation(user_id, "تحليل الملف الشخصي", analysis, "profile_analysis")
    
    # عرض النتيجة
    if len(analysis) > 4000:
        parts = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
        for part in parts[:-1]:
            await update.callback_query.message.reply_text(part)
        
        keyboard = []
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(parts[-1], reply_markup=reply_markup)
    else:
        keyboard = []
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(analysis, reply_markup=reply_markup)


async def ai_review_letter_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء مراجعة Motivation Letter"""
    
    text = """📝 مراجعة Motivation Letter

أرسل لي رسالة الدافع الخاصة بك (Motivation Letter) وسأقوم بمراجعتها وإعطائك نصائح للتحسين.

يمكنك:
• نسخ النص مباشرة
• إرسال ملف PDF/Word
• كتابة مسودة أولية

اكتب أو أرسل الرسالة الآن:"""

    keyboard = [
        [InlineKeyboardButton("❌ إلغاء", callback_data='ai_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    context.user_data['waiting_for_motivation_letter'] = True


async def ai_compare_scholarships_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء مقارنة المنح"""
    user_id = update.effective_user.id
    favorites = get_favorites(user_id)
    
    if len(favorites) < 2:
        text = "⚠️ تحتاج منحتين على الأقل في المفضلة لعمل المقارنة.\n\nاحفظ بعض المنح أولاً!"
        keyboard = []
        add_navigation_row(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return
    
    text = "⚖️ مقارنة المنح بالذكاء الاصطناعي\n\nاختر المنحة الأولى:"
    
    keyboard = []
    for i, fav in enumerate(favorites[:5]):
        keyboard.append([
            InlineKeyboardButton(f"{i+1}. {fav[3][:40]}...", callback_data=f'ai_cmp1_{fav[1]}')
        ])
    
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def ai_quick_tips_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة النصائح السريعة"""
    
    text = "💡 نصائح سريعة من AI\n\nاختر الموضوع:"
    
    keyboard = [
        [InlineKeyboardButton("📄 نصيحة للسيرة الذاتية", callback_data='ai_tip_cv')],
        [InlineKeyboardButton("📝 نصيحة للرسالة التحفيزية", callback_data='ai_tip_motivation')],
        [InlineKeyboardButton("🎤 نصيحة للمقابلة", callback_data='ai_tip_interview')],
        [InlineKeyboardButton("🌐 نصيحة لاختبار اللغة", callback_data='ai_tip_language')],
        [InlineKeyboardButton("📅 نصيحة لإدارة المواعيد", callback_data='ai_tip_deadline')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def ai_quick_tip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج النصائح السريعة"""
    category = update.callback_query.data.replace('ai_tip_', '')
    
    await update.callback_query.edit_message_text("🤔 جاري توليد نصيحة ذكية...")
    
    tip = await ai_quick_tip(category)
    
    text = f"💡 نصيحة ذكية:\n\n{tip}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 نصيحة أخرى", callback_data=f'ai_tip_{category}')],
        [InlineKeyboardButton("◀️ رجوع", callback_data='ai_quick_tips')]
    ]
    add_navigation_row(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def ai_ask_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء سؤال المساعد"""
    
    text = """❓ اسأل المساعد الذكي

اكتب سؤالك عن المنح الدراسية وسأجيبك بشكل مفصل.

أمثلة:
• ما أفضل منحة للهندسة في ألمانيا؟
• كيف أكتب Motivation Letter قوية؟
• متى أبدأ التحضير للمنحة؟

اكتب سؤالك الآن:"""

    keyboard = [
        [InlineKeyboardButton("❌ إلغاء", callback_data='ai_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    context.user_data['waiting_for_ai_question'] = True


async def handle_ai_interactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج تفاعلات AI (أسئلة، مراجعة رسائل...)"""
    user = update.effective_user
    message_text = update.message.text
    
    # مراجعة Motivation Letter
    if context.user_data.get('waiting_for_motivation_letter'):
        await update.message.reply_text("🔄 جاري مراجعة رسالتك...")
        
        # افترض منحة افتراضية (أو استخدم آخر منحة شاهدها المستخدم)
        scholarship_info = {
            'name': 'منحة عامة',
            'country': 'غير محدد',
            'major': 'جميع التخصصات'
        }
        
        review = await ai_review_motivation_letter(message_text, scholarship_info)
        
        save_ai_conversation(user.id, "مراجعة Motivation Letter", review, "letter_review")
        
        if len(review) > 4000:
            parts = [review[i:i+4000] for i in range(0, len(review), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(review)
        
        context.user_data.pop('waiting_for_motivation_letter', None)
        return True
    
    # سؤال للمساعد
    if context.user_data.get('waiting_for_ai_question'):
        await update.message.reply_text("🤔 دعني أفكر...")
        
        # جلب سياق المستخدم
        conn = sqlite3.connect('scholarship_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT major, target_country FROM users WHERE user_id = ?', (user.id,))
        user_data = cursor.fetchone()
        conn.close()
        
        user_context = {
            'major': user_data[0] if user_data else None,
            'target_country': user_data[1] if user_data else None
        }
        
        answer = await ai_answer_question(message_text, user_context)
        
        save_ai_conversation(user.id, message_text, answer, "question_answer")
        
        if len(answer) > 4000:
            parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(answer)
        
        context.user_data.pop('waiting_for_ai_question', None)
        return True
    
    return False
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    handlers = {
        'smart_search': smart_search_start,
        'advanced_search': advanced_search_start,
        'browse_countries': browse_countries,
        'browse_majors': browse_majors,
        'featured_scholarships': show_featured_scholarships,
        'my_profile': show_profile,
        'my_favorites': show_favorites,
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

        # AI handlers
        'ai_menu': ai_assistant_menu,
        'ai_profile_analysis': ai_profile_analysis_handler,
        'ai_review_letter': ai_review_letter_start,
        'ai_compare_start': ai_compare_scholarships_start,
        'ai_quick_tips': ai_quick_tips_menu,
        'ai_ask_question': ai_ask_question_start,
        
    }

    # المعالجات الخاصة
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

    elif query.data.startswith('ai_tip_'):
        await ai_quick_tip_handler(update, context)

    elif query.data in handlers:
        await handlers[query.data](update, context)

# ============================================
# 🆕 إعداد Bot Commands
# ============================================

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

# ============================================
# 🚀 دالة Main - نقطة البداية
# ============================================

def main():
    print("🚀 جاري تشغيل البوت...")
    logger.info("🚀 بدء تشغيل البوت")
    
    init_db()

    print("📊 إعداد قاعدة البيانات...")

    # تحديث المنح عند بدء التشغيل
    print("🌐 جاري تحديث المنح...")
    gov_scholarships = search_government_sites(None)
    save_scholarships_to_db(gov_scholarships)
    print(f"✅ تم تحديث {len(gov_scholarships)} منحة")
    logger.info(f"✅ تم تحديث {len(gov_scholarships)} منحة")

    application = Application.builder().token(TOKEN).build()

    # إعداد Bot Commands
    application.post_init = setup_commands

    # المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart_bot))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    # Background Jobs
    job_queue = application.job_queue
    job_queue.run_repeating(auto_update_scholarships, interval=3600, first=10)  # كل ساعة
    job_queue.run_repeating(send_pending_reminders, interval=3600, first=60)  # كل ساعة
    job_queue.run_daily(send_weekly_digest, time=datetime.strptime("09:00", "%H:%M").time())  # كل يوم 9 صباحاً

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🤖 البوت الذكي يعمل الآن...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌐 البحث في المنح العالمية متاح!")
    print(f"🌍 {len(COUNTRIES)} دولة | 📚 {len(MAJORS)} تخصص")
    print(f"👑 Admin: @{ADMIN_USERNAME}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🆕 المميزات الجديدة:")
    print("   ⚡ بحث دقيق متقدم")
    print("   ⚡ نصائح ذكية شخصية")
    print("   ⚡ حفظ المنح المفضلة مع الحالات")
    print("   ⚡ تذكيرات تلقائية قبل المواعيد")
    print("   ⚡ ملخص أسبوعي مخصص")
    print("   ⚡ نظام رد كامل للأدمن")
    print("   ⚡ Logging احترافي")
    print("   ⚡ تحديث تلقائي في الخلفية")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ البوت يعمل بنجاح")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()