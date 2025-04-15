
import os
from datetime import datetime

LOG_DIR = "logs"

def write_log(source, question, answer, ip=None):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    now = datetime.now()
    filename = f"{LOG_DIR}/qa_log_{now.strftime('%Y-%m-%d')}.txt"
    timestamp = now.strftime("%Y/%m/%d %p %I:%M:%S")
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"來源: {source} {'| IP: ' + ip if ip else ''}\n")
        f.write(f"時間: {timestamp}\n")
        f.write(f"Q: {question}\n\nA: {answer}\n")
        f.write("-" * 40 + "\n")

def read_log_list():
    if not os.path.exists(LOG_DIR):
        return []
    files = sorted(os.listdir(LOG_DIR))
    return [f for f in files if f.endswith(".txt")]

def read_log_by_date(date):
    path = f"{LOG_DIR}/qa_log_{date}.txt"
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    entries = raw.strip().split("-" * 40 + "\n")
    return [e.strip() for e in entries if e.strip()]
