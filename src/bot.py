import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from src.config import Config

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Логи будут выводиться в консоль
        logging.FileHandler('bot.log', encoding='utf-8')  # Запись логов в файл
    ]
)
logger = logging.getLogger(__name__)

class ImageBot:
    def __init__(self, token: str, camera_count_url: str, camera_image_url: str):
        self.token = token
        self.camera_count_url = camera_count_url
        self.camera_image_url = camera_image_url
        self.cameras = {}  # Словарь для хранения списка камер
        self.app = ApplicationBuilder().token(self.token).build()
        logger.info("Бот инициализирован с токеном и URL-адресами.")

    def fetch_cameras(self) -> None:
        """Получает список камер с API и сохраняет их в self.cameras."""
        try:
            response = requests.get(self.camera_count_url)
            if response.status_code == 200:
                self.cameras = {idx: camera["index"] for idx, camera in enumerate(response.json())}
                logger.info(f"Получен список камер: {self.cameras}")
            else:
                logger.error(f"Не удалось получить список камер. Код ответа: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе списка камер: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /start и отправляет клавиатуру с кнопками камер."""
        keyboard = [[f"Камера {name}"] for name in self.cameras.values()]
        keyboard.append(["Отправить текст"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        logger.info("Отправлена клавиатура с выбором камер.")
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    async def send_image(self, update: Update, camera_id: int) -> None:
        """Отправляет изображение с указанной камеры."""
        try:
            response = requests.get(f'{self.camera_image_url}/{camera_id}')
            logger.info(f"Запрос изображения с камеры {camera_id}: {self.camera_image_url}/{camera_id}")
            if response.status_code == 200:
                await update.message.reply_photo(photo=response.content)
                logger.info(f"Изображение с камеры {camera_id} отправлено.")
            else:
                await update.message.reply_text(f"Не удалось получить изображение с камеры {camera_id}.")
                logger.error(f"Ошибка при запросе изображения с камеры {camera_id}. Код ответа: {response.status_code}")
        except requests.RequestException as e:
            await update.message.reply_text(f"Ошибка при получении изображения с камеры {camera_id}: {e}")
            logger.error(f"Ошибка при запросе изображения с камеры {camera_id}: {e}")

    async def send_text(self, update: Update) -> None:
        """Отправляет текстовое сообщение."""
        logger.info("Отправка текстового сообщения.")
        await update.message.reply_text("Это пример текстового сообщения от бота!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает текстовые сообщения от пользователя."""
        text = update.message.text
        logger.info(f"Получено сообщение: {text}")
        for camera_id, camera_name in self.cameras.items():
            if text == f"Камера {camera_name}":
                await self.send_image(update, camera_id)
                return

        if text == "Отправить текст":
            await self.send_text(update)
        else:
            await update.message.reply_text("Неизвестная команда. Попробуйте ещё раз.")
            logger.warning(f"Неизвестная команда: {text}")

    def run(self):
        """Регистрация обработчиков и запуск бота."""
        self.fetch_cameras()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        logger.info("Бот запущен.")
        self.app.run_polling()

class CameraImageBot(ImageBot):
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        logger.info(f"Загрузка конфигурации из {dotenv_path}")
        config = Config(dotenv_path)
        config.load()

        logger.info(f"Токен Telegram: {config.telegram_token}")
        logger.info(f"URL для получения списка камер: {config.camera_count_url}")
        logger.info(f"URL для получения изображений: {config.camera_image_url}")

        token = config.telegram_token
        camera_count_url = config.camera_count_url
        camera_image_url = config.camera_image_url

        super().__init__(token, camera_count_url, camera_image_url)
