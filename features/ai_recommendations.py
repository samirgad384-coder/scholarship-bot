import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters
import json
import logging
import os

logger = logging.getLogger(__name__)

DB_NAME = "scholarship_bot.db"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ============================================
# 🧠 AI ENGINE - Groq Integration
# ============================================

async def get_ai_recommendation(user_profile, context="general"):
    """
    تحليل ذكي باستخدام Groq API لتقديم توصيات مخصصة
    """
    if not GROQ_API_KEY:
        return await get_fallback_recommendation(user_profile, context)
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = build_ai_prompt(user_profile, context)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "أنت خبير منح دراسية دولية ومستشار تعليمي محترف. قدم توصيات دقيقة ومفصلة."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=1024
        )
        
        recommendation = chat_completion.choices[0].message.content
        
        # حفظ التوصية في قاعدة البيانات
        save_ai_recommendation(user_profile.get("user_id"), context, recommendation, 0.95)
        
        return recommendation
        
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return await get_fallback_recommendation(user_profile, context)


def build_ai_prompt(user_profile, context):
    """بناء Prompt ذكي للـ AI"""
    
    prompts = {
        "acceptance_chance": f"""
        حلل فرص القبول التالية وقدم تقييم دقيق:
        - المعدل: {user_profile.get('score', 'غير متوفر')}
        - التخصص: {user_profile.get('major', 'غير متوفر')}
        - الدولة المستهدفة: {user_profile.get('target_country', 'غير متوفرة')}
        - اللغة: {user_profile.get('english_level', 'غير متوفر')}
        
        قدم:
        1. نسبة قبول متوقعة (%)
        2. نقاط القوة
        3. نقاط الضعف
        4. توصيات للتحسين
        5. أفضل 3 منح مناسبة
        """,
        
        "cv_improvement": f"""
        حلل الـ CV التالي وقدم تحسينات احترافية:
        {user_profile.get('cv_text', 'لا يوجد CV')}
        
        قدم:
        1. التقييم العام
        2. الأخطاء الشائعة
        3. تحسينات مقترحة
        4. كلمات مفتاحية يجب إضافتها
        5. تنسيق أفضل
        """,
        
        "motivation_letter": f"""
        اكتب خطاب تحفيزي احترافي للمنحة التالية:
        - اسم المنحة: {user_profile.get('scholarship_name', 'غير متوفر')}
        - التخصص: {user_profile.get('major', 'غير متوفر')}
        - الخبرات: {user_profile.get('experience', 'غير متوفرة')}
        - الأهداف: {user_profile.get('goals', 'غير محددة')}
        
        اكتب خطاباً من 3 فقرات:
        1. المقدمة والاهتمام
        2. الخبرات والإنجازات
        3. الأهداف المستقبلية
        """,
        
        "scholarship_matching": f"""
        ابحث عن أفضل المنح المناسبة لهذا الطالب:
        - المعدل: {user_profile.get('score', 'غير متوفر')}
        - التخصص: {user_profile.get('major', 'غير متوفر')}
        - الدولة: {user_profile.get('target_country', 'غير متوفرة')}
        - الميزانية: {user_profile.get('budget', 'غير متوفرة')}
        
        قدم قائمة بـ 5 منح مع:
        1. اسم المنحة
        2. نسبة التوافق (%)
        3. سبب الترشيح
        4. موعد التقديم
        5. المتطلبات الأساسية
        """,
        
        "general": f"""
        قدم نصائح مخصصة للطالب:
        - المرحلة: {user_profile.get('stage', 'غير متوفرة')}
        - التخصص: {user_profile.get('major', 'غير متوفر')}
        - الهدف: الدراسة في {user_profile.get('target_country', 'خارج البلاد')}
        
        قدم:
        1. خطة عمل شهرية
        2. مهارات يجب تطويرها
        3. شهادات مقترحة
        4. أخطاء شائعة لتجنبها
        """
    }
    
    return prompts.get(context, prompts["general"])


async def get_fallback_recommendation(user_profile, context):
    """توصيات بديلة عند عدم توفر AI"""
    
    fallbacks = {
        "acceptance_chance": f"""
📊 تحليل فرص القبول:

✅ نقاط القوة:
• معدل جيد ({user_profile.get('score', 'N/A')})
• تخصص مطلوب ({user_profile.get('major', 'N/A')})

⚠️ نقاط للتحسين:
• حسّن مستوى اللغة الإنجليزية
• أضف شهادات إضافية
• عزّز خبراتك العملية

🎯 توصيات:
• قدّم على 5-10 منح مختلفة
• ركّز على المنح المتوسطة التنافسية
• حضّر مستندات قوية
        """,
        
        "general": f"""
💡 نصائح مخصصة لك:

📅 خطة الشهر القادم:
• الأسبوع 1: تجهيز المستندات الأساسية
• الأسبوع 2: تحسين CV وكتابة الخطابات
• الأسبوع 3: البحث عن منح مناسبة
• الأسبوع 4: التقديم على المنح

🎓 مهارات مهمة:
• IELTS/TOEFL
• كتابة Academic Writing
• مقابلات شخصية

🏆 منح ننصح بها:
• Erasmus+ (أوروبا)
• Chevening (بريطانيا)
• Fulbright (أمريكا)
        """
    }
    
    return fallbacks.get(context, fallbacks["general"])


# ============================================
# 🗄️ DATABASE FUNCTIONS
# ============================================

def save_ai_recommendation(user_id, rec_type, content, confidence):
    """حفظ التوصية في قاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO ai_recommendations 
    (user_id, recommendation_type, content, confidence_score, created_at, is_accepted)
    VALUES (?, ?, ?, ?, ?, 0)
    """, (
        user_id,
        rec_type,
        content,
        confidence,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    conn.commit()
    conn.close()


def get_user_recommendations(user_id, limit=5):
    """جلب توصيات المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT recommendation_type, content, confidence_score, created_at, is_accepted
    FROM ai_recommendations
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """, (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return results


def accept_recommendation(rec_id):
    """وضع علامة على التوصية كمقبولة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE ai_recommendations
    SET is_accepted = 1
    WHERE id = ?
    """, (rec_id,))
    
    conn.commit()
    conn.close()


# ============================================
# 🎯 APPLICATION PLANNER
# ============================================

async def create_application_plan(user_id, scholarship_id, scholarship_data):
    """إنشاء خطة تقدم ذكية للمنحة"""
    
    plan_steps = [
        {"step": "prepare_documents", "name": "تجهيز المستندات", "duration_days": 7},
        {"step": "write_essays", "name": "كتابة المقالات", "duration_days": 10},
        {"step": "get_recommendations", "name": "خطابات التوصية", "duration_days": 14},
        {"step": "take_tests", "name": "اختبارات اللغة", "duration_days": 30},
        {"step": "submit_application", "name": "إرسال الطلب", "duration_days": 1},
        {"step": "prepare_interview", "name": "تحضير المقابلة", "duration_days": 14},
        {"step": "follow_up", "name": "المتابعة", "duration_days": 30}
    ]
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO application_plans
    (user_id, scholarship_id, plan_data, progress, current_step, created_at, updated_at)
    VALUES (?, ?, ?, 0, ?, ?, ?)
    """, (
        user_id,
        scholarship_id,
        json.dumps(plan_steps),
        plan_steps[0]["step"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    conn.commit()
    conn.close()
    
    return plan_steps


async def update_plan_progress(user_id, scholarship_id, new_step, progress_percent):
    """تحديث تقدم الخطة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE application_plans
    SET current_step = ?, progress = ?, updated_at = ?
    WHERE user_id = ? AND scholarship_id = ?
    """, (
        new_step,
        progress_percent,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_id,
        scholarship_id
    ))
    
    conn.commit()
    conn.close()


# ============================================
# 📊 ANALYTICS & REPORTING
# ============================================

def get_ai_analytics():
    """تحليلات استخدام الـ AI"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        recommendation_type,
        COUNT(*) as total,
        AVG(confidence_score) as avg_confidence,
        SUM(is_accepted) as accepted_count
    FROM ai_recommendations
    GROUP BY recommendation_type
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return results


# ============================================
# 🔘 UI HANDLERS
# ============================================

async def ai_analysis_menu(update, context):
    """قائمة التحليل الذكي"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 تحليل فرص القبول", callback_data="ai_acceptance")],
        [InlineKeyboardButton("📄 تحسين CV", callback_data="ai_cv")],
        [InlineKeyboardButton("✉️ كتابة خطاب تحفيز", callback_data="ai_motivation")],
        [InlineKeyboardButton("🎯 ترشيح منح ذكي", callback_data="ai_matching")],
        [InlineKeyboardButton("💡 نصائح مخصصة", callback_data="ai_tips")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "🤖 مركز التحليل الذكي بالـ AI\n\n"
        "اختر الخدمة المطلوبة:\n"
        "• تحليل دقيق لفرص قبولك\n"
        "• تحسين CV احترافي\n"
        "• كتابة خطابات تحفيزية\n"
        "• ترشيح منح مناسب\n"
        "• نصائح مخصصة لحالتك",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_ai_request(update, context):
    """معالجة طلبات AI"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # جلب بيانات المستخدم
    user_profile = get_user_profile(user_id)
    
    action = query.data.replace("ai_", "")
    
    await query.edit_message_text("🔄 جاري التحليل بالذكاء الاصطناعي...")
    
    recommendation = await get_ai_recommendation(user_profile, action)
    
    keyboard = [
        [InlineKeyboardButton("✅ مفيد", callback_data=f"rate_rec_1")],
        [InlineKeyboardButton("❌ غير مفيد", callback_data=f"rate_rec_0")]
    ]
    
    await query.edit_message_text(
        f"🤖 نتيجة التحليل:\n\n{recommendation}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def get_user_profile(user_id):
    """جلب ملف المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    profile = {
        "user_id": user_id,
        "score": "85",
        "major": "علوم حاسوب",
        "target_country": "ألمانيا",
        "english_level": "متوسط",
        "stage": "بكالوريوس"
    }
    
    if user_data:
        profile.update({
            "major": user_data[3] if len(user_data) > 3 else profile["major"],
            "target_country": user_data[4] if len(user_data) > 4 else profile["target_country"]
        })
    
    conn.close()
    return profile


# ============================================
# 📦 REGISTER
# ============================================

def register(application):
    """تسجيل ميزة AI Recommendations"""
    
    global GROQ_API_KEY
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    application.add_handler(
        CallbackQueryHandler(ai_analysis_menu, pattern="ai_analysis")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_ai_request, pattern="ai_")
    )
    
    logger.info("✅ AI Recommendations feature loaded")
