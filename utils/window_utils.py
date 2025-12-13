import sys
import ctypes
from ctypes import wintypes
from config import WDA_EXCLUDEFROMCAPTURE

# Click-Through constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20  # Window becomes click-through

def apply_window_privacy(hwnd: int) -> None:
    """
    Apply privacy mode (WDA_EXCLUDEFROMCAPTURE).
    Window is excluded from screen capture by other apps.
    """
    if sys.platform != "win32":
        return

    try:
        user32 = ctypes.windll.user32
        user32.SetWindowDisplayAffinity(wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE)
    except Exception as e:
        print(f"Error applying window privacy: {e}")

def set_click_through(hwnd: int, enable: bool) -> None:
    """
    Enable or disable click-through mode.
    If enable=True, mouse clicks pass through the window.
    """
    if sys.platform != "win32":
        return

    try:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE)
        
        if enable:
            new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            print("Click-through ENABLED")
        else:
            new_style = style & ~WS_EX_TRANSPARENT
            print("Click-through DISABLED")
            
        user32.SetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE, new_style)
        
    except Exception as e:
        print(f"Error toggling click-through: {e}")

