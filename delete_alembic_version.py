import sqlite3

def delete_alembic_version():
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # Удаляем таблицу alembic_version если она существует
        cursor.execute("DROP TABLE IF EXISTS alembic_version")
        
        # Создаем новую таблицу alembic_version
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL
        )
        """)
        
        conn.commit()
        print("Successfully reset alembic version")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    delete_alembic_version() 