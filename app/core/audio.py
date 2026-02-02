"""
Audio capture using SoundDevice (PyAudio replacement for Py 3.14).
"""
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import io
from app.utils.logger import log


class AudioCapture:
    """Handles microphone input using sounddevice."""
    
    RATE = 16000
    CHANNELS = 1
    
    def __init__(self):
        # Check devices
        try:
            device_info = sd.query_devices(kind='input')
            log.info(f"🎤 valid: SoundDevice microphone ready ({device_info['name']})")
        except Exception as e:
            log.error(f"mic error: {e}")
        
    def start_stream(self):
        # SoundDevice doesn't need an explicit stream start for blocking records
        pass
        
    def cleanup(self):
        sd.stop()

    def record_until_silence(self, max_seconds=10) -> bytes:
        """
        Record audio until silence is detected.
        Uses a blocking loop with small chunks.
        """
        log.info("🔴 Listening...")
        
        chunk_duration = 0.5  # Check silence every 0.5s
        chunk_samples = int(self.RATE * chunk_duration)
        
        frames = []
        silence_threshold = 0.005  # Lowered threshold for better sensitivity
        silence_chunks = 0
        max_chunks = int(max_seconds / chunk_duration)
        has_speech = False
        
        try:
            with sd.InputStream(samplerate=self.RATE, channels=self.CHANNELS, dtype='float32') as stream:
                for i in range(max_chunks):
                    data, overflowed = stream.read(chunk_samples)
                    frames.append(data.copy())  # Important: copy the data
                    
                    # Simple VAD based on RMS
                    rms = np.sqrt(np.mean(data**2))
                    
                    if rms >= silence_threshold:
                        has_speech = True
                        silence_chunks = 0
                        log.debug(f"Chunk {i}: RMS={rms:.4f} (speech)")
                    else:
                        silence_chunks += 1
                        log.debug(f"Chunk {i}: RMS={rms:.4f} (silence {silence_chunks})")
                    
                    # Only stop on silence AFTER we've detected speech
                    if has_speech and silence_chunks > 3:  # 1.5 seconds of silence after speech
                        break
                        
        except Exception as e:
            log.error(f"Recording error: {e}")
            return b""
            
        if not frames:
            return b""
            
        log.info(f"⏹️ Stopped (recorded {len(frames)} chunks)")
        
        # Concatenate and flatten to 1D array
        recording = np.concatenate(frames).flatten()
        
        # Convert float32 (-1.0 to 1.0) to int16 (-32768 to 32767)
        # Clip to avoid overflow, then scale
        recording = np.clip(recording, -1.0, 1.0)
        recording_int16 = (recording * 32767).astype(np.int16)
        
        wav_buffer = io.BytesIO()
        wav.write(wav_buffer, self.RATE, recording_int16)
        wav_buffer.seek(0)  # Reset to start for reading
        
        audio_bytes = wav_buffer.getvalue()
        log.debug(f"Recorded {len(audio_bytes)} bytes, {len(recording_int16)} samples")
        
        return audio_bytes

