import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
from .audio_processor import AudioProcessor

load_dotenv()

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Enable discord.py debug logging
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

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
                    
                    # Start transcription monitoring and status reporting
                    asyncio.create_task(self._monitor_transcriptions())
                    asyncio.create_task(self._status_reporter())
                    break
                except Exception as e:
                    print(f"❌ Failed to join Brodan channel: {e}")
        
        print("Ready to receive commands!")
        
    @commands.command(name="debug_audio")
    async def debug_audio(self, ctx):
        """Debug command to analyze recorded audio"""
        await ctx.send("🎧 Analyzing recorded audio...")
        self.audio_processor.get_audio_analysis()
        await ctx.send("Check logs for audio analysis results!")
        
    @commands.command(name="stop_debug")
    async def stop_debug(self, ctx):
        """Stop audio recording and analyze"""
        if self.audio_processor.recording:
            self.audio_processor.stop_recording(self.voice_client)
            await asyncio.sleep(1)  # Wait for files to close
            self.audio_processor.get_audio_analysis()
            await ctx.send("🎧 Audio recording stopped and analyzed - check logs!")
        else:
            await ctx.send("No recording in progress.")
        
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
    
    async def _status_reporter(self):
        """Periodic status reporting for system health"""
        while True:
            try:
                await asyncio.sleep(30)  # Report every 30 seconds
                
                # Check STT connection status
                stt_status = "🟢 Connected" if self.audio_processor.stt_client.connected else "🔴 Disconnected"
                recording_status = "🎙️ Recording" if self.audio_processor.recording else "⏸️ Stopped"
                voice_status = "🔊 Connected" if self.voice_client and self.voice_client.is_connected() else "🔇 Disconnected"
                
                print("\n" + "=" * 60)
                print("📊 SYSTEM STATUS REPORT")
                print(f"   STT Service: {stt_status}")
                print(f"   Voice Recording: {recording_status}")
                print(f"   Discord Voice: {voice_status}")
                print("=" * 60 + "\n")
                
            except Exception as e:
                print(f"Status reporting error: {e}")
                await asyncio.sleep(30)
    
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
            
            # Choose appropriate emoji and formatting
            if transcription_type == "partial" or not completed:
                icon = "🔄"
                status = "PARTIAL"
                border = "-" * 50
            else:
                icon = "🎤" 
                status = "FINAL"
                border = "=" * 50
            
            # Format the output
            print(border)
            print(f"{icon} {status} TRANSCRIPTION:")
            print(f"   📝 Text: {text}")
            
            if start_time and end_time:
                print(f"   ⏱️  Time: {start_time}s - {end_time}s")
            
            if uid:
                print(f"   🆔 Session: {uid[:8]}...")
                
            print(border)
            
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