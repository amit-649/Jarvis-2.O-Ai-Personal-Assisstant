"""
Application settings loaded from environment variables.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # --- LLM ---
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    
    # --- STT ---
    deepgram_api_key: str = Field(default="", description="Deepgram API Key")
    
    # --- TTS ---
    cartesia_api_key: str = Field(default="", description="Cartesia API Key")
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API Key")
    tts_voice: str = Field(default="en-IN-NeerjaNeural", description="Edge-TTS voice (fallback)")
    
    # --- Weather ---
    openweather_api_key: str = Field(default="", description="OpenWeatherMap API Key")
    default_city: str = Field(default="Kolkata", description="Default city")
    
    # --- Search ---
    serpapi_api_key: str = Field(default="", description="SerpApi Key")
    
    # --- Security ---
    # Stored as comma-separated string in .env, parsed via property
    confirm_commands: str = Field(
        default="delete,remove,send,email,shutdown",
        description="Commands requiring confirmation (comma-separated)"
    )
    
    @property
    def confirm_commands_list(self) -> list[str]:
        """Get confirm_commands as a list."""
        return [cmd.strip() for cmd in self.confirm_commands.split(",") if cmd.strip()]
    
    # --- Paths ---
    notes_dir: Path = Field(default=Path("./notes"), description="Directory for notes")
    logs_dir: Path = Field(default=Path("./logs"), description="Directory for logs")


settings = Settings()
settings.notes_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)

