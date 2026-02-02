"""
File Operations - Create, delete, read, write
"""
import os
from pathlib import Path


def create_file(filepath: str, content: str = "") -> tuple[bool, str]:
    """Create a new file with optional content."""
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return True, f"Created file: {filepath}"
    except Exception as e:
        return False, f"Create file failed: {e}"


def delete_file(filepath: str) -> tuple[bool, str]:
    """Delete a file."""
    try:
        path = Path(filepath)
        if not path.exists():
            return False, f"File not found: {filepath}"
        
        path.unlink()
        return True, f"Deleted file: {filepath}"
    except Exception as e:
        return False, f"Delete failed: {e}"


def read_file(filepath: str) -> tuple[bool, str]:
    """Read file contents."""
    try:
        path = Path(filepath)
        if not path.exists():
            return False, f"File not found: {filepath}"
        
        content = path.read_text(encoding='utf-8')
        return True, f"File content:\n{content[:500]}"  # Limit output
    except Exception as e:
        return False, f"Read failed: {e}"
