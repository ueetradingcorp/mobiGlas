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
    
    async def blueprint_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete für Blueprint-Namen"""
        
        if not current:
            query = "SELECT name FROM blueprints ORDER BY name LIMIT 25"
            results = self.db.execute_query(query)
        else:
            query = """
                SELECT name FROM blueprints 
                WHERE name ILIKE %s 
                ORDER BY name 
                LIMIT 25
            """
            results = self.db.execute_query(query, (f"%{current}%",))
        
        if not results:
            return []
        
        choices = [
            app_commands.Choice(name=result[0], value=result[0])
            for result in results
        ]
        
        return choices
    
    @app_commands.command(name="rezept", description="Zeige ein Blueprint-Rezept an")
    @app_commands.describe(blueprint="Name des Blueprints")
    @app_commands.autocomplete(blueprint=blueprint_autocomplete)
    async def rezept(self, interaction: discord.Interaction, blueprint: str):
        """Zeige Rezept-Informationen für einen Blueprint"""
        
        if not self.has_user_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            query = """
                SELECT id, name, crafting_time_minutes, source
                FROM blueprints
                WHERE name = %s
                LIMIT 1
            """
            result = self.db.execute_query(query, (blueprint,))
            
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
            
            # Hole User die diesen Blueprint haben
            user_query = """
                SELECT user_id FROM user_blueprints
                WHERE blueprint_id = %s
            """
            user_result = self.db.execute_query(user_query, (bp_id,))
            
            # Erstelle Embed
            embed = discord.Embed(
                title=f"🔧 {bp_name}",
                color=discord.Color.blue()
            )
            
            # Benötigte Zutaten
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
            
            # Crafting-Zeit
            embed.add_field(
                name="⏱️ Crafting-Zeit",
                value=f"{craft_time} Minuten",
                inline=False
            )
            
            # Mission (Fraktion) - TODO: Könnte aus unlocking_missions kommen
            embed.add_field(
                name="📍 Mission (Fraktion)",
                value="Informationen noch nicht verfügbar",
                inline=False
            )
            
            # Rezeptinhaber - ohne Ping, mit echtem Namen
            if user_result:
                owner_names = []
                for row in user_result:
                    user_id = row[0]
                    try:
                        user = await self.bot.fetch_user(user_id)
                        owner_names.append(user.name)
                    except discord.NotFound:
                        owner_names.append(f"User#{user_id}")
                
                owners_display = ", ".join(owner_names) if owner_names else "Unbekannt"
                embed.add_field(
                    name="👤 Rezeptinhaber",
                    value=owners_display,
                    inline=False
                )
            else:
                embed.add_field(
                    name="👤 Rezeptinhaber",
                    value="Noch niemand",
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
    @app_commands.describe(blueprint="Name des Blueprints")
    @app_commands.autocomplete(blueprint=blueprint_autocomplete)
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
            query = "SELECT id FROM blueprints WHERE name = %s LIMIT 1"
            result = self.db.execute_query(query, (blueprint,))
            
            if not result:
                await interaction.followup.send(
                    f"❌ Blueprint '{blueprint}' nicht gefunden."
                )
                return
            
            bp_id = result[0][0]
            
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
    @app_commands.describe(blueprint="Name des Blueprints")
    @app_commands.autocomplete(blueprint=blueprint_autocomplete)
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
            query = "SELECT id FROM blueprints WHERE name = %s LIMIT 1"
            result = self.db.execute_query(query, (blueprint,))
            
            if not result:
                await interaction.followup.send(
                    f"❌ Blueprint '{blueprint}' nicht gefunden."
                )
                return
            
            bp_id = result[0][0]
            
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
