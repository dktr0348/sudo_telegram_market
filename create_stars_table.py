import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stars_transactions (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        stars_amount INTEGER NOT NULL,
        amount_rub REAL NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)
    
    # Добавляем колонки в таблицу orders если их нет
    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'stars_amount' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN stars_amount INTEGER")
    if 'payment_status' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50)")
    
    conn.commit()
    print("Таблица stars_transactions создана успешно")
    
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    conn.close() 