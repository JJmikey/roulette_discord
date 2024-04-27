import discord
import os


# 準備好用於通訊的 intents
intents = discord.Intents.default()
intents.messages = True  # 必須啟用消息 intents

# Initialize discord
client = discord.Client(intents=intents)

# 當機器人完成登錄準備並連接到Discord時，會觸發此事件
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

# 當接收到新消息時，會觸發此事件
@client.event
async def on_message(message):
    # 如果消息來自我們自己的機器人，則忽略
    if message.author == client.user:
        return

    # 如果消息內容是 'hello'，則回應 'Hello world'
    if message.content.lower() == 'hello':
        await message.channel.send('Hello World!')

# 從環境變數中讀取TOKEN並啟動機器人
client.run('DISCORD_BOT_TOKEN')