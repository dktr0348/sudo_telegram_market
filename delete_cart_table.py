import sqlite3

def delete_cart_table():
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cart'")
        if cursor.fetchone():
            cursor.execute("DROP TABLE cart")
            print("Таблица cart успешно удалена")
        else:
            print("Таблица cart не найдена")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при удалении таблицы: {e}")

if __name__ == "__main__":
    delete_cart_table() 