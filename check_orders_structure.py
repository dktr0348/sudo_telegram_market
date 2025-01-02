import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    # Получаем информацию о структуре таблицы orders
    cursor.execute("PRAGMA table_info(orders)")
    columns = cursor.fetchall()
    print("Структура таблицы orders:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    conn.close() 