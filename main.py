"""
mobiGlas Discord Bot - Hauptdatei
Star Citizen Crafting & Missionen Bot
"""

import discord
from discord.ext import commands
import logging
import os
import asyncio
from config import DISCORD_TOKEN, BOT_STATUS
from database.db_connection import init_database

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# BOT KONFIGURATION
# ============================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ============================================
# BOT EVENTS
# ============================================

@bot.event
async def on_ready():
    """Wird aufgerufen wenn Bot bereit ist"""
    logger.info(f"✅ Bot '{bot.user}' ist online!")
    logger.info(f"📊 Bot ist in {len(bot.guilds)} Servern")
    
    # Setze Bot-Status
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=BOT_STATUS
    )
    await bot.change_presence(activity=activity)
    
    logger.info(f"📍 Status gesetzt auf: {BOT_STATUS}")

@bot.event
async def on_command_error(ctx, error):
    """Fehlerbehandlung für Text-Commands"""
    logger.error(f"Command-Fehler: {error}")

# ============================================
# COGS LADEN
# ============================================

async def load_cogs():
    """Lade alle Cogs (Bot-Funktionen)"""
    cogs_dir = "cogs"
    
    if not os.path.exists(cogs_dir):
        logger.error(f"❌ Ordner '{cogs_dir}' nicht gefunden!")
        return
    
    logger.info("Lade Cogs...")
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith("_cog.py"):
            cog_name = filename[:-3]  # Entferne .py
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                logger.info(f"✓ Cog geladen: {cog_name}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden von {cog_name}: {e}")
    
    logger.info("✓ Alle Cogs geladen!")

# ============================================
# SYNC SLASH-COMMANDS
# ============================================

async def sync_commands():
    """Synchronisiere Slash-Commands mit Discord"""
    try:
        synced = await bot.tree.sync()
        logger.info(f"✓ {len(synced)} Slash-Commands synchronisiert")
    except Exception as e:
        logger.error(f"❌ Fehler beim Synchronisieren: {e}")

# ============================================
# BOT STARTUP
# ============================================

async def main():
    """Hauptfunktion zum Starten des Bots"""
    
    # Initialisiere Datenbank
    logger.info("Initialisiere Datenbank...")
    try:
        init_database()
        logger.info("✓ Datenbank initialisiert")
    except Exception as e:
        logger.error(f"❌ Fehler bei DB-Initialisierung: {e}")
        return
    
    # Lade Cogs
    await load_cogs()
    
    # Starte Bot
    async with bot:
        # Sync Commands beim Start
        @bot.event
        async def on_ready_once():
            await sync_commands()
            bot.remove_listener(on_ready_once)
        
        bot.add_listener(on_ready_once, "on_ready")
        
        # Starte Bot mit Token
        if not DISCORD_TOKEN:
            logger.error("❌ DISCORD_TOKEN nicht gesetzt!")
            return
        
        try:
            await bot.start(DISCORD_TOKEN)
        except discord.LoginFailure:
            logger.error("❌ Fehler beim Bot-Login - Token ungültig?")
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten: {e}")

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 mobiGlas Bot startet...")
    logger.info("=" * 50)
    
    asyncio.run(main())