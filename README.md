# LINE + Google Sheet 查詢機器人 (支援 GPT-4o-mini)

這是一個整合 LINE Messaging API、Google 試算表查詢與 OpenAI GPT-4o-mini 回覆強化的聊天機器人專案，可部署至 [Render](https://render.com) 並透過 GitHub 自動佈署。

## 📦 專案架構

```
.
├── app_gpt.py          # 主程式（使用 .env 與 GPT 回答美化）
├── .env.example        # 環境變數範本（Render 可透過設定管理）
├── requirements.txt    # Python 套件清單
├── render.yaml         # Render 雲端部署設定
├── .gitignore          # Git 忽略設定
└── README.md           # 說明文件
```

## 🚀 部署步驟

### 1. 建立 GitHub Repo

```bash
git init
git remote add origin https://github.com/你的帳號/你的Repo.git
```

### 2. 加入檔案並推送

```bash
git add .
git commit -m "initial commit"
git push -u origin master
```

### 3. Render 連接 GitHub 自動部署

1. 登入 [https://render.com](https://render.com)
2. 點選 **New Web Service** → **Connect account**
3. 授權 GitHub 帳號，選擇此 repo
4. 設定：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app_gpt:app`
   - Python version: 3.10+
   - Environment: `Add Environment Variables` 將 `.env` 中變數加入

---

## 🧪 本地測試

```bash
cp .env.example .env
python app_gpt.py
```

然後使用 [ngrok](https://ngrok.com) 或 [localtunnel](https://theboroer.github.io/localtunnel-www/) 測試 Webhook。

---

## 🔐 設定環境變數（Render 上）

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `OPENAI_API_KEY`