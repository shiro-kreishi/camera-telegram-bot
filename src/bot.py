import os

import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from src.config import Config


class ImageBot:
    def __init__(self, token: str, camera_count_url: str, camera_image_url: str):
        """
        :param token: Токен Telegram бота
        :param camera_count_url: URL для получения списка камер
        :param camera_image_url: URL для получения изображений с камер
        """
        self.token = token
        self.camera_count_url = camera_count_url
        self.camera_image_url = camera_image_url
        self.cameras = {}  # Словарь для хранения списка камер
        self.app = ApplicationBuilder().token(self.token).build()

    def fetch_cameras(self) -> None:
        """Получает список камер с API и сохраняет их в self.cameras."""
        try:
            response = requests.get(self.camera_count_url)
            if response.status_code == 200:
                self.cameras = {idx: camera["index"] for idx, camera in enumerate(response.json())}
            else:
                print("Не удалось получить список камер.")
        except requests.RequestException as e:
            print(f"Ошибка при запросе списка камер: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /start и отправляет клавиатуру с кнопками камер."""
        keyboard = [[f"Камера {name}"] for name in self.cameras.values()]
        keyboard.append(["Отправить текст"])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    async def send_image(self, update: Update, camera_id: int) -> None:
        """Отправляет изображение с указанной камеры."""
        try:
            response = requests.get(f'{self.camera_image_url}/{camera_id}')
            print(f'{self.camera_image_url}/{camera_id}')
            if response.status_code == 200:
                await update.message.reply_photo(photo=response.content)
            else:
                await update.message.reply_text(f"Не удалось получить изображение с камеры {camera_id}.")
        except requests.RequestException as e:
            await update.message.reply_text(f"Ошибка при получении изображения с камеры {camera_id}: {e}")

    async def send_text(self, update: Update) -> None:
        """Отправляет текстовое сообщение."""
        await update.message.reply_text("Это пример текстового сообщения от бота!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает текстовые сообщения от пользователя."""
        text = update.message.text
        for camera_id, camera_name in self.cameras.items():
            if text == f"Камера {camera_name}":
                await self.send_image(update, camera_id)
                return

        if text == "Отправить текст":
            await self.send_text(update)
        else:
            await update.message.reply_text("Неизвестная команда. Попробуйте ещё раз.")

    def run(self):
        """Регистрация обработчиков и запуск бота."""
        self.fetch_cameras()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.run_polling()


class CameraImageBot(ImageBot):
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        print(dotenv_path)
        config = Config(dotenv_path)
        config.load()

        print(config.telegram_token)  # Должен вывести ваш токен
        print(config.camera_count_url)  # http://192.168.88.219:8001/cameras/
        print(config.camera_image_url)  # http://192.168.88.219:8001/images/

        # Используем корректные значения из Config
        token = config.telegram_token
        camera_count_url = config.camera_count_url
        camera_image_url = config.camera_image_url

        # Передаем их в родительский класс
        super().__init__(token, camera_count_url, camera_image_url)
