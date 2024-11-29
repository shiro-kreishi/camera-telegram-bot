from dotenv import load_dotenv
import os


class Config:
    def __init__(self, path: str):
        self.path = path
        self.telegram_token = None
        self.camera_ip_service = None
        self.camera_count_url = None
        self.camera_image_url = None

        self._url_protocol = 'http'
        self._get_camera_image_endpoint = 'image'
        self._get_camera_count_endpoint = 'cameras'

    def load(self):
        """Загружает все настройки из .env файла."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'Файл {self.path} не найден!')

        load_dotenv(self.path)

        # Загружаем токен телеграм бота
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.telegram_token:
            raise ValueError("Переменная TELEGRAM_TOKEN не найдена в .env файле!")

        # Загружаем настройки камеры
        self.camera_ip_service = os.getenv('CAMERA_IP_SERVICE')
        if not self.camera_ip_service:
            raise ValueError("Переменная CAMERA_IP_SERVICE не найдена в .env файле!")

        self.camera_image_url = f"{self._url_protocol}://{self.camera_ip_service}/{self._get_camera_image_endpoint}"
        self.camera_count_url = f"{self._url_protocol}://{self.camera_ip_service}/{self._get_camera_count_endpoint}"
