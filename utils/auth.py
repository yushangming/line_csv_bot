
import os
from datetime import datetime, timedelta

login_attempts = {}
lockouts = {}

MAX_ATTEMPTS = 5
LOCKOUT_TIME_MINUTES = 10

def is_locked(username):
    now = datetime.now()
    if username in lockouts and now < lockouts[username]:
        return True
    return False

def check_login(username, password):
    now = datetime.now()

    if is_locked(username):
        return False

    if username not in login_attempts:
        login_attempts[username] = []

    login_attempts[username] = [ts for ts in login_attempts[username] if now - ts < timedelta(minutes=10)]

    if password == os.getenv("ADMIN_PASSWORD", "Password") and username == os.getenv("ADMIN_USERNAME", "Admin"):
        login_attempts[username] = []
        return True
    else:
        login_attempts[username].append(now)
        if len(login_attempts[username]) >= MAX_ATTEMPTS:
            lockouts[username] = now + timedelta(minutes=LOCKOUT_TIME_MINUTES)
        return False
