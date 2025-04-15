
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import pandas as pd
import requests
import openai
import os
from io import StringIO
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

app = Flask(__name__)

# 環境變數設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# Google Sheet CSV URL
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

        if matched.empty:
            reply_text = "查無資料，請嘗試其他關鍵字。"
        else:
            extracted = []
            for _, row in matched.head(5).iterrows():
                data = {
                    "日期": str(row.get("日期", "")),
                    "公司": str(row.get("公司", "")),
                    "姓名": str(row.get("姓名", "")),
                    "電話": str(row.get("電話", "")),
                    "Email": str(row.get("E-MAIL", ""))
                }
                extracted.append(data)

            gpt_prompt = f"使用者查詢關鍵字：「{keyword}」，請根據以下聯絡紀錄摘要並美化回覆給使用者：\n"
            for d in extracted:
                gpt_prompt += f"- {d['日期']}，{d['公司']}，{d['姓名']}，{d['電話']}，Email：{d['Email']}\n"

            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一個客服助理，會根據聯絡紀錄精簡並格式化回答"},
                    {"role": "user", "content": gpt_prompt}
                ]
            )
            reply_text = completion.choices[0].message.content.strip()

    except Exception as e:
        reply_text = f"處理時發生錯誤：{str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
