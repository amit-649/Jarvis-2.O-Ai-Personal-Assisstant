"""
Dynamic App Launcher - Find and launch any installed Windows app
"""
import subprocess
from pathlib import Path
import os

def find_app_shortcut(app_name: str):
    """Search Windows Start Menu for app shortcuts."""
    search_dirs = [
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
    ]
    
    app_lower = app_name.lower()
    
    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        
        # Search for .lnk files
        for lnk_file in base_dir.rglob("*.lnk"):
            if app_lower in lnk_file.stem.lower():
                return str(lnk_file)
    
    return None


def launch_app(app_name: str) -> tuple[bool, str]:
    """
    Launch any Windows app by name.
    Returns: (success: bool, message: str)
    """
    # Try to find shortcut
    shortcut = find_app_shortcut(app_name)
    
    if shortcut:
        try:
            subprocess.Popen(f'start "" "{shortcut}"', shell=True)
            return True, f"Opened {app_name}"
        except Exception as e:
            return False, f"Failed to open {app_name}: {e}"
    else:
        # Try direct command
        try:
            subprocess.Popen(app_name, shell=True)
            return True, f"Opened {app_name}"
        except:
            return False, f"Could not find {app_name}"
