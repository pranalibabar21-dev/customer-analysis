import sqlite3

conn = sqlite3.connect("users.db")

cursor = conn.cursor()

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    '''
)

cursor.execute(
    "INSERT INTO users(username, password, role) VALUES(?, ?, ?)",
    ("admin", "admin123", "admin")
)

conn.commit()

print("Admin user created successfully")