import sys
import os
import time
from typing import List, Optional
from PIL import Image

from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QWidget, QTextEdit, QHBoxLayout, QLineEdit)
from PyQt6.QtCore import Qt, QEvent

from services.screenshot import ScreenshotService
from services.hotkeys import HotkeyListener
from services.ai_handler import GeminiHandler
from services.audio_service import AudioService
from utils.window_utils import apply_window_privacy, set_click_through

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.image_buffer: List[Image.Image] = []
        self.click_through_enabled = False  # State flag
        
        self.screenshot_service = ScreenshotService()
        self.hotkey_listener = HotkeyListener()
        self.gemini_handler = GeminiHandler()
        self.audio_service = AudioService()
        self.audio_service.ensure_recorder_running()
        
        self._connect_signals()
        self._setup_window_properties()
        self._setup_ui()
        self._enable_privacy_mode()
        
        self.hotkey_listener.start()

    def _connect_signals(self) -> None:
        self.hotkey_listener.add_to_stack_signal.connect(self.handle_add_to_stack)
        self.hotkey_listener.analyze_stack_signal.connect(self.handle_analyze_stack)
        self.hotkey_listener.clear_buffer_signal.connect(self.handle_clear_buffer)
        self.hotkey_listener.toggle_click_through_signal.connect(self.handle_toggle_click_through)
        self.hotkey_listener.save_audio_signal.connect(self.handle_save_audio)
        
        self.gemini_handler.response_received.connect(self.display_solution)
        self.gemini_handler.error_occurred.connect(self.display_error)
        self.gemini_handler.processing_started.connect(self.show_loading)

    def _setup_window_properties(self) -> None:
        self.setWindowTitle("Code Assistant")
        self.resize(1000, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.85)
        self.setStyleSheet("background-color: #1e1e1e;")

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        self.buffer_badge = QLabel("Buffered: 0")
        self._update_buffer_badge()
        header_layout.addWidget(self.buffer_badge)
        layout.addLayout(header_layout)

        # Content Area
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.content_area.setPlaceholderText(
            "Ctrl+Alt+S: Add Screenshot\n"
            "Ctrl+Alt+Space: Analyze All\n"
            "Ctrl+Alt+A: Send Last Audio\n"
            "Ctrl+Alt+Z: Toggle Click-Through"
        )
        self.content_area.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.content_area)
        
        # Chat Input
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a follow-up question... (Enter to send)")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                color: white;
                border: 1px solid #007acc;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        self.chat_input.returnPressed.connect(self.handle_chat_send)
        layout.addWidget(self.chat_input)
        
        # Footer
        hint_text = (
            "Ctrl+Alt+S: Add Screen | Ctrl+Alt+Space: Solve | "
            "Ctrl+Alt+A: Send Audio | Ctrl+Alt+X: Reset | "
            "Ctrl+Alt+Z: Overlay | Esc: Close"
        )
        hint_label = QLabel(hint_text)
        hint_label.setStyleSheet("color: #666666; font-size: 11px; font-weight: bold;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

    def _enable_privacy_mode(self) -> None:
        try:
            hwnd = int(self.winId())
            apply_window_privacy(hwnd)
        except Exception as e:
            print(f"Failed to get HWND: {e}")

    # --- Click-Through Logic ---
    def handle_toggle_click_through(self) -> None:
        self.click_through_enabled = not self.click_through_enabled
        try:
            hwnd = int(self.winId())
            set_click_through(hwnd, self.click_through_enabled)
            
            if self.click_through_enabled:
                self.setWindowOpacity(0.4)  # More transparent so code beneath is visible
                self.status_label.setText("OVERLAY MODE (Click-Through)")
                self.status_label.setStyleSheet("color: #e67e22; font-size: 14px; font-weight: bold;")
                self.content_area.setStyleSheet("background-color: rgba(30, 30, 30, 100); color: white; border: none;")  # Semi-transparent editor background
            else:
                self.setWindowOpacity(0.85)  # Restore readability
                self.status_label.setText("Interactive Mode")
                self.status_label.setStyleSheet("color: #cccccc; font-size: 14px; font-weight: bold;")
                self.content_area.setStyleSheet("""
                    QTextEdit {
                        background-color: #2d2d2d;
                        color: #d4d4d4;
                        border: 1px solid #3e3e3e;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 14px;
                        padding: 10px;
                    }
                """)
                
        except Exception as e:
            print(f"Toggle error: {e}")

    # --- Chat Logic ---
    def handle_chat_send(self) -> None:
        text = self.chat_input.text().strip()
        if not text:
            return
            
        self.content_area.append(f"\n\n**You:** {text}")
        self.chat_input.clear()
        
        self.gemini_handler.send_request(text)

    # --- Capture Logic ---
    def _perform_capture(self) -> Optional[Image.Image]:
        self.hide()
        QApplication.processEvents()
        time.sleep(0.15)
        img = None
        try:
            timestamp = int(time.time())
            _, img = self.screenshot_service.take_screenshot(f"snap_{timestamp}.png")
        except Exception as e:
            print(f"Capture failed: {e}")
        finally:
            self.show()
            # If we were in overlay mode, ensure click-through is restored after show()
            if self.click_through_enabled:
                hwnd = int(self.winId())
                set_click_through(hwnd, True)
                
            self.activateWindow()
        return img

    def handle_add_to_stack(self) -> None:
        print("Adding to stack...")
        img = self._perform_capture()
        if img:
            self.image_buffer.append(img)
            self._update_buffer_badge()
            self.status_label.setText("Image Added")

    def handle_analyze_stack(self) -> None:
        print("Analyze request...")
        if not self.image_buffer:
            img = self._perform_capture()
            if img:
                self.image_buffer.append(img)
        
        if not self.image_buffer:
            return

        images_to_send = list(self.image_buffer) 
        self.gemini_handler.send_request(images_to_send)
        
        self.image_buffer.clear()
        self._update_buffer_badge()

    def handle_clear_buffer(self) -> None:
        self.image_buffer.clear()
        self.gemini_handler.reset_session()
        self._update_buffer_badge()
        self.status_label.setText("Buffer & Context Cleared")
        self.content_area.setPlainText("Stack and history cleared.")

    def _update_buffer_badge(self) -> None:
        count = len(self.image_buffer)
        self.buffer_badge.setText(f"Buffered: {count}")
        style_color = "#007acc" if count > 0 else "#444444"
        self.buffer_badge.setStyleSheet(f"background-color: {style_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")

    def show_loading(self) -> None:
        self.status_label.setText("Thinking...")
        self.status_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold;")

    def display_solution(self, text: str) -> None:
        self.status_label.setText("Solution Ready")
        self.status_label.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
        self.content_area.append(f"\n\n**Gemini:**\n{text}")
        sb = self.content_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def display_error(self, error: str) -> None:
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        self.content_area.append(f"\nError: {error}")

    def keyPressEvent(self, event: QEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hotkey_listener.stop()
            self.close()

    # --- Audio ---
    def handle_save_audio(self) -> None:
        try:
            self.audio_service.ensure_recorder_running()
            wav_bytes = self.audio_service.get_last_audio_wav_bytes(seconds=30)
            if not wav_bytes:
                self.display_error("Audio not captured")
                return
            self.gemini_handler.send_audio(wav_bytes, prompt="")
            self.status_label.setText("Audio Sent")
            self.status_label.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
            self.content_area.append("\nAudio: last ~30s sent to Gemini")
        except Exception as e:
            self.display_error(f"Audio send failed: {e}")
