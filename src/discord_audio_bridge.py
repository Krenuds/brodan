"""
Discord Audio Bridge - OpenAI-compatible STT API for voice-mode MCP integration

This service provides an OpenAI-compatible /v1/audio/transcriptions endpoint
that streams Discord audio data directly to whisper.cpp for transcription.
Enables Claude Code voice-mode integration through Discord voice channels.
"""

import asyncio
import io
import json
import logging
import os
import struct
import threading
import time
import uuid
from queue import Queue
from typing import Dict, Optional

import httpx
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logger = logging.getLogger(__name__)

class DiscordAudioBridge:
    """OpenAI-compatible audio bridge for Discord voice integration"""
    
    def __init__(self):
        self.config = self._load_config()
        self.whisper_base_url = os.getenv('WHISPER_CPP_BASE_URL', 'http://whisper-stt:9000')
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Audio streaming state
        self.audio_streams: Dict[str, Queue] = {}
        self.active_transcriptions: Dict[str, dict] = {}
        self.stream_lock = threading.Lock()
        
        # Discord audio processor integration
        self.discord_audio_queue = Queue()
        self.processing_active = False
        self.processing_thread = None
        
    async def start_processing(self):
        """Start Discord audio processing thread"""
        if not self.processing_active:
            self.processing_active = True
            self.processing_thread = threading.Thread(target=self._process_discord_audio)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            logger.info("Discord audio processing started")
    
    async def stop_processing(self):
        """Stop Discord audio processing"""
        self.processing_active = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
            logger.info("Discord audio processing stopped")
    
    def _process_discord_audio(self):
        """Process Discord audio data from queue"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.processing_active:
            try:
                if not self.discord_audio_queue.empty():
                    audio_data = self.discord_audio_queue.get(timeout=1)
                    # Process the audio data asynchronously
                    loop.run_until_complete(self._handle_discord_audio(audio_data))
                else:
                    time.sleep(0.1)  # Brief sleep if no data
            except Exception as e:
                logger.error(f"Error processing Discord audio: {e}")
                time.sleep(1)
        
        # Close the loop when done
        loop.close()
    
    async def _handle_discord_audio(self, audio_data: bytes):
        """Handle Discord audio data for real-time transcription"""
        try:
            # Convert and transcribe audio
            transcription = await self._transcribe_audio_data(audio_data)
            if transcription:
                logger.info(f"Discord transcription: {transcription}")
        except Exception as e:
            logger.error(f"Error handling Discord audio: {e}")
    
    def add_discord_audio(self, audio_data: bytes):
        """Add Discord audio data to processing queue"""
        try:
            self.discord_audio_queue.put(audio_data)
        except Exception as e:
            logger.error(f"Error adding Discord audio: {e}")
    
    async def transcribe_audio(self, 
                             file: UploadFile,
                             model: str = "whisper-1",
                             language: Optional[str] = None,
                             prompt: Optional[str] = None,
                             response_format: str = "json",
                             temperature: float = 0.0) -> dict:
        """
        OpenAI-compatible audio transcription endpoint
        Compatible with /v1/audio/transcriptions API format
        """
        try:
            # Read audio file data
            audio_data = await file.read()
            
            # Transcribe the audio
            result = await self._transcribe_audio_data(audio_data, language=language)
            
            if response_format == "json":
                return {"text": result}
            elif response_format == "text":
                return result
            elif response_format == "srt":
                return self._format_as_srt(result)
            elif response_format == "verbose_json":
                return {
                    "task": "transcribe",
                    "language": language or "en",
                    "duration": 0.0,  # We don't track duration in this simple implementation
                    "text": result,
                    "segments": [{"id": 0, "start": 0.0, "end": 0.0, "text": result}]
                }
            else:
                return {"text": result}
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    async def _transcribe_audio_data(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """Send audio data to whisper.cpp for transcription"""
        try:
            # Prepare audio for whisper.cpp
            wav_data = self._prepare_audio_for_whisper(audio_data)
            if not wav_data:
                return ""
            
            # Prepare multipart form data for whisper.cpp /asr endpoint
            files = {
                'audio_file': ('audio.wav', wav_data, 'audio/wav')
            }
            params = {
                'task': 'transcribe',
                'language': language or 'en',
                'output': 'json'
            }
            
            # Make request to whisper.cpp service
            response = await self.client.post(
                f"{self.whisper_base_url}/asr",
                files=files,
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                return text
            else:
                logger.error(f"Whisper.cpp error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return ""
    
    def _prepare_audio_for_whisper(self, audio_data: bytes) -> Optional[bytes]:
        """Prepare audio data for whisper.cpp API"""
        try:
            # Check if data is already WAV format
            if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
                return audio_data
            
            # Assume PCM data and convert to WAV
            return self._pcm_to_wav(audio_data)
            
        except Exception as e:
            logger.error(f"Audio preparation error: {e}")
            return None
    
    def _pcm_to_wav(self, pcm_data: bytes) -> Optional[bytes]:
        """Convert PCM data to WAV format for whisper.cpp"""
        try:
            if len(pcm_data) < 2:
                return None
            
            # Convert 16-bit PCM to numpy array and resample to 16kHz
            audio_array = self._pcm_to_float32(pcm_data)
            if audio_array is None:
                return None
            
            # Convert float32 back to 16-bit PCM for WAV
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Create WAV header for 16kHz mono
            sample_rate = 16000
            num_channels = 1
            bits_per_sample = 16
            byte_rate = sample_rate * num_channels * bits_per_sample // 8
            block_align = num_channels * bits_per_sample // 8
            data_size = len(audio_int16) * 2
            
            # WAV header (44 bytes)
            wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                b'RIFF', 36 + data_size, b'WAVE', b'fmt ', 16,
                1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample,
                b'data', data_size
            )
            
            return wav_header + audio_int16.tobytes()
            
        except Exception as e:
            logger.error(f"PCM to WAV conversion error: {e}")
            return None
    
    def _pcm_to_float32(self, pcm_data: bytes) -> Optional[np.ndarray]:
        """Convert PCM bytes to float32 numpy array and resample to 16kHz"""
        try:
            # Convert 16-bit PCM to numpy array
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            
            # Convert to float32 and normalize
            audio_array = np.array(samples, dtype=np.float32) / 32768.0
            
            # Simple downsampling: 48kHz to 16kHz (take every 3rd sample)
            resampled_array = audio_array[::3]
            
            return resampled_array
            
        except Exception as e:
            logger.error(f"PCM conversion error: {e}")
            return None
    
    def _format_as_srt(self, text: str) -> str:
        """Format transcription as SRT subtitle format"""
        return f"1\n00:00:00,000 --> 00:00:10,000\n{text}\n\n"
    
    async def health_check(self) -> dict:
        """Health check endpoint"""
        try:
            # Test whisper.cpp connectivity
            response = await self.client.get(f"{self.whisper_base_url}/docs", timeout=5)
            whisper_healthy = response.status_code == 200
        except:
            whisper_healthy = False
        
        return {
            "status": "healthy" if whisper_healthy else "degraded",
            "whisper_cpp": "connected" if whisper_healthy else "disconnected",
            "bridge_version": "1.0.0",
            "active_streams": len(self.audio_streams)
        }
    
    def _load_config(self) -> dict:
        """Load configuration from file or use defaults"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'stt_config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        return {
            "whisper": {
                "host": "whisper-stt",
                "port": 9000,
                "language": "en"
            }
        }

# Create FastAPI application
app = FastAPI(
    title="Discord Audio Bridge",
    description="OpenAI-compatible STT API for Discord voice integration with Claude Code",
    version="1.0.0"
)

# Global bridge instance
bridge = DiscordAudioBridge()

@app.on_event("startup")
async def startup_event():
    """Initialize bridge on startup"""
    await bridge.start_processing()
    logger.info("Discord Audio Bridge started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await bridge.stop_processing()
    await bridge.client.aclose()
    logger.info("Discord Audio Bridge stopped")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return await bridge.health_check()

@app.post("/v1/audio/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form(None),
    prompt: str = Form(None),
    response_format: str = Form("json"),
    temperature: float = Form(0.0)
):
    """
    OpenAI-compatible audio transcription endpoint
    
    Transcribes audio files using whisper.cpp backend.
    Compatible with OpenAI's /v1/audio/transcriptions API.
    """
    return await bridge.transcribe_audio(
        file=file,
        model=model,
        language=language,
        prompt=prompt,
        response_format=response_format,
        temperature=temperature
    )

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatibility)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "whisper-1",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "discord-audio-bridge"
            }
        ]
    }

@app.post("/discord/audio")
async def receive_discord_audio(audio: bytes):
    """Endpoint to receive Discord audio data for real-time processing"""
    bridge.add_discord_audio(audio)
    return {"status": "received"}

# Function to get bridge instance for integration with audio processor
def get_bridge_instance() -> DiscordAudioBridge:
    """Get the global bridge instance for integration"""
    return bridge

def run_bridge_server(port: int = 9091):
    """Run the Discord Audio Bridge server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=False
    )

if __name__ == "__main__":
    run_bridge_server()