import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class VoiceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(command_prefix="!", intents=intents)
        
    async def on_ready(self):
        print(f"🤖 Bot ready as {self.user}")
        print(f"📡 Connected to {len(self.guilds)} guilds")
        
        # Auto-join Brodan channel
        for guild in self.guilds:
            brodan_channel = discord.utils.get(guild.voice_channels, name="Brodan")
            if brodan_channel:
                try:
                    await brodan_channel.connect()
                    print(f"✅ Auto-joined Brodan channel in {guild.name}")
                    break
                except Exception as e:
                    print(f"❌ Failed to join Brodan channel: {e}")
        
        print("Ready to receive commands!")
        
    async def on_voice_state_update(self, member, before, after):
        """Basic voice state tracking for testing"""
        if member == self.user:
            return
            
        if after.channel and not before.channel:
            print(f"👋 User {member.display_name} joined voice channel: {after.channel.name}")
            
        elif before.channel and not after.channel:
            print(f"👋 User {member.display_name} left voice channel: {before.channel.name}")



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