import sqlite3

def main():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute("DROP DATABESE finance.db}")

    conn.close()