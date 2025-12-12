# DesktopVisionAssistant

Application for automated screenshot analysis and assistance using Gemini AI.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation (Development)

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## Building the Application

To create a standalone executable (`.exe`):

1. Ensure you have installed the requirements (`pip install -r requirements.txt`).
2. Run the **`build_app.bat`** script located in the root folder.
   - You can double-click it in Windows Explorer.
   - Or run it from the terminal: `.\build_app.bat`
3. Upon success, a new folder named `dist` will be created containing `DesktopVisionAssistant.exe`.

## Running the Executable

**CRITICAL INSTRUCTIONS:**

1. **.env File**: You MUST create or copy your `.env` file into the same folder as `DesktopVisionAssistant.exe` (the `dist` folder). The application will not work without the API key found in this file.

2. **Administrator Privileges**: The application uses the `keyboard` library to intercept global hotkeys. This requires **Run as Administrator** privileges on Windows.
   - Right-click `DesktopVisionAssistant.exe` -> "Run as administrator".

## Usage

### Hotkeys

- **Ctrl+Alt+S**: Capture screenshot and add to buffer
- **Ctrl+Alt+Space**: Analyze all buffered screenshots
- **Ctrl+Alt+X**: Clear buffer and reset AI context
- **Ctrl+Alt+Z**: Toggle overlay mode (click-through)
- **Esc**: Close application

### Features

- **Screenshot Buffer**: Capture multiple screenshots for context-aware analysis
- **Overlay Mode**: Transparent window that doesn't interfere with your workflow
- **Chat Interface**: Ask follow-up questions after analysis
- **Privacy Mode**: Window is excluded from screen capture by other applications

## Troubleshooting

- **Black Screenshots**: If screenshots are black, ensure the target window is not protecting its content (DRM) or try changing the window mode.
- **Hotkeys not working**: Ensure you launched the app as Administrator.
- **API Errors**: Verify your `GEMINI_API_KEY` is correctly set in the `.env` file.
