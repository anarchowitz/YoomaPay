import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER,
        profile_url TEXT,
        purchases INTEGER DEFAULT 0,
        join_date DATE,
        promocode TEXT
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS promocodes (
        id INTEGER PRIMARY KEY,
        code TEXT,
        discount INTEGER,
        expiration_date DATE,
        used INTEGER DEFAULT 0,
        max_uses INTEGER,
        telegram_id_used_promo TEXT
    )
''')
conn.commit()

