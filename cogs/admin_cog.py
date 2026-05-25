"""
Admin-Cog für mobiGlas Bot
Handles: Admin-Commands wie Daten-Import (getrennt nach Kategorien)
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import asyncio
from database.db_connection import get_db
from database.import_data import StarCitizenDataImporter
from config import ADMIN_ROLES

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    """Admin-Befehle für Bot-Management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
        self.import_in_progress = False
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User Admin-Rechte hat"""
        if not interaction.user.roles:
            return False
        
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in ADMIN_ROLES for role_id in user_role_ids)
    
    @app_commands.command(name="import-blueprints", description="Importiere Blueprints (ADMIN ONLY)")
    @app_commands.describe(
        daten_quelle="URL zu Star Citizen Wiki API (z.B. https://api.star-citizen.wiki)"
    )
    async def import_blueprints(self, interaction: discord.Interaction, daten_quelle: str):
        """Importiere nur Blueprints"""
        
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Direktoren und Bot-Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
        if self.import_in_progress:
            await interaction.response.send_message(
                "⚠️ Ein Import läuft bereits. Bitte warten...",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            logger.info(f"Starte Blueprint-Import von: {daten_quelle}")
            
            try:
                await interaction.followup.send(
                    "⏳ Importiere Blueprints...\nDas dauert etwa 1-2 Minuten."
                )
            except discord.errors.HTTPException:
                logger.warning("Konnte erste Nachricht nicht senden")
            
            self.import_in_progress = True
            await self.run_blueprints_import_async(daten_quelle, interaction)
            
        except Exception as e:
            logger.error(f"Fehler beim Blueprint-Import: {e}")
            self.import_in_progress = False
            
            try:
                await interaction.followup.send(f"❌ Fehler beim Import: {str(e)}")
            except discord.errors.HTTPException:
                logger.warning("Konnte Fehlermeldung nicht senden - Webhook abgelaufen")
    
    @app_commands.command(name="import-commodities", description="Importiere Commodities/Zutaten (ADMIN ONLY)")
    @app_commands.describe(
        daten_quelle="URL zu Star Citizen Wiki API (z.B. https://api.star-citizen.wiki)"
    )
    async def import_commodities(self, interaction: discord.Interaction, daten_quelle: str):
        """Importiere nur Commodities"""
        
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Direktoren und Bot-Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
        if self.import_in_progress:
            await interaction.response.send_message(
                "⚠️ Ein Import läuft bereits. Bitte warten...",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            logger.info(f"Starte Commodities-Import von: {daten_quelle}")
            
            try:
                await interaction.followup.send(
                    "⏳ Importiere Commodities...\nDas dauert etwa 1-2 Minuten."
                )
            except discord.errors.HTTPException:
                logger.warning("Konnte erste Nachricht nicht senden")
            
            self.import_in_progress = True
            await self.run_commodities_import_async(daten_quelle, interaction)
            
        except Exception as e:
            logger.error(f"Fehler beim Commodities-Import: {e}")
            self.import_in_progress = False
            
            try:
                await interaction.followup.send(f"❌ Fehler beim Import: {str(e)}")
            except discord.errors.HTTPException:
                logger.warning("Konnte Fehlermeldung nicht senden - Webhook abgelaufen")
    
    @app_commands.command(name="import-missions", description="Importiere Missionen (ADMIN ONLY)")
    @app_commands.describe(
        daten_quelle="URL zu Star Citizen Wiki API (z.B. https://api.star-citizen.wiki)"
    )
    async def import_missions(self, interaction: discord.Interaction, daten_quelle: str):
        """Importiere nur Missionen"""
        
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Direktoren und Bot-Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
        if self.import_in_progress:
            await interaction.response.send_message(
                "⚠️ Ein Import läuft bereits. Bitte warten...",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            logger.info(f"Starte Missions-Import von: {daten_quelle}")
            
            try:
                await interaction.followup.send(
                    "⏳ Importiere Missionen...\nDas dauert etwa 1-2 Minuten."
                )
            except discord.errors.HTTPException:
                logger.warning("Konnte erste Nachricht nicht senden")
            
            self.import_in_progress = True
            await self.run_missions_import_async(daten_quelle, interaction)
            
        except Exception as e:
            logger.error(f"Fehler beim Missions-Import: {e}")
            self.import_in_progress = False
            
            try:
                await interaction.followup.send(f"❌ Fehler beim Import: {str(e)}")
            except discord.errors.HTTPException:
                logger.warning("Konnte Fehlermeldung nicht senden - Webhook abgelaufen")
    
    async def run_blueprints_import_async(self, daten_quelle: str, interaction: discord.Interaction):
        """Importiere Blueprints asynchron"""
        try:
            loop = asyncio.get_event_loop()
            
            # Lösche alte Blueprints
            logger.info("Lösche alte Blueprints...")
            self.db.execute_update("DELETE FROM blueprint_ingredients")
            self.db.execute_update("DELETE FROM blueprints")
            
            importer = StarCitizenDataImporter(daten_quelle)
            bp_count = await loop.run_in_executor(None, importer.import_blueprints)
            
            self.import_in_progress = False
            
            embed = discord.Embed(
                title="✅ Blueprints importiert!",
                color=discord.Color.green()
            )
            embed.add_field(name="📦 Blueprints", value=f"{bp_count:,}", inline=False)
            
            try:
                await interaction.followup.send(embed=embed)
            except discord.errors.HTTPException:
                logger.warning("Konnte Ergebnis-Nachricht nicht senden - Webhook abgelaufen")
                logger.info(f"Aber Import war erfolgreich: {bp_count} Blueprints")
            
        except Exception as e:
            self.import_in_progress = False
            logger.error(f"Fehler beim async Blueprint-Import: {e}")
            
            try:
                await interaction.followup.send(f"❌ Fehler beim Import: {str(e)}")
            except discord.errors.HTTPException:
                logger.warning("Konnte Fehlermeldung nicht senden - Webhook abgelaufen")
    
    async def run_commodities_import_async(self, daten_quelle: str, interaction: discord.Interaction):
        """Importiere Commodities asynchron"""
        try:
            loop = asyncio.get_event_loop()
            
            # Lösche alte Commodities
            logger.info("Lösche alte Commodities...")
            self.db.execute_update("DELETE FROM crafting_materials")
            
            importer = StarCitizenDataImporter(daten_quelle)
            commodities_count = await loop.run_in_executor(None, importer.import_commodities)
            
            self.import_in_progress = False
            
            embed = discord.Embed(
                title="✅ Commodities importiert!",
                color=discord.Color.green()
            )
            embed.add_field(name="📦 Commodities", value=f"{commodities_count:,}", inline=False)
            
            try:
                await interaction.followup.send(embed=embed)
            except discord.errors.HTTPException:
                logger.warning("Konnte Ergebnis-Nachricht nicht senden - Webhook abgelaufen")
                logger.info(f"Aber Import war erfolgreich: {commodities_count} Commodities")
            
        except Exception as e:
            self.import_in_progress = False
            logger.error(f"Fehler beim async Commodities-Import: {e}")
            
            try:
                await interaction.followup.send(f"❌ Fehler beim Import: {str(e)}")
            except discord.errors.HTTPException:
                logger.warning("Konnte Fehlermeldung nicht senden - Webhook abgelaufen")
    
    async def run_missions_import_async(self, daten_quelle: str, interaction: discord.Interaction):
        """Importiere Missionen asynchron"""
        try:
            loop = asyncio.get_event_loop()
            
            # Lösche alte Missionen
            logger.info("Lösche alte Missionen...")
            self.db.execute_update("DELETE FROM missions")
            
            importer = StarCitizenDataImporter(daten_quelle)
            missions_count = await loop.run_in_executor(None, importer.import_missions)
            
            self.import_in_progress = False
            
            embed = discord.Embed(
                title="✅ Missionen importiert!",
                color=discord.Color.green()
            )
            embed.add_field(name="👑 Missionen", value=f"{missions_count:,}", inline=False)
            
            try:
                await interaction.followup.send(embed=embed)
            except discord.errors.HTTPException:
                logger.warning("Konnte Ergebnis-Nachricht nicht senden - Webhook abgelaufen")
                logger.info(f"Aber Import war erfolgreich: {missions_count} Missionen")
            
        except Exception as e:
            self.import_in_progress = False
            logger.error(f"Fehler beim async Missions-Import: {e}")
            
            try:
                await interaction.followup.send(f"❌ Fehler beim Import: {str(e)}")
            except discord.errors.HTTPException:
                logger.warning("Konnte Fehlermeldung nicht senden - Webhook abgelaufen")
    
    @app_commands.command(name="db-status", description="Zeige Datenbank-Status (ADMIN ONLY)")
    async def db_status(self, interaction: discord.Interaction):
        """Zeige den Status der Datenbank"""
        
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Direktoren und Bot-Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            bp_count_result = self.db.execute_query("SELECT COUNT(*) FROM blueprints")
            bp_count = bp_count_result[0][0] if bp_count_result else 0
            
            commodities_result = self.db.execute_query("SELECT COUNT(*) FROM crafting_materials")
            commodities_count = commodities_result[0][0] if commodities_result else 0
            
            missions_count_result = self.db.execute_query("SELECT COUNT(*) FROM missions")
            missions_count = missions_count_result[0][0] if missions_count_result else 0
            
            user_bp_count_result = self.db.execute_query("SELECT COUNT(*) FROM user_blueprints")
            user_bp_count = user_bp_count_result[0][0] if user_bp_count_result else 0
            
            embed = discord.Embed(
                title="🗄️ Datenbank-Status",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="📦 Blueprints", value=f"{bp_count:,}", inline=True)
            embed.add_field(name="📦 Commodities", value=f"{commodities_count:,}", inline=True)
            embed.add_field(name="👑 Missionen", value=f"{missions_count:,}", inline=True)
            embed.add_field(name="💾 User-Blueprints", value=f"{user_bp_count:,}", inline=True)
            
            if self.import_in_progress:
                embed.add_field(name="⏳ Status", value="Import läuft noch...", inline=False)
            
            embed.set_footer(text="mobiGlas Star Citizen Bot")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Fehler beim DB-Status: {e}")
            await interaction.followup.send(f"❌ Fehler: {str(e)}")
    
    @app_commands.command(name="ping", description="Prüfe Bot-Latenz")
    async def ping(self, interaction: discord.Interaction):
        """Zeige die Bot-Latenz"""
        
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Nur Direktoren und Bot-Admins können diesen Befehl nutzen.",
                ephemeral=True
            )
            return
        
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
