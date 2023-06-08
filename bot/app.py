import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import configparser
import mysql.connector
from datetime import datetime
import os


app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))




@app.route("/", methods=['GET','POST'])
def callback():
    if request.method == 'GET':
        return 'ok'
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# linebot處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # linebot回傳訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='收到您的訊息囉!'))

    # 將文字資訊紀錄至資料庫
    conn = mysql.connector.connect(
        host=config.get('line-bot', 'host'),  # 連線主機名稱  
        user=config.get('line-bot', 'user'),  # 登入帳號
        password=config.get('line-bot', 'passwd'),
        database=config.get('line-bot', 'database'),
        port=3306)
    
    cursor = conn.cursor()
    query = 'INSERT INTO linebot.msg (time, msg) VALUES (%s, %s)'
    value = (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event.message.text)
    cursor.execute(query, value)
    conn.commit()
    conn.close()
# linebot處理照片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # 使用者傳送的照片
    message_content = line_bot_api.get_message_content(event.message.id)

    # 照片儲存名稱
    fileName = event.message.id + '.jpg'


    folder_name = 'image'

    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)

    # 儲存照片
    with open('./image/' + fileName, 'wb')as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # linebot回傳訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='收到您上傳的照片囉!'))

    # 將照片路徑資訊紀錄至資料庫
    conn = mysql.connector.connect(
        host=config.get('line-bot', 'host'),  # 連線主機名稱  
        user=config.get('line-bot', 'user'),  # 登入帳號
        password=config.get('line-bot', 'passwd'),
        database=config.get('line-bot', 'database'),
        port=3306)  
    cursor = conn.cursor()
    query = 'INSERT INTO linebot.upload_fig (time, file_path) VALUES (%s, %s)'
    value = (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fileName)
    cursor.execute(query, value)
    conn.commit()
    conn.close()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000,debug=True)
