# Role
You are an Expert Python Developer specializing in PyQt6 and Windows Win32 API (`ctypes`).

# Project Goal
Create a Desktop Assistant application that overlays on the screen.
**CRITICAL REQUIREMENT:** The application window must use Windows Display Affinity to prevent it from appearing in Screen Sharing (Zoom/Meet/OBS) and Screenshots. To the interviewer, the app is invisible. To the user, it is a semi-transparent dark overlay.

# Tech Stack
- Python 3.10+
- PyQt6 (GUI)
- `ctypes` (for Windows API interaction)
- `mss` (for screen capture)
- `keyboard` (for global hotkeys)
- `google-generativeai` (Gemini 3.5 Flash)

# Architecture & Features

## 1. The "Ghost" Window (MainWindow)
- **Visuals:** Frameless, Always on Top, Semi-transparent black background (opacity ~0.8), White text.
- **Stealth Implementation (Must use this code):**
  You must add a method to the MainWindow class to set display affinity.
  ```python
  import ctypes
  from ctypes import wintypes
  
  def set_window_stealth(hwnd):
      # Constant for WDA_EXCLUDEFROMCAPTURE is 0x00000011
      # This prevents the window from being captured by BitBlt or Screen Sharing
      WDA_EXCLUDEFROMCAPTURE = 0x00000011
      user32 = ctypes.windll.user32
      user32.SetWindowDisplayAffinity(wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE)