# ============================================
# 🤖 AI Assistant - Professional Groq Integration
# Clean, Safe, Structured Version
# ============================================

import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict
from groq import Groq


# ============================================
# ⚙️ Configuration
# ============================================

logger = logging.getLogger(__name__)

# ============================================
# 🚀 Groq AI Setup
# ============================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logger.warning("⚠️ GROQ_API_KEY not set — AI features will fail")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL_NAME = "llama3-8b-8192"
MAX_RETRIES = 2


# ============================================
# 🧠 Core AI Call Wrapper
# ============================================

async def _call_ai(prompt: str, max_tokens: int = 1500) -> str:
    """Safe Groq API wrapper with retries + error handling"""

    if not client:
        return "⚠️ لم يتم إعداد مفتاح الذكاء الاصطناعي بعد."

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"AI Error (attempt {attempt+1}): {e}")

    return "⚠️ حدث خطأ في خدمة الذكاء الاصطناعي. حاول لاحقاً."


# ============================================
# 🎯 AI Features
# ============================================

async def ai_analyze_profile(user_data: Dict) -> str:
    prompt = f"""أنت مستشار تعليمي خبير في المنح الدراسية.

التخصص: {user_data.get('major', 'غير محدد')}
الدولة المستهدفة: {user_data.get('target_country', 'غير محدد')}
المرحلة: {user_data.get('degree_level', 'غير محدد')}

المطلوب:
1- تحليل فرص القبول
2- أفضل 3 منح مناسبة
3- نصائح تحسين
4- خطة 6 شهور

أجب بالعربية."""

    return await _call_ai(prompt)


async def ai_review_motivation_letter(letter_text: str, scholarship_info: Dict) -> str:
    prompt = f"""أنت خبير في مراجعة رسائل الدافع.

المنحة: {scholarship_info.get('name', 'غير محدد')}
الدولة: {scholarship_info.get('country', 'غير محدد')}

النص:
{letter_text}

قيّم الرسالة من 10 وقدم تحسينات مفصلة بالعربية."""

    return await _call_ai(prompt, 2000)


async def ai_answer_question(question: str, context: Optional[Dict] = None) -> str:
    ctx = ""
    if context:
        ctx = f"التخصص: {context.get('major')}\nالدولة: {context.get('target_country')}"

    prompt = f"""أنت مستشار منح دراسية.

{ctx}

السؤال:
{question}

أجب بإجابة واضحة ومباشرة بالعربية."""

    return await _call_ai(prompt, 1000)


async def ai_compare_scholarships(s1: Dict, s2: Dict, profile: Dict) -> str:
    prompt = f"""قارن بين المنحتين:

المنحة 1: {s1}
المنحة 2: {s2}
ملف الطالب: {profile}

أعط مقارنة + توصية نهائية بالعربية."""

    return await _call_ai(prompt)


async def ai_generate_application_checklist(scholarship_info: Dict) -> str:
    prompt = f"""أنشئ checklist للتقديم على:

{scholarship_info}

رتبها حسب الأولوية بالعربية."""

    return await _call_ai(prompt)


async def ai_career_path_advice(major: str, country: str) -> str:
    prompt = f"""فرص العمل بعد دراسة {major} في {country}.

اشرح الرواتب والفرص ونصائح النجاح."""

    return await _call_ai(prompt)


async def ai_quick_tip(category: str) -> str:
    prompts = {
        "cv": "نصيحة قوية لتحسين السيرة الذاتية",
        "motivation": "نصيحة قوية لرسالة الدافع",
        "interview": "نصيحة لمقابلة المنح",
        "language": "نصيحة لاختبار IELTS",
        "deadline": "نصيحة لإدارة المواعيد",
    }

    prompt = prompts.get(category, "نصيحة للتقديم على المنح")
    return await _call_ai(prompt, 150)


# ============================================
# 💾 Conversation Storage
# ============================================

def save_ai_conversation(user_id: int, question: str, answer: str, feature: str):
    try:
        conn = sqlite3.connect("scholarship_bot.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question TEXT,
                answer TEXT,
                feature TEXT,
                timestamp TEXT
            )
        """
        )

        cursor.execute(
            "INSERT INTO ai_conversations VALUES (NULL,?,?,?,?,?)",
            (user_id, question, answer, feature, datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"DB Save Error: {e}")


# ============================================
# 📊 Usage Stats
# ============================================

def get_ai_usage_stats() -> Dict:
    try:
        conn = sqlite3.connect("scholarship_bot.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ai_conversations")
        total = cursor.fetchone()[0]

        conn.close()

        return {"total_queries": total}

    except:
        return {"total_queries": 0}
async def ai_smart_search_suggestions(*args, **kwargs):
    return "🔍 اقتراحات البحث الذكي قادمة قريبًا!"