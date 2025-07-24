import discord
import asyncio
import audioop
import struct
from typing import Optional
from .stt_client import WhisperLiveClient


class STTAudioSink(discord.sinks.Sink):
    """Custom audio sink for capturing Discord voice and streaming to STT"""
    
    def __init__(self, stt_client: WhisperLiveClient, loop: asyncio.AbstractEventLoop, energy_threshold: int = 300):
        super().__init__()
        self.stt_client = stt_client
        self.loop = loop  # Store reference to the bot's event loop
        self.energy_threshold = energy_threshold
        self.sample_rate = 48000  # Discord's sample rate
        self.channels = 2  # Discord uses stereo
        self.frame_size = 3840  # 20ms frame at 48kHz stereo 16-bit
        
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
                
                # Send to STT service using thread-safe method
                self._schedule_stt_send(mono_data)
            
            # Call parent write to maintain normal sink functionality
            return super().write(data, user)
            
        except Exception as e:
            print(f"Audio processing error: {e}")
            # Always call parent write to maintain sink functionality
            return super().write(data, user)
    
    def _schedule_stt_send(self, audio_data: bytes):
        """Thread-safe method to schedule STT sending"""
        try:
            # Use call_soon_threadsafe to schedule the coroutine in the bot's event loop
            asyncio.run_coroutine_threadsafe(self._send_to_stt(audio_data), self.loop)
        except Exception as e:
            print(f"Failed to schedule STT send: {e}")
    
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
            
            return rms > self.energy_threshold
            
        except Exception as e:
            print(f"VAD error: {e}")
            return False
    
    def _stereo_to_mono(self, stereo_data: bytes) -> bytes:
        """Convert stereo PCM to mono by taking left channel"""
        try:
            # Assuming 16-bit samples, take every other sample (left channel)
            mono_samples = []
            for i in range(0, len(stereo_data), 4):  # 4 bytes = 2 samples of 16-bit
                if i + 1 < len(stereo_data):
                    # Extract left channel (first 2 bytes of each frame)
                    left_sample = struct.unpack('<h', stereo_data[i:i+2])[0]
                    mono_samples.append(left_sample)
            
            return struct.pack(f'<{len(mono_samples)}h', *mono_samples)
            
        except Exception as e:
            print(f"Stereo to mono conversion error: {e}")
            return stereo_data
    
    async def _send_to_stt(self, audio_data: bytes):
        """Send audio data to STT service"""
        try:
            if self.stt_client.connected:
                # Log audio metrics occasionally 
                if hasattr(self, '_audio_chunk_count'):
                    self._audio_chunk_count += 1
                else:
                    self._audio_chunk_count = 1
                
                # Log every 100 chunks to avoid spam
                if self._audio_chunk_count % 100 == 0:
                    print(f"🎵 Audio metrics: {self._audio_chunk_count} chunks sent, {len(audio_data)} bytes/chunk")
                
                await self.stt_client.send_audio(audio_data)
        except Exception as e:
            print(f"STT send error: {e}")


class AudioProcessor:
    """Main audio processing coordinator"""
    
    def __init__(self):
        self.stt_client = WhisperLiveClient()
        self.audio_sink: Optional[STTAudioSink] = None
        self.recording = False
        
    async def initialize_stt(self) -> bool:
        """Initialize STT connection"""
        print("Connecting to STT service...")
        success = self.stt_client.connect()
        if success:
            print("STT service connected successfully")
        else:
            print("Failed to connect to STT service") 
        return success
    
    def create_audio_sink(self, loop: asyncio.AbstractEventLoop) -> STTAudioSink:
        """Create new audio sink for voice capture"""
        self.audio_sink = STTAudioSink(self.stt_client, loop)
        return self.audio_sink
    
    async def start_recording(self, voice_client: discord.VoiceClient):
        """Start recording voice with STT processing"""
        if self.recording:
            print("Already recording")
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
            print("Started voice recording with STT processing")
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self.recording = False
    
    def stop_recording(self, voice_client: discord.VoiceClient):
        """Stop voice recording"""
        if not self.recording:
            return
            
        try:
            voice_client.stop_recording()
            self.recording = False
            print("Stopped voice recording")
        except Exception as e:
            print(f"Error stopping recording: {e}")
    
    def _recording_finished(self, sink: discord.sinks.Sink, channel: discord.abc.Connectable, *args):
        """Callback when recording finishes"""
        print("Recording session finished")
    
    def get_latest_transcription(self):
        """Get latest transcription from STT service"""
        return self.stt_client.get_transcription()
    
    def cleanup(self):
        """Clean up resources"""
        if self.stt_client:
            self.stt_client.disconnect()