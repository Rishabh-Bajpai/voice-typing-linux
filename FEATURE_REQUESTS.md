# Voice Typing — Feature Requests & Implementation Status

> This document catalogs all features discussed during the development session,
> their current implementation status, and the details a developer needs to
> complete, fix, or enhance each one.

---

## Table of Contents

1. [System Tray Icon](#1-system-tray-icon)
2. [LLM Co-Pilot Mode](#2-llm-co-pilot-mode)
3. [Voice Commands (Local, Non-LLM)](#3-voice-commands-local-non-llm)
4. [Push-to-Hold Mode](#4-push-to-hold-mode)
5. [Smart Clipboard (Type vs Copy)](#5-smart-clipboard-type-vs-copy)
6. [Real-Time Transcription Preview](#6-real-time-transcription-preview)
7. [Transcription History & Export](#7-transcription-history--export)
8. [Mic Test with VU Meter](#8-mic-test-with-vu-meter)
9. [STT Endpoint Test](#9-stt-endpoint-test)
10. [Device Listing with PulseAudio Names](#10-device-listing-with-pulseaudio-names)
11. [USB/PulseAudio-Only Device Support](#11-usbpulseaudio-only-device-support)
12. [Configuration Persistence](#12-configuration-persistence)
13. [Batch Mode as Default](#13-batch-mode-as-default)
14. [Hotkey Restart on Session Change](#14-hotkey-restart-on-session-change)
15. [Thread Safety Improvements](#15-thread-safety-improvements)

---

## 1. System Tray Icon

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- A system tray icon that appears in the GNOME notification area (top panel)
- Icon changes color: green when active/idle, red when recording
- Right-click menu with:
  - Status indicator
  - Mode switching (Toggle vs Push-to-Hold)
  - Output mode (Type vs Copy to Clipboard)
  - LLM action selector (Off, Grammar Fix, Translate → language submenu, Custom)
  - "Reconnect Hotkey" option
  - "Open Web UI" option
  - "Quit" option

### What is implemented
- `tray.py` uses `/usr/bin/python3` (system Python) with `gi.repository.AyatanaAppIndicator3`
- Communicates with the Flask app via HTTP (localhost:3221)
- Started as a subprocess from `app.py` with explicit `DISPLAY`, `XAUTHORITY`, `DBUS_SESSION_BUS_ADDRESS` env vars
- Icon shows and updates properly on recording state change
- Full menu: mode radio items (Toggle/Push-to-Hold), output radio items (Type/Clipboard), LLM submenu (Off/Grammar/Translate with language submenu/Custom), Reconnect Hotkey, Open Web UI, Quit
- Polls `/llm_config` every 2s to sync menu checkmarks (✓ prefix on active LLM action/language)

### What is missing / not working
- Custom LLM action has no input field in tray (needs web UI for custom prompt entry)
- Gnome icon names used — may fall back to generic icons on non-GNOME icon themes

### Relevant files
- `tray.py` — main tray implementation
- `app.py` — subprocess launch at bottom of file
- `voice_dictation.py` — `llm_action`, `push_to_hold`, `clipboard_mode` states

### Implementation notes
- System tray uses the D-Bus StatusNotifierItem protocol (via AyatanaAppIndicator3), NOT the X11 System Tray protocol
- `pystray` was attempted (imported) but it uses the X11 System Tray protocol which is incompatible with GNOME + ubuntu-appindicators extension
- The tray runs as a **separate process** using `/usr/bin/python3` because the conda environment doesn't have `gi.repository` (GTK introspection data)
- Required system dependencies: `python3-gi`, `gir1.2-ayatanaappindicator3-0.1`, `gnome-shell-extension-appindicators`
- The tray connects to the Flask API via HTTP — the Flask server MUST be running before the tray starts (tray has a 10-second retry loop)
- Kill stale tray processes before restarting to avoid duplicate icons

---

## 2. LLM Co-Pilot Mode

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- After STT transcribes audio to text, optionally pipe it through an LLM before typing
- Supported actions:
  - **Grammar Fix** — Fix grammar, punctuation, and capitalization without changing meaning
  - **Translate** — Translate to a target language (Hindi as default)
  - **Custom** — Free-form instruction like "convert to bullet points"
- Configurable via web UI and tray menu
- Only works in **batch mode** (not streaming)

### What is implemented
- `llm_client.py` — OpenAI-compatible API client with system prompts for each action
- LLM pipeline integrated in `process_and_output()` in `voice_dictation.py`
- Web UI: dropdown selector for LLM action, language picker for translate, text input for custom prompt
- Tray menu: LLM action selector (if re-implemented)
- Batch-mode-only notice shown in UI when streaming is enabled
- LLM credentials loaded from `.env` file (OPENAI_BASE_URL, OPENAI_CHAT_MODEL_ID, OPENAI_API_KEY)

### Relevant files
- `llm_client.py` — LLM API client
- `voice_dictation.py` — `process_and_output()` method, `llm_action` / `llm_instruction` states
- `app.py` — `/llm_config` API endpoint, web UI HTML

### Implementation notes
- LLM calls use `temperature: 0.1` for consistent output
- The system prompt for grammar fix asks to "not change the meaning, word choice, or structure beyond what's needed for correctness"
- Translate action uses a format string: `"Translate the following text into {language}."`
- Custom action uses the instruction directly as the system prompt
- LLM config is NOT saved to `config.json` (secrets stay in `.env` only)
- The `/llm_config` endpoint handles both GET (read current config) and POST (update config)

---

## 3. Voice Commands (Local, Non-LLM)

**Status:** ⚠️ PARTIALLY IMPLEMENTED

### What was requested
- Process certain spoken phrases locally (before STT or LLM) to trigger actions:
  - "new line" / "newline" → type `\n`
  - "new paragraph" → type `\n\n`
  - "period" → type `.`
  - "comma" → type `,`
  - "question mark" → type `?`
  - "exclamation mark" → type `!`
  - "colon" → type `:`
  - "semicolon" → type `;`
  - "open quote" → type `"`
  - "close quote" → type `"`
  - "open parenthesis" → type `(`
  - "close parenthesis" → type `)`
  - "tab" → type `\t`
  - "delete last word" → delete last 4 characters
  - "delete last sentence" → delete last 20 characters

### What is implemented
- `_process_voice_commands()` method in `voice_dictation.py` handles all the above commands
- `process_and_output()` calls it on every transcribed text
- If a command matches, the action is performed instead of typing the text

### What is missing / not working
- **The command MUST match the full transcribed text exactly** — if the STT returns "new line" (with surrounding noise or capitalization), it won't match because the comparison is `lower = text.lower().strip()` then `if lower in commands:`
- UI lists available commands but no way to add/edit them
- No feedback when a voice command is triggered (no notification or log entry)
- `delete last word` and `delete last sentence` use hardcoded BackSpace counts (4 and 20) which is fragile — should use word/sentence boundary detection

### Relevant files
- `voice_dictation.py` — `_process_voice_commands()` method, `process_and_output()` method

### Implementation notes
- Commands are matched against the FULL lowercased + stripped transcribed text
- If the text doesn't exactly match a command key, it falls through to normal processing (LLM + type)
- Delete commands return special strings `"__DELETE_LAST_WORD__"` and `"__DELETE_LAST_SENTENCE__"` which are handled before LLM processing
- Punctuation/newline commands (.,?!"\n etc.) now **skip LLM processing** to avoid the LLM modifying or stripping them
- Delete commands use a single method (xdotool first, pynput fallback) — previously both ran, doubling the deletion to 8/40 characters

---

## 4. Push-to-Hold Mode

**Status:** ⚠️ PARTIALLY WORKING

### What was requested
- Same hotkey works for two modes:
  - **Toggle mode:** press once to start recording, press again to stop
  - **Push-to-Hold mode:** press and hold to record, release to stop + transcribe + type
- Switchable via web UI checkbox and tray menu

### What is implemented
- `push_to_hold` boolean state in `VoiceDictationApp`
- Web UI checkbox for push-to-hold, initial state synced from server at page load
- Tray menu radio items for mode selection
- Hotkey handler `_on_hotkey()` checks mode:
  - Toggle: calls `toggle_recording()`
  - Push-to-hold: calls `_push_to_hold_start()` and starts a persistent release listener
- A persistent `keyboard.Listener(on_release=...)` runs at service startup watching for the main key release
- Case-insensitive release detection (`key.char.lower() == main_key_lower`)
- **5-second safety timeout**: if the release listener doesn't fire within 5s, recording auto-stops (prevents stuck recordings)
- Timer is created in `_push_to_hold_start()` and cancelled in `_push_to_hold_stop()`
- The `_pth_timer` attribute holds the `threading.Timer` reference

### What is not working
- **The release listener does not reliably detect key release in push-to-hold mode.** Two issues:
  1. When using a mouse button assigned to the hotkey combo, the key release event might not be captured by `pynput`'s Listener
  2. The `GlobalHotKeys` (used for press detection) and `Listener` (used for release detection) both use the XRecord extension and may interfere with each other
- The 5-second timeout mitigates this but is not a true push-to-hold experience (user must wait for timeout)
- The `Manual Dictate` button in the web UI works via `toggle_recording()` which always toggles (not affected by mode)

### Relevant files
- `voice_dictation.py` — `_on_hotkey()`, `_push_to_hold_start()`, `_push_to_hold_stop()`, `_start_hotkey_listener()`, `toggle_recording()`
- `app.py` — web UI checkbox, `/llm_config` endpoint

### Suggested fix approach
- Replace `pynput`'s GlobalHotKeys + Listener with `evdev` for more reliable key detection (requires `input` group membership)
- Or use `python-xlib` directly to capture both press and release events

---

## 5. Smart Clipboard (Type vs Copy)

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Toggle between two output modes:
  - **Type into document** — use xdotool/pynput to type the text into the active window
  - **Copy to clipboard** — copy the text to the system clipboard

### What is implemented
- `clipboard_mode` boolean in `VoiceDictationApp` (True = type, False = copy)
- `process_and_output()` checks the mode and calls either `type_text()` or `copy_to_clipboard()`
- Web UI checkbox
- Tray menu switch (if re-implemented)
- `copy_to_clipboard()` uses `pyperclip` with `xclip -selection clipboard` as fallback
- `type_text()` uses `xdotool type --clearmodifiers` with `pynput.keyboard.Controller().type()` as fallback

### Relevant files
- `voice_dictation.py` — `copy_to_clipboard()`, `type_text()`, `process_and_output()`
- `app.py` — web UI checkbox

### Implementation notes
- `pyperclip` is imported lazily (inside `copy_to_clipboard()`) to avoid breaking tests
- Both typing methods include detailed logging for debugging
- On Wayland, `xdotool` and `pynput` may not work — consider `ydotool` or `wtype` as additional fallbacks

---

## 6. Real-Time Transcription Preview

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Show words appearing live in the web UI as they are transcribed in streaming mode
- A small box below the controls with the current transcription text and a blinking cursor

### What is implemented
- `preview-box` div in the web UI (hidden by default, shown when recording)
- `updatePreview()` JavaScript function polls `/status` every 500ms and shows new `last_text`
- Blinking cursor animation via CSS `@keyframes blink`

### Relevant files
- `app.py` — HTML template (preview box), JavaScript (`updatePreview`)

---

## 7. Transcription History & Export

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Scrollable history of all transcriptions with timestamps
- Export as `.txt` or `.md`

### What is implemented
- `transcription_history` list in `VoiceDictationApp` (max 50 entries)
- Each entry: `{text, time, source}`
- Collapsible history panel in web UI, auto-updates every 2 seconds
- Download buttons for TXT and MD formats
- `GET /export_history?format=txt|md` endpoint
- Color-coded dots: blue for streaming, purple for batch

### Relevant files
- `voice_dictation.py` — `transcription_history` list, history append in `process_and_output()`
- `app.py` — web UI panel, `/history` endpoint, `/export_history` endpoint

---

## 8. Mic Test with VU Meter

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- 5-second microphone test with real-time volume meter
- Visual feedback with colored bars

### What is implemented
- "Test Mic" button in web UI
- 12-bar VU meter with height animation and color zones (green → blue → purple → red)
- dBFS numerical readout
- 5-second countdown timer
- Backend: `start_mic_test()`, `stop_mic_test()`, `get_mic_test_level()` in `VoiceDictationApp`
- API: `POST /test_mic/start`, `POST /test_mic/stop`, `GET /test_mic/level`

### Relevant files
- `voice_dictation.py` — mic test methods
- `app.py` — web UI, API routes, JavaScript polling

---

## 9. STT Endpoint Test

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Record a short clip from the selected microphone
- Send it to the configured STT endpoint
- Display the result: endpoint URL, model, elapsed time, transcribed text (or error)

### What is implemented
- "Test STT Endpoint" button in web UI
- Backend: 2-second recording via `sd.rec()`, then POST to STT endpoint
- Structured result display card
- API: `POST /test_stt`

### Relevant files
- `voice_dictation.py` — `test_stt_endpoint()` method
- `app.py` — web UI, API route

### Implementation notes
- Sample rate detection: uses the device's default sample rate, only falls back to 16000 if `check_input_settings(16000)` passes
- Respects `PULSE_SOURCE` env var for PulseAudio-only devices

---

## 10. Device Listing with PulseAudio Names

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Show user-friendly device names in the microphone dropdown
- Use PulseAudio descriptions instead of raw ALSA device names
- Show ALL available microphones, including PulseAudio-only devices

### What is implemented
- `get_input_devices()` in `AudioRecorder` queries `pactl list sources` for descriptions
- Parses `alsa.card` from the source's Properties section to map to `sounddevice` indices
- Formats names as `(audio) {Description}`
- PulseAudio-only devices (not in sounddevice's ALSA list) include a `pulse_source` field
- Falls back to sounddevice if PulseAudio is unavailable

### Relevant files
- `voice_dictation.py` — `get_input_devices()` method

---

## 11. USB/PulseAudio-Only Device Support

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Show and allow selection of the USB PnP Audio Device (not visible in `sounddevice`'s ALSA list)
- Record from it by routing through PulseAudio

### What is implemented
- PulseAudio-only devices are listed with `index: 9` (the "default" PulseAudio ALSA device) and `pulse_source` field
- `PULSE_SOURCE_NAME` config stores the PulseAudio source name
- `AudioRecorder.start()` and `start_mic_test()` set `PULSE_SOURCE` env var before opening the stream if a PulseAudio source is configured
- The env var is restored to its previous value after the stream opens

### Relevant files
- `voice_dictation.py` — `AudioRecorder.start()`, `start_mic_test()`, `test_stt_endpoint()`, `PULSE_SOURCE_NAME` global
- `app.py` — frontend sends `pulse_source` in autoSave

### Implementation notes
- `PULSE_SOURCE_NAME` is loaded from `.env` (`VOICE_TYPING_PULSE_SOURCE`) and config.json
- The env var approach works because PortAudio's PulseAudio backend respects `PULSE_SOURCE`
- Only non-monitor PulseAudio sources are listed (monitors are filtered out)

---

## 12. Configuration Persistence

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- Settings changed via the web UI should survive application restarts
- `.env` file should serve as the initial template
- `config.json` should store runtime overrides

### What is implemented
- `load_config()` reads defaults from `os.getenv()` (populated by `.env` file)
- Then overlays with `config.json` values (runtime overrides take priority)
- LLM credentials are excluded from `config.json` for security
- `save_config()` writes runtime state

### Relevant files
- `voice_dictation.py` — `load_config()`, `save_config()`, `update_config()`

### Implementation notes
- `config.json` is auto-created on first save and gitignored
- The `.env` file is manually loaded at module startup (before Flask loads it)
- LLM settings (OPENAI_BASE_URL, OPENAI_CHAT_MODEL_ID, OPENAI_API_KEY) come ONLY from `.env`, not from `config.json`

---

## 13. Batch Mode as Default

**Status:** ✅ IMPLEMENTED

### What was requested
- Batch mode (record → stop → transcribe → type) should be the default, not streaming
- LLM features should only work in batch mode

### What is implemented
- `STREAMING_MODE` default is `False` (batch mode)
- `.env.example` has `VOICE_TYPING_STREAMING=0`
- Web UI shows a yellow notice when streaming is enabled: "LLM features require Batch mode"
- LLM pipeline is skipped in streaming mode

### Relevant files
- `voice_dictation.py` — `STREAMING_MODE` default, `process_and_output()` LLM skip
- `app.py` — web UI batch notice

---

## 14. Hotkey Restart on Session Change

**Status:** ✅ IMPLEMENTED & WORKING

### What was requested
- After login/logout or sleep/resume, the hotkey stops working because the X11 display connection is severed
- Should be able to restart the hotkey listener without restarting the whole app

### What is implemented
- `POST /restart_hotkey` endpoint — stops old listener, starts new one
- "⌨️ Reset" button in the web UI header
- "Reconnect Hotkey" option in the tray menu
- `restart_hotkey()` method in `VoiceDictationApp`

### Relevant files
- `voice_dictation.py` — `restart_hotkey()`, `_start_hotkey_listener()`
- `app.py` — `/restart_hotkey` endpoint, web UI button

---

## 15. Thread Safety Improvements

**Status:** ✅ IMPLEMENTED

### What was requested
- Fix race conditions from multiple threads accessing shared state

### What is implemented
- `self._lock = threading.Lock()` in `VoiceDictationApp`
- `_config_lock` for module-level global mutations
- `_streaming_worker_active` flag to prevent overlapping streaming workers
- `_transcribe_semaphore` (BoundedSemaphore 3) to limit concurrent STT requests

### Relevant files
- `voice_dictation.py` — lock usage throughout

---

## Additional Notes for the Developer

### Architecture Overview

```
app.py                  Flask web server (UI + API)
voice_dictation.py      Core logic: AudioRecorder, VoiceDictationApp
llm_client.py           OpenAI-compatible LLM client
tray.py                 System tray (runs with system Python)
config.json             Runtime settings (auto-created, gitignored)
.env                    Environment variables (gitignored)
.env.example            Template for .env
voice-typing.service.example  systemd user service template
run_app.sh              Launcher script (auto-detects conda)
```

### Key Dependencies (conda environment)
- `flask`, `flask-cors` — web server
- `sounddevice`, `scipy`, `numpy` — audio recording
- `pynput` — global hotkey detection
- `requests` — HTTP client (STT + LLM)
- `pyperclip` — clipboard access
- `pystray`, `Pillow` — system tray (used by conda's Python)
- `python-xlib` — used by pynput internally

### System Dependencies (apt)
- `/usr/bin/python3` — runs the tray icon
- `python3-gi` — GTK introspection (for tray)
- `gir1.2-ayatanaappindicator3-0.1` — AppIndicator library (for tray)
- `gnome-shell-extension-appindicators` — GNOME extension to show tray icons
- `xdotool` — keyboard input simulation
- `xclip` — clipboard access fallback
- `notify-send` (libnotify-bin) — desktop notifications

### Testing
```bash
PYTHONPATH=. pytest -q    # 33 tests, all mocking hardware/network
ruff check .              # Lint (zero warnings)
```

### Common Pitfalls
1. **pynput GlobalHotKeys** doesn't work on Wayland. The app requires X11 (`Session: x11`).
2. **pynput Listener** and **pynput GlobalHotKeys** both use XRecord and may interfere.
3. **pystray** uses X11 System Tray protocol — incompatible with GNOME AppIndicator.
4. **The tray needs DISPLAY=:1** and DBUS_SESSION_BUS_ADDRESS set. Pass explicitly in subprocess.
5. **Kill old processes before restart** — duplicate tray icons appear if old processes survive.
6. **`pkill -f` hangs** on this system — use `kill <PID>` with `timeout`.
7. **config.json can override .env values** — LLM secrets are excluded from config.json for security.
8. **Sample rate must be auto-detected** — PulseAudio devices may not support 16000 Hz.
