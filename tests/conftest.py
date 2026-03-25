import importlib
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def fake_external_modules(monkeypatch):
    """Install lightweight fakes for hardware/system modules."""

    # --- sounddevice ---
    sd_mod = types.ModuleType("sounddevice")
    sd_mod.default = types.SimpleNamespace(device=[0, 1])

    def query_devices(device=None, kind=None):
        if device is None:
            return [
                {"name": "Mic A", "max_input_channels": 1, "hostapi": 0},
                {"name": "Speaker", "max_input_channels": 0, "hostapi": 0},
                {"name": "Mic B", "max_input_channels": 2, "hostapi": 0},
            ]
        return {"default_samplerate": 16000}

    def query_hostapis(index):
        return {"name": "ALSA"}

    def check_input_settings(device=None, channels=None, samplerate=None):
        return None

    class DummyInputStream:
        def __init__(self, samplerate, device, channels, callback):
            self.samplerate = samplerate
            self.device = device
            self.channels = channels
            self.callback = callback
            self.started = False
            self.stopped = False
            self.closed = False

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def close(self):
            self.closed = True

    sd_mod.query_devices = query_devices
    sd_mod.query_hostapis = query_hostapis
    sd_mod.check_input_settings = check_input_settings
    sd_mod.InputStream = DummyInputStream
    sd_mod.play = lambda tone, samplerate=44100: None
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mod)

    # --- scipy.io.wavfile ---
    scipy_mod = types.ModuleType("scipy")
    scipy_io_mod = types.ModuleType("scipy.io")
    scipy_wav_mod = types.ModuleType("scipy.io.wavfile")
    scipy_wav_mod.write = lambda path, rate, data: None
    scipy_io_mod.wavfile = scipy_wav_mod
    scipy_mod.io = scipy_io_mod
    monkeypatch.setitem(sys.modules, "scipy", scipy_mod)
    monkeypatch.setitem(sys.modules, "scipy.io", scipy_io_mod)
    monkeypatch.setitem(sys.modules, "scipy.io.wavfile", scipy_wav_mod)

    # --- pynput keyboard ---
    pynput_mod = types.ModuleType("pynput")
    keyboard_mod = types.ModuleType("pynput.keyboard")

    class FakeGlobalHotKeys:
        def __init__(self, mapping):
            self.mapping = mapping
            self.stopped = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def join(self):
            return None

        def stop(self):
            self.stopped = True

    class FakeController:
        typed_text = []

        def type(self, text):
            self.__class__.typed_text.append(text)

    keyboard_mod.GlobalHotKeys = FakeGlobalHotKeys
    keyboard_mod.Controller = FakeController
    pynput_mod.keyboard = keyboard_mod

    monkeypatch.setitem(sys.modules, "pynput", pynput_mod)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", keyboard_mod)


@pytest.fixture(autouse=True)
def clear_voice_typing_env(monkeypatch):
    keys = [
        "VOICE_TYPING_STT_ENDPOINT",
        "VOICE_TYPING_STT_MODEL",
        "VOICE_TYPING_DEVICE_INDEX",
        "VOICE_TYPING_STREAMING",
        "VOICE_TYPING_SILENCE_THRESHOLD",
        "VOICE_TYPING_SILENCE_DURATION",
        "VOICE_TYPING_BEEP",
        "VOICE_TYPING_HOTKEY",
        "VOICE_TYPING_UI_HOST",
        "VOICE_TYPING_UI_PORT",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def vd(tmp_path, monkeypatch):
    import voice_dictation

    module = importlib.reload(voice_dictation)
    monkeypatch.setattr(module, "CONFIG_FILE", str(tmp_path / "config.json"))
    return module
