"""
Инициализация базы данных
Запуск: python init_db.py
"""
import sqlite3
from datetime import datetime

def init_database():
    conn = None
    try:
        conn = sqlite3.connect("skins.db")
        cursor = conn.cursor()
        
        print(f"[{datetime.now()}] Инициализация базы данных...")
        
        # Удаляем старую таблицу, если существует
        cursor.execute("DROP TABLE IF EXISTS skins")
        
        # Создаем новую таблицу с правильной структурой
        cursor.execute("""
            CREATE TABLE skins (
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                deposit_price REAL,
                withdraw_price REAL,
                have INTEGER,
                max INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (name, source)
            )
        """)
        
        # Создаем индексы для ускорения запросов
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON skins(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON skins(name)")
        
        conn.commit()
        print(f"[{datetime.now()}] База данных успешно инициализирована")
        
    except sqlite3.Error as e:
        print(f"[ОШИБКА] Ошибка инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_database()