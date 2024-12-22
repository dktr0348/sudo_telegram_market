import sqlite3

def delete_alembic_version():
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if cursor.fetchone():
            cursor.execute("DROP TABLE alembic_version")
            print("Таблица alembic_version успешно удалена")
        else:
            print("Таблица alembic_version не найдена")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при удалении таблицы: {e}")

if __name__ == "__main__":
    delete_alembic_version() 