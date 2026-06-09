# AGENTS.md — Voice Typing (Linux)

## Quick Start
```bash
conda activate voiceTyping
cp .env.example .env  # Required - not git-tracked
python app.py
```

## Key Commands
- **Run app**: `python app.py` (starts Flask UI + hotkey service)
- **Run tests**: `pytest -q`
- **Syntax check**: `python -m py_compile app.py voice_dictation.py`
- **Lint**: `ruff check .`

## Architecture
- `app.py` — Flask web server (UI + API), ~400-line embedded HTML template
- `voice_dictation.py` — Core: AudioRecorder, VoiceDictationApp classes
- `config.json` — Persisted settings (auto-created on first save)
- `tests/` — Uses pytest with mocked audio/network

## Critical Details
- **STT endpoint**: Must be OpenAI-compatible (`/v1/audio/transcriptions` with `model` form field)
- **Hotkey format**: Uses `pynput` format, e.g., `<cmd>+<shift>+s` (not standard key names)
- **Audio storage**: Writes to `/tmp/voice_typing.wav` and `/tmp/vds_*.wav`
- **Typing**: Falls back from `xdotool` → `pynput.keyboard.Controller().type()` if xdotool unavailable
- **Wayland**: No native support; requires X11 or `ydotool` for key injection

## Tests
- Run with: `PYTHONPATH=. pytest -q`
- Coverage config in `.github/workflows/tests.yml`
- Tests mock audio hardware and network calls

## Common Issues
- "Endpoint unreachable" — STT server not running on port 8969
- Hotkey conflicts — Desktop environment uses same shortcut
- Microphone not detected — Use web UI to select device index manually