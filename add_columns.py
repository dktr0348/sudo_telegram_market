import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    # Проверяем существующие колонки
    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    print("Существующие колонки:", columns)
    
    # Добавляем stars_amount если его нет
    if 'stars_amount' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN stars_amount INTEGER")
        print("Добавлена колонка stars_amount")
    
    # Добавляем payment_status если его нет
    if 'payment_status' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50)")
        print("Добавлена колонка payment_status")
    
    conn.commit()
    print("\nОбновленная структура таблицы orders:")
    cursor.execute("PRAGMA table_info(orders)")
    for col in cursor.fetchall():
        print(f"- {col[1]} ({col[2]})")
        
except Exception as e:
    print(f"Ошибка: {e}")
    conn.rollback()
finally:
    conn.close() 