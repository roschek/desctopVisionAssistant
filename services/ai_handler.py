from typing import List, Optional, Union
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT, AUDIO_PROMPT


class GeminiWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, chat_session, content: Union[str, List[Union[str, Image.Image]]]) -> None:
        super().__init__()
        self.chat_session = chat_session
        self.content = content

    def run(self) -> None:
        try:
            # Send message to existing chat session
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
        self.system_instruction = SYSTEM_PROMPT
        self._init_model()

    def _init_model(self) -> None:
        if not GEMINI_API_KEY or "YOUR_API_KEY" in GEMINI_API_KEY:
            print("API Key missing!")
            return
            
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=self.system_instruction)
        self.reset_session()

    def reset_session(self) -> None:
        """Reset current chat session."""
        if hasattr(self, 'model'):
             self.chat_session = self.model.start_chat(history=[])
             print("Chat session reset.")

    def send_request(self, content: Union[str, List[Image.Image]]) -> None:
        """
        Universal method: accepts list of images (with default prompt) or text.
        """
        # Check worker state
        if self.worker:
            try:
                if self.worker.isRunning():
                    print("Gemini busy.")
                    return
            except RuntimeError:
                # If C++ object is gone but Python ref remains
                self.worker = None
            except Exception:
                self.worker = None

        self.processing_started.emit()

        final_content = content
        
        # If images provided, append a default "Solve this" prompt
        if isinstance(content, list) and content and isinstance(content[0], Image.Image):
            # Copy images
            imgs = [img.copy() for img in content]
            # Message: images + text
            final_content = imgs + ["Analyze these screenshots and provide a solution."]
        
        self.worker = GeminiWorker(self.chat_session, final_content)
        self.worker.finished_signal.connect(self._on_success)
        self.worker.error_signal.connect(self._on_error)
        # Clear Python reference before deleting C++ object
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def send_audio(self, wav_bytes: bytes, prompt: str) -> None:
        """
        Send audio (wav) + prompt.
        """
        if self.worker:
            try:
                if self.worker.isRunning():
                    print("Gemini busy.")
                    return
            except RuntimeError:
                self.worker = None
            except Exception:
                self.worker = None

        self.processing_started.emit()
       
        content = [
            {"mime_type": "audio/wav", "data": wav_bytes},
            prompt or AUDIO_PROMPT,
        ]

        self.worker = GeminiWorker(self.chat_session, content)
        self.worker.finished_signal.connect(self._on_success)
        self.worker.error_signal.connect(self._on_error)
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _cleanup_worker(self) -> None:
        """Clear worker reference after completion."""
        self.worker = None

    def _on_success(self, text: str) -> None:
        self.response_received.emit(text)

    def _on_error(self, error_msg: str) -> None:
        self.error_occurred.emit(error_msg)
