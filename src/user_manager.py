import sqlite3
import os
from dotenv import load_dotenv

class UserManager:
    def __init__(self, db_path: str, env_path: str):
        self.db_path = db_path
        self.env_path = env_path

        # Загрузка переменных окружения
        load_dotenv(self.env_path)
        root_user = os.getenv("TELEGRAM_ROOT_USER")

        if not root_user:
            raise ValueError("Переменная TELEGRAM_ROOT_USER не установлена!")

        self.root_user = int(root_user)

        # Инициализация базы данных
        self.setup_db()
        self.add_user(self.root_user)  # Добавляем root-пользователя

    def setup_db(self):
        """Создает таблицу пользователей, если она еще не существует."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS allowed_users (
                id INTEGER PRIMARY KEY
            )
        ''')
        conn.commit()
        conn.close()

    def add_user(self, user_id: int):
        """Добавляет пользователя в список разрешенных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO allowed_users (id) VALUES (?)", (user_id,))
            conn.commit()
        finally:
            conn.close()

    def is_user_allowed(self, user_id: int) -> bool:
        """Проверяет, есть ли пользователь в списке разрешенных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM allowed_users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def load_allowed_users(self) -> list[int]:
        """Загружает всех разрешенных пользователей."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM allowed_users")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
