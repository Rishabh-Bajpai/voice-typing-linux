# AGENTS.md — Voice Typing (Linux)

## Quick Start
```bash
cp .env.example .env
conda activate voiceTyping
python app.py          # served at http://127.0.0.1:3221
```

## Key Commands
- **Run**: `python app.py` (Flask + hotkey daemon + system tray subprocess)
- **Tests**: `PYTHONPATH=. pytest -q` (33 tests, all mocking hardware/network)
- **Lint**: `ruff check .`
- **Single test**: `PYTHONPATH=. pytest tests/test_voice_edge_cases.py::test_name -q`

## Architecture
- `app.py` (~1150 lines) — Flask server with embedded HTML template + all JS/CSS
- `voice_dictation.py` (~880 lines) — `AudioRecorder` + `VoiceDictationApp` classes
- `llm_client.py` — OpenAI-compatible LLM post-processor (grammar/translate/custom)
- `tray.py` — System tray via `/usr/bin/python3` + `gi.repository.AyatanaAppIndicator3`
- `config.json` — Runtime settings (auto-created, gitignored)
- `.env` — Environment variables (gitignored), loaded at module level before Flask starts
- `tests/` — Pytest, mocks sounddevice/scipy/pynput via `conftest.py`

## Critical Details

### Dependencies — two environments needed
- **App runtime** (conda `voiceTyping`): `flask flask-cors requests sounddevice scipy numpy pynput pyperclip pystray Pillow`
- **System tray** (system `/usr/bin/python3`): requires `python3-gi`, `gir1.2-ayatanaappindicator3-0.1` via apt — conda's pygobject lacks GI introspection data

### Hotkey
- Uses `pynput.keyboard.GlobalHotKeys` for press detection, separate `keyboard.Listener` for push-to-hold release detection
- Format: `<cmd>+<shift>+s` (pynput syntax, not standard key names)
- On logout/login the X11 connection dies — use `POST /restart_hotkey` or the ⌨️ Reset button in the web UI
- `pkill -f` hangs; use `timeout 3 kill <PID>` instead

### Audio
- Records at 16000 Hz if the device supports it, otherwise uses the device's default sample rate
- PulseAudio-only devices (sounddevice can't see them) route through index 9 + `PULSE_SOURCE` env var
- Temp files: `/tmp/voice_typing.wav`, `/tmp/vds_*.wav`

### Config priority
1. `.env` file loaded into `os.environ` at module level
2. `config.json` overlays runtime overrides
3. LLM credentials (`OPENAI_*`) come from `.env` only — excluded from `config.json`

### Typing
- Falls back: `xdotool type --clearmodifiers` → `pynput.keyboard.Controller().type()` → printed warning
- Clipboard fallback: `pyperclip` → `xclip -selection clipboard`
- Wayland: xdotool/pynput don't work; requires `ydotool`

### Sample rate gotcha
- PulseAudio's "default" ALSA device (index 9) may not support 16000 Hz
- `check_input_settings` can lie about support — always use the device's `default_samplerate` as first choice
- All three recording paths (`AudioRecorder.start`, `start_mic_test`, `test_stt_endpoint`) must respect this

### System tray
- `pystray` uses X11 System Tray protocol (incompatible with GNOME AppIndicator)
- Must use `gi.repository.AyatanaAppIndicator3` via system Python with explicit `DISPLAY` + `DBUS_SESSION_BUS_ADDRESS`
- GNOME requires `gnome-shell-extension-ubuntu-appindicators` enabled

## Test quirks
- `conftest.py` mocks sounddevice, scipy, pynput at module level via `sys.modules` injection
- `ImmediateThread` replaces `threading.Thread` — runs target synchronously in `.start()`
- Must accept `**kwargs` because `concurrent.futures` (or other libs) pass extra args
- Tests patch `vd.subprocess`, `vd.sd`, etc. (module-level references, not global)

## Key files (agent should read first)
| File | Purpose |
|------|---------|
| `app.py` | All routes + embedded HTML template + JS |
| `voice_dictation.py` | Core logic, state machine, audio pipeline |
| `conftest.py` | Mock setup — essential for understanding test behavior |
| `tray.py` | System tray (runs as separate process via system Python) |
| `.env.example` | All configurable variables documented |
