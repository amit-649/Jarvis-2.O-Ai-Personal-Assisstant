"""
Tool Registry - Manages available tools/functions.
Provides a decorator for easy tool definition and schema generation.
"""
import inspect
from typing import Callable, Any, Optional, get_type_hints
from dataclasses import dataclass, field
from app.utils.logger import log


@dataclass
class Tool:
    """Represents a callable tool with metadata."""
    name: str
    description: str
    function: Callable
    parameters: dict = field(default_factory=dict)
    requires_confirmation: bool = False
    
    def to_gemini_schema(self) -> dict:
        """Convert to Gemini function calling schema (Dictionary format)."""
        
        # Convert parameter types to Gemini Schema format
        properties = {}
        for param_name, param_info in self.parameters.items():
            type_str = param_info.get("type", "STRING")
            
            # Map string types to Gemini schema types (strings)
            type_map = {
                "string": "STRING",
                "integer": "INTEGER",
                "number": "NUMBER",
                "boolean": "BOOLEAN",
                "array": "ARRAY",
                "object": "OBJECT",
            }
            
            gemini_type = type_map.get(type_str.lower(), "STRING")
            
            properties[param_name] = {
                "type": gemini_type,
                "description": param_info.get("description", f"Parameter: {param_name}")
            }

        # Build the function declaration
        required_params = [
            k for k, v in self.parameters.items() 
            if not v.get("optional", False)
        ]
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": required_params if required_params else None
            }
        }


class ToolRegistry:
    """Registry for all available tools."""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        
    def register(
        self,
        name: str = None,
        description: str = None,
        requires_confirmation: bool = False
    ) -> Callable:
        """
        Decorator to register a function as a tool.
        
        Usage:
            @registry.register(description="Gets the current time")
            def get_time() -> str:
                return datetime.now().isoformat()
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or "No description"
            
            # Extract parameters from type hints
            params = self._extract_parameters(func)
            
            tool = Tool(
                name=tool_name,
                description=tool_desc.strip(),
                function=func,
                parameters=params,
                requires_confirmation=requires_confirmation
            )
            
            self._tools[tool_name] = tool
            log.debug(f"📦 Registered tool: {tool_name}")
            
            return func
            
        return decorator
        
    def _extract_parameters(self, func: Callable) -> dict:
        """Extract parameter schema from function signature."""
        params = {}
        sig = inspect.signature(func)
        hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
                
            param_type = hints.get(param_name, str)
            type_map = {
                str: "string",
                int: "integer", 
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            
            params[param_name] = {
                "type": type_map.get(param_type, "string"),
                "description": f"Parameter: {param_name}"
            }
            
            # Check if optional (has default value)
            if param.default is not inspect.Parameter.empty:
                params[param_name]["optional"] = True
                params[param_name]["default"] = param.default
                
        return params
        
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
        
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
        
    def get_gemini_tools(self) -> list[dict]:
        """Get all tools in Gemini function calling format."""
        return [tool.to_gemini_schema() for tool in self._tools.values()]
        
    async def execute(self, name: str, args: dict = None) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            args: Arguments to pass to the tool
            
        Returns:
            Tool result
        """
        tool = self.get(name)
        if not tool:
            log.error(f"Tool not found: {name}")
            return f"Error: Unknown tool '{name}'"
            
        try:
            args = args or {}
            log.info(f"⚙️ Executing: {name}({args})")
            
            # Handle async functions
            if inspect.iscoroutinefunction(tool.function):
                result = await tool.function(**args)
            else:
                result = tool.function(**args)
                
            log.info(f"✅ Result: {result}")
            return result
            
        except Exception as e:
            log.error(f"Tool execution error: {e}")
            return f"Error executing {name}: {str(e)}"


# Global registry instance
registry = ToolRegistry()
