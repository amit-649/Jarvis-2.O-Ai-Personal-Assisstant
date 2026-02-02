"""
Keyboard and Mouse Automation
"""
try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None


def type_text(text: str, interval: float = 0.05) -> tuple[bool, str]:
    """Type text using keyboard automation."""
    if not pyautogui:
        return False, "PyAutoGUI not available"
    
    try:
        pyautogui.write(text, interval=interval)
        return True, f"Typed: {text[:30]}..."
    except Exception as e:
        return False, f"Typing failed: {e}"


def press_key(key: str) -> tuple[bool, str]:
    """Press a keyboard key."""
    if not pyautogui:
        return False, "PyAutoGUI not available"
    
    try:
        pyautogui.press(key)
        return True, f"Pressed {key}"
    except Exception as e:
        return False, f"Key press failed: {e}"


def press_hotkey(*keys) -> tuple[bool, str]:
    """Press a combination of keys (e.g., ctrl+c)."""
    if not pyautogui:
        return False, "PyAutoGUI not available"
    
    try:
        pyautogui.hotkey(*keys)
        return True, f"Pressed {'+'.join(keys)}"
    except Exception as e:
        return False, f"Hotkey failed: {e}"
