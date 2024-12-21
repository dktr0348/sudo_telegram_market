import sqlite3

def check_db_structure():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\nСтруктура таблицы {table_name}:")
        
        # Получаем информацию о структуре таблицы
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for column in columns:
            print(f"Колонка: {column[1]}, Тип: {column[2]}, Nullable: {not column[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_db_structure() 