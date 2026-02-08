import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import time
import math

DB_NAME = "leveling.db"

class VoiceLeveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_join_times = {}  # {user_id: join_timestamp}
        self.xp_per_minute = 10  # Amount of XP given per minute

    async def cog_load(self):
        await self.init_db()

    async def init_db(self):
        async with aiosqlite.connect(DB_NAME) as db:
            # Check if we need to migrate the table (simple check: is user_id correct PK?)
            # For this update, we'll try to create the new table definition.
            # If the old table exists with single PK, it might error or need migration.
            # Ideally, we rename the old table and copy data, or just ensuring new installs work.
            # Given the error provided by user, the table exists with bad schema.
            
            # Smart Migration: Check if user_id is the single PK
            cursor = await db.execute("PRAGMA table_info(users)")
            infos = await cursor.fetchall()
            # infos format: (cid, name, type, notnull, dflt_value, pk)
            
            # If table exists and user_id is the ONLY pk, and guild_id exists...
            # We will just ensure the CREATE TABLE works for new setups or utilize a migration logic if strictly needed.
            # For simplicity in this step, I will use "CREATE TABLE IF NOT EXISTS" with the NEW schema.
            # Note: SQLite won't change existing schema with CREATE IF NOT EXISTS.
            # To fix the user's CRASH, we likely need to drop/recreate if it's broken, OR the user might start fresh.
            # I will implement a safe migration:
            
            needs_migration = False
            pk_count = 0
            for col in infos:
                if col[5] > 0: # pk flag
                    pk_count += 1
            
            if infos and pk_count == 1: # Old schema detected
                print("Migrating database users table...")
                await db.execute("ALTER TABLE users RENAME TO users_old")
                needs_migration = True

            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    gold INTEGER DEFAULT 0,
                    platinum INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            if needs_migration:
                 # Attempt to restore data
                 try:
                    await db.execute("""
                        INSERT INTO users (user_id, guild_id, xp, level)
                        SELECT user_id, guild_id, xp, level FROM users_old
                    """)
                    await db.execute("DROP TABLE users_old")
                    print("Migration complete.")
                 except Exception as e:
                     print(f"Migration partial error (might have duplicates): {e}")

            await db.commit()

    def calculate_level(self, xp):
        # Level = 0.1 * sqrt(XP)
        level = int(0.1 * math.sqrt(xp))
        return min(level, 200) # Cap at level 200

    async def add_xp(self, user_id, guild_id, xp_to_add):
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT xp, level FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            result = await cursor.fetchone()

            if result:
                current_xp, current_level = result
                new_xp = current_xp + xp_to_add
                new_level = self.calculate_level(new_xp)
                
                await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ? AND guild_id = ?", (new_xp, new_level, user_id, guild_id))
                
                if new_level > current_level:
                    return new_level
            else:
                new_level = self.calculate_level(xp_to_add)
                await db.execute("INSERT INTO users (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)", (user_id, guild_id, xp_to_add, new_level))
                if new_level > 0:
                    return new_level
            
            await db.commit()
            return None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        print(f"Voice update detected for: {member.name} | Channel: {after.channel}")
        if member.bot:
            return

        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            self.voice_join_times[member.id] = time.time()
            print(f"{member.name} joined voice.")

        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_join_times:
                join_time = self.voice_join_times.pop(member.id)
                duration = time.time() - join_time
                
                if duration > 60:
                    minutes = duration / 60
                    xp_gained = int(minutes * self.xp_per_minute)
                    
                    if xp_gained > 0:
                        try:
                            new_level = await self.add_xp(member.id, member.guild.id, xp_gained)
                            print(f"{member.name} gained {xp_gained} XP.")
                            
                            if new_level:
                                channel = member.guild.system_channel 
                                if channel:
                                    await channel.send(f"🎉 Congratulations {member.mention}! You reached Voice Level {new_level}!")
                        except Exception as e:
                            print(f"Error adding XP: {e}")

    @app_commands.command(name="rank", description="Check your voice level")
    async def check_rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT xp, level FROM users WHERE user_id = ? AND guild_id = ?", (member.id, interaction.guild_id))
            result = await cursor.fetchone()
            
            if result:
                xp, level = result
                if level < 200:
                    next_level_xp = 100 * ((level + 1) ** 2)
                    xp_needed = next_level_xp - xp
                    await interaction.response.send_message(f"📊 **{member.name}'s Rank**\nLevel: {level}\nXP: {xp}\nXP to next level: {xp_needed}")
                else:
                    await interaction.response.send_message(f"📊 **{member.name}'s Rank**\nLevel: {level} (MAX)\nXP: {xp}")
            else:
                await interaction.response.send_message(f"📊 **{member.name}'s Rank**\nLevel: 0\nXP: 0")

    @app_commands.command(name="setlevel", description="Manually set a user's level (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, member: discord.Member, level: int):
        if level < 0 or level > 200:
            await interaction.response.send_message("Level must be between 0 and 200.", ephemeral=True)
            return

        new_xp = 100 * (level ** 2)
        
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ? AND guild_id = ?", (member.id, interaction.guild_id))
            if await cursor.fetchone():
                await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ? AND guild_id = ?", (new_xp, level, member.id, interaction.guild_id))
            else:
                 await db.execute("INSERT INTO users (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)", (member.id, interaction.guild_id, new_xp, level))
            await db.commit()
            
        await interaction.response.send_message(f"✅ Set {member.mention}'s level to {level}.")

async def setup(bot):
    await bot.add_cog(VoiceLeveling(bot))
