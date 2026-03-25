from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import threading
import os
import voice_dictation
from voice_dictation import VoiceDictationApp

app = Flask(__name__)
CORS(app)

# Initialize the dictation app
dict_app = VoiceDictationApp()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Typing Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --card: #161c2e;
            --primary: #38bdf8;
            --accent: #818cf8;
            --text: #f1f5f9;
            --text-dim: #94a3b8;
            --success: #4ade80;
            --danger: #fb7185;
            --border: rgba(255, 255, 255, 0.08);
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-image: radial-gradient(circle at 50% 50%, #1e293b 0%, #0b0f19 100%);
        }

        .container {
            width: 100%;
            max-width: 700px;
            padding: 2rem;
        }

        .card {
            background-color: var(--card);
            border-radius: 32px;
            padding: 3rem;
            box-shadow: 0 50px 100px -20px rgba(0, 0, 0, 0.7);
            border: 1px solid var(--border);
            backdrop-filter: blur(20px);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 2.5rem;
        }

        h1 {
            margin: 0 0 0.25rem 0;
            font-weight: 600;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            letter-spacing: -0.02em;
        }

        .subtitle {
            color: var(--text-dim);
            font-size: 1.1rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.6rem 1.2rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .status-on { background: rgba(74, 222, 128, 0.1); color: var(--success); box-shadow: 0 0 20px rgba(74, 222, 128, 0.15); }
        .status-off { background: rgba(251, 113, 133, 0.1); color: var(--danger); }

        .form-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2.5rem;
            padding: 2rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 20px;
            border: 1px solid var(--border);
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .input-group label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        input, select {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            padding: 0.75rem 1rem;
            border-radius: 12px;
            color: var(--text);
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.2s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
        }

        .full-width { grid-column: span 2; }

        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 2.5rem;
        }

        button {
            padding: 1.1rem 1.5rem;
            border-radius: 16px;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-family: inherit;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 1.05rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            color: white;
            box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            filter: brightness(1.1);
            box-shadow: 0 20px 30px -10px rgba(56, 189, 248, 0.6);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }

        .log-container {
            background: #080c14;
            border-radius: 20px;
            padding: 1.5rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            height: 120px;
            overflow-y: auto;
            border: 1px solid var(--border);
            margin-top: 2rem;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
        }

        .log-entry { 
            margin-bottom: 0.75rem; 
            padding-left: 1rem;
            color: var(--primary);
            opacity: 0;
            transform: translateX(-10px);
            animation: fadeIn 0.4s forwards;
        }

        @keyframes fadeIn {
            to { opacity: 1; transform: translateX(0); }
        }

        .recording-indicator {
            width: 10px;
            height: 10px;
            background: var(--danger);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 15px var(--danger);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }

        .save-banner {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            background: var(--success);
            color: #000;
            padding: 0.75rem 2rem;
            border-radius: 99px;
            font-weight: 600;
            box-shadow: 0 10px 30px rgba(74, 222, 128, 0.4);
            display: none;
            z-index: 100;
        }
    </style>
</head>
<body>
    <div id="saveBanner" class="save-banner">Settings Saved</div>
    <div class="container">
        <div class="card">
            <div class="header">
                <div>
                    <h1>Voice Typing.</h1>
                    <p class="subtitle">Real-time STT Service</p>
                </div>
                <div id="statusBadge" class="status-badge status-off">
                    <span id="statusText">Disconnected</span>
                </div>
            </div>

            <div class="form-section">
                <div class="input-group full-width">
                    <label>Microphone Device</label>
                    <select id="deviceSelect" onchange="autoSave()">
                        <option value="">Loading devices...</option>
                    </select>
                </div>
                
                <div class="input-group full-width">
                    <label>STT Endpoint</label>
                    <input type="text" id="sttEndpoint" value="{{ stt_endpoint }}" onchange="autoSave()">
                </div>

                <div class="input-group">
                    <label>STT Model</label>
                    <input type="text" id="sttModel" value="{{ stt_model }}" onchange="autoSave()">
                </div>

                <div class="input-group">
                    <label>Hotkey</label>
                    <input type="text" id="hotkey" value="{{ hotkey }}" onchange="autoSave()">
                </div>

                <div class="input-group">
                    <label>Mode</label>
                    <select id="streamingMode" onchange="autoSave()">
                        <option value="1" {% if streaming %}selected{% endif %}>Streaming (Real-time)</option>
                        <option value="0" {% if not streaming %}selected{% endif %}>Batch (Once on stop)</option>
                    </select>
                </div>

                <div class="input-group">
                    <label>VAD Threshold</label>
                    <input type="number" step="0.005" id="silenceThreshold" value="{{ silence_threshold }}" onchange="autoSave()">
                </div>

                <div class="input-group">
                    <label>Sound Effects</label>
                    <select id="beepEnabled" onchange="autoSave()">
                        <option value="1" {% if beep_enabled %}selected{% endif %}>Enabled (Beeps)</option>
                        <option value="0" {% if not beep_enabled %}selected{% endif %}>Muted</option>
                    </select>
                </div>
            </div>

            <div class="controls">
                <button onclick="toggleService()" class="btn-primary" id="toggleBtn">Start Daemon</button>
                <button onclick="toggleRecording()" class="btn-secondary" id="recBtn">Manual Dictate</button>
            </div>

            <div class="log-container" id="logs">
                <div class="log-entry">Console ready. Monitoring signals...</div>
            </div>
        </div>
    </div>

    <script>
        let isRunning = false;
        let isRecording = false;
        let lastLoggedText = "";

        async function loadDevices() {
            try {
                const res = await fetch('/devices');
                const devices = await res.json();
                const sel = document.getElementById('deviceSelect');
                sel.innerHTML = '';
                devices.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.index;
                    opt.text = d.name;
                    if (d.index == {{ active_device if active_device is not none else -1 }}) opt.selected = true;
                    sel.appendChild(opt);
                });
            } catch (e) { console.error("Device load failed", e); }
        }

        async function updateStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                
                isRunning = data.is_running;
                isRecording = data.is_recording;

                const badge = document.getElementById('statusBadge');
                const badgeText = document.getElementById('statusText');
                const toggleBtn = document.getElementById('toggleBtn');
                const recBtn = document.getElementById('recBtn');

                if (isRunning) {
                    badge.className = 'status-badge status-on';
                    badgeText.innerText = 'Service Active';
                    toggleBtn.innerText = 'Stop Daemon';
                } else {
                    badge.className = 'status-badge status-off';
                    badgeText.innerText = 'Inactive';
                    toggleBtn.innerText = 'Start Daemon';
                }

                if (isRecording) {
                    recBtn.innerHTML = '<span class="recording-indicator"></span>Listening...';
                    recBtn.className = 'btn-secondary btn-recording';
                } else {
                    recBtn.innerText = 'Manual Dictate';
                    recBtn.className = 'btn-secondary';
                }

                if (data.last_text && data.last_text !== lastLoggedText) {
                    lastLoggedText = data.last_text;
                    addLog(data.last_text);
                }
            } catch (e) {}
        }

        function addLog(text) {
            const container = document.getElementById('logs');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerText = '>> ' + text;
            container.prepend(entry);
        }

        async function autoSave() {
            const settings = {
                stt_endpoint: document.getElementById('sttEndpoint').value,
                stt_model: document.getElementById('sttModel').value,
                hotkey: document.getElementById('hotkey').value,
                streaming: document.getElementById('streamingMode').value === "1",
                device_index: document.getElementById('deviceSelect').value,
                silence_threshold: document.getElementById('silenceThreshold').value,
                beep_enabled: document.getElementById('beepEnabled').value === "1"
            };

            await fetch('/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            const banner = document.getElementById('saveBanner');
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 2000);
        }

        async function toggleService() {
            await fetch('/toggle_service', {method: 'POST'});
            updateStatus();
        }

        async function toggleRecording() {
            await fetch('/toggle_recording', {method: 'POST'});
            updateStatus();
        }

        loadDevices();
        setInterval(updateStatus, 1000);
        updateStatus();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        stt_endpoint=voice_dictation.STT_ENDPOINT,
        stt_model=voice_dictation.STT_MODEL,
        streaming=voice_dictation.STREAMING_MODE,
        hotkey=voice_dictation.HOTKEY_STR,
        active_device=voice_dictation.DEVICE_INDEX,
        silence_threshold=voice_dictation.SILENCE_THRESHOLD,
        beep_enabled=voice_dictation.BEEP_ENABLED,
    )


@app.route("/devices")
def get_devices():
    return jsonify(dict_app.recorder.get_input_devices())


@app.route("/settings", methods=["POST"])
def save_settings():
    data = request.json
    dict_app.update_config(
        stt_endpoint=data.get("stt_endpoint"),
        stt_model=data.get("stt_model"),
        streaming=data.get("streaming"),
        hotkey=data.get("hotkey"),
        device_index=data.get("device_index"),
        silence_threshold=data.get("silence_threshold"),
        beep_enabled=data.get("beep_enabled"),
    )
    return jsonify({"success": True})


@app.route("/status")
def get_status():
    return jsonify(
        {
            "is_running": dict_app.is_running,
            "is_recording": dict_app.is_recording,
            "last_text": dict_app.last_transcription,
            "status": dict_app.status,
        }
    )


@app.route("/toggle_service", methods=["POST"])
def toggle_service():
    if dict_app.is_running:
        dict_app.stop_service()
    else:
        dict_app.start_service()
    return jsonify({"success": True})


@app.route("/toggle_recording", methods=["POST"])
def toggle_recording():
    if not dict_app.is_running:
        dict_app.start_service()
    dict_app.toggle_recording()
    return jsonify({"success": True})


if __name__ == "__main__":
    dict_app.start_service()
    app.run(
        host=os.getenv("VOICE_TYPING_UI_HOST", "127.0.0.1"),
        port=int(os.getenv("VOICE_TYPING_UI_PORT", "3221")),
    )
