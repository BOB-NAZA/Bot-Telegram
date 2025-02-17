import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message TEXT
        )
        """)
        self.conn.commit()

    def save_post(self, chat_id, message):
        self.cursor.execute("INSERT INTO posts (chat_id, message) VALUES (?, ?)", (chat_id, message))
        self.conn.commit()

    def get_last_post(self):
        self.cursor.execute("SELECT chat_id, message FROM posts ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        return {"chat_id": row[0], "message": row[1]} if row else None
