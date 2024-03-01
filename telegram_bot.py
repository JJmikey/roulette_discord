import google.generativeai as genai
from google.generativeai.types import safety_types

import os 




from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Initialize Gemini-Pro
api_key = os.getenv("GOOGLE_GEMINI_KEY")
genai.configure(api_key=api_key)

bot_token=os.getenv("TELEGRAM_BOT_TOKEN")
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="我是你的 Bot，很高興見到你！")

updater = Updater(token=bot_token, use_context=True)

dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()