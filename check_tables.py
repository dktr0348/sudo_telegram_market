import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    # Проверяем структуру order_items
    print("\nСтруктура order_items:")
    cursor.execute("PRAGMA table_info(order_items)")
    print(cursor.fetchall())
    
    # Проверяем структуру orders
    print("\nСтруктура orders:")
    cursor.execute("PRAGMA table_info(orders)")
    print(cursor.fetchall())
    
    # Проверяем структуру stars_transactions
    print("\nСтруктура stars_transactions:")
    cursor.execute("PRAGMA table_info(stars_transactions)")
    print(cursor.fetchall())

except Exception as e:
    print(f"Ошибка: {e}")
finally:
    conn.close() 