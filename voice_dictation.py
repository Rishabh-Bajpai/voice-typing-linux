import os
import sys
import threading
import time
import json
import requests
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from pynput import keyboard
import subprocess
import queue

CHANNELS = 1
RATE = 16000
AUDIO_FILE = "/tmp/voice_typing.wav"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    defaults = {
        "STT_ENDPOINT": os.getenv(
            "VOICE_TYPING_STT_ENDPOINT", "http://127.0.0.1:8969/v1/audio/transcriptions"
        ),
        "STT_MODEL": os.getenv(
            "VOICE_TYPING_STT_MODEL", "Systran/faster-whisper-medium.en"
        ),
        "DEVICE_INDEX": os.getenv("VOICE_TYPING_DEVICE_INDEX", None),
        "STREAMING_MODE": os.getenv("VOICE_TYPING_STREAMING", "1") == "1",
        "SILENCE_THRESHOLD": float(
            os.getenv("VOICE_TYPING_SILENCE_THRESHOLD", "0.015")
        ),
        "SILENCE_DURATION": float(os.getenv("VOICE_TYPING_SILENCE_DURATION", "0.8")),
        "BEEP_ENABLED": os.getenv("VOICE_TYPING_BEEP", "1") == "1",
        "HOTKEY_STR": os.getenv("VOICE_TYPING_HOTKEY", "<cmd>+<shift>+s"),
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                defaults.update(loaded)
        except Exception as e:
            print(f"Error loading config: {e}")
    return defaults


def save_config(config_dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")


# Initialize globals from config
CONFIG = load_config()
STT_ENDPOINT = CONFIG["STT_ENDPOINT"]
STT_MODEL = CONFIG["STT_MODEL"]
DEVICE_INDEX = CONFIG["DEVICE_INDEX"]
STREAMING_MODE = CONFIG["STREAMING_MODE"]
SILENCE_THRESHOLD = CONFIG["SILENCE_THRESHOLD"]
SILENCE_DURATION = CONFIG["SILENCE_DURATION"]
BEEP_ENABLED = CONFIG["BEEP_ENABLED"]
HOTKEY_STR = CONFIG["HOTKEY_STR"]


class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.recording = False
        self.rate = RATE
        self.device_index = None
        self.stream_queue = queue.Queue()
        self.stream = None

        try:
            if DEVICE_INDEX is not None:
                self.device_index = int(DEVICE_INDEX)
            else:
                self.device_index = sd.default.device[0]

            device_info = sd.query_devices(self.device_index, "input")
            self.rate = int(device_info["default_samplerate"])

            try:
                sd.check_input_settings(
                    device=self.device_index, channels=CHANNELS, samplerate=RATE
                )
                self.rate = RATE
            except Exception:
                pass

            print(f"Using sample rate: {self.rate} on device {self.device_index}")
        except Exception as e:
            print(f"Error selecting device/rate: {e}")
            self.rate = 44100

    def get_input_devices(self):
        devices = []
        try:
            device_list = sd.query_devices()
            for i, d in enumerate(device_list):
                if d["max_input_channels"] > 0:
                    api_name = sd.query_hostapis(d["hostapi"])["name"]
                    name = f"{d['name']} ({api_name})"
                    devices.append({"index": i, "name": name})
        except Exception as e:
            print(f"Error listing devices: {e}")
        return devices

    def start(self, device_index=None):
        self.frames = []
        self.recording = True

        # Ensure target_device is an integer index
        try:
            raw_target = device_index if device_index is not None else self.device_index
            target_device = int(raw_target)
        except (ValueError, TypeError):
            target_device = raw_target

        while not self.stream_queue.empty():
            try:
                self.stream_queue.get_nowait()
            except queue.Empty:
                break

        def callback(indata, frames, time_val, status):
            if status:
                print(f"Status check: {status}", flush=True)
            cp = indata.copy()
            self.frames.append(cp)
            if STREAMING_MODE:
                self.stream_queue.put(cp)

        try:
            # Re-check rate if device changed
            device_info = sd.query_devices(target_device, "input")
            default_rate = int(device_info["default_samplerate"])
            rate_to_use = RATE
            try:
                sd.check_input_settings(
                    device=target_device, channels=CHANNELS, samplerate=RATE
                )
            except:
                rate_to_use = default_rate

            self.stream = sd.InputStream(
                samplerate=rate_to_use,
                device=target_device,
                channels=CHANNELS,
                callback=callback,
            )
            self.stream.start()
            print(
                f"[REC] Audio stream started on device {target_device} at {rate_to_use}Hz.",
                flush=True,
            )
        except Exception as e:
            print(f"Failed to start stream: {e}")
            raise e

    def stop(self):
        self.recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                print("[PROC] Stream closed successfully.", flush=True)
            except Exception as e:
                print(f"Stream close error: {e}", flush=True)

        if not self.frames:
            return None

        audio_data = np.concatenate(self.frames, axis=0)
        wav.write(AUDIO_FILE, self.rate, audio_data)
        return AUDIO_FILE


class VoiceDictationApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.is_recording = False
        self.is_running = False
        self.last_transcription = ""
        self.status = "Idle"
        self.hotkey_listener = None

    def notify(self, title, message):
        print(f"[{title}] {message}", flush=True)
        self.status = f"{title}: {message}"
        subprocess.run(["notify-send", "-a", "Voice Typing", title, message])

    def play_beep(self, frequency=800, duration=0.1):
        if not BEEP_ENABLED:
            return
        try:
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(frequency * t * 2 * np.pi)
            sd.play(tone, samplerate=sample_rate)
        except Exception as e:
            print(f"Beep error: {e}")

    def transcribe(self, file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/wav")}
                data = {"model": STT_MODEL}
                response = requests.post(
                    STT_ENDPOINT, files=files, data=data, timeout=30
                )
                response.raise_for_status()
                return response.json().get("text", "").strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def type_text(self, text):
        if not text:
            return
        print(f"Injecting: '{text}'", flush=True)
        self.last_transcription = text
        try:
            result = subprocess.run(
                ["xdotool", "type", "--clearmodifiers", text], capture_output=True
            )
            if result.returncode == 0:
                return
        except:
            pass
        try:
            from pynput.keyboard import Controller

            Controller().type(text)
        except:
            pass

    def update_config(
        self,
        stt_endpoint=None,
        stt_model=None,
        streaming=None,
        hotkey=None,
        device_index=None,
        silence_threshold=None,
        beep_enabled=None,
    ):
        global STT_ENDPOINT, STT_MODEL, STREAMING_MODE, HOTKEY_STR
        global DEVICE_INDEX, SILENCE_THRESHOLD, BEEP_ENABLED

        need_hotkey_restart = False

        if stt_endpoint is not None:
            STT_ENDPOINT = stt_endpoint
        if stt_model is not None:
            STT_MODEL = stt_model
        if streaming is not None:
            STREAMING_MODE = bool(streaming)
        if beep_enabled is not None:
            BEEP_ENABLED = bool(beep_enabled)
        if silence_threshold is not None:
            SILENCE_THRESHOLD = float(silence_threshold)
        if device_index is not None:
            try:
                DEVICE_INDEX = int(device_index)
                self.recorder.device_index = DEVICE_INDEX
            except:
                pass

        if hotkey is not None and hotkey != HOTKEY_STR:
            HOTKEY_STR = hotkey
            need_hotkey_restart = True

        if need_hotkey_restart and self.is_running:
            self.stop_service()
            self.start_service()

        # Save to file
        save_config(
            {
                "STT_ENDPOINT": STT_ENDPOINT,
                "STT_MODEL": STT_MODEL,
                "STREAMING_MODE": STREAMING_MODE,
                "BEEP_ENABLED": BEEP_ENABLED,
                "SILENCE_THRESHOLD": SILENCE_THRESHOLD,
                "DEVICE_INDEX": DEVICE_INDEX,
                "HOTKEY_STR": HOTKEY_STR,
                "SILENCE_DURATION": SILENCE_DURATION,
            }
        )

        self.notify("Config Updated", "Settings saved persistently")

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.play_beep(800, 0.1)
            self.notify("Recording", "Speak now...")
            self.recorder.start(device_index=DEVICE_INDEX)
            if STREAMING_MODE:
                threading.Thread(target=self._streaming_worker, daemon=True).start()
        else:
            self.is_recording = False
            self.play_beep(400, 0.1)
            self.notify("Processing", "Finalizing...")

            def process_stop():
                try:
                    audio_path = self.recorder.stop()
                    if not STREAMING_MODE and audio_path:
                        text = self.transcribe(audio_path)
                        if text:
                            self.type_text(text)
                    self.status = "Idle"
                except Exception as e:
                    print(f"Stop error: {e}")

            threading.Thread(target=process_stop, daemon=True).start()

    def _streaming_worker(self):
        utterance_buffer = []
        silence_duration = 0.0
        is_speaking = False

        while self.is_recording:
            try:
                chunk = self.recorder.stream_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            rms = np.sqrt(np.mean(chunk**2))
            if rms > SILENCE_THRESHOLD:
                is_speaking = True
                silence_duration = 0.0
            elif is_speaking:
                silence_duration += len(chunk) / float(self.recorder.rate)

            if is_speaking:
                utterance_buffer.append(chunk)
                if silence_duration > SILENCE_DURATION:
                    audio_data = np.concatenate(utterance_buffer, axis=0)
                    utterance_buffer = []
                    is_speaking = False
                    silence_duration = 0.0
                    if len(audio_data) / float(self.recorder.rate) > 0.4:
                        self._process_stream_chunk(audio_data)

        if utterance_buffer:
            audio_data = np.concatenate(utterance_buffer, axis=0)
            if len(audio_data) / float(self.recorder.rate) > 0.4:
                self._process_stream_chunk(audio_data)

    def _process_stream_chunk(self, audio_data):
        temp_file = f"/tmp/vds_{int(time.time() * 1000)}.wav"
        wav.write(temp_file, self.recorder.rate, audio_data)

        def run_trans():
            text = self.transcribe(temp_file)
            if text:
                print(f"[STREAM] '{text}'", flush=True)
                self.type_text(text + " ")
            try:
                os.remove(temp_file)
            except:
                pass

        threading.Thread(target=run_trans, daemon=True).start()

    def start_service(self):
        if self.is_running:
            return
        self.is_running = True

        def listen():
            with keyboard.GlobalHotKeys({HOTKEY_STR: self.toggle_recording}) as h:
                self.hotkey_listener = h
                h.join()

        threading.Thread(target=listen, daemon=True).start()
        self.notify("Service", "Daemon Started")

    def stop_service(self):
        if not self.is_running:
            return
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.is_running = False
        self.is_recording = False
        self.recorder.stop()
        self.notify("Service", "Daemon Stopped")


if __name__ == "__main__":
    app_instance = VoiceDictationApp()
    app_instance.start_service()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app_instance.stop_service()
