"""
LLM Brain - The intelligence layer.
Uses Google Gemini for intent understanding and tool calling.
"""
import json
from typing import Optional, Any
from app.utils.logger import log
from app.config import settings

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    log.warning("google-generativeai not installed. LLM brain unavailable.")


SYSTEM_PROMPT = """You are Jarvis, a helpful voice assistant. You are:
- Concise and to-the-point (responses will be spoken aloud)
- Friendly but professional
- Helpful and proactive

When responding:
- Keep responses SHORT (1-2 sentences max for simple queries)
- Use natural, conversational language
- Avoid markdown, bullet points, or formatting (this is spoken)
- If you need to call a tool, do so without asking for confirmation unless explicitly required

Current context:
- You are running on a Windows PC
- The current time will be provided by tools when asked
"""


class Brain:
    """LLM-powered brain for understanding and responding."""
    
    def __init__(self):
        self.model = None
        self.chat = None
        self.conversation_history: list[dict] = []
        
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            self._setup_gemini()
        else:
            log.warning("Gemini API key not configured")
            
    def _setup_gemini(self) -> None:
        """Initialize the Gemini model."""
        try:
            genai.configure(api_key=settings.gemini_api_key)
            
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-lite",
                system_instruction=SYSTEM_PROMPT,
            )
            
            # Start a chat session for context
            self.chat = self.model.start_chat(history=[])
            
            log.info("✅ Gemini model initialized")
            
        except Exception as e:
            log.error(f"Failed to initialize Gemini: {e}")
            
    def think(
        self, 
        user_input: str, 
        tool_definitions: list[dict] = None
    ) -> dict:
        """
        Process user input and return a response or tool call.
        
        Args:
            user_input: The user's spoken command
            tool_definitions: Available tools in Gemini function calling format
            
        Returns:
            dict with 'response' (text) and/or 'tool_call' (tool to execute)
        """
        if not self.chat:
            return {"response": "I'm sorry, my brain isn't working right now."}
            
        try:
            log.debug(f"🧠 Thinking about: {user_input}")
            
            # Build the message with tools if available
            if tool_definitions:
                response = self.chat.send_message(
                    user_input,
                    tools=tool_definitions
                )
            else:
                response = self.chat.send_message(user_input)
            
            # Check for function calls
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        # Handle different arg formats from Gemini SDK
                        args = {}
                        if fc.args:
                            try:
                                # Try direct dict conversion
                                args = dict(fc.args)
                            except (TypeError, ValueError):
                                # For MapComposite objects, iterate through items
                                for key in fc.args:
                                    args[key] = fc.args[key]
                        tool_call = {
                            "name": fc.name,
                            "args": args
                        }
                        log.info(f"🔧 Tool call: {tool_call['name']}")
                        return {"tool_call": tool_call}
                        
            # Regular text response
            text = response.text
            log.info(f"💬 Response: {text[:100]}...")
            return {"response": text}
            
        except Exception as e:
            log.error(f"Brain error: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return {"response": "I encountered an error processing that."}
            
    def add_tool_result(self, tool_name: str, result: Any) -> str:
        """
        Send a tool result back to continue the conversation.
        
        Args:
            tool_name: Name of the tool that was executed
            result: Result from the tool
            
        Returns:
            The LLM's response incorporating the tool result
        """
        if not self.chat:
            return "Error: Brain not initialized"
            
        try:
            # Send the function response
            response = self.chat.send_message(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=tool_name,
                            response={"result": str(result)}
                        )
                    )]
                )
            )
            
            return response.text
            
        except Exception as e:
            log.error(f"Error sending tool result: {e}")
            return f"The {tool_name} completed: {result}"
            
    def reset(self) -> None:
        """Reset the conversation history."""
        if self.model:
            self.chat = self.model.start_chat(history=[])
            log.info("🔄 Conversation reset")
