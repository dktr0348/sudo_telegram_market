import sqlite3

def check_tables():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    try:
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nСписок таблиц в базе данных:")
        for table in tables:
            print(f"\n📋 Таблица: {table[0]}")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
    
    except Exception as e:
        print(f"Ошибка при проверке таблиц: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables() 