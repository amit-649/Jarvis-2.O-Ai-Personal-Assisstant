"""
Basic built-in tools for Jarvis.
These are always available regardless of configuration.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from app.tools.registry import registry
from app.config import settings
from app.utils.logger import log


@registry.register(description="Get the current date and time")
def get_time() -> str:
    """Returns the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


@registry.register(description="Get the current weather for a city")
def get_weather(city: str = None) -> str:
    """
    Get weather for a city using OpenWeatherMap API.
    
    Args:
        city: City name (defaults to configured city)
    """
    import httpx
    
    city = city or settings.default_city
    api_key = settings.openweather_api_key
    
    if not api_key:
        return "Weather service not configured. Please add OPENWEATHER_API_KEY to .env"
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }
        
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        
        return (
            f"In {city}, it's currently {temp:.1f}°C, feels like {feels_like:.1f}°C. "
            f"{description.capitalize()}. Humidity is {humidity}%."
        )
        
    except httpx.HTTPError as e:
        log.error(f"Weather API error: {e}")
        return f"Couldn't get weather for {city}"
    except Exception as e:
        log.error(f"Weather error: {e}")
        return "Weather service unavailable"


@registry.register(description="Save a note to a file")
def add_note(content: str, title: str = None) -> str:
    """
    Save a note to the notes directory.
    
    Args:
        content: The note content
        title: Optional title (used as filename)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{title or 'note'}_{timestamp}.txt"
    
    note_path = settings.notes_dir / filename
    
    try:
        note_path.write_text(content, encoding="utf-8")
        log.info(f"📝 Note saved: {note_path}")
        return f"Note saved as {filename}"
    except Exception as e:
        log.error(f"Failed to save note: {e}")
        return "Failed to save note"


@registry.register(description="Open an application by name")
def open_app(app_name: str) -> str:
    """
    Open an application on the system.
    
    Args:
        app_name: Name of the application (e.g., 'notepad', 'chrome', 'calculator')
    """
    # Map common names to executables
    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "wt.exe",
        "vscode": "code",
        "code": "code",
    }
    
    executable = app_map.get(app_name.lower(), app_name)
    
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                executable, 
                shell=True,
                creationflags=subprocess.DETACHED_PROCESS
            )
        else:
            subprocess.Popen([executable], start_new_session=True)
            
        log.info(f"🚀 Opened: {app_name}")
        return f"Opening {app_name}"
        
    except Exception as e:
        log.error(f"Failed to open {app_name}: {e}")
        return f"Couldn't open {app_name}"


@registry.register(description="Set a timer for a specified number of minutes")
def set_timer(minutes: int, label: str = "Timer") -> str:
    """
    Set a countdown timer.
    
    Args:
        minutes: Number of minutes
        label: Optional label for the timer
    """
    import threading
    import winsound
    
    def timer_callback():
        log.info(f"⏰ Timer '{label}' completed!")
        # Beep to alert user
        try:
            winsound.Beep(1000, 500)
            winsound.Beep(1000, 500)
        except:
            pass
    
    seconds = minutes * 60
    timer = threading.Timer(seconds, timer_callback)
    timer.start()
    
    log.info(f"⏱️ Timer set: {minutes} minutes")
    return f"Timer set for {minutes} minute{'s' if minutes != 1 else ''}"


@registry.register(description="Search the web using a search engine")
def web_search(query: str) -> str:
    """
    Open a web search in the default browser.
    
    Args:
        query: Search query
    """
    import webbrowser
    import urllib.parse
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    
    webbrowser.open(url)
    log.info(f"🔍 Searching: {query}")
    
    return f"Searching for: {query}"


@registry.register(description="Tell a random joke")
def tell_joke() -> str:
    """Returns a random joke."""
    import random
    
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "There are only 10 types of people in the world: those who understand binary and those who don't.",
        "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
        "A SQL query walks into a bar, goes up to two tables and asks: 'Can I join you?'",
        "Why do Java developers wear glasses? Because they don't C#!",
    ]
    
    return random.choice(jokes)


@registry.register(description="Get system information")
def system_info() -> str:
    """Returns basic system information."""
    import platform
    
    info = {
        "OS": platform.system(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor()
    }
    
    return ", ".join(f"{k}: {v}" for k, v in info.items())
