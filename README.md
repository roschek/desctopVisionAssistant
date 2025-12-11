# GhostHelper

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
3. Upon success, a new folder named `dist` will be created containing `GhostHelper.exe`.

## Running the Executable

**CRITICAL INSTRUCTIONS:**

1. **.env File**: You MUST create or copy your `.env` file into the same folder as `GhostHelper.exe` (the `dist` folder). The application will not work without the API key found in this file.

2. **Administrator Privileges**: The application uses the `keyboard` library to intercept global hotkeys. This requires **Run as Administrator** privileges on Windows.
   - Right-click `GhostHelper.exe` -> "Run as administrator".

## Troubleshooting

- **Black Screenshots**: If screenshots are black, ensure the target window is not protecting its content (DRM) or try changing the window mode.
- **Hotkeys not working**: Ensure you launched the app as Administrator.

