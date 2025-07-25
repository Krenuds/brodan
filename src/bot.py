import discord
import os
import asyncio
import logging
import threading
import io
import tempfile
from dotenv import load_dotenv
from .audio_processor import AudioProcessor
from .discord_audio_bridge import run_bridge_server
from .service_checker import wait_for_services
from .tts_client import PiperTTSClient
from .claude_bridge import ClaudeBridge

load_dotenv()

# Configure logging - only critical and transcription data
logging.basicConfig(
    level=logging.WARNING,  # Only warnings and above
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Suppress discord.py logging except errors
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.ERROR)

class VoiceBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        
        super().__init__(intents=intents)
        self.audio_processor = AudioProcessor()
        self.tts_client = PiperTTSClient()
        self.claude_bridge = ClaudeBridge()
        self.voice_client = None
        self.last_transcription_text = ""  # Track last displayed text
        
    async def on_ready(self):
        print(f"🤖 Bot ready as {self.user}")
        
        # Auto-join Brodan channel and start recording
        for guild in self.guilds:
            brodan_channel = discord.utils.get(guild.voice_channels, name="Brodan")
            if brodan_channel:
                try:
                    self.voice_client = await brodan_channel.connect()
                    print(f"✅ Connected to Brodan channel")
                    
                    # Initialize STT and start recording
                    await self.audio_processor.initialize_stt()
                    await self.audio_processor.start_recording(self.voice_client)
                    
                    # Start transcription monitoring only
                    asyncio.create_task(self._monitor_transcriptions())
                    break
                except Exception as e:
                    print(f"❌ Failed to join Brodan channel: {e}")
        
        
    async def on_voice_state_update(self, member, before, after):
        """Voice state tracking with recording management"""
        if member == self.user:
            return
            
        if after.channel and not before.channel:
            # User joined - ensure recording is active
            if self.voice_client and not self.audio_processor.recording:
                await self.audio_processor.start_recording(self.voice_client)
    
    async def _monitor_transcriptions(self):
        """Monitor and log transcription results"""
        while True:
            try:
                transcription = self.audio_processor.get_latest_transcription()
                if transcription:
                    self._display_transcription(transcription)
                
                await asyncio.sleep(0.1)  # Check every 100ms
            except Exception as e:
                print(f"Transcription monitoring error: {e}")
                await asyncio.sleep(1)
    
    def _display_transcription(self, transcription):
        """Format and display transcription results"""
        try:
            text = transcription.get("text", "").strip()
            if not text:
                return
            
            # Skip duplicates
            if text == self.last_transcription_text:
                return
            
            # Get transcription metadata
            transcription_type = transcription.get("type", "unknown")
            completed = transcription.get("completed", True)
            
            # Simple output for transcriptions
            if transcription_type == "partial" or not completed:
                # Skip partial transcriptions to reduce noise
                print(f"🔍 Partial: {text[:50]}..." if len(text) > 50 else f"🔍 Partial: {text}")
                return
            else:
                # Only respond to substantial final transcriptions
                if len(text.strip()) < 3:  # Skip very short utterances
                    print(f"⏭️ Skipping short: '{text}'")
                    return
                
                # Skip audio feedback (repeated characters indicate feedback)
                if any(char * 10 in text for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'):
                    print(f"🔄 Skipping audio feedback: {text[:50]}...")
                    return
                
                # Skip if currently playing audio (prevent feedback)
                if self.voice_client and self.voice_client.is_playing():
                    print(f"🔇 Skipping during playback: {text[:30]}...")
                    return
                    
                # Only show final transcriptions
                print(f"🎤 {text}")
                self.last_transcription_text = text
                
                # Generate TTS response and play in voice channel
                asyncio.create_task(self._handle_voice_response(text))
            
        except Exception as e:
            print(f"Error displaying transcription: {e}")
            print(f"Raw transcription data: {transcription}")

    async def _handle_voice_response(self, input_text: str):
        """Generate TTS response and play in voice channel"""
        try:
            # Process input through Claude Code bridge
            print(f"🔄 Processing with Claude: {input_text}")
            response_text = await self.claude_bridge.process_voice_input(input_text)
            
            # Generate TTS audio
            audio_data = await self.tts_client.synthesize(response_text)
            if not audio_data:
                print("❌ TTS generation failed")
                return
            
            # Play audio in voice channel
            if self.voice_client and self.voice_client.is_connected():
                # Save audio to temporary file for FFmpeg compatibility
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file.flush()
                    
                    # Create audio source with proper mono-to-stereo conversion
                    audio_source = discord.PCMVolumeTransformer(
                        discord.FFmpegPCMAudio(
                            temp_file.name,
                            options='-ac 2 -ar 48000'  # Convert mono 22kHz to stereo 48kHz
                        )
                    )
                    
                    # Play the audio
                    if not self.voice_client.is_playing():
                        self.voice_client.play(audio_source)
                        print(f"🔊 Playing TTS response: {response_text}")
                    else:
                        print("⏳ Audio already playing, skipping...")
            else:
                print("❌ No voice connection available")
                
        except Exception as e:
            print(f"Error handling voice response: {e}")



async def wait_and_start_bot():
    """Wait for services and start the bot"""
    # Wait for all backend services to be ready
    services_ready = await wait_for_services()
    
    if not services_ready:
        print("❌ STARTUP FAILED: Not all services are ready")
        print("Please check your docker-compose logs and try again")
        return False
    
    # Start Discord bot
    bot = VoiceBot()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables")
        print("Please check your .env file")
        return False
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")
        return False
    
    return True

def main():
    # Start Discord Audio Bridge server in background thread
    bridge_port = int(os.getenv('DISCORD_AUDIO_BRIDGE_PORT', 9091))
    bridge_thread = threading.Thread(
        target=run_bridge_server,
        args=(bridge_port,),
        daemon=True
    )
    bridge_thread.start()
    print(f"🌉 Discord Audio Bridge started on port {bridge_port}")
    
    # Wait for services and start bot
    try:
        asyncio.run(wait_and_start_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot shutdown requested")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()