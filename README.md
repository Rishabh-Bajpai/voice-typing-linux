# Voice Typing UI (Linux)

A lightweight Ubuntu/Linux voice typing application with a local web UI and global hotkey support. It records microphone audio, sends it to an OpenAI-compatible speech-to-text endpoint, and types the transcribed text into the currently focused window.

## Quick Start

```bash
# 1. Copy the example environment file
cp .env.example .env

# 2. Activate your Conda environment
conda activate voiceTyping

# 3. Run the application
python app.py
```

Then open `http://127.0.0.1:3221` in your browser to access the web UI.

## Features

- **Global Hotkey** — Press `Cmd+Shift+S` to start/stop recording from anywhere
- **Dual Modes** — Choose between streaming (real-time) or batch transcription
- **Auto-Typing** — Automatically types transcribed text into the active window
- **Web UI** — Control settings, view status, and manage microphone selection
- **Native Notifications** — Desktop notifications for recording status
- **Audio Feedback** — Optional beep sounds when starting/stopping (configurable)

## Prerequisites

- Ubuntu/Linux with a desktop environment
- Conda (Miniconda or Anaconda)
- A running STT server (e.g., faster-whisper on port 8969)
- Microphone access

## Configuration

Configure via environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_TYPING_STT_ENDPOINT` | `http://127.0.0.1:8969/v1/audio/transcriptions` | Speech-to-text API endpoint |
| `VOICE_TYPING_STT_MODEL` | `Systran/faster-whisper-medium.en` | Model name |
| `VOICE_TYPING_DEVICE_INDEX` | (auto) | Microphone device index |
| `VOICE_TYPING_STREAMING` | `1` | Set `0` for batch mode |
| `VOICE_TYPING_SILENCE_THRESHOLD` | `0.015` | Audio level threshold for silence |
| `VOICE_TYPING_SILENCE_DURATION` | `0.8` | Seconds of silence to stop recording |
| `VOICE_TYPING_BEEP` | `1` | Set `0` to disable beep sounds |
| `VOICE_TYPING_HOTKEY` | `<cmd>+<shift>+s` | Global hotkey to toggle recording |
| `VOICE_TYPING_UI_HOST` | `127.0.0.1` | Web UI bind address |
| `VOICE_TYPING_UI_PORT` | `3221` | Web UI port |

**Note:** The endpoint must be OpenAI-compatible for audio transcription and accept a `model` form field.

## Running on Startup (Ubuntu)

1. Make the launcher executable:
   ```bash
   chmod +x run_app.sh
   ```

2. Edit `run_app.sh` and set:
   - `CONDA_PATH` — e.g., `/home/<your-user>/miniconda3`
   - `ENV_NAME` — e.g., `voiceTyping`

3. Open **Startup Applications** in Ubuntu and add a new entry:
   - **Name:** `Voice Typing UI`
   - **Command:** `/absolute/path/to/voice_typing/run_app.sh`
   - **Comment:** Optional

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Endpoint unreachable | Verify your STT service is running and the URL is correct |
| Hotkey not working | Choose a different hotkey if your desktop environment uses the same shortcut |
| Wayland typing issues | Use `ydotool` or run in an X11 environment where key injection is allowed |
| Microphone not detected | Check input device selection in the web UI |