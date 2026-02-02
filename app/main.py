"""
Jarvis 2.0 - Autonomous AI Assistant
Full system control with approval system.
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

# Import command modules
from app.commands import apps, system, automation, monitoring, files, approval

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

def get_greeting():
    h = datetime.now().hour
    if 5 <= h < 12: return "Good morning"
    if 12 <= h < 17: return "Good afternoon"
    if 17 <= h < 21: return "Good evening"
    return "Good night"

PROMPT = f"""You are Jarvis, Master Amit's AI.
IDENTITY: Autonomous AI Assistant.
CURRENT TIME: {datetime.now().strftime('%I:%M %p')}

CRITICAL RULES (FAILING THESE CAUSES SYSTEM ERROR):
1. NO INTERNAL MONOLOGUE. Never explain what you are doing.
2. NO FILLER. Do not say "I am now...", "Initiating...", "Tasked with...".
3. BE ROBOTIC AND PRECISE.
4. FOR TYPING: You MUST wrap the text in TRIPLE QUOTES.
   Example: "Typing '''Hello World'''"

RESPONSE FORMAT:
- To open apps: "Opening [App Name]"
- To type: "Typing '''[Exact Text]'''"
- To search: "Searching for [Query]"
- To sleep: "Goodbye Master"

USER: Write a python hello world script
JARVIS: Typing '''print("Hello World")'''
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
        else:
            console.print(f"  [dim]{ts}[/] [green]◀ {who}:[/] {msg}")
    else:
        print(f"  [{ts}] {who}: {msg}")


def execute_commands(text: str):
    """Autonomous command execution with approval system."""
    t = text.lower()
    
    # === TYPING TEXT ===
    # Fix: Look for triple quotes first (Highest Priority/Precision)
    triple_quote_match = re.search(r"'''(.*?)'''", t, re.DOTALL)
    if triple_quote_match:
        text_to_type = triple_quote_match.group(1)
        time.sleep(1) # Short delay to ensure focus
        success, msg = automation.type_text(text_to_type)
        log("Action", msg)
        return True

    # Fallback: Old logic (only if no triple quotes found)
    if any(w in t for w in ["typing", "writing", "type", "write"]):
        # Strict pattern: requires quotes "..." or '...'
        patterns = [
            r'typing\s+["\'](.+?)["\']',
            r'writing\s+["\'](.+?)["\']',
            r'write\s+["\'](.+?)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, t, re.IGNORECASE)
            if match:
                text_to_type = match.group(1)
                time.sleep(1)
                success, msg = automation.type_text(text_to_type)
                log("Action", msg)
                return True
    
    # === APPS === (Predefined + Dynamic)
    # FIX: Add "open", "opened", "start" to the keyword list
    if any(w in t for w in ["opening", "launching", "starting", "open", "opened", "start", "launch"]):
        
        # 1. Try predefined apps (from apps.json)
        for app_name, cmd in APPS.items():
            if app_name in t:
                try:
                    if cmd.startswith("start http"):
                        webbrowser.open(cmd.replace("start ", ""))
                        log("Action", f"✓ Opened {app_name} in default browser")
                    else:
                        subprocess.Popen(cmd, shell=True)
                        log("Action", f"✓ Opened {app_name}")
                        # FIX: Wait for app to actually open before doing anything else
                        time.sleep(2) 
                    return True
                except Exception as e:
                    log("Action", f"✗ {e}")
                    return True
        
        # 2. Dynamic app search (for apps not in json)
        # FIX: Update Regex to catch "Open notepad", "Opened notepad", etc.
        match = re.search(r'(?:opening|starting|launching|open|opened|start|launch)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', t)
        if match:
            app_name = match.group(1).strip()
            success, msg = apps.launch_app(app_name)
            log("Action", msg)
            if success:
                time.sleep(2) # Prevent typing before app is ready
            return True
    
    # === SYSTEM CONTROL ===
    # Require "system" or "computer" to avoid false positives from farewells
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
    
    # === FILES ===
    if "creating file" in t or "create file" in t:
        match = re.search(r'(?:creating|create)\s+file\s+(?:called\s+)?["\']?([^\s"\']+)["\']?', t)
        if match:
            filename = match.group(1)
            # Extract content if mentioned
            content_match = re.search(r'(?:with|containing)\s+["\']?(.+?)["\']?$', t)
            content = content_match.group(1) if content_match else ""
            success, msg = files.create_file(filename,content)
            log("Action", msg)
            return True
    
    if "deleting file" in t or "delete file" in t:
        match = re.search(r'(?:deleting|delete)\s+file\s+["\']?([^\s"\']+)["\']?', t)
        if match:
            filename = match.group(1)
            if approval.ask_approval(f"Delete file: {filename}"):
                success, msg = files.delete_file(filename)
                log("Action", msg)
            else:
                log("Action", "Delete cancelled")
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
    
    # === SEARCH ===
    match = re.search(r'searching\s+(?:for\s+)?["\']?(.+?)(?:["\']|$|\.)', t)
    if match:
        query = match.group(1).strip()
        if query and len(query) > 2:
            webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            log("Action", f"Searched: {query}")
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
        print("\n  JARVIS 2.0 - AUTONOMOUS MODE\n")
        return
    console.print(Panel(
        Text("""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝""", style="bold cyan"),
        title="[magenta]◈ JARVIS 2.0 - AUTONOMOUS ◈[/]",
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
        # Don't kill app immediately, but this is critical


async def send(session):
    while not exiting:
        msg = await audio_in.get()
        await session.send_realtime_input(audio=msg)


async def receive(session):
    global exiting
    while not exiting:
        async for resp in session.receive():
            if resp.server_content and resp.server_content.model_turn:
                for part in resp.server_content.model_turn.parts:
                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                        audio_out.put_nowait(part.inline_data.data)
                    
                    if hasattr(part, 'text') and part.text:
                        txt = part.text.strip()
                        
                        # Skip pure markdown headers
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


async def play():
    global exiting
    try:
        # Find default output device
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
            console.print(f"  [yellow]⚠ Audio output unavailable (Jarvis will be silent)[/]")
        else:
            print(f"  ⚠ Audio output unavailable: {e}")
        # Keep running silently - don't crash
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
                console.print("  [green]◈[/] Online & Autonomous!\n")
            else:
                print("  Online & Autonomous!")
            
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
    print("\n  Starting Jarvis Autonomous Mode...\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Stopped.")
