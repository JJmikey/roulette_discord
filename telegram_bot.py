import google.generativeai as genai
from google.generativeai.types import safety_types

import os 

from flask import Flask, request



from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext


# Initialize Gemini-Pro
api_key = os.getenv("GOOGLE_GEMINI_KEY")
genai.configure(api_key=api_key)

bot_token=os.getenv("TELEGRAM_BOT_TOKEN")


app = Flask(__name__)

def start_callback(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="你好，我是你的 Bot！")

# 初始化你的 bot 和 Dispatcher
bot = Bot(token=bot_token)
bot.set_webhook(url=f"https://telegram-bot-liart-nine.vercel.app/{bot_token}")

dispatcher = Dispatcher(bot, None, workers=1)

# 為你的 bot 添加處理函數
start_handler = CommandHandler('start', start_callback)  # 你需要定義 start_callback
dispatcher.add_handler(start_handler)

@app.route(f'/{bot_token}', methods=['POST'])
def telegram_webhook():
    update = Update.de_json(request.get_json(), bot)
    # process your telegram update
    return '', 200  # success status


@app.route('/test', methods=['GET'])
def test1():
    return 'Test successful!', 200

@app.route('/', methods=['GET'])
def test2():
    return 'Flask app is running!'


if __name__ == '__main__':
    app.run(port=5000, debug=True)






