from .db import get_db
from hashlib import sha256
from datetime import datetime

def create_user(username, email, password):
    conn = get_db()
    cursor = conn.cursor()
    hashed = sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed))
        conn.commit()
        return True
    except:
        return False


def authenticate_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    hashed = sha256(password.encode()).hexdigest()
    user = cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed)).fetchone()
    return user


def add_income(user_id, description, amount, currency):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO incomes (user_id, description, amount, currency, created_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, description, amount, currency, datetime.now().isoformat()))
    conn.commit()


def add_expense(user_id, description, amount, currency):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (user_id, description, amount, currency, created_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, description, amount, currency, datetime.now().isoformat()))
    conn.commit()


def get_user_data(user_id, month=None):
    conn = get_db()
    cursor = conn.cursor()
    if month:
        incomes = cursor.execute("SELECT * FROM incomes WHERE user_id=? AND created_at LIKE ?", (user_id, f"{month}%")).fetchall()
        expenses = cursor.execute("SELECT * FROM expenses WHERE user_id=? AND created_at LIKE ?", (user_id, f"{month}%")).fetchall()
    else:
        incomes = cursor.execute("SELECT * FROM incomes WHERE user_id=?", (user_id,)).fetchall()
        expenses = cursor.execute("SELECT * FROM expenses WHERE user_id=?", (user_id,)).fetchall()
    return incomes, expenses

def get_user_by_id(user_id):
    conn = get_db()
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

def update_monthly_limit(user_id, new_limit):
    conn = get_db()
    conn.execute("UPDATE users SET monthly_limit = ? WHERE id = ?", (new_limit, user_id))
    conn.commit()

def get_total_expenses_for_month(user_id, month_str):
    conn = get_db()
    result = conn.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE user_id = ? AND created_at LIKE ?
    """, (user_id, f"{month_str}%")).fetchone()
    return result[0] if result and result[0] else 0
