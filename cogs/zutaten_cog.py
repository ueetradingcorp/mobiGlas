"""
Zutaten-Cog für mobiGlas Bot
Handles: /zutaten
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from database.db_connection import get_db
from config import USER_ROLES

logger = logging.getLogger(__name__)

class ZutatenCog(commands.Cog):
    """Befehle für Crafting-Zutaten"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
    
    def has_user_role(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User die notwendigen Rollen hat"""
        if not interaction.user.roles:
            return False
        
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in USER_ROLES for role_id in user_role_ids)
    
    async def zutat_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete für Zutat-Namen"""
        
        if not current:
            # Keine Eingabe - zeige Top 25 Zutaten
            query = "SELECT name FROM crafting_materials ORDER BY name LIMIT 25"
            results = self.db.execute_query(query)
        else:
            # Suche Zutaten die mit dem aktuellen Text starten oder ihn enthalten
            query = """
                SELECT name FROM crafting_materials 
                WHERE name ILIKE %s 
                ORDER BY name 
                LIMIT 25
            """
            results = self.db.execute_query(query, (f"%{current}%",))
        
        if not results:
            return []
        
        # Erstelle Choice-Liste für Discord
        choices = [
            app_commands.Choice(name=result[0], value=result[0])
            for result in results
        ]
        
        return choices
    
    @app_commands.command(name="zutaten", description="Zeige Fundort einer Zutat")
    @app_commands.describe(zutat="Name der Zutat")
    @app_commands.autocomplete(zutat=zutat_autocomplete)
    async def zutaten(self, interaction: discord.Interaction, zutat: str):
        """Zeige wo eine Zutat zu finden ist"""
        
        # Rollen-Check
        if not self.has_user_role(interaction):
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
                WHERE name = %s
                LIMIT 1
            """
            result = self.db.execute_query(query, (zutat,))
            
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
