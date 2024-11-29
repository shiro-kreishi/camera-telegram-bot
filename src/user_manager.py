import sqlite3
import os

from dotenv import load_dotenv


class UserManager:
    def __init__(self, db_path: str, env_path: str):
        self.db_path = db_path
        self.env_path = env_path

        load_dotenv(self.env_path)
        root_user = os.getenv("TELEGRAM_ROOT_USER")

        if not root_user:
            raise ValueError("Переменная TELEGRAM_ROOT_USER не установлена!")

        self.root_user = int(root_user)

        # Инициализация базы данных
        self._initialize_db()

        # Добавляем root-пользователя
        self.add_user(self.root_user)

    def _initialize_db(self):
        """Инициализация базы данных и таблицы для пользователей."""
        if not os.path.exists(self.db_path):
            # Если база данных не существует, создаём её
            print(f"База данных {self.db_path} не найдена, создаём новую...")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL UNIQUE
                    )
                ''')
                conn.commit()
            print("Таблица 'users' успешно создана.")
        else:
            print(f"База данных {self.db_path} уже существует.")

    def is_user_allowed(self, user_id: int) -> bool:
        """Проверяет, есть ли пользователь в белом списке."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            return user is not None

    def add_user(self, user_id: int) -> bool:
        """Добавляет пользователя в белый список, если его там нет."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
                conn.commit()
                print(f"Пользователь с ID {user_id} добавлен в белый список.")
                return True
            except sqlite3.IntegrityError:
                print(f"Пользователь с ID {user_id} уже существует в базе.")
                return False  # Пользователь уже существует в базе

    def remove_user(self, user_id: int) -> bool:
        """Удаляет пользователя из белого списка."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Пользователь с ID {user_id} удалён из белого списка.")
            else:
                print(f"Пользователь с ID {user_id} не найден в белом списке.")
            return cursor.rowcount > 0  # Возвращаем True, если был удалён хотя бы один пользователь

    def list_users(self) -> list:
        """Возвращает список всех пользователей в белом списке."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            print("Список пользователей в белом списке:")
            return [user[0] for user in users]  # Возвращаем только IDs пользователей
