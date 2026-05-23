"""
Konfiguration für mobiGlas Bot
Alle Settings sind hier zentral konfiguriert
Railway.app verwaltet Secrets über Environment Variables
"""

import os
from dotenv import load_dotenv

# .env Datei laden (für lokale Entwicklung)
load_dotenv()

# ============================================
# DISCORD BOT KONFIGURATION
# ============================================

# Bot Token wird VON RAILWAY.APP über Environment Variable gesetzt
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    DISCORD_TOKEN = "dummy_token_for_local_import"

# Bot Prefix
COMMAND_PREFIX = "!"

# ============================================
# DATENBANK KONFIGURATION
# ============================================

# Railway.app stellt die DB-Verbindung über DATABASE_URL bereit
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "❌ DATABASE_URL ist nicht gesetzt! "
        "Bei Railway: Setze als Secret oder verlinke die Postgres DB"
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

COMMAND_COOLDOWN = 5  # Sekunden zwischen Commands

# ============================================
# LOGGING
# ============================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")