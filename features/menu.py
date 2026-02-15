from telegram import InlineKeyboardButton

# ============================================
# 🎛️ MAIN MENU (القائمة الرئيسية)
# ============================================
MAIN_MENU = [
    [InlineKeyboardButton("🔍 البحث الذكي عن المنح", callback_data="smart_search")],
    [InlineKeyboardButton("🚀 البحث الموسع الشامل", callback_data="mega_search")],
    [InlineKeyboardButton("🎯 بحث دقيق متقدم", callback_data="advanced_search")],
    [InlineKeyboardButton("🌍 تصفح حسب الدولة", callback_data="browse_countries")],
    [InlineKeyboardButton("📚 تصفح حسب التخصص", callback_data="browse_majors")],
    [InlineKeyboardButton("⭐ المنح المميزة", callback_data="featured_scholarships")],
    [InlineKeyboardButton("💾 منحي المفضلة", callback_data="my_favorites")],
    [InlineKeyboardButton("🔔 نصائح ذكية", callback_data="smart_tips")],
    [InlineKeyboardButton("📝 ملفي الشخصي", callback_data="my_profile")],
    [InlineKeyboardButton("🔔 التنبيهات", callback_data="my_reminders")],
    [InlineKeyboardButton("💎 Premium", callback_data="premium")],
    [InlineKeyboardButton("👥 قنوات البوت الاساسيه ", callback_data="community")],
    [InlineKeyboardButton("📞 تواصل مع المطور", callback_data="contact_developer")],
    [InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")],
]

# ============================================
# 👑 ADMIN MENU
# ============================================
ADMIN_MENU = [
    [InlineKeyboardButton("📊 Analytics", callback_data="admin_stats")],
    [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
    [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
    [InlineKeyboardButton("📩 الرسائل", callback_data="admin_messages")],
]

# ============================================
# 💎 PREMIUM MENU
# ============================================
PREMIUM_MENU = [
    [InlineKeyboardButton("📄 تحليل CV", callback_data="premium_cv")],
    [InlineKeyboardButton("🎯 استشارة دراسية", callback_data="premium_consult")],
    [InlineKeyboardButton("🚀 ترشيحات خاصة", callback_data="premium_recommend")],
]

# ============================================
# 🧭 NAVIGATION BUTTONS
# ============================================
NAVIGATION = [
    [
        InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main"),
        InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="restart_bot"),
    ]
]

# ============================================
# 📦 FUNCTIONS
# ============================================

def get_main_menu(is_admin=False):
    """القائمة الرئيسية - نسخة جديدة كل مرة"""
    keyboard = [row[:] for row in MAIN_MENU]
    
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")])
    
    keyboard.extend([row[:] for row in NAVIGATION])
    
    return keyboard

def get_admin_menu():
    """قائمة الأدمن"""
    keyboard = [row[:] for row in ADMIN_MENU]
    keyboard.extend([row[:] for row in NAVIGATION])
    return keyboard

def get_premium_menu():
    """قائمة Premium"""
    keyboard = [row[:] for row in PREMIUM_MENU]
    keyboard.extend([row[:] for row in NAVIGATION])
    return keyboard