import sqlite3

# Создание базы данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создание таблицы для хранения ссылок на профиль
cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER,
        profile_url TEXT,
        purchases INTEGER,
        join_date DATE
    )
''')
conn.commit()


