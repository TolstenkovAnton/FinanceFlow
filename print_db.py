import sqlite3
from tabulate import tabulate

def print_table(cursor, table_name):
    print(f"\n--- {table_name.upper()} ---")
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    if rows:
        headers = [description[0] for description in cursor.description]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("Нет записей.")

def main():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    for table in ["users", "incomes", "expenses"]:
        print_table(cursor, table)

    conn.close()

if __name__ == "__main__":
    main()
