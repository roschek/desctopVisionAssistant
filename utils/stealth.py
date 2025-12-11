import sys
import ctypes
from ctypes import wintypes
from config import WDA_EXCLUDEFROMCAPTURE

# Константы для Click-Through
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20  # Окно пропускает клики

def apply_stealth_mode(hwnd: int) -> None:
    """
    Применяет режим 'невидимки' (WDA_EXCLUDEFROMCAPTURE).
    """
    if sys.platform != "win32":
        return

    try:
        user32 = ctypes.windll.user32
        user32.SetWindowDisplayAffinity(wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE)
    except Exception as e:
        print(f"Error applying stealth mode: {e}")

def set_click_through(hwnd: int, enable: bool) -> None:
    """
    Включает или выключает режим 'сквозного клика'.
    Если enable=True, мышь будет проходить сквозь окно.
    """
    if sys.platform != "win32":
        return

    try:
        user32 = ctypes.windll.user32
        # Получаем текущие расширенные стили окна
        style = user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE)
        
        if enable:
            # Добавляем флаг прозрачности для мыши
            new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            print("Click-through ENABLED")
        else:
            # Убираем флаг
            new_style = style & ~WS_EX_TRANSPARENT
            print("Click-through DISABLED")
            
        user32.SetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE, new_style)
        
    except Exception as e:
        print(f"Error toggling click-through: {e}")
