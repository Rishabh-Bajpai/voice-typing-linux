# Voice Typing UI (Linux)

A lightweight Ubuntu/Linux voice typing app with a local web UI and global hotkey support.

It records microphone audio, sends it to an OpenAI-compatible speech-to-text endpoint, and types the transcribed text into the currently focused window.

## Features

- Global hotkey to start/stop recording
- Streaming and batch transcription modes
- Auto-typing into the active window
- Web UI for settings and service controls
- Native desktop notifications and optional beep feedback

## Run the app

```bash
cp .env.example .env
conda activate voiceTyping
python app.py
```

Edit `.env` with your endpoint/model if needed.

## Run on startup (Ubuntu Startup Applications)

If you want the app to start automatically after login, use `run_app.sh`:

1. Make the launcher executable:

   ```bash
   chmod +x run_app.sh
   ```

2. Edit `run_app.sh` and set:
   - `CONDA_PATH` (example: `/home/<your-user>/miniconda3`)
   - `ENV_NAME` (example: `voiceTyping`)

3. Open **Startup Applications** in Ubuntu and add a new entry:
   - **Name:** `Voice Typing UI`
   - **Command:** `/absolute/path/to/voice_typing/run_app.sh`
   - **Comment:** Optional

After this, the app starts automatically each time you log in.

## Configuration

Set these environment variables to customize behavior:

- `VOICE_TYPING_STT_ENDPOINT` (default: `http://127.0.0.1:8969/v1/audio/transcriptions`)
- `VOICE_TYPING_STT_MODEL` (default: `Systran/faster-whisper-medium.en`)
- `VOICE_TYPING_DEVICE_INDEX` (optional microphone device index)
- `VOICE_TYPING_STREAMING` (default: `1`, set `0` for batch mode)
- `VOICE_TYPING_SILENCE_THRESHOLD` (default: `0.015`)
- `VOICE_TYPING_SILENCE_DURATION` (default: `0.8`)
- `VOICE_TYPING_BEEP` (default: `1`, set `0` to mute beeps)
- `VOICE_TYPING_HOTKEY` (default: `<cmd>+<shift>+s`)
- `VOICE_TYPING_UI_HOST` (default: `127.0.0.1`)
- `VOICE_TYPING_UI_PORT` (default: `3221`)

Note: the endpoint must be OpenAI-compatible for audio transcription and accept a `model` form field.

## Troubleshooting

- Endpoint unreachable: verify your STT service is running and URL is correct.
- Hotkey conflicts: choose a different hotkey if your desktop uses the same shortcut.
- Wayland typing issues: use tools like `ydotool` or run in an environment where key injection is allowed.
- Microphone issues: check input device selection from the web UI.
