

## Project Description: Voice Typing Linux Client

### 🎯 Overview

Build a lightweight background service for Ubuntu that provides global "Push-to-Talk" (or toggle) transcription. The application should capture audio from the default microphone, send it to a local OpenAI-compatible API, and simulate keyboard input to type the resulting text into the currently focused window.

### 🛠 Technical Specifications

* **Operating System:** Ubuntu (Linux) with support for X11 or Wayland (via `dotool` or `ydotool`).
* **API Configuration:**
* **Endpoint:** `http://127.0.0.1:8969/v1/audio/transcriptions`
* **Model:** `Systran/faster-whisper-medium.en`


* **Core Functionality:**
1. **Hotkey Toggle:** Listen for a global hotkey (e.g., `Super+Shift+S`).
2. **State Management:** * **Press 1:** Start recording audio. Play a subtle "start" beep or show a small tray icon change.
* **Press 2:** Stop recording, send the audio buffer to the local API.


3. **Keystroke Injection:** Once the API returns JSON, parse the `text` field and "type" it into the active cursor position.
4. **Error Handling:** Notify the user via `libnotify` if the API is unreachable.



### 📦 Recommended Dependencies (For Agent Reference)

* **Audio Recording:** `PyAudio` or `sounddevice`.
* **Hotkey Detection:** `pynput`.
* **Keyboard Injection:** `evdev` (Wayland compatible) 
* **API Requests:** `requests` or `httpx`.
