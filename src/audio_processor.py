import discord
import asyncio
import audioop
import struct
import logging
import json
import os
from typing import Optional
from .stt_client import WhisperLiveClient
from .discord_audio_bridge import get_bridge_instance


class STTAudioSink(discord.sinks.Sink):
    """Custom audio sink for capturing Discord voice and streaming to STT"""
    
    def __init__(self, stt_client: WhisperLiveClient, loop: asyncio.AbstractEventLoop, config: dict):
        super().__init__()
        self.stt_client = stt_client
        self.loop = loop  # Store reference to the bot's event loop
        
        # Load audio settings from config
        audio_config = config.get('audio', {})
        self.energy_threshold = audio_config.get('energy_threshold', 50)
        self.sample_rate = audio_config.get('sample_rate', 48000)  # Discord's sample rate
        self.channels = audio_config.get('channels', 2)  # Discord uses stereo
        self.frame_size = 3840  # 20ms frame at 48kHz stereo 16-bit
        
        # Discord Audio Bridge integration
        self.bridge = get_bridge_instance()
        
    def wants_opus(self) -> bool:
        """We want PCM data, not Opus"""
        return False
    
    def write(self, data, user):
        """Override write method to intercept and process audio data"""
        try:
            # Process the raw audio data from Discord
            if hasattr(data, 'decrypted_data'):
                pcm_data = data.decrypted_data
            elif hasattr(data, 'packet'):
                pcm_data = data.packet
            else:
                # Fallback - data might be raw bytes
                pcm_data = data
            
            if not pcm_data:
                return super().write(data, user)
            
            
            # Simple voice activity detection
            if self._is_speech(pcm_data):
                # Convert stereo to mono for STT (take left channel)
                mono_data = self._stereo_to_mono(pcm_data)
                
                # Send to both STT service and Discord Audio Bridge
                self._schedule_stt_send(mono_data)
                
                # Send to Discord Audio Bridge for voice-mode MCP integration
                if self.bridge and mono_data:
                    self.bridge.add_discord_audio(mono_data)
            
            # Call parent write to maintain normal sink functionality
            return super().write(data, user)
            
        except Exception as e:
            logging.error(f"Error in STTAudioSink.write: {e}")
            # Always call parent write to maintain sink functionality
            return super().write(data, user)
    
    def _schedule_stt_send(self, audio_data: bytes):
        """Thread-safe method to schedule STT sending"""
        try:
            # Use call_soon_threadsafe to schedule the coroutine in the bot's event loop
            asyncio.run_coroutine_threadsafe(self._send_to_stt(audio_data), self.loop)
        except Exception as e:
            logging.error(f"Error scheduling STT send: {e}")
    
    def _is_speech(self, pcm_data: bytes) -> bool:
        """Basic voice activity detection using energy threshold"""
        try:
            # Calculate RMS energy
            if len(pcm_data) < 2:
                return False
                
            # Convert bytes to 16-bit integers
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            
            # Calculate RMS
            sum_squares = sum(sample * sample for sample in samples)
            rms = (sum_squares / len(samples)) ** 0.5
            
            is_speech = rms > self.energy_threshold
            
            
            return is_speech
            
        except Exception as e:
            logging.debug(f"Voice activity detection error: {e}")
            return False
    
    def _stereo_to_mono(self, stereo_data: bytes) -> bytes:
        """Convert stereo PCM to mono by mixing both channels"""
        try:
            if len(stereo_data) < 4:  # Need at least 4 bytes for one stereo sample
                return stereo_data
            
            # Convert stereo to mono by averaging left and right channels
            mono_samples = []
            for i in range(0, len(stereo_data), 4):  # 4 bytes = 1 stereo frame (16-bit L + 16-bit R)
                if i + 3 < len(stereo_data):
                    # Extract left and right samples
                    left_sample = struct.unpack('<h', stereo_data[i:i+2])[0]
                    right_sample = struct.unpack('<h', stereo_data[i+2:i+4])[0]
                    
                    # Mix by averaging (prevent overflow)
                    mixed_sample = (left_sample + right_sample) // 2
                    mono_samples.append(mixed_sample)
            
            if not mono_samples:
                return b''
            
            return struct.pack(f'<{len(mono_samples)}h', *mono_samples)
            
        except Exception as e:
            logging.debug(f"Stereo to mono conversion error: {e}")
            # Fallback: return original data truncated to valid length
            return stereo_data[:len(stereo_data) - (len(stereo_data) % 4)]
    
    async def _send_to_stt(self, audio_data: bytes):
        """Send audio data to STT service"""
        try:
            if self.stt_client.connected:
                
                await self.stt_client.send_audio(audio_data)
        except Exception as e:
            logging.debug(f"Error sending audio to STT: {e}")
    
    def format_audio(self, audio):
        """Required method for discord.sinks.Sink compatibility"""
        # This method is called during cleanup - we don't need to format anything
        # since we're processing audio in real-time via the write() method
        pass


class AudioProcessor:
    """Main audio processing coordinator"""
    
    def __init__(self):
        self.config = self._load_config()
        self.stt_client = WhisperLiveClient()
        self.audio_sink: Optional[STTAudioSink] = None
        self.recording = False
        
    async def initialize_stt(self) -> bool:
        """Initialize STT connection with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            success = self.stt_client.connect()
            if success:
                print("✅ Connected to STT service")
                return True
            
            if attempt < max_retries - 1:
                print(f"⏳ STT connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print("❌ Failed to connect to STT service after all retries")
        
        return False
    
    def create_audio_sink(self, loop: asyncio.AbstractEventLoop) -> STTAudioSink:
        """Create new audio sink for voice capture"""
        self.audio_sink = STTAudioSink(self.stt_client, loop, self.config)
        return self.audio_sink
    
    async def start_recording(self, voice_client: discord.VoiceClient):
        """Start recording voice with STT processing"""
        if self.recording:
            logging.debug("Already recording")
            return
            
        try:
            # Ensure STT is connected
            if not self.stt_client.connected:
                await self.initialize_stt()
            
            
            # Get the current event loop and create audio sink
            loop = asyncio.get_event_loop()
            sink = self.create_audio_sink(loop)
            voice_client.start_recording(sink, self._recording_finished)
            self.recording = True
            
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.recording = False
    
    def stop_recording(self, voice_client: discord.VoiceClient):
        """Stop voice recording"""
        if not self.recording:
            return
            
        try:
            voice_client.stop_recording()
            self.recording = False
        except Exception as e:
            logging.error(f"Error stopping recording: {e}")
    
    def _recording_finished(self, sink: discord.sinks.Sink, *args):
        """Callback when recording finishes"""
        # Handle variable arguments as Discord.py may pass different parameters
        logging.debug(f"Recording finished with sink: {sink}, args: {args}")
        pass
    
    def get_latest_transcription(self):
        """Get latest transcription from STT service"""
        return self.stt_client.get_transcription()
    
    
    def cleanup(self):
        """Clean up resources"""
        if self.stt_client:
            self.stt_client.disconnect()
    
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
            "audio": {
                "energy_threshold": 50,
                "sample_rate": 48000,
                "channels": 2
            }
        }