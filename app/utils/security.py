"""
Security utilities for Jarvis.
Handles permissions, confirmations, and safe execution.
"""
from typing import Optional, Callable
from app.utils.logger import log
from app.config import settings


class SecurityManager:
    """Manages security policies and confirmations."""
    
    def __init__(self):
        self.allowed_apps = {
            "notepad", "calculator", "chrome", "firefox", 
            "explorer", "code", "vscode", "terminal", "cmd"
        }
        self.confirm_keywords = set(settings.confirm_commands)
        
    def requires_confirmation(self, tool_name: str, args: dict = None) -> bool:
        """
        Check if a tool execution requires user confirmation.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            True if confirmation is required
        """
        # Check tool name against keywords
        for keyword in self.confirm_keywords:
            if keyword.lower() in tool_name.lower():
                return True
                
        # Check args for sensitive patterns
        if args:
            args_str = str(args).lower()
            for keyword in self.confirm_keywords:
                if keyword in args_str:
                    return True
                    
        return False
        
    def is_app_allowed(self, app_name: str) -> bool:
        """Check if an app is in the allowlist."""
        return app_name.lower() in self.allowed_apps
        
    def add_allowed_app(self, app_name: str) -> None:
        """Add an app to the allowlist."""
        self.allowed_apps.add(app_name.lower())
        log.info(f"✅ Added to allowlist: {app_name}")
        
    def log_action(self, action: str, details: str = "") -> None:
        """Log a security-relevant action."""
        log.info(f"🔒 SECURITY: {action} | {details}")


# Global security manager
security = SecurityManager()


def confirm_action(prompt: str) -> bool:
    """
    Ask for user confirmation (console-based for now).
    
    Args:
        prompt: The confirmation prompt
        
    Returns:
        True if confirmed
    """
    print(f"\n⚠️  {prompt}")
    response = input("Confirm? (yes/no): ").strip().lower()
    return response in ("yes", "y")
