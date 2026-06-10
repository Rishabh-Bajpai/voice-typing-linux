#!/usr/bin/python3
"""
System tray for Voice Typing using GNOME AppIndicator (D-Bus StatusNotifierItem).
Run as subprocess from app.py, communicates via HTTP.
"""

import subprocess
import sys
import threading
import time
import json
import urllib.request

UI_URL = "http://127.0.0.1:3221"

try:
    import gi
    gi.require_version("AyatanaAppIndicator3", "0.1")
    gi.require_version("Gtk", "3.0")
    from gi.repository import AyatanaAppIndicator3, Gtk, GLib
except ImportError as e:
    print(f"[TRAY] Missing dependency: {e}", flush=True)
    sys.exit(1)


def api_get(path):
    try:
        r = urllib.request.urlopen(f"{UI_URL}{path}", timeout=2)
        return json.loads(r.read().decode())
    except Exception:
        return None


def api_post(path):
    try:
        req = urllib.request.Request(f"{UI_URL}{path}", data=b"", method="POST")
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass


def update_icon(indicator):
    status = api_get("/status")
    if not status:
        indicator.set_label("Offline", "")
        indicator.set_icon("dialog-information")
        return

    rec = status.get("is_recording", False)
    running = status.get("is_running", False)

    if rec:
        icon_name = "media-record"
        label = "Recording..."
    elif running:
        icon_name = "microphone-sensitivity-high"
        label = "Active"
    else:
        icon_name = "microphone-sensitivity-muted"
        label = "Stopped"

    indicator.set_label(label, "")
    indicator.set_icon(icon_name)
    indicator.set_attention_icon("media-record")


def build_menu(indicator):
    menu = Gtk.Menu()

    item_status = Gtk.MenuItem(label="Voice Typing")
    item_status.set_sensitive(False)
    menu.append(item_status)
    menu.append(Gtk.SeparatorMenuItem())

    item_reconnect = Gtk.MenuItem(label="Reconnect Hotkey")
    item_reconnect.connect("activate", lambda _: api_post("/restart_hotkey"))
    menu.append(item_reconnect)

    item_web = Gtk.MenuItem(label="Open Web UI")
    item_web.connect("activate", lambda _: subprocess.run(
        ["xdg-open", UI_URL], capture_output=True
    ))
    menu.append(item_web)

    item_quit = Gtk.MenuItem(label="Quit")
    item_quit.connect("activate", lambda _: Gtk.main_quit())
    menu.append(item_quit)

    menu.show_all()
    indicator.set_menu(menu)


def main():
    indicator = AyatanaAppIndicator3.Indicator.new(
        "voice-typing",
        "",
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

    # Wait for Flask to be ready
    for _ in range(10):
        if api_get("/status") is not None:
            break
        time.sleep(1)

    update_icon(indicator)
    build_menu(indicator)

    def poll():
        while True:
            time.sleep(2)
            GLib.idle_add(update_icon, indicator)

    threading.Thread(target=poll, daemon=True).start()
    Gtk.main()


if __name__ == "__main__":
    main()
