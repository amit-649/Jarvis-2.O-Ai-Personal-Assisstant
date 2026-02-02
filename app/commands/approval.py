"""
Approval System for Dangerous Commands
"""
try:
    from rich.console import Console
    from rich.prompt import Confirm
    console = Console()
except ImportError:
    console = None


DANGEROUS_COMMANDS = {
    "shutdown", "restart", "delete", "remove", "format",
    "install", "uninstall", "system"
}


def requires_approval(command_desc: str) -> bool:
    """Check if command requires user approval."""
    return any(word in command_desc.lower() for word in DANGEROUS_COMMANDS)


def ask_approval(action: str) -> bool:
    """
    Ask user for approval in terminal.
    Returns True if approved, False otherwise.
    """
    if not console:
        # Fallback to basic input
        print(f"\n⚠️  Jarvis wants to: {action}")
        response = input("Approve? (yes/no): ")
        return response.lower() in ['yes', 'y']
    
    console.print(f"\n[yellow]⚠️  Jarvis wants to: {action}[/]")
    return Confirm.ask("Approve?", default=False)
