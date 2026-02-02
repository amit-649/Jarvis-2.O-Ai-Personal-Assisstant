"""
Speech-to-Text service using Deepgram API.
Compatible with Python 3.14 (no heavy local wheels needed).
"""
import httpx
import json
from app.utils.logger import log
from app.config import settings


class STTEngine:
    """Speech-to-Text engine using Deepgram."""
    
    def __init__(self):
        self.api_key = settings.deepgram_api_key
        if not self.api_key:
            log.warning("Deepgram API key not found. STT will be disabled.")
        else:
            log.info("🎙️ Deepgram STT initialized")
            
    def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio using Deepgram API.
        
        Args:
            audio_data: Raw audio bytes (WAV/PCM)
            
        Returns:
            Transcribed text
        """
        if not self.api_key:
            log.warning("No Deepgram API key - cannot transcribe")
            return ""
        
        if not audio_data or len(audio_data) < 1000:
            log.warning(f"Audio too short or empty: {len(audio_data) if audio_data else 0} bytes")
            return ""
            
        log.debug(f"🎤 Sending {len(audio_data)} bytes to Deepgram...")
            
        try:
            url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "audio/wav"
            }
            
            # Send request
            response = httpx.post(url, headers=headers, content=audio_data, timeout=15)
            
            log.debug(f"Deepgram status: {response.status_code}")
            
            if response.status_code != 200:
                log.error(f"Deepgram API error: {response.status_code} - {response.text[:200]}")
                return ""
                
            data = response.json()
            transcript = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
            
            if transcript:
                log.info(f"📝 Heard: {transcript}")
                return transcript.strip()
            else:
                log.warning(f"Deepgram returned empty transcript. Response: {json.dumps(data)[:300]}")
                
        except httpx.TimeoutException:
            log.error("Deepgram request timed out")
        except Exception as e:
            log.error(f"Deepgram STT error: {e}")
            
        return ""

