"""
Memory management for Jarvis.
Handles short-term context and long-term preferences.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from app.utils.logger import log
from app.config import settings


class Memory:
    """Simple file-based memory for preferences and context."""
    
    def __init__(self, memory_file: str = "memory.json"):
        self.memory_path = settings.notes_dir.parent / memory_file
        self.data: dict = self._load()
        
    def _load(self) -> dict:
        """Load memory from file."""
        if self.memory_path.exists():
            try:
                return json.loads(self.memory_path.read_text(encoding="utf-8"))
            except Exception as e:
                log.error(f"Failed to load memory: {e}")
        
        return {
            "preferences": {},
            "facts": {},
            "history": []
        }
        
    def _save(self) -> None:
        """Save memory to file."""
        try:
            self.memory_path.write_text(
                json.dumps(self.data, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            log.error(f"Failed to save memory: {e}")
            
    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        self.data["preferences"][key] = value
        self._save()
        log.info(f"💾 Saved preference: {key}")
        
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.data["preferences"].get(key, default)
        
    def remember_fact(self, key: str, value: str) -> None:
        """Remember a fact about the user."""
        self.data["facts"][key] = {
            "value": value,
            "remembered_at": datetime.now().isoformat()
        }
        self._save()
        log.info(f"💾 Remembered: {key}")
        
    def recall_fact(self, key: str) -> Optional[str]:
        """Recall a fact."""
        fact = self.data["facts"].get(key)
        return fact["value"] if fact else None
        
    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.data["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 messages
        if len(self.data["history"]) > 50:
            self.data["history"] = self.data["history"][-50:]
            
        self._save()
        
    def get_history(self, limit: int = 10) -> list[dict]:
        """Get recent conversation history."""
        return self.data["history"][-limit:]
        
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.data["history"] = []
        self._save()
        log.info("🔄 History cleared")
        
    def forget_all(self) -> None:
        """Reset all memory."""
        self.data = {
            "preferences": {},
            "facts": {},
            "history": []
        }
        self._save()
        log.info("🔄 Memory reset")
        
    def get_context_summary(self) -> str:
        """Get a summary of known facts for LLM context."""
        facts = self.data.get("facts", {})
        prefs = self.data.get("preferences", {})
        
        lines = []
        
        if facts:
            lines.append("Known facts about the user:")
            for key, fact in facts.items():
                lines.append(f"- {key}: {fact['value']}")
                
        if prefs:
            lines.append("User preferences:")
            for key, value in prefs.items():
                lines.append(f"- {key}: {value}")
                
        return "\n".join(lines) if lines else "No stored context."


# Global memory instance
memory = Memory()
