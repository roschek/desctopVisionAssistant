import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyListener(QObject):
    add_to_stack_signal = pyqtSignal()
    analyze_stack_signal = pyqtSignal()
    clear_buffer_signal = pyqtSignal()
    toggle_click_through_signal = pyqtSignal() # Ctrl+Alt+Z

    def __init__(self) -> None:
        super().__init__()
        self._is_active = False

    def start(self) -> None:
        try:
            keyboard.add_hotkey("ctrl+alt+s", lambda: self.add_to_stack_signal.emit())
            keyboard.add_hotkey("ctrl+alt+space", lambda: self.analyze_stack_signal.emit())
            keyboard.add_hotkey("ctrl+alt+x", lambda: self.clear_buffer_signal.emit())
            keyboard.add_hotkey("ctrl+alt+z", lambda: self.toggle_click_through_signal.emit())
            
            self._is_active = True
            print("Hotkeys: S=Add, Space=Analyze, X=Clear, Z=OverlayMode")
        except Exception as e:
            print(f"Failed to bind hotkeys: {e}")

    def stop(self) -> None:
        if self._is_active:
            keyboard.unhook_all()
            self._is_active = False
