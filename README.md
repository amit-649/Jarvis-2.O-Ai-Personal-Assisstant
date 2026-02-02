# Jarvis 2.0 - IRL Voice Assistant

A modular, local-first voice assistant for Windows.

## Features
- 🎤 Wake word detection ("Hey Jarvis")
- 🗣️ Natural speech recognition (Faster-Whisper)
- 🧠 LLM-powered brain (Gemini Flash)
- 🔧 Extensible tool system
- 🔊 Natural TTS (Edge-TTS)

## Quick Start

### 1. Prerequisites
- Python 3.11+
- A microphone

### 2. Installation

```bash
# Clone/navigate to this directory
cd "Jarvis 2.0"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your API keys:
# - GEMINI_API_KEY (get from https://aistudio.google.com/app/apikey)
# - OPENWEATHER_API_KEY (get from https://openweathermap.org/)
```

### 4. Run

```bash
python -m app.main
# Or use the batch file:
run.bat
```

## Usage

1. Say **"Hey Jarvis"** to wake the assistant
2. Speak your command (e.g., "What's the weather like?")
3. Listen to the response

### Push-to-Talk Mode
Press and hold **SPACE** to speak without wake word.

## Project Structure

```
app/
├── main.py          # Entry point & main loop
├── config.py        # Configuration management
├── core/
│   ├── audio.py     # Microphone & wake word
│   └── brain.py     # LLM interface
├── services/
│   ├── stt.py       # Speech-to-Text
│   └── tts.py       # Text-to-Speech
├── tools/
│   ├── registry.py  # Tool decorator & manager
│   └── basic.py     # Built-in tools
└── utils/
    └── logger.py    # Logging setup
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_time` | Current time and date |
| `get_weather` | Weather for a city |
| `set_timer` | Set a countdown timer |
| `add_note` | Save a note to file |
| `open_app` | Open an application |

## Security

- Sensitive commands require confirmation
- All API keys stored in `.env` (never committed)
- Audit logging enabled by default

## License
MIT
