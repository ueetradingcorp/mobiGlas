"""
Ruf/Reputation-Cog für mobiGlas Bot
Handles: /ruf
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from database.db_connection import get_db
from config import ALLOWED_ROLES

logger = logging.getLogger(__name__)

class RufCog(commands.Cog):
    """Befehle für Reputation/Ruf-Informationen"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_db()
    
    def has_allowed_role(self, interaction: discord.Interaction) -> bool:
        """Prüfe ob User die notwendigen Rollen hat"""
        if not interaction.user.roles:
            return False
        
        user_roles = [role.name for role in interaction.user.roles]
        return any(role in ALLOWED_ROLES for role in user_roles)
    
    @app_commands.command(name="ruf", description="Zeige Ruf-Anforderungen für eine Fraktion")
    @app_commands.describe(fraktion="Name der Fraktion (z.B. ADAGIO HOLDINGS)")
    async def ruf(self, interaction: discord.Interaction, fraktion: str):
        """Zeige Missionen und Ruf-Anforderungen für eine Fraktion"""
        
        # Rollen-Check
        if not self.has_allowed_role(interaction):
            await interaction.response.send_message(
                "❌ Du hast keine Berechtigung, diesen Befehl zu nutzen.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Suche Missionen der Fraktion
            query = """
                SELECT name, mission_type, reward_xp, reward_auc, reputation_rank
                FROM missions
                WHERE faction ILIKE %s
                ORDER BY reward_xp DESC
                LIMIT 20
            """
            results = self.db.execute_query(query, (f"%{fraktion}%",))
            
            if not results:
                await interaction.followup.send(
                    f"❌ Fraktion '{fraktion}' oder Missionen nicht gefunden."
                )
                return
            
            # Erstelle Embed
            embed = discord.Embed(
                title=f"👑 Ruf-Missionen: {fraktion}",
                color=discord.Color.gold()
            )
            
            # Sammle Statistiken
            total_missions = len(results)
            total_xp = sum(result[2] if result[2] else 0 for result in results)
            total_auc = sum(result[3] if result[3] else 0 for result in results)
            
            # Füge Statistiken hinzu
            embed.add_field(
                name="📊 Statistiken",
                value=f"**Anzahl Missionen:** {total_missions}\n"
                      f"**Gesamt XP:** ~{total_xp:,}\n"
                      f"**Gesamt aUEC:** ~{total_auc:,}",
                inline=False
            )
            
            # Füge erste 10 Missionen hinzu
            missions_text = ""
            for i, (name, mission_type, reward_xp, reward_auc, rank) in enumerate(results[:10], 1):
                xp_str = f"{reward_xp} XP" if reward_xp else "? XP"
                auc_str = f"{reward_auc:,} aUEC" if reward_auc else "? aUEC"
                missions_text += f"**{i}. {name}**\n"
                missions_text += f"   💰 {auc_str} | ⭐ {xp_str}\n"
            
            if missions_text:
                embed.add_field(
                    name="📋 Top 10 Missionen",
                    value=missions_text,
                    inline=False
                )
            
            if total_missions > 10:
                embed.set_footer(text=f"mobiGlas Star Citizen Bot | Zeigt 10 von {total_missions} Missionen")
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