import google.generativeai as genai
from google.generativeai.types import safety_types

import os 

import logging
from flask import Flask, request, jsonify

from telegram import Bot, Update
from telegram.ext import CommandHandler, CallbackContext,MessageHandler,Dispatcher, Filters


# Ini)tialize Gemini-Pro
api_key = os.getenv("GOOGLE_GEMINI_KEY")
genai.configure(api_key=api_key)

bot_token=os.getenv("TELEGRAM_BOT_TOKEN")


app = Flask(__name__)


def start_callback(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="你好，我是你的 Bot！")


def text_callback(update: Update, context: CallbackContext):
    logging.info("執行 text_callback 函數")  # 這是新增的日誌語句
    context.bot.send_message(chat_id=update.effective_chat.id, text="你好")

# 初始化你的 bot 和 Dispatcher
bot = Bot(bot_token)
bot.set_webhook(url=f"https://telegram-bot-liart-nine.vercel.app/{bot_token}")

dispatcher = Dispatcher(bot, None, workers=1)

# 為你的 bot 添加處理函數
start_handler = CommandHandler('start', start_callback)  # 你需要定義 start_callback
dispatcher.add_handler(start_handler)

# 創建一個新的處理器來處理所有 text 信息
text_handler = MessageHandler(Filters.text, text_callback)
dispatcher.add_handler(text_handler)



@app.route(f"/{bot_token}", methods=['POST'])
def telegram_webhook():
    #建立一個 Update 物件，並使用進來的 JSON 進行填充
    update = Update.de_json(request.get_json(), bot)
    #使用 Dispatcher 物件來處理該 Update
    dispatcher.process_update(update)
    return '', 200  # success status





@app.route('/webhook_info', methods=['GET'])
def get_webhook_info():
    info = bot.getWebhookInfo()
    return jsonify({
      'URL': info.url, 
      'Has custom certificate': info.has_custom_certificate, 
      'Pending update count': info.pending_update_count, 
      'Last error date': info.last_error_date, 
      'Last error message': info.last_error_message
    })

@app.route("/test1", methods=['GET'])
def test1():
    return 'Test successful!', 200

@app.route('/', methods=['GET'])
def hello_world():
    app.logger.info('訊息：執行中...')
    return 'Hello, World!'

@app.route("/site-map")
def site_map():
    output = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods))
        output.append(f"{rule} ({methods})")
    return "<br>".join(sorted(output))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel
            






