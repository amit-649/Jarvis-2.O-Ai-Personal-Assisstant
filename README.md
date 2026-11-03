<div align="center">

# 🎙️ Jarvis 2.0 — Autonomous IRL Voice Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Brain-Gemini_Flash_Live_Audio-8E75B2?style=flat-square&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Audio-PyAudio_Streaming-38BDF8?style=flat-square" />
  <img src="https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

**A modular, local-first autonomous voice assistant engineered with low-latency bidirectional Gemini native audio streaming and Windows automation tooling.**

</div>

---

## ⚡ Core Architecture

```text
       🎤 User Speech
             │
             ▼
    ┌─────────────────┐
    │  PyAudio Stream │ (16kHz PCM Audio Chunks)
    └────────┬────────┘
             │
             ▼
  ┌──────────────────────┐
  │ Google GenAI SDK     │ (Bidirectional WebSocket)
  │ Gemini Flash Live    │
  └──────────┬───────────┘
             │
             ├──────────────────────────┐
             ▼                          ▼
     🔊 Real-Time Voice        🧠 Tool & Command Router
    (24kHz Audio Response)              │
                                        ├── 🚀 Apps & Window Management
                                        ├── ⚙️ System Commands & Monitor
                                        ├── 📁 File & Note Management
                                        └── 🛡️ Approval & Safety Guardrails
```

---

## ✨ Features

- **Bidirectional Native Audio Streaming**: Direct real-time audio interchange using Google Gemini Flash native audio preview model via the official `google-genai` SDK.
- **Hands-Free Wake Word & Push-to-Talk**: Say *"Hey Jarvis"* to wake the assistant or hold **SPACE** for instant push-to-talk.
- **Deep Windows App Integration**: Launches, closes, and focuses applications (`notepad`, `calculator`, `chrome`, etc.) using native Win32 window handles.
- **Extensible Tool Registry**: Built-in tools for weather inquiries, timers, note-taking, and system telemetry monitoring.
- **Safety & Approval Protocols**: Dangerous commands require explicit user verification before execution.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: 3.11 or later
- **OS**: Windows 10 / 11
- Working **Microphone** & **Speakers**

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/amit-649/Jarvis-2.O-Ai-Personal-Assisstant.git
cd Jarvis-2.O-Ai-Personal-Assisstant

# Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment configuration:
```bash
copy .env.example .env
```

Open `.env` and configure your API credentials:
```env
GEMINI_API_KEY="your_google_ai_studio_api_key_here"
OPENWEATHER_API_KEY="your_openweather_api_key_here"  # Optional: for weather tool
```
> *Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).*

### 4. Run Jarvis

```bash
# Direct Python execution
python -m app.main

# Or double-click the bundled launcher
run.bat
```

---

## 🛠️ Tool Catalog

| Tool Command | Module | Functionality |
| :--- | :--- | :--- |
| `open_app` / `close_app` | `commands.apps` | Launches or terminates Windows applications with window focus restoration |
| `get_weather` | `commands.system` | Fetches live meteorological conditions for any global city |
| `get_time` | `commands.system` | Reports localized current time and date |
| `set_timer` | `commands.automation` | Spawns a background countdown timer |
| `add_note` | `commands.files` | Appends persistent notes to local disk storage |
| `system_stats` | `commands.monitoring` | Reports CPU, Memory, and battery utilization metrics |

---

## 🛡️ Security & Privacy

- **Local Secrets**: All credentials reside solely inside your local `.env` and are strictly ignored by `.gitignore`.
- **Destructive Command Approvals**: File deletion and system shutdown commands require explicit audible confirmation.
- **Audit Logging**: Interactions are timestamped and logged locally for inspection.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
