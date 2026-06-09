# AGENTS.md — Voice Typing (Linux)

## Quick Start
```bash
cp .env.example .env  # Required — not git-tracked
conda activate voiceTyping  # or your venv of choice
python app.py
```

## Key Commands
- **Run app**: `python app.py` (starts Flask UI + hotkey service)
- **Run tests**: `PYTHONPATH=. pytest -q`
- **Lint**: `ruff check .`

## Architecture
- `app.py` — Flask web server (UI + API), ~700-line embedded HTML template
- `voice_dictation.py` — Core: `AudioRecorder`, `VoiceDictationApp` classes
- `config.json` — Persisted settings (auto-created on first save, gitignored)
- `.env` — Environment variable overrides (gitignored)
- `tests/` — Pytest suite with mocked audio/network/hardware

## Dependencies
Install in a fresh environment:
```bash
conda create -n voiceTyping python=3.11
conda activate voiceTyping
pip install flask flask-cors requests sounddevice scipy numpy pynput
```

## Critical Details
- **STT endpoint**: Must be OpenAI-compatible (`/v1/audio/transcriptions` with `model` form field)
- **Hotkey format**: Uses `pynput` format, e.g., `<cmd>+<shift>+s` (not standard key names)
- **Audio storage**: Writes to `/tmp/voice_typing.wav` and `/tmp/vds_*.wav`
- **Typing**: Falls back from `xdotool` → `pynput.keyboard.Controller().type()` if xdotool unavailable
- **PulseAudio-only devices**: Routed via `PULSE_SOURCE` env var — set `VOICE_TYPING_PULSE_SOURCE` in `.env`
- **Wayland**: No native `xdotool` support; requires `ydotool` for key injection

## Device Listing
Uses `pactl list sources` for user-friendly device names, mapped to `sounddevice` ALSA indices.
Devices not directly accessible via ALSA are routed through PulseAudio (index 9 + `PULSE_SOURCE`).

## Mic Test
- 5-second test recording with real-time 12-bar VU meter + dBFS readout
- Uses `sounddevice.InputStream` callback to compute RMS → normalized level (0.0–1.0)

## STT Test
- 2-second recording from the selected mic, sent to the configured STT endpoint
- Displays endpoint, model, elapsed time, and transcribed result in the UI

## Tests
- `PYTHONPATH=. pytest -q` — 33 tests, all mocking hardware/network
- Test helper `ImmediateThread` runs threaded code synchronously (`**kwargs` compatible)
- Coverage config in `.github/workflows/tests.yml`

## Common Issues
- "Endpoint unreachable" — STT server not running on port 8969 or wrong URL
- Hotkey conflicts — Desktop environment uses same shortcut
- Microphone not detected — Use web UI to select device index manually
- USB/PulseAudio-only devices not in sounddevice list — They appear with `pulse_source` and route through the "default" PulseAudio device