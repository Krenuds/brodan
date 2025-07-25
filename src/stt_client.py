import httpx
import json
import threading
from queue import Queue
import time
import numpy as np
import uuid
import struct
import logging
import os
import asyncio
import io

# Configure STT client logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Only warnings and errors

class WhisperLiveClient:
    """HTTP client for whisper.cpp STT service with OpenAI-compatible API"""
    
    def __init__(self, host=None, port=None):
        # Load configuration
        self.config = self._load_config()
        
        # Use provided values or fall back to config
        whisper_config = self.config.get('whisper', {})
        self.host = host or whisper_config.get('host', 'whisper-stt')
        self.port = port or whisper_config.get('port', 9000)
        self.base_url = f"http://{self.host}:{self.port}"
        
        self.client = httpx.AsyncClient(timeout=30.0)
        self.transcription_queue = Queue()
        self.connected = False
        self.uid = str(uuid.uuid4())
        
        # Audio buffer for accumulating chunks
        self.audio_buffer = io.BytesIO()
        self.buffer_lock = threading.Lock()
        
        # Load timeout settings
        timeout_config = self.config.get('timeouts', {})
        self.segment_timeout = timeout_config.get('segment_timeout_s', 3.0)
        self.connection_timeout = timeout_config.get('connection_timeout_s', 5.0)
        
        # Processing state
        self.last_transcription_time = time.time()
        self.processing_thread = None
        self.processing_active = False
        
    def connect(self):
        """Test HTTP connection to whisper.cpp server"""
        try:
            # Test connection with docs endpoint (no health endpoint available)
            response = httpx.get(f"http://{self.host}:{self.port}/docs", timeout=self.connection_timeout)
            self.connected = response.status_code == 200
            
            if self.connected:
                # Start audio processing thread
                self.processing_active = True
                self.processing_thread = threading.Thread(target=self._process_audio_buffer)
                self.processing_thread.daemon = True
                self.processing_thread.start()
            
            return self.connected
            
        except Exception as e:
            print(f"STT Connection Error: {e}")
            self.connected = False
            return False
    
    def _process_audio_buffer(self):
        """Process accumulated audio data periodically"""
        while self.processing_active and self.connected:
            try:
                time.sleep(self.segment_timeout)  # Process every segment_timeout seconds
                
                audio_data = None
                with self.buffer_lock:
                    if self.audio_buffer.tell() > 0:
                        # Get audio data from buffer
                        audio_data = self.audio_buffer.getvalue()
                        self.audio_buffer = io.BytesIO()  # Reset buffer
                
                if audio_data and len(audio_data) > 1024:  # Only process if we have enough audio
                    asyncio.run(self._transcribe_audio(audio_data))
                    
            except Exception as e:
                print(f"Error in audio processing: {e}")
                time.sleep(1)
    
    async def _transcribe_audio(self, audio_data: bytes):
        """Send audio to whisper.cpp for transcription"""
        try:
            # Convert PCM to WAV format for the API
            wav_data = self._pcm_to_wav(audio_data)
            if not wav_data:
                return
            
            # Prepare multipart form data for /asr endpoint
            files = {
                'audio_file': ('audio.wav', wav_data, 'audio/wav')
            }
            params = {
                'task': 'transcribe',
                'language': self.config.get('whisper', {}).get('language', 'en'),
                'output': 'json'
            }
            
            # Make request to whisper service /asr endpoint
            response = await self.client.post(
                f"{self.base_url}/asr",
                files=files,
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                
                if text:
                    print(f"🎤 {text}")
                    
                    # Create transcription result
                    transcription = {
                        "text": text,
                        "start": 0,
                        "end": self.segment_timeout,
                        "completed": True,
                        "uid": self.uid,
                        "type": "final"
                    }
                    
                    self.transcription_queue.put(transcription)
                    self.last_transcription_time = time.time()
            
        except Exception as e:
            print(f"Transcription error: {e}")
    
    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert PCM data to WAV format for whisper.cpp API"""
        try:
            # Convert 16-bit PCM to numpy array and resample
            audio_array = self._pcm_to_float32(pcm_data)
            if audio_array is None:
                return None
            
            # Convert float32 back to 16-bit PCM for WAV
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Create WAV header
            sample_rate = 16000  # whisper.cpp expects 16kHz
            num_channels = 1
            bits_per_sample = 16
            byte_rate = sample_rate * num_channels * bits_per_sample // 8
            block_align = num_channels * bits_per_sample // 8
            data_size = len(audio_int16) * 2  # 2 bytes per sample
            
            # WAV header (44 bytes)
            wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                b'RIFF', 36 + data_size, b'WAVE', b'fmt ', 16,
                1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample,
                b'data', data_size
            )
            
            # Combine header and audio data
            wav_data = wav_header + audio_int16.tobytes()
            
            return wav_data
        except Exception as e:
            print(f"PCM to WAV conversion error: {e}")
            return None
    
    async def send_audio(self, audio_chunk: bytes):
        """Buffer audio chunk for periodic transcription"""
        if self.connected and len(audio_chunk) > 0:
            try:
                with self.buffer_lock:
                    self.audio_buffer.write(audio_chunk)
                return True
            except Exception as e:
                print(f"Error buffering audio: {e}")
                return False
        return False
    
    def _pcm_to_float32(self, pcm_data: bytes) -> np.ndarray:
        """Convert PCM bytes to float32 numpy array and resample to 16kHz"""
        try:
            # Convert 16-bit PCM to numpy array
            if len(pcm_data) < 2:
                return None
            
            # Unpack as 16-bit signed integers  
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_array = np.array(samples, dtype=np.float32) / 32768.0
            
            # Resample from 48kHz (Discord) to 16kHz (WhisperLive requirement)
            # Simple downsampling: take every 3rd sample (48000/16000 = 3)
            resampled_array = audio_array[::3]
            
            return resampled_array
            
        except Exception as e:
            print(f"PCM to float32 conversion error: {e}")
            return None
    
    def get_transcription(self):
        """Get latest transcription if available"""
        if not self.transcription_queue.empty():
            return self.transcription_queue.get()
        return None
    
    def test_connection(self):
        """Test basic connectivity to STT service"""
        try:
            response = httpx.get(f"http://{self.host}:{self.port}/docs", timeout=self.connection_timeout)
            return response.status_code == 200
        except Exception as e:
            print(f"STT connection test failed: {e}")
            return False
    
    def disconnect(self):
        """Clean disconnect"""
        self.connected = False
        self.processing_active = False
        
        try:
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
                if self.processing_thread.is_alive():
                    print("Warning: STT processing thread did not terminate cleanly")
        except Exception as e:
            print(f"Error joining STT processing thread: {e}")
        
        try:
            asyncio.run(self.client.aclose())
        except Exception as e:
            print(f"Error closing HTTP client: {e}")
    
    def _load_config(self):
        """Load configuration from file or use defaults"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'stt_config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logging.warning(f"STT config file not found at {config_path}, using defaults")
        except Exception as e:
            logging.error(f"Error loading STT config: {e}, using defaults")
        
        # Return default configuration
        return {
            "whisper": {
                "host": "whisper-stt",
                "port": 9000,
                "model": "small",
                "language": "en",
                "task": "transcribe"
            },
            "vad": {
                "enabled": True,
                "min_silence_duration_ms": 1000,
                "min_speech_duration_ms": 250,
                "max_speech_duration_s": 30,
                "speech_pad_ms": 200,
                "threshold": 0.5
            },
            "timeouts": {
                "segment_timeout_s": 3.0,
                "monitor_interval_s": 0.5,
                "connection_timeout_s": 5.0
            }
        }
