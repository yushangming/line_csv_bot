
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import pandas as pd
import requests
from io import StringIO

app = Flask(__name__)

# LINE 機器人金鑰
LINE_CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
LINE_CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Sheet 連結（CSV 格式）
CSV_URL = "https://docs.google.com/spreadsheets/d/1P6CscAxsxkqSPBiOP2s2X1-J5P_2YCNKKi4FOIM8zT0/gviz/tq?tqx=out:csv&gid=1348505043"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    keyword = event.message.text.strip()
    try:
        response = requests.get(CSV_URL)
        df = pd.read_csv(StringIO(response.text))

        matched = df[df.apply(lambda row: keyword in str(row.values), axis=1)]

        if not matched.empty:
            results = []
            for _, row in matched.iterrows():
                name = str(row.get("姓名", ""))
                company = str(row.get("公司", ""))
                phone = str(row.get("電話", ""))
                email = str(row.get("E-MAIL", ""))
                date_val = str(row.get("日期", ""))
                result = f"{date_val}\n公司：{company}\n姓名：{name}\n電話：{phone}\nEmail：{email}"
                results.append(result)

            reply_text = "\n---\n".join(results[:5])  # 最多5筆
        else:
            reply_text = "查無資料，請嘗試其他關鍵字。"

    except Exception as e:
        reply_text = f"處理時發生錯誤：{str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
