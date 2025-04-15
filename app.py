
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import pandas as pd
import requests
import os
from io import StringIO
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Sheet CSV URL
CSV_URL = "https://docs.google.com/spreadsheets/d/1P6CscAxsxkqSPBiOP2s2X1-J5P_2YCNKKi4FOIM8zT0/gviz/tq?tqx=out:csv&gid=1348505043"

# 分頁狀態記憶（簡易測試用，可改為 Redis 或 DB）
user_sessions = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def format_page(results, page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    sliced = results[start:end]
    formatted = []

    for i, row in enumerate(sliced, start=start + 1):
        name = str(row.get("姓名", ""))
        company = str(row.get("公司", ""))
        phone = str(row.get("電話", "未提供"))
        email = str(row.get("E-MAIL", "未提供"))
        date = str(row.get("日期", ""))
        formatted.append(f"{i}. **{name}**\n- 公司：{company}\n- 日期：{date}\n- 電話：{phone}\n- Email：{email}\n")

    return "\n".join(formatted)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # 換頁請求
    if user_id in user_sessions and text.lower() in ["下一頁", "下一页", "more", "more >>"]:
        session = user_sessions[user_id]
        session["page"] += 1
        page = session["page"]
        page_size = session["page_size"]
        keyword = session["keyword"]
        results = session["results"]

        if (page - 1) * page_size >= len(results):
            reply = "已經是最後一頁了。"
        else:
            reply = f"🔎 關鍵字：{keyword}（第 {page} 頁）\n\n" + format_page(results, page, page_size)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 關鍵字查詢流程
    try:
        response = requests.get(CSV_URL)
        df = pd.read_csv(StringIO(response.text))
        matched = df[df.apply(lambda row: text in str(row.values), axis=1)]

        if matched.empty:
            reply_text = "查無資料，請嘗試其他關鍵字。"
        else:
            records = matched.to_dict("records")
            user_sessions[user_id] = {
                "keyword": text,
                "results": records,
                "page": 1,
                "page_size": 5
            }
            reply_text = f"🔎 關鍵字：{text}（第 1 頁）\n\n" + format_page(records, 1, 5)
            if len(records) > 5:
                reply_text += "\n\n👉 輸入「下一頁」以查看更多結果"

    except Exception as e:
        reply_text = f"處理時發生錯誤：{str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
