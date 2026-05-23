# mobiGlas - Star Citizen Discord Bot

Ein Discord Bot für Star Citizen Spieler zum Abfragen von Crafting-Rezepten, Crafting-Zutaten, Missionen und Rufs-Anforderungen.

## 🎯 Features

- **🔧 Blueprint-Rezepte** - Zeige Crafting-Rezepte und benötigte Zutaten
  - `/rezept [BLUEPRINT_NAME]` - Blueprint-Informationen anzeigen
  - `/rezept-eintragen [BLUEPRINT]` - Blueprint zum Inventar hinzufügen
  - `/rezept-entfernen [BLUEPRINT]` - Blueprint aus Inventar entfernen

- **📦 Crafting-Zutaten** - Finde Fundorte von Crafting-Materialien
  - `/zutaten [ZUTAT_NAME]` - Zeige Fundort und Abbau-Typ

- **👑 Ruf-System** - Abfrage von Missionen und Ruf-Anforderungen
  - `/ruf [FRAKTION]` - Zeige Missionen einer Fraktion

- **🗄️ Admin-Commands**
  - `/import-daten [PFAD]` - Importiere Star Citizen Daten (nur Server-Owner)
  - `/db-status` - Zeige Datenbank-Status (nur Server-Owner)
  - `/ping` - Prüfe Bot-Latenz

## 🔐 Berechtigungen

Nur Nutzer mit folgenden Rollen können die Bot-Commands nutzen:
- Freund
- Interessent
- Mitglied

## 📋 Anforderungen

- Python 3.10+
- PostgreSQL Datenbank
- Discord Bot Token
- scunpacked-data (Star Citizen Daten)

## 📦 Installation

### 1. Repository klonen
```bash
git clone https://github.com/ueetradingcorp/mobiGlas.git
cd mobiGlas
```

### 2. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 3. Umgebungsvariablen einrichten (Railway.app)

Bei Railway.app als Secrets hinzufügen:
- `DISCORD_TOKEN` - Dein Discord Bot Token
- `DATABASE_URL` - PostgreSQL Connection String (postgresql://user:password@host:port/database)

### 4. Lokal testen (optional)

Erstelle eine `.env` Datei (wird nicht zu GitHub committed):