"""
Text-to-Speech service using Cartesia (Sonic).
Super-fast, low latency TTS. Fallback to Edge-TTS.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional
from app.utils.logger import log
from app.config import settings

# Edge-TTS (Fallback)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# Cartesia
try:
    from cartesia import Cartesia
    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False

# Pygame for audio playback (no external window)
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


class TTSEngine:
    """TTS Engine with Cartesia support."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "jarvis_tts"
        self.temp_dir.mkdir(exist_ok=True)
        self.client = None
        
        # Initialize Cartesia
        if CARTESIA_AVAILABLE and settings.cartesia_api_key:
            try:
                self.client = Cartesia(api_key=settings.cartesia_api_key)
                log.info("🔊 Cartesia TTS initialized")
            except Exception as e:
                log.error(f"Failed to init Cartesia: {e}")
                
    async def speak(self, text: str) -> None:
        """Synthesize and play speech."""
        if not text.strip():
            return
            
        output_file = self.temp_dir / "response.mp3"
        
        # Try Cartesia first
        if self.client:
            try:
                # Cartesia SDK v2 returns a generator of audio chunks
                audio_chunks = self.client.tts.bytes(
                    model_id="sonic-english",
                    transcript=text,
                    voice={"id": "79a125e8-cd45-4c13-8a67-188112f4dd22"},  # Cartesia voice
                    output_format={
                        "container": "mp3",
                        "bit_rate": 128000,
                        "sample_rate": 44100,
                    },
                )
                # Join all chunks into bytes
                data = b"".join(audio_chunks)
                output_file.write_bytes(data)
                await self._play_audio(output_file)
                return
            except Exception as e:
                log.error(f"Cartesia error, falling back to Edge-TTS: {e}")

        # Fallback to Edge-TTS
        if EDGE_TTS_AVAILABLE:
            try:
                communicate = edge_tts.Communicate(text, settings.tts_voice)
                await communicate.save(str(output_file))
                await self._play_audio(output_file)
            except Exception as e:
                log.error(f"Edge-TTS error: {e}")
                
    async def _play_audio(self, audio_path: Path) -> None:
        """Play audio file natively using pygame (no external player)."""
        if PYGAME_AVAILABLE:
            try:
                # Unload any previous audio to release file handle
                pygame.mixer.music.unload()
                pygame.mixer.music.load(str(audio_path))
                pygame.mixer.music.play()
                # Wait for audio to finish playing
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                # Unload to release file handle for next write
                pygame.mixer.music.unload()
            except Exception as e:
                log.error(f"Pygame audio error: {e}")
        else:
            # Fallback to system player if pygame not available
            if os.name == 'nt':
                os.system(f'start /min "" "{audio_path}"')
                await asyncio.sleep(2)

