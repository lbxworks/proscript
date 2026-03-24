import sqlite3
import os

# 获取当前 init_db.py 所在的真实目录路径 (即 data 文件夹)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 设定数据库文件名为 app.db，放在 data 文件夹下
DB_PATH = os.path.join(CURRENT_DIR, 'app.db')

def init_db():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users (Creator Profiles) table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            style_prompt TEXT NOT NULL, 
            few_shot TEXT               
        )
    ''')

    # 2. Scripts (Generated Shooting Scripts) table — aligned with GraphState
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic TEXT NOT NULL,
            platform TEXT,
            duration TEXT,
            creativity REAL,
            language TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def migrate_db():
    """Add new columns to existing scripts table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(scripts)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    new_columns = {
        "platform": "TEXT",
        "duration": "TEXT",
        "creativity": "REAL",
        "language": "TEXT",
    }

    for col_name, col_type in new_columns.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE scripts ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ Added column: {col_name} ({col_type})")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    migrate_db()