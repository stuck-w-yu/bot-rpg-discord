import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Setup
intents = discord.Intents.default()
# Note: To use commands like !rank, you must enable Message Content Intent in the Developer Portal
# intents.message_content = True 
intents.voice_states = True # Crucial for voice leveling
# Note: To detect all members, you must enable Server Members Intent in the Developer Portal
# intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    # Load cogs
    await load_extensions()
    
    # FORCE SYNC TO ALL GUILDS (Instant updates)
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Synced commands to guild: {guild.name} ({guild.id})")
        except Exception as e:
            print(f"Failed to sync to {guild.name}: {e}")
            
    print("------")
    print("Bot is ready! If commands don't appear, restart your Discord app (Ctrl+R).")

async def load_extensions():
    # Only load the specific voice leveling cog for now
    try:
        await bot.load_extension('cogs.voice_leveling')
        print(f'Loaded extension: cogs.voice_leveling')
    except Exception as e:
        print(f'Failed to load extension cogs.voice_leveling: {e}')
        
    try:
        await bot.load_extension('cogs.rpg_system')
        print(f'Loaded extension: cogs.rpg_system')
    except Exception as e:
        print(f'Failed to load extension cogs.rpg_system: {e}')
        
    try:
        await bot.load_extension('cogs.help')
        print(f'Loaded extension: cogs.help')
    except Exception as e:
        print(f'Failed to load extension cogs.help: {e}')

if __name__ == '__main__':
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file.")
    else:
        bot.run(TOKEN)
