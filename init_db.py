import sqlite3

def init():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        monthly_limit REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        description TEXT,
        amount REAL,
        currency DEFAULT 'RUB',
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        description TEXT,
        amount REAL,
        currency DEFAULT 'RUB',
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init()
