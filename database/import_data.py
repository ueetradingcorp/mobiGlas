"""
Import von Star Citizen Spieldaten in die Datenbank
Importiert Blueprints, Items, Missionen direkt von GitHub (scunpacked-data)
"""

import json
import logging
import requests
from pathlib import Path
from database.db_connection import get_db

logger = logging.getLogger(__name__)

class StarCitizenDataImporter:
    """Importiert Star Citizen Daten von GitHub oder lokal"""
    
    def __init__(self, data_source):
        """
        Initialisiere den Importer
        
        Args:
            data_source: Entweder URL zu GitHub Repo oder lokaler Pfad
        """
        self.data_source = data_source.rstrip('/')  # Entferne trailing slash
        self.db = get_db()
        self.is_url = data_source.startswith("http")
        
        if not self.is_url:
            self.data_path = Path(data_source)
    
    def download_json(self, url):
        """Lade JSON von URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Fehler beim Download von {url}: {e}")
            return None
    
    def read_local_json(self, filename):
        """Lese JSON lokal"""
        file_path = self.data_path / filename
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Lesen von {filename}: {e}")
            return None
    
    def import_all(self):
        """Importiere alle Daten"""
        logger.info("=" * 50)
        logger.info("Starte Star Citizen Daten-Import...")
        logger.info(f"Quelle: {self.data_source}")
        logger.info("=" * 50)
        
        bp_count = self.import_blueprints()
        items_count = self.import_items()
        missions_count = self.import_missions()
        
        logger.info("=" * 50)
        logger.info("✅ IMPORT ABGESCHLOSSEN!")
        logger.info(f"   - {bp_count} Blueprints")
        logger.info(f"   - {items_count} Items")
        logger.info(f"   - {missions_count} Missionen")
        logger.info("=" * 50)
    
    def import_blueprints(self):
        """Importiere Blueprint-Daten"""
        logger.info("Importiere Blueprints...")
        
        # Lade Daten
        if self.is_url:
            url = f"{self.data_source}/blueprints.json"
            logger.info(f"Lade von: {url}")
            blueprints = self.download_json(url)
        else:
            blueprints = self.read_local_json("blueprints.json")
        
        if not blueprints:
            logger.error("❌ Blueprints konnten nicht geladen werden")
            return 0
        
        imported = 0
        
        for bp_id, bp_data in blueprints.items():
            if not isinstance(bp_data, dict):
                continue
            
            name = bp_data.get("name", f"Unknown_{bp_id}")
            craft_time = bp_data.get("craftTime", 0)
            
            try:
                # Insertiere Blueprint
                query = """
                    INSERT INTO blueprints (name, crafting_time_minutes, source)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE 
                    SET crafting_time_minutes = EXCLUDED.crafting_time_minutes
                """
                self.db.execute_update(query, (name, craft_time, bp_id))
                
                # Hole die Blueprint-ID
                select_query = "SELECT id FROM blueprints WHERE name = %s"
                result = self.db.execute_query(select_query, (name,))
                
                if result:
                    bp_db_id = result[0][0]
                    
                    # Importiere Zutaten
                    ingredients = bp_data.get("ingredients", [])
                    if isinstance(ingredients, list):
                        for ingredient in ingredients:
                            if isinstance(ingredient, dict):
                                ing_name = ingredient.get("name", "Unknown")
                                ing_qty = ingredient.get("quantity", 1)
                                
                                ing_query = """
                                    INSERT INTO blueprint_ingredients 
                                    (blueprint_id, ingredient_name, quantity)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT DO NOTHING
                                """
                                self.db.execute_update(ing_query, (bp_db_id, ing_name, ing_qty))
                
                imported += 1
            except Exception as e:
                logger.debug(f"Fehler bei Blueprint {name}: {e}")
                continue
        
        logger.info(f"✓ {imported} Blueprints importiert!")
        return imported
    
    def import_items(self):
        """Importiere Item/Zutaten-Daten"""
        logger.info("Importiere Items...")
        
        # Lade Daten
        if self.is_url:
            url = f"{self.data_source}/items.json"
            logger.info(f"Lade von: {url}")
            items = self.download_json(url)
        else:
            items = self.read_local_json("items.json")
        
        if not items:
            logger.error("❌ Items konnten nicht geladen werden")
            return 0
        
        imported = 0
        
        for item_id, item_data in items.items():
            if not isinstance(item_data, dict):
                continue
            
            name = item_data.get("name", f"Unknown_{item_id}")
            location = item_data.get("location", "Unknown")
            item_type = item_data.get("type", "OTHER")
            
            try:
                query = """
                    INSERT INTO crafting_materials (name, location, mining_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE 
                    SET location = EXCLUDED.location
                """
                self.db.execute_update(query, (name, location, item_type))
                imported += 1
            except Exception as e:
                logger.debug(f"Fehler bei Item {name}: {e}")
                continue
        
        logger.info(f"✓ {imported} Items importiert!")
        return imported
    
    def import_missions(self):
        """Importiere Missionen"""
        logger.info("Importiere Missionen...")
        
        if self.is_url:
            # Von GitHub: Liste alle contracts/*.json Dateien
            return self.import_missions_from_github()
        else:
            # Lokal: Lese aus contracts/ Ordner
            return self.import_missions_from_local()
    
    def import_missions_from_github(self):
        """Importiere Missionen von GitHub (API)"""
        imported = 0
        processed = 0
        
        # GitHub API für Dateiliste
        api_url = "https://api.github.com/repos/StarCitizenWiki/scunpacked-data/contents/contracts"
        
        logger.info(f"Hole Dateiliste von: {api_url}")
        
        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            files = response.json()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Dateiliste: {e}")
            return 0
        
        logger.info(f"Gefunden: {len(files)} Mission-Dateien")
        
        for file_info in files:
            if not file_info["name"].endswith(".json"):
                continue
            
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"   Verarbeite Datei {processed}...")
            
            # Download JSON
            download_url = file_info["download_url"]
            mission_data = self.download_json(download_url)
            
            if not mission_data or not isinstance(mission_data, dict):
                continue
            
            name = mission_data.get("name", file_info["name"])
            faction = mission_data.get("faction", "Unknown")
            mission_type = mission_data.get("type", "Unknown")
            reward = mission_data.get("reward", 0)
            xp = mission_data.get("xp", 0)
            
            try:
                query = """
                    INSERT INTO missions 
                    (name, faction, mission_type, reward_auc, reward_xp)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE 
                    SET faction = EXCLUDED.faction
                """
                self.db.execute_update(query, (name, faction, mission_type, reward, xp))
                imported += 1
            except Exception as e:
                logger.debug(f"Fehler bei Mission {name}: {e}")
                continue
        
        logger.info(f"✓ {imported} Missionen importiert! (aus {processed} Dateien)")
        return imported
    
    def import_missions_from_local(self):
        """Importiere Missionen lokal"""
        contracts_dir = self.data_path / "contracts"
        
        if not contracts_dir.exists():
            logger.error(f"❌ Ordner nicht gefunden: {contracts_dir}")
            return 0
        
        imported = 0
        processed = 0
        
        for contract_file in contracts_dir.glob("*.json"):
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"   Verarbeite Datei {processed}...")
            
            try:
                with open(contract_file, "r", encoding="utf-8") as f:
                    mission_data = json.load(f)
            except Exception as e:
                logger.debug(f"Fehler beim Lesen von {contract_file.name}: {e}")
                continue
            
            if not isinstance(mission_data, dict):
                continue
            
            name = mission_data.get("name", contract_file.stem)
            faction = mission_data.get("faction", "Unknown")
            mission_type = mission_data.get("type", "Unknown")
            reward = mission_data.get("reward", 0)
            xp = mission_data.get("xp", 0)
            
            try:
                query = """
                    INSERT INTO missions 
                    (name, faction, mission_type, reward_auc, reward_xp)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE 
                    SET faction = EXCLUDED.faction
                """
                self.db.execute_update(query, (name, faction, mission_type, reward, xp))
                imported += 1
            except Exception as e:
                logger.debug(f"Fehler bei Mission {name}: {e}")
                continue
        
        logger.info(f"✓ {imported} Missionen importiert! (aus {processed} Dateien)")
        return imported