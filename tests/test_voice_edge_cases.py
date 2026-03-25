import queue
from types import SimpleNamespace

import numpy as np


class ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self.target = target

    def start(self):
        if self.target:
            self.target()


def test_load_and_save_config_error_paths(vd, monkeypatch, capsys):
    monkeypatch.setattr(vd.os.path, "exists", lambda _: True)
    monkeypatch.setattr(
        "builtins.open",
        lambda *a, **k: (_ for _ in ()).throw(OSError("bad open")),
    )

    cfg = vd.load_config()
    assert "STT_ENDPOINT" in cfg
    assert "Error loading config" in capsys.readouterr().out

    monkeypatch.setattr(
        "builtins.open",
        lambda *a, **k: (_ for _ in ()).throw(OSError("bad save")),
    )
    vd.save_config({"x": 1})
    assert "Error saving config" in capsys.readouterr().out


def test_audio_recorder_init_falls_back_when_query_fails(vd, monkeypatch):
    monkeypatch.setattr(
        vd.sd,
        "query_devices",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no device")),
    )
    rec = vd.AudioRecorder()
    assert rec.rate == 44100


def test_get_input_devices_success_and_exception(vd, monkeypatch):
    rec = vd.AudioRecorder()

    devices = rec.get_input_devices()
    assert len(devices) == 2

    monkeypatch.setattr(
        vd.sd,
        "query_devices",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert rec.get_input_devices() == []


def test_audio_start_drains_queue_and_callback_streaming(vd, monkeypatch):
    vd.STREAMING_MODE = True
    rec = vd.AudioRecorder()
    rec.stream_queue.put(np.zeros((2, 1)))
    rec.stream_queue.put(np.zeros((2, 1)))

    rec.start(device_index="not-an-int")
    assert rec.stream is not None
    assert rec.stream_queue.empty()

    rec.stream.callback(np.ones((4, 1)), 4, None, "warn")
    assert len(rec.frames) == 1
    assert not rec.stream_queue.empty()


def test_audio_start_raises_when_stream_creation_fails(vd, monkeypatch):
    rec = vd.AudioRecorder()
    monkeypatch.setattr(
        vd.sd,
        "InputStream",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("stream fail")),
    )

    try:
        rec.start(device_index=0)
        assert False, "expected RuntimeError"
    except RuntimeError:
        assert True


def test_audio_stop_handles_stream_close_error_and_no_frames(vd):
    rec = vd.AudioRecorder()

    class BadStream:
        def stop(self):
            raise RuntimeError("stop fail")

        def close(self):
            raise RuntimeError("close fail")

    rec.stream = BadStream()
    rec.frames = []
    assert rec.stop() is None


def test_notify_and_beep_error_paths(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    called = {"notify": None}
    monkeypatch.setattr(
        vd.subprocess, "run", lambda cmd: called.__setitem__("notify", cmd)
    )

    app.notify("Title", "Body")
    assert called["notify"][0] == "notify-send"

    vd.BEEP_ENABLED = True
    monkeypatch.setattr(
        vd.sd, "play", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("audio fail"))
    )
    app.play_beep()


def test_type_text_handles_subprocess_and_controller_exceptions(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    monkeypatch.setattr(
        vd.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("xdotool missing")),
    )

    import pynput.keyboard as keyboard_mod

    class BadController:
        def type(self, text):
            raise RuntimeError("type fail")

    monkeypatch.setattr(keyboard_mod, "Controller", BadController)
    app.type_text("hello")
    assert app.last_transcription == "hello"


def test_toggle_recording_streaming_starts_worker_thread(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    vd.STREAMING_MODE = True
    vd.DEVICE_INDEX = 0

    starts = {"threads": 0}

    class CountThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            starts["threads"] += 1

    monkeypatch.setattr(vd.threading, "Thread", CountThread)
    monkeypatch.setattr(app, "notify", lambda *a, **k: None)
    monkeypatch.setattr(app, "play_beep", lambda *a, **k: None)
    monkeypatch.setattr(app.recorder, "start", lambda device_index=None: None)

    app.toggle_recording()
    assert app.is_recording is True
    assert starts["threads"] == 1


def test_toggle_recording_stop_handles_exception(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    app.is_recording = True
    vd.STREAMING_MODE = False

    monkeypatch.setattr(vd.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(app, "notify", lambda *a, **k: None)
    monkeypatch.setattr(app, "play_beep", lambda *a, **k: None)
    monkeypatch.setattr(
        app.recorder, "stop", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    app.toggle_recording()
    assert app.is_recording is False


def test_streaming_worker_processes_chunk_and_flushes_tail(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    app.is_recording = True
    app.recorder.rate = 16000

    processed = []
    monkeypatch.setattr(
        app, "_process_stream_chunk", lambda audio: processed.append(audio.shape[0])
    )

    chunks = [
        np.ones((16000, 1), dtype=np.float32) * 0.5,  # speaking
        np.zeros((16000, 1), dtype=np.float32),  # silence > duration => emits
        np.ones((8000, 1), dtype=np.float32) * 0.5,  # leftover flush on stop
    ]

    def fake_get(timeout=0.1):
        if chunks:
            return chunks.pop(0)
        app.is_recording = False
        raise queue.Empty

    monkeypatch.setattr(app.recorder.stream_queue, "get", fake_get)
    vd.SILENCE_THRESHOLD = 0.015
    vd.SILENCE_DURATION = 0.8

    app._streaming_worker()

    assert len(processed) >= 2


def test_process_stream_chunk_cleanup_exception_is_swallowed(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    monkeypatch.setattr(vd.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(vd.wav, "write", lambda path, rate, data: None)
    monkeypatch.setattr(app, "transcribe", lambda path: "ok")
    monkeypatch.setattr(app, "type_text", lambda text: None)
    monkeypatch.setattr(
        vd.os, "remove", lambda path: (_ for _ in ()).throw(RuntimeError("rm fail"))
    )

    app._process_stream_chunk(np.ones((9000, 1), dtype=np.float32))


def test_service_idempotent_branches(vd, monkeypatch):
    app = vd.VoiceDictationApp()
    monkeypatch.setattr(vd.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(app, "notify", lambda *a, **k: None)
    monkeypatch.setattr(app.recorder, "stop", lambda: None)

    app.start_service()
    app.start_service()  # early return branch when already running

    app.is_running = False
    app.stop_service()  # early return branch when already stopped
