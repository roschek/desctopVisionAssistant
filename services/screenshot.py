from pathlib import Path
from typing import Tuple
import mss
import mss.tools
from PIL import Image
from config import DEBUG_SCREENSHOTS_DIR

class ScreenshotService:
    def __init__(self, output_dir: str = DEBUG_SCREENSHOTS_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def take_screenshot(self, filename: str = "debug_snap.png") -> Tuple[str, Image.Image]:
        """
        Захватывает основной экран.
        Возвращает: (путь_к_файлу, объект_PIL_Image)
        """
        file_path = self.output_dir / filename
        
        with mss.mss() as sct:
            # Захват первого монитора
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            # Сохранение на диск (для дебага)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(file_path))
            
            # Конвертация в PIL Image для работы в памяти
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            
        print(f"Screenshot saved: {file_path}")
        return str(file_path), img

