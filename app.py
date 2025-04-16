from flask import Flask, request, abort, render_template, redirect, url_for, session
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
from dotenv import load_dotenv

from utils.auth import check_login
from utils.logger import write_log, read_log_list, read_log_by_date

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

CSV_URL = "https://docs.google.com/spreadsheets/d/1P6CscAxsxkqSPBiOP2s2X1-J5P_2YCNKKi4FOIM8zT0/gviz/tq?tqx=out:csv&gid=1348505043"

user_sessions = {}

def format_response(results):
    reply = []
    for r in results:
        reply.append(
            f"{r.get('日期','')}"
            f"\n公司：{r.get('公司','')}"
            f"\n姓名：{r.get('姓名','')}"
            f"\n電話：{r.get('電話','未提供')}"
            f"\nEmail：{r.get('E-MAIL','未提供')}"
            f"\n問題：{r.get('問題','')}"
            f"\n處理：{r.get('處理','')}"
            f"\n--------------------"
        )
    return "\n".join(reply)

@app.route("/")
def index():
    return render_template("index.html", title="查詢首頁")

@app.route("/ask", methods=["POST"])
def ask_web():
    user_msg = request.form.get("question")
    user_ip = request.remote_addr
    try:
        df = pd.read_csv(StringIO(requests.get(CSV_URL).text))
        df = df.iloc[::-1]
        matched = df[df.apply(lambda row: user_msg in str(row.values), axis=1)]
        if matched.empty:
            answer = "查無資料，請嘗試其他關鍵字。 提示:非模糊比對, 輸入查詢文字必須100%符合, 包含大小寫。"
        else:
            results = matched.to_dict("records")
            answer = format_response(results)
        write_log("WEB", user_msg, answer, user_ip)
    except Exception as e:
        answer = f"錯誤：{e}"
    return render_template("index.html", question=user_msg, answer=answer, title="查詢結果")

@app.route("/logs")
def logs():
    return render_template("logs.html", log_files=read_log_list(), title="查詢紀錄")

@app.route("/logs/<date>")
def log_detail(date):
    return render_template("log_detail.html", logs=read_log_by_date(date), date=date, title=f"{date} 詳細紀錄")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if check_login(username, password):
            session["admin"] = True
            return redirect("/admin/logs")
    return render_template("admin.html", title="管理登入")

@app.route("/admin/logs")
def admin_logs():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("admin_logs.html", log_files=read_log_list(), title="管理紀錄")

@app.route("/admin/logs/<filename>")
def admin_log_file(filename):
    if not session.get("admin"):
        return redirect("/admin")
    date = filename.replace("qa_log_", "").replace(".txt", "")
    return render_template("log_detail.html", logs=read_log_by_date(date), date=date, title=f"{date} 詳細紀錄")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_line_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.strip()
    try:
        if user_msg.lower() in ["more", "下一頁", "more >>"]:
            if user_id not in user_sessions:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("尚未查詢資料，請先輸入關鍵字。"))
                return
            session = user_sessions[user_id]
            page = session["page"] + 1
            session["page"] = page
            results = session["results"]
            sliced = results[(page-1)*3:page*3]
            if not sliced:
                reply = "已經是最後一頁。"
            else:
                reply = format_response(sliced)
                if page * 3 < len(results):
                    reply += "\n👉 輸入「下一頁」繼續查看"
        else:
            df = pd.read_csv(StringIO(requests.get(CSV_URL).text))
            df = df.iloc[::-1]
            matched = df[df.apply(lambda row: user_msg in str(row.values), axis=1)]
            if matched.empty:
                reply = "查無資料，請嘗試其他關鍵字。 提示:非模糊比對, 輸入查詢文字必須100%符合, 包含大小寫。"
            else:
                results = matched.to_dict("records")
                user_sessions[user_id] = {"results": results, "page": 1}
                reply = format_response(results[:3])
                if len(results) > 3:
                    reply += "\n👉 輸入「下一頁」繼續查看"
        write_log("LINE", user_msg, reply, None)
    except Exception as e:
        reply = f"錯誤：{e}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
