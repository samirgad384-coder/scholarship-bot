from telegram.ext import CommandHandler, CallbackQueryHandler


async def my_feature(update, context):
    await update.message.reply_text("الميزة شغالة ✅")


def register(application):
    application.add_handler(
        CommandHandler("myfeature", my_feature)
    )
