"""
System Monitoring - CPU, RAM, Disk, Battery, Processes
"""
try:
    import psutil
except ImportError:
    psutil = None


def get_cpu_usage() -> tuple[bool, str]:
    """Get current CPU usage percentage."""
    if not psutil:
        return False, "psutil not available"
    
    try:
        cpu = psutil.cpu_percent(interval=1)
        return True, f"CPU usage: {cpu}%"
    except Exception as e:
        return False, f"CPU check failed: {e}"


def get_ram_usage() -> tuple[bool, str]:
    """Get current RAM usage."""
    if not psutil:
        return False, "psutil not available"
    
    try:
        ram = psutil.virtual_memory()
        return True, f"RAM: {ram.percent}% ({ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB)"
    except Exception as e:
        return False, f"RAM check failed: {e}"


def get_disk_usage() -> tuple[bool, str]:
    """Get disk usage for C: drive."""
    if not psutil:
        return False, "psutil not available"
    
    try:
        disk = psutil.disk_usage('C:')
        return True, f"Disk C: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"
    except Exception as e:
        return False, f"Disk check failed: {e}"


def get_battery_status() -> tuple[bool, str]:
    """Get battery status (laptops only)."""
    if not psutil:
        return False, "psutil not available"
    
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return False, "No battery detected (desktop?)"
        
        status = "Charging" if battery.power_plugged else "Discharging"
        return True, f"Battery: {battery.percent}% ({status})"
    except Exception as e:
        return False, f"Battery check failed: {e}"
