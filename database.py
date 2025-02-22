import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER,
        profile_url TEXT,
        purchases INTEGER DEFAULT 0,
        join_date DATE
    )
''')
conn.commit()


