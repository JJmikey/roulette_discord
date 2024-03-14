import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


import os 
import requests

import logging
from flask import Flask, request, jsonify

from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext,CallbackQueryHandler, MessageHandler,Dispatcher, Filters

from PIL import Image
import base64
from io import BytesIO

# Initialize Gemini-Pro
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

def generate_img_response(photo_bytes_io, prompt_text):    
    # 先將 BytesIO 對象轉換成圖片
    photo_image = Image.open(photo_bytes_io)

    model = genai.GenerativeModel('gemini-pro-vision')

    # 將圖片轉換為 base64 編碼
    buffered = BytesIO()
    photo_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')  # 轉化為 base64 字串

    photo_blob = {'mime_type': 'image/png', 'data': img_str}  # 修改為正確的鍵和資料格式

    # 現在 photo_blob 和 prompt_text 都是一個適當的格式，可以被模型處理
    response = model.generate_content({"prompt": prompt_text, "blob": photo_blob})

    #response = model.generate_content(["Write a short, engaging blog post based on this picture.", photo_bytes_io], stream=True)

    # 尝试从响应对象中提取文本内容    
    return response.text


bot_token=os.getenv("TELEGRAM_BOT_TOKEN")


app = Flask(__name__)





# 將 chat_history 初始化為字典
chat_history = {}



def start_callback(update: Update, context: CallbackContext):
    # 創建你的按鈕
    button_list = [
        [InlineKeyboardButton("要", callback_data='yes'),InlineKeyboardButton("不要", callback_data='no')], 
        [InlineKeyboardButton("👍🏽", callback_data='good')]
    ]
    # 創建你的鍵盤並將按鈕添加到鍵盤上
    reply_markup = InlineKeyboardMarkup(button_list)
    # 發送消息並將你的鍵盤作為響應使用
    context.bot.send_message(chat_id=update.effective_chat.id, text='要總結嗎?', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    # 獲取按鈕的回調數據
    query = update.callback_query
    query.answer()

    # Get chat_id from the query message
    chat_id = query.message.chat.id

    # 在添加任何新的聊天記錄之前，確保 chat_history 中已有 chat_id 鍵值
    if chat_id not in chat_history:
        chat_history[chat_id] = []

    # execute a GET request
    response = requests.get("http://todo4coze.vercel.app/task")  # here you need to replace with your API URL
    data = response.json()   # convert the response to JSON format

    

    # now you can check the returned data and replace 'message' with the correct key
    # 例如假設你的 API 回覆了一條訊息在 'message' 鍵中，你可以這樣操作：
    msg = str(data)  # 將 json 數據轉換為易讀的字符串

    # 將数据添加到聊天历史记录（context）中
    chat_history[chat_id].append({"role": "system", "parts": msg})
    # 在對話歷史中添加用戶消息
    chat_history[chat_id].append({'role': 'user', 'parts': 'show tasks in a readable way.Translate to zh-繁體中文.'})
    # 僅將對話歷史中的 'role' 和 'parts' 結合
    input_context = "".join(f"{msg['role']}:{msg['parts']}" for msg in chat_history[chat_id])
    # 使用 GEMINI 生成器創建回應
    response = generate_response(input_context)
    # 在聊天历史记录中添加机器人的回应
    chat_history[chat_id].append({"role": "bot", "parts": response})

    query.edit_message_text(text="你按了：{}，API 回覆了：{}".format(query.data, response))



    # 你可以在這裡使用 ID 進行判斷然後調用你想要的函數
    #query.edit_message_text(text="你按了：{}".format(query.data))


def text_callback(update: Update, context: CallbackContext):
   
    logging.info("執行 text_callback 函數")  # 這是新增的日誌語句
    # 獲取用户的消息和chat_id
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # 將用户的消息添加到聊天历史记录
    if chat_id not in chat_history:
        chat_history[chat_id] = []
   
    # 在對話歷史中添加用戶消息
    chat_history[chat_id].append({'role': 'user', 'parts': user_text})

    # 僅將對話歷史中的 'role' 和 'parts' 結合
    input_context = "".join(f"{msg['role']}:{msg['parts']}" for msg in chat_history[chat_id])


    # 使用 GEMINI 生成器創建回應
    response = generate_response(input_context)

    # 在聊天历史记录中添加机器人的回应
    chat_history[chat_id].append({"role": "bot", "parts": response})  
    
 

    # 將生成的回應傳給用戶
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def photo_callback(update: Update, context: CallbackContext):
    # 獲取用戶發送的照片列表（PhotoSize 對象）
    photos = update.message.photo

    # 獲取照片的標題文字，如果有的話
    prompt_text = update.message.caption if update.message.caption else "請提供一個提示文本。"
    
    # 通常，照片列表中最後一張是解析度最高的版本
    # 獲取最後一張照片的 file_id
    photo_id = photos[-1].file_id
    
    # 使用 getFile 方法獲得 PhotoSize 對象
    photo_file = context.bot.get_file(photo_id)
    
    # 下載照片作為一個字節流 (BytesIO 對象)
    photo_bytes_io = BytesIO(photo_file.download_as_bytearray())
    
    # 現在可以處理下載的照片 'photo.jpg'，或者將 file_path 傳遞給下一個功能來進一步處理

    # 反饋信息給用戶
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_bytes_io, caption='您的圖片')

    # 重設游標位置，如果要再次讀取 BytesIO 對象
    photo_bytes_io.seek(0)    
       
    # 使用 GEMINI 生成器創建回應
    response = generate_img_response(photo_bytes_io, prompt_text)

    # 處理完成後，清理內存
    photo_bytes_io.close() 

    # 如果沒有收到提示文本，通知用戶
    if not prompt_text:
        response = "請重新發送圖片並添加有效的提示文本。"

    # 最後，向用戶反饋處理完成的訊息
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def set_webhook(update: Update, context: CallbackContext):
    bot.set_webhook(url=f"https://telegram-bot-liart-nine.vercel.app/{bot_token}")




# 初始化你的 bot 和 Dispatcher
bot = Bot(bot_token)
dispatcher = Dispatcher(bot, None, workers=1)



# 為你的 bot 添加處理函數
start_handler = CommandHandler('start', start_callback)  # 你需要定義 start_callback
dispatcher.add_handler(start_handler)
dispatcher.add_handler(CallbackQueryHandler(button))

# 將 'set_webhook' 命令對應到 set_webhook function
dispatcher.add_handler(CommandHandler('set_webhook', set_webhook)) #手動觸發設定更新的 command。輸入 "/set_webhook"



# 創建一個新的處理器來處理所有 text 信息
text_handler = MessageHandler(Filters.text, text_callback)
dispatcher.add_handler(text_handler)


# 創建一個新的處理器來處理有照片的消息
photo_handler = MessageHandler(Filters.photo, photo_callback)
dispatcher.add_handler(photo_handler)


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
            






