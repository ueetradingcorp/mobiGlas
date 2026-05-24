"""
Ruf/Reputation-Cog für mobiGlas Bot
Handles: /ruf
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from database.db_connection import get_db
from config import USER_ROLES

logger = logging.getLogger(__name__)

class RufCog(commands.Cog):
    """Befehle für Reputation/Ruf-Informationen"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
    
    def has_user_role(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User die notwendigen Rollen hat"""
        if not interaction.user.roles:
            return False
        
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in USER_ROLES for role_id in user_role_ids)
    
    async def fraktion_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete für Fraktions-Namen"""
        
        if not current:
            query = """
                SELECT DISTINCT reputation_faction FROM missions 
                WHERE reputation_faction != 'Unknown' 
                ORDER BY reputation_faction LIMIT 25
            """
            results = self.db.execute_query(query)
        else:
            query = """
                SELECT DISTINCT reputation_faction FROM missions 
                WHERE reputation_faction ILIKE %s AND reputation_faction != 'Unknown'
                ORDER BY reputation_faction 
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
    
    @app_commands.command(name="ruf", description="Zeige Ruf-Anforderungen für eine Fraktion")
    @app_commands.describe(fraktion="Name der Fraktion")
    @app_commands.autocomplete(fraktion=fraktion_autocomplete)
    async def ruf(self, interaction: discord.Interaction, fraktion: str):
        """Zeige Missionen und Ruf-Anforderungen für eine Fraktion"""
        
        if not self.has_user_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            query = """
                SELECT name, mission_type, reward_xp, reward_auc, reputation_amount
                FROM missions
                WHERE reputation_faction = %s
                ORDER BY reputation_amount DESC, reward_xp DESC
                LIMIT 20
            """
            results = self.db.execute_query(query, (fraktion,))
            
            if not results:
                await interaction.followup.send(
                    f"❌ Fraktion '{fraktion}' oder Missionen nicht gefunden."
                )
                return
            
            embed = discord.Embed(
                title=f"👑 {fraktion}",
                color=discord.Color.gold()
            )
            
            # Berechne benötigte Reputation
            total_missions = len(results)
            total_rep = sum(result[4] if result[4] else 0 for result in results)
            total_xp = sum(result[2] if result[2] else 0 for result in results)
            total_auc = sum(result[3] if result[3] else 0 for result in results)
            
            # Statistiken
            embed.add_field(
                name="📊 Benötigte Reputation & Rewards",
                value=f"**Benötigte Rep-Punkte:** ~{total_rep:,}\n"
                      f"**Gesamt XP:** ~{total_xp:,}\n"
                      f"**Gesamt aUEC:** ~{total_auc:,}\n"
                      f"**Anzahl Missionen:** {total_missions}",
                inline=False
            )
            
            # Missionen aufzählen
            missions_text = ""
            for i, (name, mission_type, reward_xp, reward_auc, rep_amount) in enumerate(results[:15], 1):
                xp_str = f"{reward_xp} XP" if reward_xp else "? XP"
                auc_str = f"{reward_auc:,} aUEC" if reward_auc else "? aUEC"
                rep_str = f"{rep_amount} Rep" if rep_amount else "? Rep"
                
                missions_text += f"**{i}. {name}**\n"
                missions_text += f"   💰 {auc_str} | ⭐ {xp_str} | 👑 {rep_str}\n"
            
            if missions_text:
                embed.add_field(
                    name="📋 Missionen",
                    value=missions_text,
                    inline=False
                )
            
            if total_missions > 15:
                embed.set_footer(text=f"mobiGlas Star Citizen Bot | Zeigt 15 von {total_missions} Missionen")
            else:
                embed.set_footer(text="mobiGlas Star Citizen Bot")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Fehler in /ruf: {e}")
            await interaction.followup.send(
                f"❌ Ein Fehler ist aufgetreten: {str(e)}"
            )

async def setup(bot):
    """Lade das Cog in den Bot"""
    await bot.add_cog(RufCog(bot))
