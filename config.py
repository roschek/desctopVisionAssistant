import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Определяем путь к директории, где находится config.py
# Это работает и для скрипта, и для .exe файла
if getattr(sys, 'frozen', False):
    # Если запущено как .exe (PyInstaller)
    base_dir = Path(sys.executable).parent
else:
    # Если запущено как скрипт
    base_dir = Path(__file__).parent

# Загружаем переменные из .env файла (должен лежать рядом с .exe или скриптом)
env_path = base_dir / '.env'
load_dotenv(dotenv_path=env_path)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: API Key not found in .env file!")
GEMINI_MODEL = 'gemini-2.5-flash' # Можно менять на 'gemini-1.5-flash' или 'gemini-1.5-pro'
DEFAULT_SYSTEM_PROMPT = """
You are an intelligent Desktop Assistant designed to improve developer productivity.
Your goal is to analyze the visual context (UI mockups, code snippets, errors) and provide instant technical assistance.

ROLE: Senior Frontend Engineer (React, TypeScript, Tailwind).

INSTRUCTIONS:
1. If the user provides a UI screenshot -> Generate clean, component-based React code (JSX/TSX).
2. If the user provides a code snippet -> Detect bugs, explain logic, or suggest refactoring.
3. If the user provides text -> Answer concisely and technically.
4. Language: Russian (unless context demands English).
Keep answers production-ready and concise.
"""
raw_prompt = os.getenv("CUSTOM_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
SYSTEM_PROMPT = raw_prompt.replace("\\n", "\n")
# Windows Display Affinity Constants
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011 # Excludes window from screen capture (privacy feature)

# Paths
DEBUG_SCREENSHOTS_DIR = "debug_screenshots"

