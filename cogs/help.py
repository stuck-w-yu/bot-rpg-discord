import discord
from discord import app_commands
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Bot Commands", description="Here are the available commands:", color=discord.Color.brand_green())
        
        # Leveling Commands
        embed.add_field(name="🔊 Voice Leveling", value=(
            "`/rank` - Check your current voice level and XP.\n"
            "`/setlevel` - (Admin) Manually set a user's level."
        ), inline=False)
        
        # ⚔️ Monster RPG Guide
        rpg_guide = (
            "**🦖 Monster Taming Adventure**\n"
            "1. **Start**: Use `/start` to get your team of 3 Monsters!\n"
            "2. **Battle**: Use `/adventure` to fight using **unique Skills** like *Ember* or *Hydro Pump*!\n"
            "3. **Collect**: Win battles to get **XP**, **Items**, and a chance to **CAPTURE** the enemy!\n"
            "4. **Summon**: Use `/summon` to spend Gold and get **Rare** to **Mythical** monsters!\n"
            "5. **Rarities**: Common ➡ Uncommon ➡ Rare ➡ Super Rare ➡ Ultra Rare ➡ Mythical.\n"
        )
        embed.add_field(name="🎮 How to Play", value=rpg_guide, inline=False)

        # Commands List
        commands_list = (
            "`/start` - Get your Starter Monsters 🥚\n"
            "`/summon` - Gacha for Rare Monsters (100G) 🔮\n"
            "`/adventure` - Battle with your Team ⚔️\n"
            "`/team` - View your active Team 🛡️\n"
            "`/collection` - View all captured Monsters 📖\n"
            "`/inventory` - View collected Items 🎒\n"
            "`/balance` - Check Gold/Platinum 💰\n"
            "`/trade` - Trade currency with players 🤝"
        )
        embed.add_field(name="📜 Commands", value=commands_list, inline=False)
        
        # GM Section (only visible if user is the GM)
        if interaction.user.id == 737579270083182632:
            gm_list = (
                "`/gmgive [user] [gold] [plat]` - Give Currency 💸\n"
                "`/gmset [user] [slot] [level]` - Set Monster Level 🆙"
            )
            embed.add_field(name="👑 Game Master", value=gm_list, inline=False)
    
        embed.set_footer(text="Use these commands in any channel!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
