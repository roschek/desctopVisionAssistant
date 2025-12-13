import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Determine base directory (works for script and PyInstaller exe)
if getattr(sys, 'frozen', False):
    # Running as .exe (PyInstaller)
    base_dir = Path(sys.executable).parent
else:
    # Running as script
    base_dir = Path(__file__).parent

# Load variables from .env (should be next to exe or script)
env_path = base_dir / '.env'
load_dotenv(dotenv_path=env_path)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AUDIO_PROMPT = os.getenv("AUDIO_PROMPT")
if not GEMINI_API_KEY:
    print("WARNING: API Key not found in .env file!")
GEMINI_MODEL = 'gemini-2.5-flash'  # can switch to gemini-1.5-flash or gemini-1.5-pro
DEFAULT_SYSTEM_PROMPT = """
You are a concise desktop assistant. Analyze provided context (text, code, images) and respond briefly and clearly in Russian by default. If code or technical details are present, be accurate and practical. Keep outputs short and helpful.
"""
raw_prompt = os.getenv("CUSTOM_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
SYSTEM_PROMPT = raw_prompt.replace("\\n", "\n")
# Windows Display Affinity Constants
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Excludes window from screen capture (privacy feature)

# Paths
DEBUG_SCREENSHOTS_DIR = "debug_screenshots"

