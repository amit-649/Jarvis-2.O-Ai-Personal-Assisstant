"""
System Control - Shutdown, restart, lock, sleep
"""
import subprocess

def shutdown_system() -> tuple[bool, str]:
    """Shutdown Windows."""
    try:
        subprocess.Popen("shutdown /s /t 0", shell=True)
        return True, "Shutting down system"
    except Exception as e:
        return False, f"Shutdown failed: {e}"


def restart_system() -> tuple[bool, str]:
    """Restart Windows."""
    try:
        subprocess.Popen("shutdown /r /t 0", shell=True)
        return True, "Restarting system"
    except Exception as e:
        return False, f"Restart failed: {e}"


def lock_screen() -> tuple[bool, str]:
    """Lock Windows screen."""
    try:
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return True, "Locking screen"
    except Exception as e:
        return False, f"Lock failed: {e}"


def sleep_system() -> tuple[bool, str]:
    """Put Windows to sleep."""
    try:
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return True, "Entering sleep mode"
    except Exception as e:
        return False, f"Sleep failed: {e}"
