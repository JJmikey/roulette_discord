import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import os 

import logging
from flask import Flask, request, jsonify

from telegram import Bot, Update
from telegram.ext import CommandHandler, CallbackContext,MessageHandler,Dispatcher, Filters


# Ini)tialize Gemini-Pro
api_key = os.getenv("GOOGLE_GEMINI_KEY")
genai.configure(api_key=api_key)

def generate_response(input_text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(
        input_text,
        safety_settings={
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH:HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=['||'],
            max_output_tokens=4000,
            temperature=0.6,
        )
    )
    # 尝试从响应对象中提取文本内容
   
    if hasattr(response, 'parts'):
        # 如果回答包含多个部分，则遍历所有部分
        for part in response.parts:
                response_text = part.text
                return response_text
    else:
        #如果回答只有一个简单的文本部分, 直接打印response.text
        return response_text

     


bot_token=os.getenv("TELEGRAM_BOT_TOKEN")


app = Flask(__name__)

# 將 chat_history 初始化為字典
chat_history = {}

def start_callback(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="你好，我是你的 Bot！")


def text_callback(update: Update, context: CallbackContext):
    logging.info("執行 text_callback 函數")  # 這是新增的日誌語句
    # 獲取用户的消息和chat_id
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # 將用户的消息添加到聊天历史记录
    if chat_id not in chat_history:
        chat_history[chat_id] = []
   

    # 僅將對話歷史中的 'role' 和 'parts' 結合
    chat_history[chat_id] = "".join(f"{msg['role']}:{msg['parts']}" for msg in chat_history[chat_id]if "user" in msg)
    chat_history[chat_id].append({'role': 'user', 'parts': user_text})
    full_input = f" {chat_history[chat_id]}"

    # 使用 GEMINI 生成器創建回應
    response = generate_response(full_input)

    # 在聊天历史记录中添加机器人的回应
    chat_history[chat_id].append({"bot": response})

    # 將生成的回應傳給用戶
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

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
            






