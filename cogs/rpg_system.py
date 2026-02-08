import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import random
import time
import math

DB_NAME = "leveling.db"

# Skill Data
SKILLS = {
    # Basic (No CD)
    "Scratch": {"power": 1.0, "cd": 0, "element": "Normal", "desc": "A basic scratch attack."},
    "Tackle": {"power": 1.0, "cd": 0, "element": "Normal", "desc": "A full-body charge."},
    "Peck": {"power": 1.0, "cd": 0, "element": "Air", "desc": "A sharp beak strike."},
    "Bite": {"power": 1.1, "cd": 0, "element": "Dark", "desc": "A strong bite."},
    
    # Tier 1 Skills (Low CD)
    "Vine Whip": {"power": 1.5, "cd": 2, "element": "Nature", "desc": "Strikes with thin vines."},
    "Rock Throw": {"power": 1.5, "cd": 2, "element": "Earth", "desc": "Hurls a small rock."},
    "Water Gun": {"power": 1.5, "cd": 2, "element": "Water", "desc": "Squirts water forcefully."},
    "Ember": {"power": 1.6, "cd": 2, "element": "Fire", "desc": "A small flame attack."},
    "Gust": {"power": 1.5, "cd": 2, "element": "Air", "desc": "Whips up a strong wind."},
    "Iron Head": {"power": 1.6, "cd": 2, "element": "Metal", "desc": "Slams with a hard head."},
    "Ice Shard": {"power": 1.6, "cd": 2, "element": "Ice", "desc": "Hurls chunks of ice."},
    "Dark Pulse": {"power": 1.7, "cd": 2, "element": "Dark", "desc": "Emits a horrible aura."},
    "Lava Plume": {"power": 1.8, "cd": 2, "element": "Magma", "desc": "Scarlet flames torch everything."},
    "Meteor Mash": {"power": 2.0, "cd": 3, "element": "Cosmic", "desc": "Punches with meteor force."},
    "Void Strike": {"power": 2.2, "cd": 3, "element": "Void", "desc": "Strikes from the void."},

    # Tier 2 Skills (Ultimates, High CD)
    "Leaf Storm": {"power": 2.5, "cd": 4, "element": "Nature", "desc": "A storm of sharp leaves."},
    "Earthquake": {"power": 2.5, "cd": 4, "element": "Earth", "desc": "Shakes the ground violently."},
    "Hydro Pump": {"power": 2.5, "cd": 4, "element": "Water", "desc": "Blasts water at high pressure."},
    "Fire Blast": {"power": 2.6, "cd": 4, "element": "Fire", "desc": "Incinerates everything."},
    "Hurricane": {"power": 2.5, "cd": 4, "element": "Air", "desc": "Traps enemy in a whirlwind."},
    "Flash Cannon": {"power": 2.6, "cd": 4, "element": "Metal", "desc": "Releases light energy."},
    "Blizzard": {"power": 2.6, "cd": 4, "element": "Ice", "desc": "Summons a howling blizzard."},
    "Hyper Fang": {"power": 2.7, "cd": 4, "element": "Normal", "desc": "A vicious bite."},
    "Eruption": {"power": 3.0, "cd": 5, "element": "Magma", "desc": "Explosive volcanic fury."},
    "Supernova": {"power": 3.5, "cd": 6, "element": "Cosmic", "desc": "A massive stellar explosion."},
    "Black Hole": {"power": 4.0, "cd": 6, "element": "Void", "desc": "Consumes all light and hope."}
}

# Monster Data with Skills
MONSTERS = {
    "Leafybug": {"rarity": "Common", "hp": 100, "attack": 10, "element": "Nature", "image": "🍃", "drop": "Leaf Essence", "skills": ["Scratch", "Vine Whip", "Leaf Storm"]},
    "Rockpup": {"rarity": "Common", "hp": 120, "attack": 8, "element": "Earth", "image": "🪨", "drop": "Hard Stone", "skills": ["Tackle", "Rock Throw", "Earthquake"]},
    "Bubblefin": {"rarity": "Common", "hp": 90, "attack": 12, "element": "Water", "image": "💧", "drop": "Water Bubble", "skills": ["Tackle", "Water Gun", "Hydro Pump"]},
    
    "Emberfox": {"rarity": "Uncommon", "hp": 130, "attack": 15, "element": "Fire", "image": "🔥", "drop": "Fox Fire", "skills": ["Scratch", "Ember", "Fire Blast"]},
    "Stormbeak": {"rarity": "Uncommon", "hp": 110, "attack": 18, "element": "Air", "image": "⚡", "drop": "Feather", "skills": ["Peck", "Gust", "Hurricane"]},
    "Ironclad": {"rarity": "Uncommon", "hp": 160, "attack": 12, "element": "Metal", "image": "🛡️", "drop": "Iron Scrap", "skills": ["Tackle", "Iron Head", "Flash Cannon"]},
    
    "Crystalstag": {"rarity": "Rare", "hp": 180, "attack": 22, "element": "Ice", "image": "💎", "drop": "Ice Shard", "skills": ["Tackle", "Ice Shard", "Blizzard"]},
    "Shadowfang": {"rarity": "Rare", "hp": 150, "attack": 28, "element": "Dark", "image": "🌑", "drop": "Shadow Orb", "skills": ["Bite", "Dark Pulse", "Hyper Fang"]},
    
    "Volcanorle": {"rarity": "Super Rare", "hp": 250, "attack": 35, "element": "Magma", "image": "🌋", "drop": "Magma Core", "skills": ["Tackle", "Lava Plume", "Eruption"]},
    
    "Starweaver": {"rarity": "Ultra Rare", "hp": 400, "attack": 50, "element": "Cosmic", "image": "✨", "drop": "Stardust", "skills": ["Tackle", "Meteor Mash", "Supernova"]},
    
    "Voidwalker": {"rarity": "Mythical Rare", "hp": 600, "attack": 80, "element": "Void", "image": "🌌", "drop": "Void Essence", "skills": ["Scratch", "Void Strike", "Black Hole"]}
}

DROP_RATES = {
    "Common": 0.50,
    "Uncommon": 0.30,
    "Rare": 0.15,
    "Super Rare": 0.05,
    "Ultra Rare": 0.01,
    "Mythical Rare": 0.001
}

# --- CUSTOM BUTTON FOR SKILLS ---
class SkillButton(discord.ui.Button):
    def __init__(self, skill_name, row, parent_view):
        self.skill_name = skill_name
        self.skill_data = SKILLS.get(skill_name, SKILLS["Tackle"])
        self.parent_view = parent_view
        
        # Style based on CD
        style = discord.ButtonStyle.secondary
        if self.skill_data['cd'] == 0: style = discord.ButtonStyle.primary
        elif self.skill_data['cd'] >= 4: style = discord.ButtonStyle.danger
        else: style = discord.ButtonStyle.success

        label = f"{skill_name}"
        if self.skill_data['cd'] > 0:
            label += f" ({self.skill_data['cd']}T)"
            
        super().__init__(style=style, label=label, row=row)

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.use_skill(interaction, self)


class CombatView(discord.ui.View):
    def __init__(self, player, player_monster, enemy_monster, cog):
        super().__init__(timeout=120)
        self.player = player
        self.player_monster = player_monster # dictionary from DB
        self.enemy_monster = enemy_monster # dictionary from constant
        self.cog = cog
        
        # Player Stats (incorporating leveled stats)
        base_hp = MONSTERS[player_monster['monster_name']]['hp']
        base_atk = MONSTERS[player_monster['monster_name']]['attack']
        level = player_monster['level']
        
        self.p_max_hp = base_hp + (level * 20)
        self.p_hp = self.p_max_hp
        self.p_atk = base_atk + (level * 3)
        self.p_skills = MONSTERS[player_monster['monster_name']].get('skills', ['Tackle', 'Scratch'])
        
        # Enemy Stats
        self.e_max_hp = enemy_monster['hp'] 
        self.e_hp = self.e_max_hp
        self.e_atk = enemy_monster['attack']
        
        self.potions = 3
        self.commenced = False
        self.combat_log = f"Battle Start!\nGo {player_monster['monster_name']}!"
        
        # Cooldown Tracker {SkillName: TurnsRemaining}
        self.cooldowns = {skill: 0 for skill in self.p_skills}

        # Setup Buttons
        self.setup_buttons()

    def setup_buttons(self):
        # Clear existing buttons
        self.clear_items()
        
        # Add Skill Buttons (Max 3)
        for i, skill in enumerate(self.p_skills[:3]):
            self.add_item(SkillButton(skill, 0, self))
            
        # Add Heal and Flee on Row 1
        self.add_item(self.heal_button)
        self.add_item(self.flee_button)
        
    def update_buttons(self):
        # Update labels/states based on CD
        for item in self.children:
            if isinstance(item, SkillButton):
                cd = self.cooldowns.get(item.skill_name, 0)
                if cd > 0:
                    item.disabled = True
                    item.label = f"{item.skill_name} ({cd})"
                else:
                    item.disabled = False
                    item.label = item.skill_name

    def get_embed(self):
        p_name = self.player_monster['monster_name']
        p_icon = MONSTERS[p_name]['image']
        e_name = self.enemy_monster['name']
        e_icon = self.enemy_monster['image']
        
        embed = discord.Embed(title=f"⚔️ Battle vs {e_name}", color=discord.Color.red())
        
        # Player Field
        embed.add_field(name=f"{p_icon} {p_name} (Lvl {self.player_monster['level']})", 
                        value=f"❤️ {self.p_hp}/{self.p_max_hp}\n⚔️ {self.p_atk} ATK\n🧪 {self.potions}", inline=True)
        
        # Enemy Field
        embed.add_field(name=f"{e_icon} {e_name}", 
                        value=f"❤️ {self.e_hp}/{self.e_max_hp}\n⚔️ {self.e_atk} ATK", inline=True)
        
        # Log with scroll-like feel
        embed.add_field(name="📜 Combat Log", value=f"```\n{self.combat_log}\n```", inline=False)
        return embed
    
    async def use_skill(self, interaction, button):
        if interaction.user != self.player: return
        
        skill_name = button.skill_name
        skill_data = button.skill_data
        
        # Cooldown Check
        if self.cooldowns.get(skill_name, 0) > 0:
            await interaction.response.send_message("Skill is on cooldown!", ephemeral=True)
            return

        # DAMAGE CALC
        base_dmg = self.p_atk
        power = skill_data['power']
        variance = random.uniform(0.9, 1.1)
        
        total_dmg = int(base_dmg * power * variance)
        
        # Critical Hit
        crit = False
        if random.random() < 0.1: # 10% Crit
            total_dmg = int(total_dmg * 1.5)
            crit = True

        self.e_hp -= total_dmg
        
        # Apply Cooldown
        self.cooldowns[skill_name] = skill_data['cd'] + 1 
        self.cooldowns[skill_name] = skill_data['cd'] 

        # Log
        self.combat_log = f"💥 Used **{skill_name}**!"
        if crit: self.combat_log += " (CRIT!)"
        self.combat_log += f"\nDealt **{total_dmg}** damage to {self.enemy_monster['name']}."

        # Check Win
        if self.e_hp <= 0:
            self.e_hp = 0
            self.combat_log += f"\n🏆 **VICTORY!** {self.enemy_monster['name']} defeated!"
            self.disable_all_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
            await self.cog.process_battle_win(interaction, self.player, self.player_monster, self.enemy_monster)
            return

        # End Turn (Enemy Attacks + Reduce CD)
        await self.end_round(interaction)

    async def end_round(self, interaction):
        # Reduce Cooldowns
        for skill in self.cooldowns:
            if self.cooldowns[skill] > 0:
                self.cooldowns[skill] -= 1
        
        self.update_buttons()
        
        # Enemy Turn
        if self.e_hp > 0:
            # Enemy attacks
            dmg = max(1, self.e_atk + random.randint(-5, 5))
            self.p_hp -= dmg
            self.combat_log += f"\n🔻 {self.enemy_monster['name']} attacked! Hit for {dmg}."
            
            if self.p_hp <= 0:
                self.p_hp = 0
                self.combat_log += "\n☠️ **DEFEAT**... Your monster fainted."
                self.disable_all_buttons()
                await interaction.response.edit_message(embed=self.get_embed(), view=self)
                return

        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def disable_all_buttons(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="Heal", style=discord.ButtonStyle.success, emoji="🧪", row=1)
    async def heal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        
        if self.potions > 0:
            heal = int(self.p_max_hp * 0.4)
            self.p_hp = min(self.p_max_hp, self.p_hp + heal)
            self.potions -= 1
            self.combat_log = f"🧪 Used Potion! Restored {heal} HP."
            await self.end_round(interaction)
        else:
            await interaction.response.send_message("Out of potions!", ephemeral=True)

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.secondary, emoji="🏃", row=1)
    async def flee_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        
        if random.random() < 0.4:
            self.combat_log = "🏃 **ESCAPED!** You got away safely."
            self.disable_all_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            self.combat_log = "🚫 **FAILED!** Couldn't escape!"
            await self.end_round(interaction)


# --- TEAM MANAGEMENT UI ---

class MonsterSelect(discord.ui.Select):
    def __init__(self, monsters, slot, cog, user_id, guild_id, parent_view):
        self.slot = slot
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        self.parent_view = parent_view
        
        options = []
        for mon in monsters:
            info = MONSTERS.get(mon['monster_name'], {})
            label = f"{mon['monster_name']} (Lvl {mon['level']})"
            desc = f"{info.get('rarity','?')} - {info.get('element','?')}"
            options.append(discord.SelectOption(label=label, description=desc, value=str(mon['id']), emoji=info.get('image', '❓')))
            
        super().__init__(placeholder=f"Select Monster for Slot {slot}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        monster_id = int(self.values[0])
        
        async with aiosqlite.connect(DB_NAME) as db:
            # 1. Clear current slot owner
            await db.execute("UPDATE user_monsters SET team_slot = 0 WHERE user_id = ? AND guild_id = ? AND team_slot = ?", (self.user_id, self.guild_id, self.slot))
            # 2. Assign new owner
            await db.execute("UPDATE user_monsters SET team_slot = ? WHERE id = ?", (self.slot, monster_id))
            await db.commit()
            
        await interaction.response.send_message(f"✅ Set **Slot {self.slot}**!", ephemeral=True)
        # Refresh the parent view
        await self.parent_view.refresh_content(interaction)


class TeamView(discord.ui.View):
    def __init__(self, cog, user_id, guild_id):
        super().__init__(timeout=180)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def refresh_content(self, interaction: discord.Interaction):
        # Helper to refresh the message embed
        team = await self.cog.get_team(self.user_id, self.guild_id)
        embed = self.cog.create_team_embed(team)
         # We can't easily edit the original message from here without passing it or using followup if we responded
        try:
             await interaction.message.edit(embed=embed, view=self)
        except:
             pass

    @discord.ui.button(label="Edit Slot 1 (Active)", style=discord.ButtonStyle.primary, emoji="1️⃣")
    async def edit_slot_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_selector(interaction, 1)

    @discord.ui.button(label="Edit Slot 2", style=discord.ButtonStyle.secondary, emoji="2️⃣")
    async def edit_slot_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_selector(interaction, 2)

    @discord.ui.button(label="Edit Slot 3", style=discord.ButtonStyle.secondary, emoji="3️⃣")
    async def edit_slot_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_selector(interaction, 3)

    async def send_selector(self, interaction: discord.Interaction, slot):
        # Get Bench (monsters not in team_slot 1, 2, or 3 OR just all monsters to allow swapping easily?)
        # Let's show ALL monsters to make it easy. Slicing top 25.
        
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM user_monsters 
                WHERE user_id = ? AND guild_id = ? 
                ORDER BY level DESC, rarity DESC LIMIT 25
            """, (self.user_id, self.guild_id))
            monsters = [dict(row) for row in await cursor.fetchall()]
            
        if not monsters:
            await interaction.response.send_message("No monsters found!", ephemeral=True)
            return

        view = discord.ui.View()
        view.add_item(MonsterSelect(monsters, slot, self.cog, self.user_id, self.guild_id, self))
        await interaction.response.send_message(f"Select a monster for **Slot {slot}**:", view=view, ephemeral=True)

class RPGSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.adventure_cooldowns = {} 

    async def cog_load(self):
        await self.init_db()

    async def init_db(self):
        async with aiosqlite.connect(DB_NAME) as db:
            # Check for team_slot column and add if missing
            db.row_factory = aiosqlite.Row
            try:
                await db.execute("ALTER TABLE user_monsters ADD COLUMN team_slot INTEGER DEFAULT 0")
                print("Added team_slot column.")
                # Migration: Set existing team members (in_team=1) to slots 1, 2, 3
                cursor = await db.execute("SELECT id FROM user_monsters WHERE in_team = 1")
                rows = await cursor.fetchall()
                for i, row in enumerate(rows):
                    if i < 3:
                        await db.execute("UPDATE user_monsters SET team_slot = ? WHERE id = ?", (i + 1, row['id']))
                await db.commit()
            except Exception as e:
                # Column likely exists
                pass

            # Users
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
            
            # User Monsters - Ensure table exists (though migration handles alter)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_monsters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    monster_name TEXT,
                    rarity TEXT,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    in_team BOOLEAN DEFAULT 0,
                    team_slot INTEGER DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    async def add_monster(self, user_id, guild_id, monster_name, in_team=False):
        monster_info = MONSTERS.get(monster_name)
        if not monster_info: return
        
        # Determine slot if in_team is True (legacy support or starter)
        team_slot = 0
        if in_team:
             # Find first available slot 1-3
             current_team = await self.get_team(user_id, guild_id)
             used_slots = [m['team_slot'] for m in current_team]
             for s in [1, 2, 3]:
                 if s not in used_slots:
                     team_slot = s
                     break
        
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO user_monsters (user_id, guild_id, monster_name, rarity, level, xp, in_team, team_slot)
                VALUES (?, ?, ?, ?, 1, 0, ?, ?)
            """, (user_id, guild_id, monster_name, monster_info['rarity'], in_team, team_slot))
            await db.commit()

    async def add_item(self, user_id, guild_id, item_name, quantity=1):
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT quantity FROM user_items WHERE user_id = ? AND guild_id = ? AND item_name = ?", (user_id, guild_id, item_name))
            result = await cursor.fetchone()
            
            if result:
                new_qty = result[0] + quantity
                await db.execute("UPDATE user_items SET quantity = ? WHERE user_id = ? AND guild_id = ? AND item_name = ?", (new_qty, user_id, guild_id, item_name))
            else:
                await db.execute("INSERT INTO user_items (user_id, guild_id, item_name, quantity) VALUES (?, ?, ?, ?)", (user_id, guild_id, item_name, quantity))
            await db.commit()

    async def get_team(self, user_id, guild_id):
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM user_monsters 
                WHERE user_id = ? AND guild_id = ? AND team_slot > 0 
                ORDER BY team_slot ASC LIMIT 3
            """, (user_id, guild_id)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_active_monster(self, user_id, guild_id):
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM user_monsters 
                WHERE user_id = ? AND guild_id = ? AND team_slot = 1 
            """, (user_id, guild_id)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def process_battle_win(self, interaction, user, my_monster, enemy_monster_data):
        msg = ""
        
        # 1. Gold Reward
        gold_gain = enemy_monster_data.get('gold', 20)
        await self.update_balance(user.id, interaction.guild_id, amount_gold=gold_gain)
        msg += f"\n💰 Earned **{gold_gain} Gold**!"

        # 2. XP Gain
        xp_gain = 100
        new_xp = my_monster['xp'] + xp_gain
        xp_needed = 100 * (my_monster['level'] ** 2)
        
        leveled_up = False
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            my_monster['level'] += 1
            xp_needed = 100 * (my_monster['level'] ** 2)
            leveled_up = True
            
        async with aiosqlite.connect(DB_NAME) as db:
             await db.execute("UPDATE user_monsters SET xp = ?, level = ? WHERE id = ?", 
                              (new_xp, my_monster['level'], my_monster['id']))
             await db.commit()

        msg += f"\n📊 {my_monster['monster_name']} gained {xp_gain} XP."
        if leveled_up:
            msg += f"\n🎉 **LEVEL UP!** Now Level {my_monster['level']}!"

        # 3. Item Drop (50% Chance)
        target_monster_name = enemy_monster_data['name']
        drop_item = MONSTERS.get(target_monster_name, {}).get('drop')
        
        if drop_item and random.random() < 0.5:
             await self.add_item(user.id, interaction.guild_id, drop_item, 1)
             msg += f"\n📦 Drop: **{drop_item}**"

        # 4. Monster Capture
        # Check if enemy is in our MONSTER list
        if target_monster_name in MONSTERS:
            rarity = MONSTERS[target_monster_name]['rarity']
            rate = DROP_RATES.get(rarity, 0)
            
            if random.random() < rate:
                await self.add_monster(user.id, interaction.guild_id, target_monster_name)
                msg += f"\n🥚 **CAPTURED!** You obtained a **{target_monster_name}** ({rarity})!"

        try:
             await interaction.followup.send(content=f"{user.mention} {msg}")
        except:
             pass 

    # --- Balance Helpers ---
    async def update_balance(self, user_id, guild_id, amount_gold=0, amount_platinum=0):
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            if not await cursor.fetchone():
                 await db.execute("INSERT INTO users (user_id, guild_id, gold, platinum) VALUES (?, ?, ?, ?)", (user_id, guild_id, amount_gold, amount_platinum))
            else:
                 await db.execute("UPDATE users SET gold = gold + ?, platinum = platinum + ? WHERE user_id = ? AND guild_id = ?", (amount_gold, amount_platinum, user_id, guild_id))
            await db.commit()
            
    async def get_balance(self, user_id, guild_id):
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT gold, platinum FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            result = await cursor.fetchone()
            if result: return result[0], result[1]
            return 0, 0

    # --- COMMANDS ---

    @app_commands.command(name="start", description="Begin your adventure! Receive 3 starter monsters.")
    async def start(self, interaction: discord.Interaction):
        team = await self.get_team(interaction.user.id, interaction.guild_id)
        if team:
            await interaction.response.send_message("You have already started your adventure!", ephemeral=True)
            return

        starters = ["Leafybug", "Rockpup", "Bubblefin"]
        for mon in starters:
            await self.add_monster(interaction.user.id, interaction.guild_id, mon, in_team=True)
            
        embed = discord.Embed(title="🎒 Adventure Started!", description="You received 3 Starter Monsters!", color=discord.Color.green())
        embed.add_field(name="Team", value="🍃 Leafybug\n🪨 Rockpup\n💧 Bubblefin", inline=False)
        embed.set_footer(text="Use /team to view them or /adventure to battle!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="adventure", description="Battle with your active monster!")
    async def adventure(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        current_time = time.time()
        if user_id in self.adventure_cooldowns:
            elapsed = current_time - self.adventure_cooldowns[user_id]
            if elapsed < 10:
                remaining = int(10 - elapsed)
                await interaction.response.send_message(f"⏳ Rest for {remaining}s.", ephemeral=True)
                return
        
        active_mon = await self.get_active_monster(user_id, interaction.guild_id)
        if not active_mon:
            await interaction.response.send_message("❌ You have no monsters in Slot 1! Use `/team` to set your Active monster.", ephemeral=True)
            return

        self.adventure_cooldowns[user_id] = current_time

        rarities = ["Common", "Uncommon", "Rare", "Super Rare", "Ultra Rare", "Mythical Rare"]
        weights = [0.5, 0.3, 0.15, 0.04, 0.009, 0.001]
        chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
        
        possible_enemies = [name for name, data in MONSTERS.items() if data['rarity'] == chosen_rarity]
        if not possible_enemies: possible_enemies = ["Leafybug"] 
        
        enemy_name = random.choice(possible_enemies)
        enemy_stats = MONSTERS[enemy_name]
        
        enemy_data = {
            'name': enemy_name,
            'hp': enemy_stats['hp'],
            'attack': enemy_stats['attack'],
            'image': enemy_stats['image'],
            'gold': random.randint(10, 50) * (rarities.index(chosen_rarity) + 1),
            'xp_yield': 50
        }

        view = CombatView(interaction.user, active_mon, enemy_data, self)
        await interaction.response.send_message(embed=view.get_embed(), view=view)

    def create_team_embed(self, team):
        embed = discord.Embed(title="🛡️ Your Team", color=discord.Color.blue())
        
        # Create map of slots
        slots = {1: None, 2: None, 3: None}
        for mon in team:
            slots[mon['team_slot']] = mon
            
        for i in range(1, 4):
            mon = slots[i]
            if mon:
                info = MONSTERS.get(mon['monster_name'], {})
                is_active = " (Active 🌟)" if i == 1 else ""
                stats = f"Lvl {mon['level']} | {info.get('rarity', 'Unknown')}\nATK: {info.get('attack', '?')} | El: {info.get('element', '?')}"
                embed.add_field(name=f"Slot {i}: {info.get('image','')} {mon['monster_name']}{is_active}", value=stats, inline=False)
            else:
                embed.add_field(name=f"Slot {i}: 🚫 Empty", value="Use buttons to set.", inline=False)
        return embed

    @app_commands.command(name="team", description="View and manage your team")
    async def team(self, interaction: discord.Interaction):
        team = await self.get_team(interaction.user.id, interaction.guild_id)
        
        # Even if empty, show the UI so they can set it?
        # But get_team might be empty if they never started.
        if not team:
             pass # Continue to show empty team
             
        embed = self.create_team_embed(team)
        view = TeamView(self, interaction.user.id, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="collection", description="View all your monsters")
    async def collection(self, interaction: discord.Interaction):
         async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM user_monsters WHERE user_id = ? AND guild_id = ? ORDER BY rarity DESC, level DESC", (interaction.user.id, interaction.guild_id))
            all_monsters = await cursor.fetchall()
            
         if not all_monsters:
             await interaction.response.send_message("Empty collection.", ephemeral=True)
             return

         desc = ""
         for mon in all_monsters[:15]: 
             info = MONSTERS.get(mon['monster_name'], {})
             icon = info.get('image', '❓')
             slot_tag = f" [Slot {mon['team_slot']}]" if mon['team_slot'] > 0 else ""
             desc += f"{icon} **{mon['monster_name']}** (Lvl {mon['level']}) - {mon['rarity']}{slot_tag}\n"
             
         if len(all_monsters) > 15:
             desc += f"...and {len(all_monsters) - 15} more."
             
         embed = discord.Embed(title=f"📖 Monster Collection ({len(all_monsters)})", description=desc, color=discord.Color.gold())
         await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="View your collected items")
    async def inventory(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT item_name, quantity FROM user_items WHERE user_id = ? AND guild_id = ? AND quantity > 0", (interaction.user.id, interaction.guild_id))
            items = await cursor.fetchall()
            
        if not items:
            await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
            return
            
        embed = discord.Embed(title="🎒 Inventory", color=discord.Color.orange())
        desc = ""
        for item in items:
            desc += f"📦 **{item['item_name']}**: x{item['quantity']}\n"
            
        embed.description = desc
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="Check your RPG wallet")
    async def balance(self, interaction: discord.Interaction):
        gold, platinum = await self.get_balance(interaction.user.id, interaction.guild_id)
        embed = discord.Embed(title=f"💰 {interaction.user.display_name}'s Wallet", color=discord.Color.gold())
        embed.add_field(name="🟡 Gold", value=f"{gold:,}", inline=True)
        embed.add_field(name="⚪ Platinum", value=f"{platinum:,}", inline=True)
        await interaction.response.send_message(embed=embed)

    # --- GM COMMANDS ---
    def is_gm(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == 737579270083182632

    @app_commands.command(name="gmgive", description="[GM] Give Gold/Platinum to a user")
    async def gmgive(self, interaction: discord.Interaction, user: discord.User, gold: int = 0, platinum: int = 0):
        if not self.is_gm(interaction):
            await interaction.response.send_message("❌ You are not the Game Master!", ephemeral=True)
            return
            
        await self.update_balance(user.id, interaction.guild_id, amount_gold=gold, amount_platinum=platinum)
        await interaction.response.send_message(f"✅ Gave **{gold}G** and **{platinum}P** to {user.mention}.", ephemeral=True)

    @app_commands.command(name="gmset", description="[GM] Set Monster Level for a user's slot")
    async def gmset(self, interaction: discord.Interaction, user: discord.User, slot: int, level: int):
        if not self.is_gm(interaction):
            await interaction.response.send_message("❌ You are not the Game Master!", ephemeral=True)
            return
            
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM user_monsters WHERE user_id = ? AND guild_id = ? AND team_slot = ?", (user.id, interaction.guild_id, slot))
            monster = await cursor.fetchone()
            
            if not monster:
                await interaction.response.send_message(f"❌ {user.display_name} has no monster in Slot {slot}.", ephemeral=True)
                return
                
            await db.execute("UPDATE user_monsters SET level = ? WHERE id = ?", (level, monster['id']))
            await db.commit()
            
        await interaction.response.send_message(f"✅ Set {user.display_name}'s Slot {slot} monster to **Level {level}**.", ephemeral=True)

    @app_commands.command(name="summon", description="Summon a Monster! (Cost: 100 Gold)")
    async def summon(self, interaction: discord.Interaction):
        cost = 100
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        
        # Check Balance
        params = (user_id, guild_id)
        current_gold, _ = await self.get_balance(*params)
        
        if current_gold < cost:
            await interaction.response.send_message(f"❌ You need **{cost} Gold** to summon! You have {current_gold}.", ephemeral=True)
            return
            
        # Deduct Gold
        await self.update_balance(user_id, guild_id, amount_gold=-cost)
        
        # Gacha Logic (No Commons)
        rarities = ["Uncommon", "Rare", "Super Rare", "Ultra Rare", "Mythical Rare"]
        weights = [0.60, 0.25, 0.10, 0.04, 0.01]
        
        chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
        
        # Filter pool
        pool = [name for name, data in MONSTERS.items() if data['rarity'] == chosen_rarity]
        if not pool: pool = ["Emberfox"] # Fallback
        
        monster_name = random.choice(pool)
        mon_data = MONSTERS[monster_name]
        
        # Add to DB
        await self.add_monster(user_id, guild_id, monster_name)
        
        # Animation / Embed
        embed = discord.Embed(title="🔮 Summoning...", description="You spent 100 Gold...", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)
        
        import asyncio
        await asyncio.sleep(2)
        
        result_embed = discord.Embed(title=f"✨ You summoned **{monster_name}**!", color=discord.Color.from_str("#FFD700"))
        result_embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3R6eWJueDl5eXJueDl5eXJueDl5eXJueDl5eXJueDl5eXJcJmN0PWc/3o7aD2saalBwwftBIY/giphy.gif") # Placeholder or remove
        result_embed.add_field(name="Rarity", value=f"**{chosen_rarity}**")
        result_embed.add_field(name="Element", value=f"{mon_data['image']} {mon_data['element']}")
        result_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.edit_original_response(embed=result_embed)

async def setup(bot):
    await bot.add_cog(RPGSystem(bot))
