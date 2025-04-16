import os

def check_login(username, password):
    return (
        username == os.getenv("ADMIN_USERNAME", "Admin") and
        password == os.getenv("ADMIN_PASSWORD", "Password")
)
