"""
Keyboard and Mouse Automation with Window Focus Management
"""
try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def get_active_window_title() -> str:
    """Get the title of the currently focused window."""
    if not WIN32_AVAILABLE:
        return ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except:
        return ""


def find_window_by_title(title_contains: str) -> int:
    """
    Find a window handle by partial title match.
    Returns hwnd or 0 if not found.
    """
    if not WIN32_AVAILABLE:
        return 0
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_contains.lower() in window_title.lower():
                windows.append(hwnd)
        return True
    
    windows = []
    try:
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else 0
    except:
        return 0


def focus_window(window_title: str, timeout: float = 3.0) -> tuple[bool, str]:
    """
    Focus a window by title with retry logic.
    
    Args:
        window_title: Partial window title to match
        timeout: Maximum time to wait for window
        
    Returns:
        (success, message)
    """
    if not WIN32_AVAILABLE:
        return False, "Win32 API not available"
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        hwnd = find_window_by_title(window_title)
        
        if hwnd:
            try:
                # Restore if minimized
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Bring to foreground
                win32gui.SetForegroundWindow(hwnd)
                
                # Verify it worked
                time.sleep(0.2)
                current = win32gui.GetForegroundWindow()
                if current == hwnd:
                    actual_title = win32gui.GetWindowText(hwnd)
                    return True, f"Focused: {actual_title}"
                    
            except Exception as e:
                pass  # Window might have closed, try again
        
        time.sleep(0.1)
    
    return False, f"Could not focus window: {window_title}"


def type_text(text: str, interval: float = 0.03, focus_window_title: str = None) -> tuple[bool, str]:
    """
    Type text using keyboard automation with optional window focusing.
    
    Args:
        text: Text to type
        interval: Delay between keystrokes
        focus_window_title: Optional window to focus before typing
        
    Returns:
        (success, message)
    """
    if not pyautogui:
        return False, "PyAutoGUI not available"
    
    # Focus window if specified
    if focus_window_title:
        success, msg = focus_window(focus_window_title)
        if not success:
            return False, f"Focus failed: {msg}"
    
    try:
        # Click to ensure cursor is in the right place (optional safety)
        # pyautogui.click()  # Uncomment if you want a click before typing
        
        pyautogui.write(text, interval=interval)
        return True, f"Typed: {text[:30]}{'...' if len(text) > 30 else ''} ({len(text)} chars)"
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


# Utility: Get list of all open windows (for debugging)
def list_open_windows() -> list[str]:
    """Get list of all visible window titles."""
    if not WIN32_AVAILABLE:
        return []
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append(title)
        return True
    
    windows = []
    try:
        win32gui.EnumWindows(callback, windows)
    except:
        pass
    return windows