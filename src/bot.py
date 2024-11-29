import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from src.config import Config
from src.user_manager import UserManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class NoGetUpdatesFilter(logging.Filter):
    """Фильтр для исключения логов 'getUpdates'."""
    def filter(self, record: logging.LogRecord) -> bool:
        return 'getUpdates' not in record.getMessage()

# Применяем фильтр ко всем логгерам
for handler in logging.getLogger().handlers:
    handler.addFilter(NoGetUpdatesFilter())


class ImageBot:
    def __init__(self, token: str, camera_count_url: str, camera_image_url: str, user_manager: UserManager):
        self.token = token
        self.camera_count_url = camera_count_url
        self.camera_image_url = camera_image_url
        self.user_manager = user_manager
        self.cameras = {}
        self.app = ApplicationBuilder().token(self.token).build()
        logger.info("Бот успешно инициализирован.")

    def fetch_cameras(self) -> None:
        """Получает список камер с API и сохраняет их в self.cameras."""
        try:
            response = requests.get(self.camera_count_url)
            if response.status_code == 200:
                self.cameras = {idx: camera["index"] for idx, camera in enumerate(response.json())}
                logger.info(f"Получено {len(self.cameras)} камер.")
            else:
                logger.error(f"Не удалось получить список камер. Код ошибки: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе списка камер: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /start и проверяет доступ пользователя."""
        user_id = update.effective_user.id
        user_name = update.effective_user.username

        if not self.user_manager.is_user_allowed(user_id):
            logger.warning(f"Пользователь {user_name} (ID: {user_id}) попытался получить доступ.")
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return

        logger.info(f"Пользователь {user_name} (ID: {user_id}) начал сессию.")
        keyboard = [[f"Камера {name}"] for name in self.cameras.values()]
        keyboard.append(["Отправить текст"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    async def send_image(self, update: Update, camera_id: int) -> None:
        """Отправляет изображение с указанной камеры."""
        try:
            response = requests.get(f'{self.camera_image_url}/{camera_id}')
            logger.info(f"Запрос изображения с камеры {camera_id} по URL: {self.camera_image_url}/{camera_id}")
            if response.status_code == 200:
                await update.message.reply_photo(photo=response.content)
                logger.info(f"Успешно отправлено изображение с камеры {camera_id}.")
            else:
                logger.error(f"Ошибка получения изображения с камеры {camera_id}: код {response.status_code}")
                await update.message.reply_text(f"Не удалось получить изображение с камеры {camera_id}.")
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении изображения с камеры {camera_id}: {e}")
            await update.message.reply_text(f"Ошибка при получении изображения с камеры {camera_id}: {e}")

    async def send_text(self, update: Update) -> None:
        """Отправляет текстовое сообщение."""
        await update.message.reply_text("Это пример текстового сообщения от бота!")
        logger.info("Отправлено текстовое сообщение пользователю.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает текстовые сообщения от пользователя и проверяет доступ."""
        user_id = update.effective_user.id
        user_name = update.effective_user.username

        if not self.user_manager.is_user_allowed(user_id):
            logger.warning(f"Пользователь {user_name} (ID: {user_id}) попытался использовать неизвестную команду.")
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return

        text = update.message.text
        logger.info(f"Получено сообщение от {user_name} (ID: {user_id}): {text}")

        for camera_id, camera_name in self.cameras.items():
            if text == f"Камера {camera_name}":
                await self.send_image(update, camera_id)
                return

        if text == "Отправить текст":
            await self.send_text(update)
        else:
            logger.warning(f"Неизвестная команда от пользователя {user_name} (ID: {user_id}): {text}")
            await update.message.reply_text("Неизвестная команда. Попробуйте ещё раз.")

    def run(self):
        """Регистрация обработчиков и запуск бота."""
        self.fetch_cameras()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        logger.info("Бот запущен и готов к работе.")
        self.app.run_polling()


class CameraImageBot(ImageBot):
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        config = Config(dotenv_path)
        config.load()

        user_manager = UserManager(db_path="users.db", env_path=dotenv_path)

        token = config.telegram_token
        camera_count_url = config.camera_count_url
        camera_image_url = config.camera_image_url

        logger.info("Инициализация CameraImageBot с параметрами из Config.")
        super().__init__(token, camera_count_url, camera_image_url, user_manager)
