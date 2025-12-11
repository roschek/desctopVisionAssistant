from typing import List, Optional, Union
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

class GeminiWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, chat_session, content: Union[str, List[Union[str, Image.Image]]]) -> None:
        super().__init__()
        self.chat_session = chat_session
        self.content = content

    def run(self) -> None:
        try:
            # Отправка сообщения в существующую сессию чата
            response = self.chat_session.send_message(self.content)
            self.finished_signal.emit(response.text)
        except Exception as e:
            self.error_signal.emit(str(e))

class GeminiHandler(QObject):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    processing_started = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.worker: Optional[GeminiWorker] = None
        self.chat_session = None
        self.system_instruction = (
            "Ты помощник на техническом собеседовании. Твоя цель — помогать кандидату незаметно и быстро. "
            "1. Отвечай строго на **Русском языке**.\n"
            "2. Код пиши в блоках ```python (или другой язык) ... ```.\n"
            "3. Используй Clean Code, современные паттерны, типизацию.\n"
            "4. Если прислали картинку — решай задачу. Если текст — отвечай на вопрос по контексту."
        )
        self._init_model()

    def _init_model(self) -> None:
        if not GEMINI_API_KEY or "YOUR_API_KEY" in GEMINI_API_KEY:
            print("API Key missing!")
            return
            
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=self.system_instruction)
        self.reset_session()

    def reset_session(self) -> None:
        """Сбрасывает текущую сессию чата."""
        if hasattr(self, 'model'):
             self.chat_session = self.model.start_chat(history=[])
             print("Chat session reset.")

    def send_request(self, content: Union[str, List[Image.Image]]) -> None:
        """
        Универсальный метод: принимает или список картинок (с дефолтным промптом), или текст.
        """
        # Проверка на то, что воркер существует и работает
        if self.worker:
            try:
                if self.worker.isRunning():
                    print("Gemini busy.")
                    return
            except RuntimeError:
                # Если объект C++ уже удален, но ссылка в Python осталась
                self.worker = None
            except Exception:
                self.worker = None

        self.processing_started.emit()

        final_content = content
        
        # Если пришли картинки, добавляем к ним промпт "Реши это"
        if isinstance(content, list) and content and isinstance(content[0], Image.Image):
            # Копируем картинки
            imgs = [img.copy() for img in content]
            # Формируем сообщение: Картинки + текст
            final_content = imgs + ["Проанализируй эти скриншоты и дай решение."]
        
        self.worker = GeminiWorker(self.chat_session, final_content)
        self.worker.finished_signal.connect(self._on_success)
        self.worker.error_signal.connect(self._on_error)
        # Сначала очищаем ссылку в Python, потом удаляем объект в C++
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _cleanup_worker(self) -> None:
        """Очищает ссылку на воркер после завершения."""
        self.worker = None

    def _on_success(self, text: str) -> None:
        self.response_received.emit(text)

    def _on_error(self, error_msg: str) -> None:
        self.error_occurred.emit(error_msg)
