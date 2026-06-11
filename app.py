from flask import Flask, jsonify, request, render_template_string, Response
from flask_cors import CORS
import os
import subprocess
import voice_dictation
from voice_dictation import VoiceDictationApp

app = Flask(__name__)
_ui_port = int(os.getenv("VOICE_TYPING_UI_PORT", "3221"))
_ui_host = os.getenv("VOICE_TYPING_UI_HOST", "127.0.0.1")
_cors_origins = [f"http://127.0.0.1:{_ui_port}", f"http://localhost:{_ui_port}"]
if _ui_host not in ("127.0.0.1", "localhost"):
    _cors_origins.append(f"http://{_ui_host}:{_ui_port}")
CORS(app, origins=_cors_origins)

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
            grid-template-columns: 1fr 1fr 1fr;
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

        .mic-meter {
            display: none;
            margin-top: 1.5rem;
            padding: 1.25rem 1.5rem;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 16px;
            border: 1px solid var(--border);
        }

        .mic-meter.visible {
            display: block;
        }

        .meter-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }

        .meter-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .meter-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .meter-db {
            font-size: 1.1rem;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            min-width: 4.5rem;
            text-align: right;
        }

        .meter-db.low { color: var(--success); }
        .meter-db.mid { color: var(--primary); }
        .meter-db.high { color: var(--danger); }

        .meter-timer {
            color: var(--text-dim);
            font-size: 0.85rem;
            font-variant-numeric: tabular-nums;
        }

        .meter-track {
            display: flex;
            gap: 4px;
            height: 32px;
            align-items: flex-end;
        }

        .meter-bar {
            flex: 1;
            height: 4px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 3px;
            transition: height 0.06s ease, background 0.06s ease, box-shadow 0.06s ease;
            align-self: flex-end;
        }

        .meter-bar.lit {
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.3);
        }

        .meter-bar:nth-child(1).lit,
        .meter-bar:nth-child(2).lit,
        .meter-bar:nth-child(3).lit { background: #4ade80; }
        .meter-bar:nth-child(4).lit,
        .meter-bar:nth-child(5).lit,
        .meter-bar:nth-child(6).lit { background: #38bdf8; }
        .meter-bar:nth-child(7).lit,
        .meter-bar:nth-child(8).lit,
        .meter-bar:nth-child(9).lit { background: #818cf8; }
        .meter-bar:nth-child(10).lit,
        .meter-bar:nth-child(11).lit,
        .meter-bar:nth-child(12).lit { background: #fb7185; }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding: 0.75rem 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-top: 1.5rem;
            user-select: none;
            transition: background 0.2s;
        }

        .section-header:hover {
            background: rgba(0, 0, 0, 0.35);
        }

        .section-header .label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .section-header .count {
            font-size: 0.75rem;
            color: var(--primary);
            font-weight: 600;
        }

        .section-header .chevron {
            color: var(--text-dim);
            font-size: 0.85rem;
            transition: transform 0.2s;
        }

        .section-header .chevron.open {
            transform: rotate(90deg);
        }

        .section-body {
            display: none;
            max-height: 200px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-top: 0.5rem;
            padding: 0.5rem 0;
        }

        .section-body.open {
            display: block;
        }

        .history-entry {
            display: flex;
            align-items: flex-start;
            gap: 0.6rem;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 0.85rem;
        }

        .history-entry:last-child {
            border-bottom: none;
        }

        .history-time {
            color: var(--text-dim);
            font-size: 0.75rem;
            white-space: nowrap;
            min-width: 3.5rem;
            padding-top: 0.05rem;
        }

        .history-text {
            color: var(--text);
            line-height: 1.4;
            word-break: break-word;
        }

        .history-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            flex-shrink: 0;
            margin-top: 0.35rem;
        }

        .history-dot.streaming { background: var(--primary); }
        .history-dot.batch { background: var(--accent); }

        .stt-test-area {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem;
            margin-top: 1rem;
        }

        .stt-result {
            display: none;
            grid-column: span 2;
            padding: 1rem 1.25rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 14px;
            border: 1px solid var(--border);
            font-size: 0.85rem;
        }

        .stt-result.visible {
            display: block;
        }

        .stt-result .row {
            display: flex;
            justify-content: space-between;
            padding: 0.3rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }

        .stt-result .row:last-child {
            border-bottom: none;
        }

        .stt-result .key {
            color: var(--text-dim);
        }

        .stt-result .val {
            color: var(--text);
            text-align: right;
            max-width: 60%;
            word-break: break-word;
        }

        .stt-result .val.success { color: var(--success); }
        .stt-result .val.fail { color: var(--danger); }

        .btn-stt {
            background: linear-gradient(135deg, #a78bfa, #818cf8);
            color: white;
            box-shadow: 0 10px 25px -5px rgba(129, 140, 248, 0.4);
        }

        .btn-stt:hover {
            transform: translateY(-3px);
            filter: brightness(1.1);
            box-shadow: 0 20px 30px -10px rgba(129, 140, 248, 0.6);
        }

        .btn-stt:disabled {
            opacity: 0.5;
            transform: none;
            cursor: not-allowed;
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
                <button onclick="restartHotkey()" id="hkBtn" style="background:none;border:none;color:var(--text-dim);cursor:pointer;font-size:0.7rem;padding:0.25rem 0.5rem;border-radius:6px;margin-left:0.5rem;" title="Reconnect hotkey after login/sleep">⌨️ Reset</button>
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

                <div class="input-group full-width batch-notice" id="llmNotice" style="display:none;padding:0.6rem 1rem;background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.2);border-radius:10px;color:#fbbf24;font-size:0.8rem;text-align:center;">
                    LLM features require <strong>Batch mode</strong>. Switch above to enable.
                </div>

                <div class="input-group" id="llmActionGroup">
                    <label>LLM Post-Process</label>
                    <select id="llmAction" onchange="onLlmActionChange()">
                        <option value="off">Off</option>
                        <option value="grammar">Grammar Fix</option>
                        <option value="translate">Translate</option>
                        <option value="custom">Custom</option>
                    </select>
                </div>

                <div class="input-group" id="llmLangGroup" style="display:none">
                    <label>Translate Language</label>
                    <select id="llmLang" onchange="autoSave()">
                        <option value="Hindi">Hindi</option>
                        <option value="English">English</option>
                        <option value="French">French</option>
                        <option value="Spanish">Spanish</option>
                        <option value="German">German</option>
                        <option value="Japanese">Japanese</option>
                        <option value="Chinese">Chinese</option>
                        <option value="Arabic">Arabic</option>
                    </select>
                </div>

                <div class="input-group" id="llmCustomGroup" style="display:none">
                    <label>Custom Prompt</label>
                    <input type="text" id="llmCustomPrompt" placeholder="e.g. Convert to bullet points" onchange="autoSave()">
                </div>

                <div class="input-group full-width" style="grid-column:span 2;display:flex;gap:1rem;">
                    <label style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;">
                        <input type="checkbox" id="pushToHold" onchange="autoSave()" {% if push_to_hold %}checked{% endif %}> Push-to-Hold
                    </label>
                    <label style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;">
                        <input type="checkbox" id="clipboardMode" onchange="autoSave()" {% if clipboard_mode %}checked{% endif %}> Type into document
                    </label>
                </div>
            </div>

            <div class="controls">
                <button onclick="toggleService()" class="btn-primary" id="toggleBtn">Start Daemon</button>
                <button onclick="toggleRecording()" class="btn-secondary" id="recBtn">Manual Dictate</button>
                <button onclick="toggleMicTest()" class="btn-secondary" id="micTestBtn">Test Mic</button>
            </div>

            <div class="preview-box" id="previewBox" style="display:none;margin-top:1rem;padding:0.75rem 1rem;background:rgba(0,0,0,0.25);border-radius:12px;border:1px solid var(--border);font-size:0.9rem;min-height:1.2rem;">
                <span id="previewText" style="color:var(--primary);"></span>
                <span id="previewCursor" style="animation:blink 1s step-end infinite;">▊</span>
            </div>
            <style>
                @keyframes blink { 50% { opacity: 0; } }
            </style>

            <div class="mic-meter" id="micMeter">
                <div class="meter-header">
                    <span class="meter-label">Microphone Level</span>
                    <div class="meter-info">
                        <span class="meter-db" id="meterDb">-inf dB</span>
                        <span class="meter-timer" id="meterTimer">5s</span>
                    </div>
                </div>
                <div class="meter-track" id="meterTrack">
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                    <div class="meter-bar"></div>
                </div>
            </div>

            <div class="stt-test-area">
                <button onclick="testStt()" class="btn-stt" id="sttTestBtn">Test STT Endpoint</button>
                <span></span>
                <div class="stt-result" id="sttResult">
                    <div class="row"><span class="key">Endpoint</span><span class="val" id="sttEndpointVal"></span></div>
                    <div class="row"><span class="key">Model</span><span class="val" id="sttModelVal"></span></div>
                    <div class="row"><span class="key">Time</span><span class="val" id="sttTimeVal"></span></div>
                    <div class="row"><span class="key">Result</span><span class="val" id="sttResultVal"></span></div>
                </div>
            </div>

            <div class="section-header" onclick="toggleCommands()">
                <span class="label">Voice Commands</span>
                <span><span class="count">13</span> <span class="chevron" id="cmdChevron">▶</span></span>
            </div>
            <div class="section-body" id="cmdBody">
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"new line" / "newline"</span><span style="color:var(--text-dim);">→ line break</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"new paragraph"</span><span style="color:var(--text-dim);">→ double line break</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"period" / "comma" / "?" / "!"</span><span style="color:var(--text-dim);">→ punctuation</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"colon" / "semicolon"</span><span style="color:var(--text-dim);">→ : ;</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"open/close quote"</span><span style="color:var(--text-dim);">→ ""</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"open/close parenthesis"</span><span style="color:var(--text-dim);">→ ( )</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"tab"</span><span style="color:var(--text-dim);">→ tab character</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"delete last word"</span><span style="color:var(--text-dim);">→ 4 backspaces</span></div>
                <div class="history-entry"><span style="color:var(--primary);min-width:10rem;display:inline-block;font-size:0.75rem;">"delete last sentence"</span><span style="color:var(--text-dim);">→ 20 backspaces</span></div>
                <div class="history-entry" style="color:var(--text-dim);font-size:0.75rem;padding-top:0.25rem;border:none;">Say these phrases exactly for them to be recognized.</div>
            </div>

            <div class="section-header" onclick="toggleHistory()">
                <span class="label">Transcription History</span>
                <span>
                    <a href="/export_history?format=txt" style="color:var(--text-dim);font-size:0.75rem;text-decoration:none;margin-right:0.5rem;" title="Export as TXT" onclick="event.stopPropagation()">⬇ TXT</a>
                    <a href="/export_history?format=md" style="color:var(--text-dim);font-size:0.75rem;text-decoration:none;margin-right:0.75rem;" title="Export as Markdown" onclick="event.stopPropagation()">⬇ MD</a>
                    <span class="count" id="historyCount">0</span> <span class="chevron" id="historyChevron">▶</span>
                </span>
            </div>
            <div class="section-body" id="historyBody">
                <div class="history-entry" style="color:var(--text-dim);padding:1rem;text-align:center">No transcriptions yet</div>
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
                const activeIdx = {{ active_device if active_device is not none else -1 }};
                let hadActive = false;
                devices.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.index;
                    opt.text = d.name;
                    opt.dataset.pulseSource = d.pulse_source || '';
                    if (d.index == activeIdx) { opt.selected = true; hadActive = true; }
                    sel.appendChild(opt);
                });
                if (!hadActive && devices.length > 0) {
                    sel.value = devices[0].index;
                    autoSave();
                }
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

        function getLlmInstruction() {
            const action = document.getElementById('llmAction').value;
            if (action === 'translate') return document.getElementById('llmLang').value;
            if (action === 'custom') return document.getElementById('llmCustomPrompt').value;
            return '';
        }

        function onLlmActionChange() {
            const action = document.getElementById('llmAction').value;
            document.getElementById('llmLangGroup').style.display = action === 'translate' ? '' : 'none';
            document.getElementById('llmCustomGroup').style.display = action === 'custom' ? '' : 'none';
            autoSave();
        }

        async function autoSave() {
            const devSelect = document.getElementById('deviceSelect');
            const devOpt = devSelect.selectedOptions[0];
            const pulseSource = devOpt ? devOpt.dataset.pulsesource || '' : '';
            const settings = {
                stt_endpoint: document.getElementById('sttEndpoint').value,
                stt_model: document.getElementById('sttModel').value,
                hotkey: document.getElementById('hotkey').value,
                streaming: document.getElementById('streamingMode').value === "1",
                device_index: devSelect.value,
                pulse_source: pulseSource,
                silence_threshold: document.getElementById('silenceThreshold').value,
                beep_enabled: document.getElementById('beepEnabled').value === "1",
                llm_action: document.getElementById('llmAction').value,
                llm_instruction: getLlmInstruction(),
                push_to_hold: document.getElementById('pushToHold').checked,
                clipboard_mode: document.getElementById('clipboardMode').checked,
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

        async function restartHotkey() {
            const btn = document.getElementById('hkBtn');
            btn.innerText = '⌨️ ...';
            await fetch('/restart_hotkey', {method: 'POST'});
            setTimeout(() => btn.innerText = '⌨️ Reset', 1000);
        }

        let micTestActive = false;
        let micTestStartTime = null;
        let micTestInterval = null;

        async function toggleMicTest() {
            if (micTestActive) {
                await stopMicTest();
            } else {
                await startMicTest();
            }
        }

        async function startMicTest() {
            await fetch('/test_mic/start', {method: 'POST'});
            micTestActive = true;
            micTestStartTime = Date.now();
            document.getElementById('micTestBtn').innerText = 'Stop Test';
            document.getElementById('micTestBtn').className = 'btn-primary';
            document.getElementById('micMeter').classList.add('visible');
            micTestInterval = setInterval(updateMeter, 80);
        }

        async function stopMicTest() {
            await fetch('/test_mic/stop', {method: 'POST'});
            micTestActive = false;
            if (micTestInterval) clearInterval(micTestInterval);
            micTestInterval = null;
            document.getElementById('micTestBtn').innerText = 'Test Mic';
            document.getElementById('micTestBtn').className = 'btn-secondary';
            document.getElementById('micMeter').classList.remove('visible');
        }

        async function updateMeter() {
            try {
                const res = await fetch('/test_mic/level');
                const data = await res.json();
                let level = parseFloat(data.level) || 0;
                level = Math.min(1, Math.max(0, level));
                const bars = document.querySelectorAll('.meter-bar');
                const n = bars.length;
                const active = Math.round(level * n);
                bars.forEach((bar, i) => {
                    bar.classList.toggle('lit', i < active);
                    const pct = ((i + 1) / n) * 100;
                    bar.style.height = Math.max(4, pct * 0.7) + '%';
                });

                const dbEl = document.getElementById('meterDb');
                if (level > 0.001) {
                    const db = 20 * Math.log10(level);
                    const dbStr = db.toFixed(1);
                    dbEl.innerText = dbStr + ' dB';
                    dbEl.className = 'meter-db' + (db > -12 ? ' high' : db > -24 ? ' mid' : ' low');
                } else {
                    dbEl.innerText = '-inf dB';
                    dbEl.className = 'meter-db low';
                }

                const elapsed = (Date.now() - micTestStartTime) / 1000;
                const remaining = Math.max(0, 5 - elapsed);
                document.getElementById('meterTimer').innerText = Math.ceil(remaining) + 's';
                if (remaining <= 0) await stopMicTest();
            } catch (e) {}
        }

        let historyOpen = false;
        let commandsOpen = false;

        function toggleCommands() {
            commandsOpen = !commandsOpen;
            document.getElementById('cmdBody').classList.toggle('open', commandsOpen);
            document.getElementById('cmdChevron').classList.toggle('open', commandsOpen);
        }

        function toggleHistory() {
            historyOpen = !historyOpen;
            document.getElementById('historyBody').classList.toggle('open', historyOpen);
            document.getElementById('historyChevron').classList.toggle('open', historyOpen);
        }

        async function updateHistory() {
            try {
                const res = await fetch('/history');
                const entries = await res.json();
                document.getElementById('historyCount').innerText = entries.length;
                const body = document.getElementById('historyBody');
                if (!entries.length) {
                    body.innerHTML = '<div class="history-entry" style="color:var(--text-dim);padding:1rem;text-align:center">No transcriptions yet</div>';
                    return;
                }
                body.innerHTML = entries.slice().reverse().map(e =>
                    '<div class="history-entry">' +
                    '<span class="history-dot ' + e.source + '"></span>' +
                    '<span class="history-time">' + e.time + '</span>' +
                    '<span class="history-text">' + escapeHtml(e.text) + '</span>' +
                    '</div>'
                ).join('');
            } catch (e) {}
        }

        function escapeHtml(str) {
            const d = document.createElement('div');
            d.textContent = str;
            return d.innerHTML;
        }

        async function testStt() {
            const btn = document.getElementById('sttTestBtn');
            btn.disabled = true;
            btn.innerText = 'Recording for 2s...';
            const resultEl = document.getElementById('sttResult');
            resultEl.classList.remove('visible');
            try {
                const res = await fetch('/test_stt', {method: 'POST'});
                const data = await res.json();
                document.getElementById('sttEndpointVal').innerText = data.endpoint;
                document.getElementById('sttModelVal').innerText = data.model;
                if (data.success) {
                    document.getElementById('sttTimeVal').innerHTML = '<span class="val success">' + data.elapsed + 's</span>';
                    document.getElementById('sttResultVal').innerHTML = '<span class="val success">' + escapeHtml(data.text) + '</span>';
                } else {
                    document.getElementById('sttTimeVal').innerHTML = '<span class="val fail">—</span>';
                    document.getElementById('sttResultVal').innerHTML = '<span class="val fail">' + escapeHtml(data.error) + '</span>';
                }
                resultEl.classList.add('visible');
            } catch (e) {
                document.getElementById('sttEndpointVal').innerText = '—';
                document.getElementById('sttModelVal').innerText = '—';
                document.getElementById('sttTimeVal').innerHTML = '<span class="val fail">—</span>';
                document.getElementById('sttResultVal').innerHTML = '<span class="val fail">' + e.message + '</span>';
                resultEl.classList.add('visible');
            }
            btn.disabled = false;
            btn.innerText = 'Test STT Endpoint';
        }

        async function loadLlmConfig() {
            try {
                const res = await fetch('/llm_config');
                const data = await res.json();
                document.getElementById('llmAction').value = data.llm_action || 'off';
                document.getElementById('pushToHold').checked = data.push_to_hold || false;
                document.getElementById('clipboardMode').checked = data.clipboard_mode !== false;
                const langSel = document.getElementById('llmLang');
                if (data.llm_instruction && langSel.querySelector('option[value="' + data.llm_instruction + '"]')) {
                    langSel.value = data.llm_instruction;
                }
                document.getElementById('llmCustomPrompt').value = (data.llm_action === 'custom' ? data.llm_instruction : '') || '';
                onLlmActionChange();
            } catch (e) {}
        }

        let lastPreviewText = '';

        async function updatePreview() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                const box = document.getElementById('previewBox');
                const el = document.getElementById('previewText');
                if (data.is_recording && data.last_text && data.last_text !== lastPreviewText) {
                    box.style.display = 'block';
                    el.innerText = data.last_text;
                    lastPreviewText = data.last_text;
                    box.scrollIntoView({behavior: 'smooth', block: 'nearest'});
                }
            } catch (e) {}
        }

        loadDevices();
        loadLlmConfig();
        setInterval(updateStatus, 1000);
        setInterval(updateHistory, 2000);
        setInterval(updatePreview, 500);
        updateStatus();
        updateHistory();
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
        push_to_hold=dict_app.push_to_hold,
        clipboard_mode=dict_app.clipboard_mode,
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
        pulse_source=data.get("pulse_source"),
        push_to_hold=data.get("push_to_hold"),
        clipboard_mode=data.get("clipboard_mode"),
    )
    # Apply non-persisted LLM state immediately
    llm_action = data.get("llm_action")
    if llm_action is not None:
        dict_app.llm_action = llm_action
    llm_instruction = data.get("llm_instruction")
    if llm_instruction is not None:
        dict_app.llm_instruction = llm_instruction
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


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/test_mic/start", methods=["POST"])
def start_mic_test():
    dict_app.start_mic_test()
    return jsonify({"success": True})


@app.route("/test_mic/stop", methods=["POST"])
def stop_mic_test():
    dict_app.stop_mic_test()
    return jsonify({"success": True})


@app.route("/test_mic/level")
def mic_test_level():
    return jsonify({"level": dict_app.get_mic_test_level()})


@app.route("/history")
def get_history():
    return jsonify(dict_app.transcription_history)


@app.route("/test_stt", methods=["POST"])
def test_stt():
    return jsonify(dict_app.test_stt_endpoint())


@app.route("/llm_config", methods=["GET", "POST"])
def llm_config():
    if request.method == "POST":
        data = request.json
        import voice_dictation as vd
        vd.OPENAI_BASE_URL = data.get("openai_base_url", vd.OPENAI_BASE_URL)
        vd.OPENAI_CHAT_MODEL_ID = data.get("openai_chat_model_id", vd.OPENAI_CHAT_MODEL_ID)
        vd.OPENAI_API_KEY = data.get("openai_api_key", vd.OPENAI_API_KEY)
        dict_app.llm_action = data.get("llm_action", dict_app.llm_action)
        dict_app.llm_instruction = data.get("llm_instruction", dict_app.llm_instruction)
        dict_app.push_to_hold = data.get("push_to_hold", dict_app.push_to_hold)
        dict_app.clipboard_mode = data.get("clipboard_mode", dict_app.clipboard_mode)
        return jsonify({"success": True})
    import voice_dictation as vd
    return jsonify({
        "openai_base_url": vd.OPENAI_BASE_URL,
        "openai_chat_model_id": vd.OPENAI_CHAT_MODEL_ID,
        "openai_api_key": vd.OPENAI_API_KEY,
        "llm_action": dict_app.llm_action,
        "llm_instruction": dict_app.llm_instruction,
        "push_to_hold": dict_app.push_to_hold,
        "clipboard_mode": dict_app.clipboard_mode,
    })


@app.route("/export_history")
def export_history():
    fmt = request.args.get("format", "txt")
    lines = [f"[{e['time']}] {e['text']}" for e in dict_app.transcription_history]
    text = "\n".join(lines) if lines else "No transcriptions yet."
    ext = "txt"
    if fmt == "md":
        text = "# Transcription History\n\n" + "\n".join(
            f"- **{e['time']}** {e['text']}" for e in dict_app.transcription_history
        )
        ext = "md"
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename=transcriptions.{ext}"},
    )


@app.route("/restart_hotkey", methods=["POST"])
def restart_hotkey():
    dict_app.restart_hotkey()
    return jsonify({"success": True})


if __name__ == "__main__":
    dict_app.start_service()
    try:
        _tray_env = os.environ.copy()
        for _k in ("DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS"):
            if _k not in _tray_env:
                _tray_env[_k] = ""
        subprocess.Popen(
            ["/usr/bin/python3", os.path.join(os.path.dirname(__file__), "tray.py")],
            env=_tray_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    app.run(host=_ui_host, port=_ui_port)
