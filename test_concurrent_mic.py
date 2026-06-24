#!/usr/bin/env python3
"""Test that PulseAudio shares microphone between multiple apps.

Usage:
  python test_concurrent_mic.py             # auto-detect mic, run test
  python test_concurrent_mic.py <PA_SOURCE>  # use a specific source
"""

import os
import sys
import time
import subprocess
import numpy as np
import sounddevice as sd

CHANNELS = 1
RATE = 16000
DURATION = 3.0


def get_default_source():
    out = subprocess.run(
        ["pactl", "get-default-source"], capture_output=True, text=True, timeout=3
    )
    return out.stdout.strip()


def list_sources():
    out = subprocess.run(
        ["pactl", "list", "sources", "short"], capture_output=True, text=True, timeout=3
    )
    print("Available PulseAudio sources:")
    for line in out.stdout.strip().split("\n"):
        if line:
            parts = line.split()
            name = parts[1] if len(parts) > 1 else line
            if ".monitor" not in name:
                print(f"  {name}")


def check_index_9():
    """Verify device index 9 exists (PulseAudio pseudo-device)."""
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if i == 9:
            return True, d["name"]
    return False, None


def callback_app1(indata, frames, time_val, status):
    """Callback for app1 (simulating a call) — collects frames."""
    global app1_frames
    if status:
        print(f"[app1] Status: {status}")
    app1_frames.append(indata.copy())


def callback_app2(indata, frames, time_val, status):
    """Callback for app2 (voice typing) — collects frames."""
    global app2_frames
    if status:
        print(f"[app2] Status: {status}")
    app2_frames.append(indata.copy())


def test_concurrent(source_name):
    global app1_frames, app2_frames
    app1_frames = []
    app2_frames = []

    old_pulse = os.environ.get("PULSE_SOURCE")
    os.environ["PULSE_SOURCE"] = source_name

    print(f"\nOpening both streams via device 9 with PULSE_SOURCE={source_name}")

    stream1 = None
    stream2 = None

    try:
        stream1 = sd.InputStream(
            samplerate=RATE, device=9, channels=CHANNELS, callback=callback_app1,
        )
        stream1.start()
        print("[app1] Stream opened (simulating a call/mic-in-use)")

        time.sleep(0.5)

        stream2 = sd.InputStream(
            samplerate=RATE, device=9, channels=CHANNELS, callback=callback_app2,
        )
        stream2.start()
        print("[app2] Stream opened (voice typing recording simultaneously)")

        time.sleep(DURATION)

        stream1.stop()
        stream1.close()
        stream1 = None
        print("[app1] Closed")

        time.sleep(0.2)
        stream2.stop()
        stream2.close()
        stream2 = None
        print("[app2] Closed")

    except Exception as e:
        print(f"ERROR: {e}")
        if stream1:
            try:
                stream1.stop()
                stream1.close()
            except Exception:
                pass
        if stream2:
            try:
                stream2.stop()
                stream2.close()
            except Exception:
                pass
        return False
    finally:
        if old_pulse is not None:
            os.environ["PULSE_SOURCE"] = old_pulse
        else:
            os.environ.pop("PULSE_SOURCE", None)

    app1_data = np.concatenate(app1_frames, axis=0) if app1_frames else np.array([])
    app2_data = np.concatenate(app2_frames, axis=0) if app2_frames else np.array([])

    app1_rms = np.sqrt(np.mean(app1_data**2)) if len(app1_data) > 0 else 0
    app2_rms = np.sqrt(np.mean(app2_data**2)) if len(app2_data) > 0 else 0

    print(f"\nResults:")
    print(f"  app1 (call) frames:   {len(app1_frames)} chunks, RMS={app1_rms:.6f}")
    print(f"  app2 (voice typing) frames: {len(app2_frames)} chunks, RMS={app2_rms:.6f}")

    if len(app1_frames) == 0:
        print("  FAIL: app1 captured no audio (device not shared or wrong source)")
        return False
    if len(app2_frames) == 0:
        print("  FAIL: app2 captured no audio — concurrent access failed!")
        return False

    print("  PASS: both apps captured audio simultaneously via PulseAudio")
    return True


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else get_default_source()
    if not source:
        print("No PulseAudio source found. Is PulseAudio running?")
        list_sources()
        sys.exit(1)

    print(f"PulseAudio source: {source}")

    exists, name = check_index_9()
    if not exists:
        print("WARNING: Device index 9 (PulseAudio) not found in sounddevice.")
        print("PulseAudio may not be the default ALSA device.")
        list_sources()
        answer = input("Continue anyway? [y/N] ").strip().lower()
        if answer != "y":
            sys.exit(1)
    else:
        print(f"Device index 9 found: {name}")

    result = test_concurrent(source)

    if result:
        print("\n=== SUCCESS: Microphone sharing works! ===")
        print("You can use the mic with voice typing and other apps simultaneously.")
        sys.exit(0)
    else:
        print("\n=== FAILURE: Microphone sharing test failed ===")
        print("Check PulseAudio configuration or try a different source.")
        sys.exit(1)


if __name__ == "__main__":
    main()
