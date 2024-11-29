from dotenv import load_dotenv
import os
from bot import ImageBot, CameraImageBot

if __name__ == '__main__':
    # dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    # if not os.path.exists(dotenv_path):
    #     print('No .env file found. Creating .env')
    #     exit(1)
    # load_dotenv(dotenv_path)
    # token = os.getenv('TELEGRAM_BOT_TOKEN')
    #
    # bot = ImageBot(token=token, ip_address='192.168.88.219:8001', cameras_url='http://192.168.88.219:8001/cameras')
    # bot.run()
    bot = CameraImageBot()
    bot.run()


