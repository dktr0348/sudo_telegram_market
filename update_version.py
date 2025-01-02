import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    # Проверяем текущую версию
    cursor.execute("SELECT version_num FROM alembic_version")
    current_version = cursor.fetchone()[0]
    print(f"Current version: {current_version}")
    
    # Обновляем на последнюю версию из истории
    cursor.execute("UPDATE alembic_version SET version_num = '7d9e2ba74a46'")
    conn.commit()
    print("Version updated to: 7d9e2ba74a46")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close() 