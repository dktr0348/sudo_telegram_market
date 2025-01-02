import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    # Получаем информацию о структуре таблицы
    cursor.execute("PRAGMA table_info(stars_transactions)")
    columns = cursor.fetchall()
    print("Структура таблицы stars_transactions:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    conn.close() 