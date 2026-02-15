from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters


# ============================================
# ⚙️ إعدادات الجروب
# ============================================

GROUP_LINK = "https://t.me/+sqpOtr5zsathM2Vk"
GROUP_USERNAME = None  # لو الجروب public حط @username
SUPPORT_USERNAME = "@ENG_GAD"  # حساب الدعم


# ============================================
# 👥 صفحة المجتمع الرئيسية
# ============================================

async def show_community(update, context):
    query = update.callback_query
    await query.answer()

    text = """
👥 مجتمع الطلاب العالمي

🚀 هنا تقدر:

• تسأل عن أي منحة
• تتواصل مع طلاب قدموا قبلك
• تبادل خبرات التقديم
• دعم ومساعدة فورية
• مشاركة فرص دراسية
• مناقشة التخصصات

⚠️ قوانين الجروب:
✓ احترام الجميع
✓ ممنوع السبام
✓ ممنوع الإعلانات
✓ التزم بموضوع الدراسة

انضم الآن 👇
"""

    keyboard = [
        [InlineKeyboardButton("🚀 دخول الجروب", url=GROUP_LINK)],
        [InlineKeyboardButton("📩 تواصل مع الدعم", url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("📊 عدد الأعضاء", callback_data="group_stats")],
        [InlineKeyboardButton("✉️ ارسل رسالة للمجتمع", callback_data="send_to_group")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="back_to_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================
# 📊 عدد أعضاء الجروب
# ============================================

async def group_stats(update, context):
    query = update.callback_query
    await query.answer()

    if not GROUP_USERNAME:
        await query.answer("⚠️ لا يمكن جلب الإحصائيات للجروب الخاص", show_alert=True)
        return

    try:
        count = await context.bot.get_chat_member_count(GROUP_USERNAME)
        await query.answer(f"👥 عدد الأعضاء: {count}", show_alert=True)
    except:
        await query.answer("❌ لا يمكن جلب البيانات الآن", show_alert=True)


# ============================================
# ✉️ إرسال رسالة للجروب (اقتراح / سؤال)
# ============================================

async def ask_send_to_group(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["send_group_mode"] = True

    await query.edit_message_text(
        "✉️ اكتب رسالتك للمجتمع الآن:\n\nسيتم إرسالها للإدارة للمراجعة."
    )


async def handle_group_message(update, context):
    if not context.user_data.get("send_group_mode"):
        return

    context.user_data["send_group_mode"] = False

    msg = update.message.text
    user = update.effective_user

    # هنا تقدر تبعتها للأدمن أو قناة خاصة
    print(f"رسالة من {user.id}: {msg}")

    await update.message.reply_text(
        "✅ تم إرسال رسالتك للمراجعة.\nشكراً لمساهمتك ❤️"
    )


# ============================================
# 📦 تسجيل handlers
# ============================================

def register(application):
    application.add_handler(
        CallbackQueryHandler(show_community, pattern="community")
    )

    application.add_handler(
        CallbackQueryHandler(group_stats, pattern="group_stats")
    )

    application.add_handler(
        CallbackQueryHandler(ask_send_to_group, pattern="send_to_group")
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message)
    )
