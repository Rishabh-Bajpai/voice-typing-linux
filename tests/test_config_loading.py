import json


def test_load_config_reads_voice_typing_env(vd, monkeypatch):
    monkeypatch.setenv(
        "VOICE_TYPING_STT_ENDPOINT", "http://localhost:9999/v1/audio/transcriptions"
    )
    monkeypatch.setenv("VOICE_TYPING_STT_MODEL", "test-model")
    monkeypatch.setenv("VOICE_TYPING_DEVICE_INDEX", "4")
    monkeypatch.setenv("VOICE_TYPING_STREAMING", "0")
    monkeypatch.setenv("VOICE_TYPING_SILENCE_THRESHOLD", "0.2")
    monkeypatch.setenv("VOICE_TYPING_SILENCE_DURATION", "1.2")
    monkeypatch.setenv("VOICE_TYPING_BEEP", "0")
    monkeypatch.setenv("VOICE_TYPING_HOTKEY", "<ctrl>+<alt>+v")

    cfg = vd.load_config()

    assert cfg["STT_ENDPOINT"].startswith("http://localhost:9999")
    assert cfg["STT_MODEL"] == "test-model"
    assert cfg["DEVICE_INDEX"] == "4"
    assert cfg["STREAMING_MODE"] is False
    assert cfg["SILENCE_THRESHOLD"] == 0.2
    assert cfg["SILENCE_DURATION"] == 1.2
    assert cfg["BEEP_ENABLED"] is False
    assert cfg["HOTKEY_STR"] == "<ctrl>+<alt>+v"


def test_load_config_merges_config_file(vd, tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "STT_ENDPOINT": "http://file-endpoint",
                "STT_MODEL": "file-model",
                "STREAMING_MODE": False,
                "HOTKEY_STR": "<ctrl>+k",
            }
        )
    )
    monkeypatch.setattr(vd, "CONFIG_FILE", str(cfg_path))

    cfg = vd.load_config()
    assert cfg["STT_ENDPOINT"] == "http://file-endpoint"
    assert cfg["STT_MODEL"] == "file-model"
    assert cfg["STREAMING_MODE"] is False
    assert cfg["HOTKEY_STR"] == "<ctrl>+k"


def test_save_config_writes_json(vd, tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(vd, "CONFIG_FILE", str(cfg_path))

    payload = {"STT_ENDPOINT": "http://x", "STT_MODEL": "m"}
    vd.save_config(payload)

    saved = json.loads(cfg_path.read_text())
    assert saved == payload
