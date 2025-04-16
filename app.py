#（略過 import 與 app 初始化部分）...

def format_response(results):
    reply = []
    for r in results:
        reply.append(
            f"{r.get('日期','')}"
            f"\n公司：{r.get('公司','')}"
            f"\n姓名：{r.get('姓名','')}"
            f"\n電話：{r.get('電話','未提供')}"
            f"\nEmail：{r.get('E-MAIL','未提供')}"
            f"\n--------------------"
        )
    return "\n".join(reply)

@handler.add(MessageEvent, message=TextMessage)
def handle_line_message(event):
    user_msg = event.message.text.strip()

    try:
        df = pd.read_csv(StringIO(requests.get(CSV_URL).text))
        matched = df[df.apply(lambda row: user_msg in str(row.values), axis=1)]

        if matched.empty:
            reply = "查無資料，請嘗試其他關鍵字。"
        else:
            results = matched.to_dict("records")
            reply = format_response(results)

        write_log("LINE", user_msg, reply, None)

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
            results = matched.to_dict("records")
            answer = format_response(results)

        write_log("WEB", user_msg, answer, user_ip)

    except Exception as e:
        answer = f"錯誤：{e}"

    return render_template("index.html", question=user_msg, answer=answer)