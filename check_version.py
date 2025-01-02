import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    print(f"Current version: {version[0]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close() 