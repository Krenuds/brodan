import discord
import os
import asyncio
import logging
import threading
from dotenv import load_dotenv
from .audio_processor import AudioProcessor
from .discord_audio_bridge import run_bridge_server

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
        self.voice_client = None
        
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
            
            # Get transcription metadata
            start_time = transcription.get("start", "")
            end_time = transcription.get("end", "")
            transcription_type = transcription.get("type", "unknown")
            completed = transcription.get("completed", True)
            uid = transcription.get("uid", "")
            
            # Simple output for transcriptions
            if transcription_type == "partial" or not completed:
                # Skip partial transcriptions to reduce noise
                return
            else:
                # Only show final transcriptions
                print(f"🎤 {text}")
            
        except Exception as e:
            print(f"Error displaying transcription: {e}")
            print(f"Raw transcription data: {transcription}")



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
    
    # Start Discord bot
    bot = VoiceBot()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables")
        print("Please check your .env file")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()