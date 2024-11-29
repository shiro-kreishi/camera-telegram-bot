from dotenv import load_dotenv
import os
from bot import ImageBot, CameraImageBot


if __name__ == '__main__':
    bot = CameraImageBot()
    bot.run()
