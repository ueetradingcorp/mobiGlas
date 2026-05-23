"""
Zutaten-Cog für mobiGlas Bot
Handles: /zutaten
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from database.db_connection import get_db
from config import ALLOWED_ROLES

logger = logging.getLogger(__name__)

class ZutatenCog(commands.Cog):
    """Befehle für Crafting-Zutaten"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
    
    def has_allowed_role(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User die notwendigen Rollen hat"""
        if not interaction.user.roles:
            return False
        
        user_roles = [role.name for role in interaction.user.roles]
        return any(role in ALLOWED_ROLES for role in user_roles)
    
    @app_commands.command(name="zutaten", description="Zeige Fundort einer Zutat")
    @app_commands.describe(zutat="Name der Zutat (z.B. IRON, EISEN)")
    async def zutaten(self, interaction: discord.Interaction, zutat: str):
        """Zeige wo eine Zutat zu finden ist"""
        
        # Rollen-Check
        if not self.has_allowed_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Suche Zutat
            query = """
                SELECT name, location, mining_type
                FROM crafting_materials
                WHERE name ILIKE %s
                LIMIT 1
            """
            result = self.db.execute_query(query, (f"%{zutat}%",))
            
            if not result:
                await interaction.followup.send(
                    f"❌ Zutat '{zutat}' nicht gefunden."
                )
                return
            
            name, location, mining_type = result[0]
            
            # Bestimme das Icon basierend auf Mining-Type
            type_icons = {
                "HAND_MINEABLE": "🚶 Hand-abbaubar",
                "SHIP_MINEABLE": "🚀 Schiff-abbaubar",
                "NPC_MISSION": "📋 NPC-Mission",
                "OTHER": "❓ Sonstiges"
            }
            
            type_display = type_icons.get(mining_type, f"❓ {mining_type}")
            
            # Erstelle Embed
            embed = discord.Embed(
                title=f"📦 Zutat: {name}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📍 Fundort",
                value=location if location != "Unknown" else "Unbekannt",
                inline=False
            )
            
            embed.add_field(
                name="🔨 Abbau-Typ",
                value=type_display,
                inline=False
            )
            
            embed.set_footer(text="mobiGlas Star Citizen Bot")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Fehler in /zutaten: {e}")
            await interaction.followup.send(
                f"❌ Ein Fehler ist aufgetreten: {str(e)}"
            )

async def setup(bot):
    """Lade das Cog in den Bot"""
    await bot.add_cog(ZutatenCog(bot))