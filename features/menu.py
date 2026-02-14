from telegram import InlineKeyboardButton, InlineKeyboardMarkup, User

from app import is_admin

# ============================================
# 🎛️ MENU SYSTEM - احترافي ومنظم
# ============================================

class ScholarshipBotMenus:
    """نظام القوائم الاحترافي - كل قائمة جديدة كل مرة"""
    
    @staticmethod
    def get_navigation_row():
        """صف التنقل الثابت"""
        return [
            [
                InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main"),
                InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="restart_bot"),
            ]
        ]
    
    @staticmethod
    def get_main_menu(is_admin=False):
        """القائمة الرئيسية - منظمة في أقسام"""
        keyboard = []
        
        # القسم الأول: البحث (2 صفوف)
        keyboard.extend([
            [InlineKeyboardButton("🔍 البحث الذكي", callback_data="smart_search")],
            [InlineKeyboardButton("🚀 البحث الموسع", callback_data="mega_search")],
        ])
        
        # القسم الثاني: التصفح (صف واحد)
        keyboard.append([
            InlineKeyboardButton("🌍 حسب الدولة", callback_data="browse_countries"),
            InlineKeyboardButton("📚 حسب التخصص", callback_data="browse_majors"),
        ])
        
        # القسم الثالث: شخصي (صف واحد)
        keyboard.append([
            InlineKeyboardButton("💾 منحي المفضلة", callback_data="my_favorites"),
            InlineKeyboardButton("🔔 التنبيهات", callback_data="my_reminders"),
        ])
        
        # القسم الرابع: مساعدة ودعم (صف واحد)
        keyboard.append([
            InlineKeyboardButton("🔔 نصائح ذكية", callback_data="smart_tips"),
            InlineKeyboardButton("ℹ️ المساعدة", callback_data="help"),
        ])
        
        # لو أدمن: قسم الأدمن في الأول
        if is_admin:
            keyboard.insert(0, [
                InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")
            ])
        
        # إضافة التنقل في الآخر
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_search_menu():
        """قائمة البحث المتقدم"""
        keyboard = [
            [InlineKeyboardButton("🎯 بحث متقدم", callback_data="advanced_search")],
            [InlineKeyboardButton("⭐ المنح المميزة", callback_data="featured_scholarships")],
            [InlineKeyboardButton("📢 آخر التحديثات", callback_data="latest_updates")],
        ]
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_profile_menu():
        """قائمة الملف الشخصي"""
        keyboard = [
            [InlineKeyboardButton("✏️ تحديث التخصص", callback_data="edit_major")],
            [InlineKeyboardButton("🌍 تحديث الدولة", callback_data="edit_country")],
            [InlineKeyboardButton("🔔 الإشعارات", callback_data="notification_settings")],
            [InlineKeyboardButton("📧 الملخص الأسبوعي", callback_data="toggle_digest")],
        ]
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_panel():
        """لوحة تحكم الأدمن"""
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("📢 الإرسال الجماعي", callback_data="admin_broadcast")],
            [InlineKeyboardButton("💬 الرسائل الواردة", callback_data="admin_messages")],
            [InlineKeyboardButton("🔄 تحديث المنح", callback_data="admin_update")],
        ]
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_premium_menu():
        """قائمة المميزات المدفوعة"""
        keyboard = [
            [InlineKeyboardButton("📄 تحليل CV", callback_data="premium_cv")],
            [InlineKeyboardButton("🎯 ترشيحات خاصة", callback_data="premium_recommend")],
            [InlineKeyboardButton("💎 اشتراك Premium", callback_data="premium_subscribe")],
        ]
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_notification_menu():
        """إعدادات الإشعارات"""
        keyboard = [
            [InlineKeyboardButton("⏰ تنبيهات المواعيد", callback_data="toggle_deadline")],
            [InlineKeyboardButton("📋 تحديثات المتطلبات", callback_data="toggle_requirements")],
            [InlineKeyboardButton("📄 تذكيرات الوثائق", callback_data="toggle_documents")],
            [InlineKeyboardButton("📅 3 أيام قبل", callback_data="days_3")],
            [InlineKeyboardButton("📅 7 أيام قبل", callback_data="days_7")],
            [InlineKeyboardButton("📅 14 يوم قبل", callback_data="days_14")],
        ]
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_countries_menu():
        """قائمة الدول - مقسمة جغرافياً"""
        keyboard = [
            # أوروبا
            [
                InlineKeyboardButton("🇬🇧 بريطانيا", callback_data="country_uk"),
                InlineKeyboardButton("🇩🇪 ألمانيا", callback_data="country_germany"),
            ],
            [
                InlineKeyboardButton("🇫🇷 فرنسا", callback_data="country_france"),
                InlineKeyboardButton("🇮🇹 إيطاليا", callback_data="country_italy"),
            ],
            # آسيا
            [
                InlineKeyboardButton("🇨🇳 الصين", callback_data="country_china"),
                InlineKeyboardButton("🇯🇵 اليابان", callback_data="country_japan"),
            ],
            [
                InlineKeyboardButton("🇰🇷 كوريا", callback_data="country_south_korea"),
                InlineKeyboardButton("🇹🇷 تركيا", callback_data="country_turkey"),
            ],
            # أمريكا
            [
                InlineKeyboardButton("🇺🇸 أمريكا", callback_data="country_usa"),
                InlineKeyboardButton("🇨🇦 كندا", callback_data="country_canada"),
            ],
            # الخليج
            [
                InlineKeyboardButton("🇦🇪 الإمارات", callback_data="country_uae"),
                InlineKeyboardButton("🇸🇦 السعودية", callback_data="country_saudi"),
            ],
        ]
        keyboard.extend(ScholarshipBotMenus.get_navigation_row())
        return InlineKeyboardMarkup(keyboard)

# ============================================
# 🎨 استخدام سهل في main.py
# ============================================

# في دالة start:
menus = ScholarshipBotMenus()
keyboard = menus.get_main_menu(is_admin(User))
reply_markup = keyboard

# في أي مكان تاني:
admin_keyboard = ScholarshipBotMenus.get_admin_panel()
profile_keyboard = ScholarshipBotMenus.get_profile_menu()
