import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config
from user_manager import UserManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ImageBot:
    def __init__(self, token: str, api_base_url: str, user_manager: UserManager):
        self.token = token
        self.api_base_url = api_base_url
        self.user_manager = user_manager
        self.cameras = {}
        self.app = ApplicationBuilder().token(self.token).build()
        logger.info("Бот успешно инициализирован.")

    def fetch_cameras(self) -> None:
        """Получает список камер с API и сохраняет их в self.cameras."""
        try:
            response = requests.get(f"{self.api_base_url}/cameras")
            if response.status_code == 200:
                cameras_data = response.json()
                self.cameras = {idx: camera for idx, camera in enumerate(cameras_data)}
                logger.info(f"Получено {len(self.cameras)} камер.")
            else:
                logger.error(f"Не удалось получить список камер {response.url}. Код ошибки: {response.status_code}")
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
        keyboard = [[camera["name"]] for camera in self.cameras.values()]
        keyboard.append(["Показать справку"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите камеру:", reply_markup=reply_markup)

    async def send_image(self, update: Update, camera_id: int) -> None:
        """Отправляет изображение с указанной камеры."""
        camera = self.cameras.get(camera_id)
        if not camera:
            await update.message.reply_text("Указанная камера не найдена.")
            return

        try:
            response = requests.get(f"{self.api_base_url}/image/{camera_id}")
            if response.status_code == 200:
                await update.message.reply_photo(photo=response.content)
                logger.info(f"Отправлено изображение с камеры {camera['name']}.")
            else:
                logger.error(f"Ошибка получения изображения с камеры {camera['name']}: код {response.status_code}")
                await update.message.reply_text(f"Не удалось получить изображение с камеры {camera['name']}.")
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе изображения с камеры {camera_id}: {e}")
            await update.message.reply_text(f"Ошибка при получении изображения: {e}")

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет справку для пользователя."""
        user_id = update.message.from_user.id
        if self.user_manager.is_user_allowed(user_id):
            # Для root пользователя показываем полную справку
            help_text = """
            Полная справка для администратора:
            - /start - Стартовая команда.
            - Камера [номер] - Получить изображение с камеры.
            - Показать справку - Получить справку от бота.
            - /add_user [user_id] - Добавить пользователя в белый список.
            - /remove_user [user_id] - Удалить пользователя из белого списка.
            - /list_user - Список пользователей в белом списке.
            """
        else:
            # Для обычного пользователя только базовая справка
            help_text = """
            Справка для пользователя:
            - /start - Стартовая команда.
            - Камера [номер] - Получить изображение с камеры.
            - Показать справку - Получить справку от бота.
            """
        await update.message.reply_text(help_text)

    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Добавление пользователя в белый список."""
        admin_id = os.getenv("TELEGRAM_ROOT_USER")
        if update.effective_user.id != int(admin_id):
            logger.warning(f"Пользователь {update.effective_user.id} попытался использовать команду без прав.")
            await update.message.reply_text("У вас нет прав для добавления пользователей.")
            return

        if context.args:
            user_id = int(context.args[0])
            if not self.user_manager.add_user(user_id):
                await update.message.reply_text(f"Пользователь {user_id} уже в белом списке.")
            else:
                await update.message.reply_text(f"Пользователь {user_id} добавлен в белый список.")
                logger.info(f"Пользователь {user_id} добавлен в белый список.")
        else:
            await update.message.reply_text("Укажите ID пользователя для добавления.")

    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Удаление пользователя из белого списка."""
        admin_id = os.getenv("TELEGRAM_ROOT_USER")
        if update.effective_user.id != int(admin_id):
            logger.warning(f"Пользователь {update.effective_user.id} попытался использовать команду без прав.")
            await update.message.reply_text("У вас нет прав для удаления пользователей.")
            return

        if context.args:
            user_id = int(context.args[0])
            if not self.user_manager.remove_user(user_id):
                await update.message.reply_text(f"Пользователь {user_id} не найден в белом списке.")
            else:
                await update.message.reply_text(f"Пользователь {user_id} удален из белого списка.")
                logger.info(f"Пользователь {user_id} удален из белого списка.")
        else:
            await update.message.reply_text("Укажите ID пользователя для удаления.")

    async def list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отображение всех пользователей в белом списке."""
        users = self.user_manager.list_users()
        if users:
            await update.message.reply_text("Белый список пользователей:\n" + "\n".join(str(user) for user in users))
        else:
            await update.message.reply_text("Белый список пуст.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает текстовые сообщения от пользователя."""
        user_id = update.effective_user.id
        user_name = update.effective_user.username

        if not self.user_manager.is_user_allowed(user_id):
            logger.warning(f"Пользователь {user_name} (ID: {user_id}) попытался отправить сообщение.")
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return

        text = update.message.text
        logger.info(f"Получено сообщение от {user_name} (ID: {user_id}): {text}")

        for camera_id, camera in self.cameras.items():
            if text == camera["name"]:
                await self.send_image(update, camera_id)
                return

        if text == "Показать справку":
            await self.show_help(update, context)
        else:
            logger.warning(f"Неизвестная команда от пользователя {user_name} (ID: {user_id}): {text}")
            await update.message.reply_text("Неизвестная команда. Попробуйте ещё раз.")

    def run(self):
        """Регистрация обработчиков и запуск бота."""
        self.fetch_cameras()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("add_user", self.add_user))
        self.app.add_handler(CommandHandler("remove_user", self.remove_user))
        self.app.add_handler(CommandHandler("list_user", self.list_users))
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
        api_base_url = f'http://{config.camera_ip_service}'

        logger.info("Инициализация CameraImageBot с параметрами из Config.")
        super().__init__(token, api_base_url, user_manager)
