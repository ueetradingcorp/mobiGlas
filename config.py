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
# DISCORD ROLLEN
# ============================================

# Rollen für normale Bot-Commands (/rezept, /zutaten, /ruf)
USER_ROLES = [
    966290443090407464,   # Freund
    915601784343498793,   # Interessent
    915572343600992296,   # Mitglied
]

# Rollen für Admin-Commands (/import-daten, /db-status, /ping)
ADMIN_ROLES = [
    920642041959038976,   # Direktoren
    1481345670223888475,  # Bot-Admins
]

# ============================================
# BOT SETTINGS
# ============================================

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
