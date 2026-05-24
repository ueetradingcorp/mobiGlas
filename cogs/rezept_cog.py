"""
Blueprint/Rezept-Cog für mobiGlas Bot
Handles: /rezept, /rezept-eintragen, /rezept-entfernen
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from database.db_connection import get_db
from config import USER_ROLES

logger = logging.getLogger(__name__)

class RezeptCog(commands.Cog):
    """Befehle für Blueprint-Rezepte"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
    
    def has_user_role(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User die notwendigen Rollen hat"""
        if not interaction.user.roles:
            return False
        
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in USER_ROLES for role_id in user_role_ids)
    
    @app_commands.command(name="rezept", description="Zeige ein Blueprint-Rezept an")
    @app_commands.describe(blueprint="Name oder ID des Blueprints (z.B. P8-AR)")
    async def rezept(self, interaction: discord.Interaction, blueprint: str):
        """Zeige Rezept-Informationen für einen Blueprint"""
        
        # Rollen-Check
        if not self.has_user_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Suche Blueprint
            query = """
                SELECT id, name, crafting_time_minutes, source
                FROM blueprints
                WHERE name ILIKE %s OR source ILIKE %s
                LIMIT 1
            """
            result = self.db.execute_query(query, (f"%{blueprint}%", f"%{blueprint}%"))
            
            if not result:
                await interaction.followup.send(
                    f"❌ Blueprint '{blueprint}' nicht gefunden."
                )
                return
            
            bp_id, bp_name, craft_time, source = result[0]
            
            # Hole Zutaten
            ingredients_query = """
                SELECT ingredient_name, quantity
                FROM blueprint_ingredients
                WHERE blueprint_id = %s
                ORDER BY ingredient_name
            """
            ingredients = self.db.execute_query(ingredients_query, (bp_id,))
            
            # Erstelle Embed
            embed = discord.Embed(
                title=f"🔧 Blueprint: {bp_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="⏱️ Crafting-Zeit",
                value=f"{craft_time} Minuten",
                inline=False
            )
            
            if ingredients:
                ingredients_text = "\n".join(
                    [f"• {ing[0]} (x{ing[1]})" for ing in ingredients]
                )
                embed.add_field(
                    name="📦 Benötigte Zutaten",
                    value=ingredients_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📦 Benötigte Zutaten",
                    value="Keine Zutaten erforderlich",
                    inline=False
                )
            
            if source:
                embed.add_field(
                    name="📍 Quelle",
                    value=source,
                    inline=False
                )
            
            embed.set_footer(text="mobiGlas Star Citizen Bot")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Fehler in /rezept: {e}")
            await interaction.followup.send(
                f"❌ Ein Fehler ist aufgetreten: {str(e)}"
            )
    
    @app_commands.command(name="rezept-eintragen", description="Trage einen Blueprint in dein Inventar ein")
    @app_commands.describe(blueprint="Name oder ID des Blueprints")
    async def rezept_eintragen(self, interaction: discord.Interaction, blueprint: str):
        """Speichere einen Blueprint im User-Inventar"""
        
        if not self.has_user_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Suche Blueprint
            query = "SELECT id FROM blueprints WHERE name ILIKE %s OR source ILIKE %s LIMIT 1"
            result = self.db.execute_query(query, (f"%{blueprint}%", f"%{blueprint}%"))
            
            if not result:
                await interaction.followup.send(
                    f"❌ Blueprint '{blueprint}' nicht gefunden."
                )
                return
            
            bp_id = result[0][0]
            
            # Prüfe ob bereits vorhanden
            check_query = """
                SELECT id FROM user_blueprints
                WHERE user_id = %s AND blueprint_id = %s
            """
            check_result = self.db.execute_query(check_query, (interaction.user.id, bp_id))
            
            if check_result:
                await interaction.followup.send(
                    "⚠️ Du besitzt diesen Blueprint bereits."
                )
                return
            
            # Füge Blueprint zum Inventar hinzu
            insert_query = """
                INSERT INTO user_blueprints (user_id, blueprint_id)
                VALUES (%s, %s)
            """
            success = self.db.execute_update(insert_query, (interaction.user.id, bp_id))
            
            if success:
                await interaction.followup.send(
                    f"✅ Blueprint '{blueprint}' zu deinem Inventar hinzugefügt!"
                )
            else:
                await interaction.followup.send(
                    "❌ Fehler beim Hinzufügen des Blueprints."
                )
        
        except Exception as e:
            logger.error(f"Fehler in /rezept-eintragen: {e}")
            await interaction.followup.send(
                f"❌ Ein Fehler ist aufgetreten: {str(e)}"
            )
    
    @app_commands.command(name="rezept-entfernen", description="Entferne einen Blueprint aus deinem Inventar")
    @app_commands.describe(blueprint="Name oder ID des Blueprints")
    async def rezept_entfernen(self, interaction: discord.Interaction, blueprint: str):
        """Entferne einen Blueprint aus dem User-Inventar"""
        
        if not self.has_user_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Suche Blueprint
            query = "SELECT id FROM blueprints WHERE name ILIKE %s OR source ILIKE %s LIMIT 1"
            result = self.db.execute_query(query, (f"%{blueprint}%", f"%{blueprint}%"))
            
            if not result:
                await interaction.followup.send(
                    f"❌ Blueprint '{blueprint}' nicht gefunden."
                )
                return
            
            bp_id = result[0][0]
            
            # Prüfe ob User diesen Blueprint hat
            check_query = """
                SELECT id FROM user_blueprints
                WHERE user_id = %s AND blueprint_id = %s
            """
            check_result = self.db.execute_query(check_query, (interaction.user.id, bp_id))
            
            if not check_result:
                await interaction.followup.send(
                    "⚠️ Du besitzt diesen Blueprint nicht."
                )
                return
            
            # Lösche Blueprint aus Inventar
            delete_query = """
                DELETE FROM user_blueprints
                WHERE user_id = %s AND blueprint_id = %s
            """
            success = self.db.execute_update(delete_query, (interaction.user.id, bp_id))
            
            if success:
                await interaction.followup.send(
                    f"✅ Blueprint '{blueprint}' aus deinem Inventar entfernt!"
                )
            else:
                await interaction.followup.send(
                    "❌ Fehler beim Entfernen des Blueprints."
                )
        
        except Exception as e:
            logger.error(f"Fehler in /rezept-entfernen: {e}")
            await interaction.followup.send(
                f"❌ Ein Fehler ist aufgetreten: {str(e)}"
            )

async def setup(bot):
    """Lade das Cog in den Bot"""
    await bot.add_cog(RezeptCog(bot))
