import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from .audio_processor import AudioProcessor

load_dotenv()

class VoiceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(command_prefix="!", intents=intents)
        self.audio_processor = AudioProcessor()
        self.voice_client = None
        
    async def on_ready(self):
        print(f"🤖 Bot ready as {self.user}")
        print(f"📡 Connected to {len(self.guilds)} guilds")
        
        # Auto-join Brodan channel and start recording
        for guild in self.guilds:
            brodan_channel = discord.utils.get(guild.voice_channels, name="Brodan")
            if brodan_channel:
                try:
                    self.voice_client = await brodan_channel.connect()
                    print(f"✅ Auto-joined Brodan channel in {guild.name}")
                    
                    # Initialize STT and start recording
                    await self.audio_processor.initialize_stt()
                    await self.audio_processor.start_recording(self.voice_client)
                    
                    # Start transcription monitoring
                    asyncio.create_task(self._monitor_transcriptions())
                    break
                except Exception as e:
                    print(f"❌ Failed to join Brodan channel: {e}")
        
        print("Ready to receive commands!")
        
    async def on_voice_state_update(self, member, before, after):
        """Voice state tracking with recording management"""
        if member == self.user:
            return
            
        if after.channel and not before.channel:
            print(f"👋 User {member.display_name} joined voice channel: {after.channel.name}")
            # User joined - ensure recording is active
            if self.voice_client and not self.audio_processor.recording:
                await self.audio_processor.start_recording(self.voice_client)
            
        elif before.channel and not after.channel:
            print(f"👋 User {member.display_name} left voice channel: {before.channel.name}")
    
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
            
            # Get additional metadata if available
            language = transcription.get("language", "")
            confidence = transcription.get("confidence", "")
            timestamp = transcription.get("timestamp", "")
            
            # Format the output
            print("=" * 60)
            print(f"🎤 TRANSCRIPTION:")
            print(f"   Text: {text}")
            
            if language:
                print(f"   Language: {language}")
            if confidence:
                print(f"   Confidence: {confidence}")
            if timestamp:
                print(f"   Timestamp: {timestamp}")
                
            print("=" * 60)
            
        except Exception as e:
            print(f"Error displaying transcription: {e}")
            print(f"Raw transcription data: {transcription}")



def main():
    bot = VoiceBot()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables")
        print("Please check your .env file")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()