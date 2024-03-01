import google.generativeai as genai
from google.generativeai.types import safety_types

import os 

from flask import Flask, request



from telegram import Bot
from telegram.ext import Updater, CommandHandler
from telegram.ext import Dispatcher

# Initialize Gemini-Pro
api_key = os.getenv("GOOGLE_GEMINI_KEY")
genai.configure(api_key=api_key)

bot_token=os.getenv("TELEGRAM_BOT_TOKEN")

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="我是你的 Bot，很高興見到你！")

app = Flask(__name__)
bot = Bot(token=bot_token)
dispatcher = Dispatcher(bot, None, workers=1)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

@app.route(f'/{bot_token}', methods=['POST'])
def index():
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return ''

@app.route('/', methods=['GET'])
def test():
    return 'Flask app is running!'


if __name__ == '__main__':
    app.run(port=5000)






