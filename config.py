import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла (должен лежать рядом с .exe или скриптом)
load_dotenv()

# API Configuration
# Лучше использовать переменные окружения, но оставляем фоллбэк для удобства
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCio66CuQS--sHweza2KOonERY8ZI48qyc")
GEMINI_MODEL = 'gemini-2.5-flash' # Можно менять на 'gemini-1.5-flash' или 'gemini-1.5-pro'

# Windows Display Affinity Constants
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011 # Скрывает окно от захвата (черный прямоугольник)

# Paths
DEBUG_SCREENSHOTS_DIR = "debug_screenshots"

