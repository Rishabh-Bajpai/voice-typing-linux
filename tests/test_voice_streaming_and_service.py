from types import SimpleNamespace

import numpy as np


class ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self.target = target

    def start(self):
        if self.target:
            self.target()


def test_process_stream_chunk_transcribes_types_and_cleans_file(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    monkeypatch.setattr(vd.threading, "Thread", ImmediateThread)

    removed = []
    typed = []
    writes = []

    monkeypatch.setattr(
        vd.wav,
        "write",
        lambda path, rate, data: writes.append((path, rate, data.shape)),
    )
    monkeypatch.setattr(app, "transcribe", lambda _: "streamed text")
    monkeypatch.setattr(app, "type_text", lambda text: typed.append(text))
    monkeypatch.setattr(vd.os, "remove", lambda p: removed.append(p))

    app._process_stream_chunk(np.ones((8000, 1), dtype=np.float32))

    assert writes
    assert typed == ["streamed text "]
    assert removed


def test_toggle_recording_start_and_stop_non_streaming(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    vd.STREAMING_MODE = False
    vd.DEVICE_INDEX = 2

    events = {"start_called_with": None, "typed": None}
    monkeypatch.setattr(vd.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(app, "notify", lambda title, msg: None)
    monkeypatch.setattr(app, "play_beep", lambda *a, **k: None)
    monkeypatch.setattr(
        app.recorder,
        "start",
        lambda device_index=None: events.__setitem__("start_called_with", device_index),
    )
    monkeypatch.setattr(app.recorder, "stop", lambda: "/tmp/a.wav")
    monkeypatch.setattr(app, "transcribe", lambda p: "hello")
    monkeypatch.setattr(app, "type_text", lambda t: events.__setitem__("typed", t))

    app.toggle_recording()  # start
    assert app.is_recording is True
    assert events["start_called_with"] == 2

    app.toggle_recording()  # stop/process
    assert app.is_recording is False
    assert events["typed"] == "hello"


def test_start_and_stop_service(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    calls = {"notify": [], "stop": 0}

    monkeypatch.setattr(vd.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        app, "notify", lambda title, msg: calls["notify"].append((title, msg))
    )
    monkeypatch.setattr(
        app.recorder, "stop", lambda: calls.__setitem__("stop", calls["stop"] + 1)
    )

    app.start_service()
    assert app.is_running is True
    assert app.hotkey_listener is not None

    app.stop_service()
    assert app.is_running is False
    assert calls["stop"] == 1
    assert ("Service", "Daemon Started") in calls["notify"]
    assert ("Service", "Daemon Stopped") in calls["notify"]


def test_type_text_noop_on_empty(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    ran = {"subprocess": False}
    monkeypatch.setattr(
        vd.subprocess, "run", lambda *a, **k: ran.__setitem__("subprocess", True)
    )
    app.type_text("")
    assert ran["subprocess"] is False


def test_audio_recorder_start_uses_default_rate_when_check_fails(vd, monkeypatch):
    rec = vd.AudioRecorder()

    monkeypatch.setattr(
        vd.sd,
        "check_input_settings",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("unsupported")),
    )
    monkeypatch.setattr(
        vd.sd, "query_devices", lambda device, kind: {"default_samplerate": 44100}
    )

    rec.start(device_index=1)
    assert rec.stream is not None
    assert rec.stream.samplerate == 44100
