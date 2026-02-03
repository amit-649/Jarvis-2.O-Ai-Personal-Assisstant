"""
Jarvis 2.0 - FULLY AUTONOMOUS
Complete autonomous operation with:
- Close apps
- YouTube/Google search
- Proper focus management after speech
- More natural command detection
"""
import asyncio
import os
import sys
import subprocess
import webbrowser
import re
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Rich console
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    console = Console()
except ImportError:
    console = None

# Core dependencies
try:
    from google import genai
    from google.genai import types
    import pyaudio
except ImportError as e:
    print(f"Missing: {e}")
    sys.exit(1)

# Optional dependencies
try:
    import requests
except ImportError:
    requests = None

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    import win32gui
    import win32con
    import win32process
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("  ⚠️  Win32 not available - install with: pip install pywin32 psutil")

# Import command modules
from app.commands import apps, system, monitoring, files, approval

# Load predefined apps
APPS_FILE = Path(__file__).parent.parent / "apps.json"
APPS = {}
if APPS_FILE.exists():
    try:
        with open(APPS_FILE, encoding="utf-8") as f:
            data = json.load(f)
            for k, v in data.items():
                if not k.startswith("_"):
                    APPS[k.lower()] = v
        print(f"  Loaded {len(APPS)} predefined apps")
    except Exception as e:
        print(f"  Warning: Could not load apps.json: {e}")

# Audio config
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16000
RECV_RATE = 24000
CHUNK = 1024
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

# CRITICAL: Track state
LAST_OPENED_APP = {"name": None, "window_title": None, "hwnd": None, "timestamp": None}
SPEECH_IN_PROGRESS = False
PENDING_COMMANDS = []

# App name to window title mapping
APP_WINDOW_TITLES = {
    "notepad": "Notepad",
    "calculator": "Calculator",
    "chrome": "Chrome",
    "firefox": "Firefox",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "cmd": "Command Prompt",
    "terminal": "Windows Terminal",
    "explorer": "File Explorer",
    "spotify": "Spotify",
}


PROMPT = f"""You are Jarvis, Master Amit's AI.
IDENTITY: Autonomous AI Assistant.
CURRENT TIME: {datetime.now().strftime('%I:%M %p')}

CRITICAL RULES:
1. NO INTERNAL MONOLOGUE. Never explain what you are doing.
2. NO FILLER. Do not say "I am now...", "Initiating...", "Tasked with...".
3. BE ROBOTIC AND PRECISE.
4. For typing: wrap text in triple quotes: "Typing '''text'''"
5. Ask for confirmation only for dangerous actions.

RESPONSE FORMAT:
- Open app: "Opening [App]"
- Close app: "Closing [App]"
- Type text: "Typing '''exact text'''"
- Search YouTube: "Searching YouTube for [query]"
- Search Google: "Searching for [query]"
- Play song: "Playing [song name]"
- Exit: "Goodbye Master"

EXAMPLES:
User: Open notepad and write hello world
Jarvis: Opening Notepad
Jarvis: Typing '''hello world'''

User: Search YouTube for hello song
Jarvis: Searching YouTube for hello song

User: Close Chrome
Jarvis: Closing Chrome
"""

# State
audio_out = asyncio.Queue()
audio_in = asyncio.Queue(maxsize=5)
mic = None
pya = None
exiting = False
SS_DIR = Path.home() / "Pictures" / "Jarvis_Screenshots"


def log(who: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    if console:
        if who == "Jarvis":
            console.print(f"  [dim]{ts}[/] [cyan]▶ Jarvis:[/] {msg}")
        elif who == "Action":
            console.print(f"  [dim]{ts}[/] [yellow]⚡ Action:[/] {msg}")
        elif who == "Focus":
            console.print(f"  [dim]{ts}[/] [magenta]👁 Focus:[/] {msg}")
        else:
            console.print(f"  [dim]{ts}[/] [green]◀ {who}:[/] {msg}")
    else:
        print(f"  [{ts}] {who}: {msg}")


def find_window_by_title(title_contains: str):
    """Find window handle by partial title match."""
    if not WIN32_AVAILABLE:
        return None
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_contains.lower() in window_title.lower():
                windows.append(hwnd)
        return True
    
    windows = []
    try:
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None
    except:
        return None


def focus_window(window_title: str, max_attempts: int = 3):
    """Focus a window with retry logic."""
    if not WIN32_AVAILABLE:
        log("Focus", "Win32 not available")
        return False
    
    for attempt in range(max_attempts):
        hwnd = find_window_by_title(window_title)
        
        if hwnd:
            try:
                # Restore if minimized
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Bring to foreground
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                
                # Verify
                current = win32gui.GetForegroundWindow()
                if current == hwnd:
                    log("Focus", f"✓ Focused: {window_title}")
                    return True
                    
            except Exception as e:
                log("Focus", f"Attempt {attempt + 1} failed: {e}")
        
        time.sleep(0.3)
    
    log("Focus", f"✗ Could not focus: {window_title}")
    return False


def close_window_by_title(title_contains: str) -> tuple[bool, str]:
    """Close a window by title."""
    if not WIN32_AVAILABLE:
        return False, "Win32 not available"
    
    hwnd = find_window_by_title(title_contains)
    if hwnd:
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            time.sleep(0.5)
            return True, f"Closed: {title_contains}"
        except Exception as e:
            return False, f"Failed to close: {e}"
    return False, f"Window not found: {title_contains}"


def close_process_by_name(process_name: str) -> tuple[bool, str]:
    """Force close a process by name."""
    if not WIN32_AVAILABLE:
        try:
            subprocess.run(f"taskkill /F /IM {process_name}.exe", shell=True, capture_output=True)
            return True, f"Killed process: {process_name}"
        except:
            return False, f"Failed to kill: {process_name}"
    
    try:
        killed = False
        for proc in psutil.process_iter(['name']):
            if process_name.lower() in proc.info['name'].lower():
                proc.kill()
                killed = True
        
        if killed:
            return True, f"Killed process: {process_name}"
        return False, f"Process not found: {process_name}"
    except Exception as e:
        return False, f"Failed: {e}"


def type_text_safe(text: str, target_window: str = None):
    """Type text with automatic focus management."""
    if not pyautogui:
        return False, "PyAutoGUI not available"
    
    # Focus target window if specified
    if target_window:
        if not focus_window(target_window):
            return False, f"Could not focus {target_window}"
    
    # Extra safety delay
    time.sleep(0.3)
    
    try:
        pyautogui.write(text, interval=0.025)
        return True, f"Typed: {text[:30]}{'...' if len(text) > 30 else ''}"
    except Exception as e:
        return False, f"Typing failed: {e}"


def track_opened_app(app_name: str):
    """Track opened app for later operations."""
    window_title = APP_WINDOW_TITLES.get(app_name.lower(), app_name)
    LAST_OPENED_APP["name"] = app_name
    LAST_OPENED_APP["window_title"] = window_title
    LAST_OPENED_APP["timestamp"] = time.time()
    log("Focus", f"Tracking: {app_name} → {window_title}")


def execute_commands(text: str):
    """Autonomous command execution."""
    global SPEECH_IN_PROGRESS
    
    t = text.lower()
    
    # === CLOSE APPS ===
    if any(w in t for w in ["closing", "close", "exit", "quit", "kill"]):
        # Extract app name
        patterns = [
            r'(?:closing|close|exit|quit|kill)\s+(?:the\s+)?(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, t)
            if match:
                app_name = match.group(1).strip()
                
                # Try window close first
                window_title = APP_WINDOW_TITLES.get(app_name.lower(), app_name)
                success, msg = close_window_by_title(window_title)
                
                if not success:
                    # Fallback: kill process
                    success, msg = close_process_by_name(app_name)
                
                log("Action", msg)
                
                # Clear tracking if we closed the tracked app
                if LAST_OPENED_APP["name"] and app_name.lower() in LAST_OPENED_APP["name"].lower():
                    LAST_OPENED_APP["name"] = None
                    LAST_OPENED_APP["window_title"] = None
                
                return True
    
    # === YOUTUBE SEARCH ===
    if "youtube" in t and any(w in t for w in ["search", "play", "find", "look"]):
        patterns = [
            r'(?:search|searching|play|playing|find|look)\s+(?:youtube\s+for|on\s+youtube\s+for|for)\s+(.+?)(?:\.|$)',
            r'youtube\s+(?:search|for)\s+(.+?)(?:\.|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, t)
            if match:
                query = match.group(1).strip()
                if query and len(query) > 2:
                    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
                    webbrowser.open(url)
                    log("Action", f"YouTube search: {query}")
                    return True
    
    # === GOOGLE SEARCH (not YouTube) ===
    if "search" in t and "youtube" not in t:
        patterns = [
            r'(?:searching|search)\s+(?:for|google)\s+["\']?(.+?)(?:["\']|$|\.)',
            r'google\s+["\']?(.+?)(?:["\']|$|\.)',
        ]
        for pattern in patterns:
            match = re.search(pattern, t)
            if match:
                query = match.group(1).strip()
                if query and len(query) > 2:
                    url = f"https://www.google.com/search?q={quote_plus(query)}"
                    webbrowser.open(url)
                    log("Action", f"Google search: {query}")
                    return True
    
    # === TYPING TEXT ===
    triple_quote_match = re.search(r"'''(.*?)'''", text, re.DOTALL)
    if triple_quote_match:
        text_to_type = triple_quote_match.group(1)
        log("Action", f"🔍 Typing: '{text_to_type[:50]}'")
        
        # CRITICAL: Wait for speech to finish
        if SPEECH_IN_PROGRESS:
            log("Focus", "⏳ Waiting for speech to finish...")
            # This will be queued and executed after speech
            PENDING_COMMANDS.append(("type", text_to_type))
            return True
        
        # Execute immediately if not speaking
        target_window = LAST_OPENED_APP["window_title"] if LAST_OPENED_APP["name"] else None
        success, msg = type_text_safe(text_to_type, target_window)
        log("Action", msg)
        return True
    
    # Fallback typing patterns
    if any(w in t for w in ["typing", "writing", "type", "write"]):
        patterns = [
            r'typing\s+["\'](.+?)["\']',
            r'writing\s+["\'](.+?)["\']',
            r'write\s+["\'](.+?)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, t, re.IGNORECASE)
            if match:
                text_to_type = match.group(1)
                log("Action", f"🔍 Typing (fallback): '{text_to_type[:50]}'")
                
                if SPEECH_IN_PROGRESS:
                    PENDING_COMMANDS.append(("type", text_to_type))
                    return True
                
                target_window = LAST_OPENED_APP["window_title"] if LAST_OPENED_APP["name"] else None
                success, msg = type_text_safe(text_to_type, target_window)
                log("Action", msg)
                return True
    
    # === OPEN APPS ===
    if any(w in t for w in ["opening", "launching", "starting", "open", "opened", "start", "launch"]):
        
        # Predefined apps
        for app_name, cmd in APPS.items():
            if app_name in t:
                try:
                    if cmd.startswith("start http"):
                        webbrowser.open(cmd.replace("start ", ""))
                        log("Action", f"✓ Opened {app_name} (browser)")
                    else:
                        subprocess.Popen(cmd, shell=True)
                        log("Action", f"✓ Opened {app_name}")
                        track_opened_app(app_name)
                        time.sleep(3.5)  # Wait for app to fully open
                    return True
                except Exception as e:
                    log("Action", f"✗ {e}")
                    return True
        
        # Dynamic app search
        match = re.search(r'(?:opening|starting|launching|open|opened|start|launch)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', t)
        if match:
            app_name = match.group(1).strip()
            success, msg = apps.launch_app(app_name)
            log("Action", msg)
            if success:
                track_opened_app(app_name)
                time.sleep(3.5)
            return True
    
    # === SYSTEM CONTROL ===
    if ("shutting down" in t or "shutdown" in t) and any(w in t for w in ["system", "computer", "pc", "machine"]):
        if approval.ask_approval(f"Shutdown the system"):
            success, msg = system.shutdown_system()
            log("Action", msg)
            return True
        else:
            log("Action", "Shutdown cancelled")
            return True
    
    if ("restarting" in t or "restart" in t) and any(w in t for w in ["system", "computer", "pc", "machine"]):
        if approval.ask_approval(f"Restart the system"):
            success, msg = system.restart_system()
            log("Action", msg)
            return True
        else:
            log("Action", "Restart cancelled")
            return True
    
    if "locking" in t or "lock screen" in t:
        success, msg = system.lock_screen()
        log("Action", msg)
        return True
    
    if "sleep" in t and ("going to" in t or "entering" in t):
        success, msg = system.sleep_system()
        log("Action", msg)
        return True
    
    # === MONITORING ===
    if "cpu" in t and ("checking" in t or "usage" in t or "check" in t):
        success, msg = monitoring.get_cpu_usage()
        log("Action", msg)
        return True
    
    if "ram" in t or "memory" in t:
        success, msg = monitoring.get_ram_usage()
        log("Action", msg)
        return True
    
    if "disk" in t and ("space" in t or "usage" in t):
        success, msg = monitoring.get_disk_usage()
        log("Action", msg)
        return True
    
    if "battery" in t:
        success, msg = monitoring.get_battery_status()
        log("Action", msg)
        return True
    
    # === SCREENSHOT ===
    if "screenshot" in t:
        if pyautogui:
            try:
                SS_DIR.mkdir(parents=True, exist_ok=True)
                fn = SS_DIR / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                pyautogui.screenshot().save(str(fn))
                log("Action", f"✓ Screenshot: {fn.name}")
            except Exception as e:
                log("Action", f"✗ {e}")
        return True
    
    # === VOLUME ===
    if pyautogui and ("volume" in t or "louder" in t or "quieter" in t):
        if "up" in t or "louder" in t or "increas" in t or "rais" in t:
            for _ in range(3):
                pyautogui.press('volumeup')
            log("Action", "✓ Volume UP")
            return True
        if "down" in t or "quieter" in t or "decreas" in t or "lower" in t:
            for _ in range(3):
                pyautogui.press('volumedown')
            log("Action", "✓ Volume DOWN")
            return True
        if "mute" in t or "muting" in t:
            pyautogui.press('volumemute')
            log("Action", "✓ Mute toggled")
            return True
    
    # === WEATHER ===
    if "weather" in t and requests:
        match = re.search(r'weather\s+(?:in|for|of)\s+(\w+)', t)
        if match:
            city = match.group(1)
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if api_key:
                try:
                    r = requests.get(
                        f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric",
                        timeout=5
                    )
                    if r.ok:
                        d = r.json()
                        log("Action", f"Weather: {city} - {d['main']['temp']}°C, {d['weather'][0]['description']}")
                except:
                    pass
            return True
    
    return False


def process_pending_commands():
    """Execute commands that were queued during speech."""
    global PENDING_COMMANDS
    
    if not PENDING_COMMANDS:
        return
    
    log("Focus", f"📋 Processing {len(PENDING_COMMANDS)} pending commands")
    
    for cmd_type, data in PENDING_COMMANDS:
        if cmd_type == "type":
            target_window = LAST_OPENED_APP["window_title"] if LAST_OPENED_APP["name"] else None
            success, msg = type_text_safe(data, target_window)
            log("Action", f"⏭️  {msg}")
    
    PENDING_COMMANDS = []


def check_exit(text: str) -> bool:
    t = text.lower()
    exit_words = [
        "goodbye", "bye", "farewell", "rest well", "take rest", 
        "shutting down", "going offline", "shut down", "signing off",
        "good night master", "see you later"
    ]
    return any(word in t for word in exit_words)


def banner():
    if not console:
        print("\n  JARVIS 2.0 - FULLY AUTONOMOUS\n")
        return
    console.print(Panel(
        Text("""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝""", style="bold cyan"),
        title="[magenta]◈ JARVIS 2.0 - FULLY AUTONOMOUS ◈[/]",
        subtitle=f"[dim]{datetime.now().strftime('%H:%M:%S')}[/]",
        border_style="cyan", box=box.DOUBLE
    ))


async def listen():
    global mic
    try:
        info = pya.get_default_input_device_info()
        mic = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_RATE,
            input=True, input_device_index=info["index"], frames_per_buffer=CHUNK
        )
        while not exiting:
            data = await asyncio.to_thread(mic.read, CHUNK, exception_on_overflow=False)
            await audio_in.put({"data": data, "mime_type": "audio/pcm"})
    except Exception as e:
        print(f"  ❌ Audio Input Error: {e}")


async def send(session):
    while not exiting:
        msg = await audio_in.get()
        await session.send_realtime_input(audio=msg)


async def receive(session):
    global exiting, SPEECH_IN_PROGRESS
    
    while not exiting:
        async for resp in session.receive():
            if resp.server_content and resp.server_content.model_turn:
                for part in resp.server_content.model_turn.parts:
                    # Audio output
                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                        SPEECH_IN_PROGRESS = True
                        audio_out.put_nowait(part.inline_data.data)
                    
                    # Text output (commands)
                    if hasattr(part, 'text') and part.text:
                        txt = part.text.strip()
                        
                        # Skip markdown
                        is_markdown = (
                            txt.startswith('**') and txt.endswith('**') or
                            txt.startswith('###') or
                            txt.startswith('##') and len(txt) < 50 or
                            txt.startswith('*') and txt.endswith('*') and len(txt) < 30
                        )
                        
                        if txt and not is_markdown:
                            log("Jarvis", txt)
                            execute_commands(txt)
                            
                            if check_exit(txt):
                                await asyncio.sleep(2)
                                exiting = True
            
            # Check if turn is complete (speech finished)
            if resp.server_content and resp.server_content.turn_complete:
                SPEECH_IN_PROGRESS = False
                # Process any pending commands
                await asyncio.to_thread(process_pending_commands)


async def play():
    global exiting
    try:
        out_info = pya.get_default_output_device_info()
        spk = await asyncio.to_thread(
            pya.open, 
            format=FORMAT, 
            channels=CHANNELS, 
            rate=RECV_RATE, 
            output=True,
            output_device_index=out_info["index"]
        )
        while not exiting:
            try:
                data = await asyncio.wait_for(audio_out.get(), timeout=0.5)
                await asyncio.to_thread(spk.write, data)
            except asyncio.TimeoutError:
                pass
        spk.close()
    except OSError as e:
        if console:
            console.print(f"  [yellow]⚠ Audio output unavailable[/]")
        while not exiting:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"  ❌ Audio Output Error: {e}")


async def main():
    global pya, exiting
    
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("  ❌ GEMINI_API_KEY not set in .env")
        return
    
    banner()
    pya = pyaudio.PyAudio()
    
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=PROMPT,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
            )
        )
    )
    
    if console:
        console.print("\n  [yellow]◈[/] Connecting...")
    else:
        print("  Connecting...")
    
    try:
        async with genai.Client(api_key=key).aio.live.connect(model=MODEL, config=config) as session:
            if console:
                console.print("  [green]◈[/] Fully Autonomous Mode Active!\n")
            else:
                print("  Fully Autonomous!")
            
            async with asyncio.TaskGroup() as tg:
                tg.create_task(send(session))
                tg.create_task(listen())
                tg.create_task(receive(session))
                tg.create_task(play())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        if mic:
            mic.close()
        pya.terminate()
        if console:
            console.print(Panel("[cyan]◈ OFFLINE ◈[/]", border_style="magenta"))


if __name__ == "__main__":
    print("\n  Starting Jarvis - Fully Autonomous Mode...\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Stopped.")
