import sqlite3

conn = sqlite3.connect("skins.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE skins ADD COLUMN updated_at TEXT")
    conn.commit()
    print("✅ Column 'updated_at' added")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ Column 'updated_at' already exists")
    else:
        print(f"❌ Error: {e}")
finally:
    conn.close()