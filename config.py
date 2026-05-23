"""
Konfiguration für mobiGlas Bot
Alle Settings sind hier zentral konfiguriert
Railway.app verwaltet Secrets über Environment Variables
"""

import os

# ============================================
# DISCORD BOT KONFIGURATION
# ============================================

# Bot Token wird VON RAILWAY.APP über Environment Variable gesetzt
# (NICHT in .env - nur in railway.app Secrets!)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError(
        "❌ DISCORD_TOKEN ist nicht gesetzt! "
        "Bitte setze es als Secret in railway.app"
    )

# Bot Prefix (falls nötig für Text-Commands, wir nutzen hauptsächlich Slash-Commands)
COMMAND_PREFIX = "!"

# ============================================
# DATENBANK KONFIGURATION
# ============================================

# Railway.app stellt die DB-Verbindung über DATABASE_URL bereit
# (NICHT in .env - nur in railway.app Secrets!)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "❌ DATABASE_URL ist nicht gesetzt! "
        "Bitte verlinke die PostgreSQL Datenbank in railway.app"
    )

# ============================================
# BOT SETTINGS
# ============================================

# Welche Discord Rollen dürfen den Bot nutzen?
ALLOWED_ROLES = ["Freund", "Interessent", "Mitglied"]

# Bot Status
BOT_STATUS = "Star Citizen Crafting | /rezept"

# ============================================
# COMMAND SETTINGS
# ============================================

# Für später - Limits setzen
COMMAND_COOLDOWN = 5  # Sekunden zwischen Commands

# ============================================
# LOGGING
# ============================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")