"""
Admin-Cog für mobiGlas Bot
Handles: Admin-Commands wie Daten-Import
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import requests
from database.db_connection import get_db
from database.import_data import StarCitizenDataImporter

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    """Admin-Befehle für Bot-Management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User Admin-Rechte hat"""
        return interaction.user.guild_permissions.administrator
    
    @app_commands.command(name="import-daten", description="Importiere Star Citizen Daten (ADMIN ONLY)")
    @app_commands.describe(
        daten_quelle="URL zu GitHub Repo oder lokaler Pfad (z.B. https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/master)"
    )
    async def import_daten(self, interaction: discord.Interaction, daten_quelle: str):
        """Importiere Star Citizen Daten in die Datenbank"""
        
        # Nur Admins
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Prüfe ob URL oder lokaler Pfad
            if daten_quelle.startswith("http"):
                # URL: Prüfe ob erreichbar
                logger.info(f"Prüfe URL: {daten_quelle}")
                response = requests.head(daten_quelle, timeout=10)
                if response.status_code != 200:
                    await interaction.followup.send(
                        f"❌ URL nicht erreichbar: {daten_quelle}"
                    )
                    return
            else:
                # Lokaler Pfad: Prüfe ob existiert
                if not os.path.exists(daten_quelle):
                    await interaction.followup.send(
                        f"❌ Pfad nicht gefunden: {daten_quelle}"
                    )
                    return
            
            logger.info(f"Starte Daten-Import von: {daten_quelle}")
            
            # Starte Import
            importer = StarCitizenDataImporter(daten_quelle)
            importer.import_all()
            
            await interaction.followup.send(
                "✅ Daten-Import erfolgreich abgeschlossen!"
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Daten-Import: {e}")
            await interaction.followup.send(
                f"❌ Fehler beim Import: {str(e)}"
            )
    
    @app_commands.command(name="db-status", description="Zeige Datenbank-Status (ADMIN ONLY)")
    async def db_status(self, interaction: discord.Interaction):
        """Zeige den Status der Datenbank"""
        
        # Nur Admins
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Zähle Einträge in den Tabellen
            bp_count_result = self.db.execute_query("SELECT COUNT(*) FROM blueprints")
            bp_count = bp_count_result[0][0] if bp_count_result else 0
            
            items_count_result = self.db.execute_query("SELECT COUNT(*) FROM crafting_materials")
            items_count = items_count_result[0][0] if items_count_result else 0
            
            missions_count_result = self.db.execute_query("SELECT COUNT(*) FROM missions")
            missions_count = missions_count_result[0][0] if missions_count_result else 0
            
            user_bp_count_result = self.db.execute_query("SELECT COUNT(*) FROM user_blueprints")
            user_bp_count = user_bp_count_result[0][0] if user_bp_count_result else 0
            
            # Erstelle Embed
            embed = discord.Embed(
                title="🗄️ Datenbank-Status",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📦 Blueprints",
                value=f"{bp_count:,}",
                inline=True
            )
            
            embed.add_field(
                name="🔨 Crafting-Materialien",
                value=f"{items_count:,}",
                inline=True
            )
            
            embed.add_field(
                name="👑 Missionen",
                value=f"{missions_count:,}",
                inline=True
            )
            
            embed.add_field(
                name="💾 User-Blueprints",
                value=f"{user_bp_count:,}",
                inline=True
            )
            
            embed.set_footer(text="mobiGlas Star Citizen Bot")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Fehler beim DB-Status: {e}")
            await interaction.followup.send(
                f"❌ Fehler: {str(e)}"
            )
    
    @app_commands.command(name="ping", description="Prüfe Bot-Latenz")
    async def ping(self, interaction: discord.Interaction):
        """Zeige die Bot-Latenz"""
        
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latenz: **{latency}ms**",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Lade das Cog in den Bot"""
    await bot.add_cog(AdminCog(bot))