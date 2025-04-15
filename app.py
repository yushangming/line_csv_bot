
from flask import Flask, request, abort, render_template, redirect, url_for, session, send_from_directory
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

# 初始化
load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Sheet 設定
CSV_URL = "https://docs.google.com/spreadsheets/d/1P6CscAxsxkqSPBiOP2s2X1-J5P_2YCNKKi4FOIM8zT0/gviz/tq?tqx=out:csv&gid=1348505043"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logs")
def logs():
    log_files = read_log_list()
    return render_template("logs.html", log_files=log_files)

@app.route("/logs/<date>")
def log_detail(date):
    logs = read_log_by_date(date)
    return render_template("log_detail.html", logs=logs, date=date)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if check_login(username, password):
            session["admin"] = True
            return redirect("/admin/logs")
    return render_template("admin.html")

@app.route("/admin/logs")
def admin_logs():
    if not session.get("admin"):
        return redirect("/admin")
    log_files = read_log_list()
    return render_template("admin_logs.html", log_files=log_files)

@app.route("/admin/logs/<filename>")
def admin_log_file(filename):
    if not session.get("admin"):
        return redirect("/admin")
    date = filename.replace("qa_log_", "").replace(".txt", "")
    logs = read_log_by_date(date)
    return render_template("log_detail.html", logs=logs, date=date)

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
def handle_line_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.strip()

    try:
        df = pd.read_csv(StringIO(requests.get(CSV_URL).text))
        matched = df[df.apply(lambda row: user_msg in str(row.values), axis=1)]

        if matched.empty:
            reply = "查無資料，請嘗試其他關鍵字。"
        else:
            results = matched.head(5).to_dict("records")
            reply = ""
            for r in results:
                reply += f"{r.get('日期','')}: {r.get('公司','')} - {r.get('姓名','')}\\n"

        # 寫入日誌
        write_log(
            source="LINE",
            question=user_msg,
            answer=reply,
            ip=None
        )

    except Exception as e:
        reply = f"錯誤：{e}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/ask", methods=["POST"])
def ask_web():
    user_msg = request.form.get("question")
    user_ip = request.remote_addr

    try:
        df = pd.read_csv(StringIO(requests.get(CSV_URL).text))
        matched = df[df.apply(lambda row: user_msg in str(row.values), axis=1)]

        if matched.empty:
            answer = "查無資料，請嘗試其他關鍵字。"
        else:
            results = matched.head(5).to_dict("records")
            answer = ""
            for r in results:
                answer += f"{r.get('日期','')}: {r.get('公司','')} - {r.get('姓名','')}\\n"

        write_log("WEB", user_msg, answer, user_ip)

    except Exception as e:
        answer = f"錯誤：{e}"

    return render_template("index.html", question=user_msg, answer=answer)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
