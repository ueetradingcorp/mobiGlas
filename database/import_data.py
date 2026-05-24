"""
Import von Star Citizen Daten aus der Wiki API
Importiert Blueprints, Items, Missionen direkt von der Star Citizen Wiki API
Mit Pagination für komplette Daten
"""

import json
import logging
import requests
from database.db_connection import get_db

logger = logging.getLogger(__name__)

class StarCitizenDataImporter:
    """Importiert Star Citizen Daten von der Wiki API"""
    
    def __init__(self, api_base_url):
        """
        Initialisiere den Importer
        
        Args:
            api_base_url: Basis-URL der Star Citizen Wiki API
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.db = get_db()
        
        # API Endpoints
        self.items_url = f"{self.api_base_url}/api/items"
        self.blueprints_url = f"{self.api_base_url}/api/blueprints"
        self.missions_url = f"{self.api_base_url}/api/missions"
    
    def fetch_json(self, url):
        """Lade JSON von URL"""
        try:
            logger.info(f"Lade von: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Fehler beim Download von {url}: {e}")
            return None
    
    def import_all(self):
        """Importiere alle Daten"""
        logger.info("=" * 50)
        logger.info("Starte Star Citizen Daten-Import...")
        logger.info(f"API: {self.api_base_url}")
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
        """Importiere Blueprint-Daten mit Pagination"""
        logger.info("Importiere Blueprints...")
        
        imported = 0
        page = 1
        
        while True:
            url = f"{self.blueprints_url}?page={page}"
            data = self.fetch_json(url)
            
            if not data:
                break
            
            # Extrahiere Blueprints
            if isinstance(data, dict) and "data" in data:
                blueprints = data["data"]
            elif isinstance(data, list):
                blueprints = data
            else:
                break
            
            if not blueprints or not isinstance(blueprints, list) or len(blueprints) == 0:
                break
            
            page_imported = 0
            
            for bp_data in blueprints:
                if not isinstance(bp_data, dict):
                    continue
                
                name = bp_data.get("output_name", bp_data.get("name", "Unknown"))
                
                craft_time_seconds = bp_data.get("craft_time_seconds", 0)
                craft_time_minutes = int(craft_time_seconds / 60) if craft_time_seconds else 0
                
                source = bp_data.get("key", "")
                
                try:
                    query = """
                        INSERT INTO blueprints (name, crafting_time_minutes, source)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (name) DO UPDATE 
                        SET crafting_time_minutes = EXCLUDED.crafting_time_minutes
                    """
                    self.db.execute_update(query, (name, craft_time_minutes, source))
                    
                    select_query = "SELECT id FROM blueprints WHERE name = %s"
                    result = self.db.execute_query(select_query, (name,))
                    
                    if result:
                        bp_db_id = result[0][0]
                        
                        ingredients = bp_data.get("ingredients", [])
                        if isinstance(ingredients, list):
                            for ingredient in ingredients:
                                if isinstance(ingredient, dict):
                                    ing_name = ingredient.get("name", "Unknown")
                                    ing_qty = ingredient.get("quantity", ingredient.get("quantity_scu", 1))
                                    
                                    try:
                                        ing_qty = int(ing_qty) if ing_qty else 1
                                    except:
                                        ing_qty = 1
                                    
                                    ing_query = """
                                        INSERT INTO blueprint_ingredients 
                                        (blueprint_id, ingredient_name, quantity)
                                        VALUES (%s, %s, %s)
                                        ON CONFLICT DO NOTHING
                                    """
                                    self.db.execute_update(ing_query, (bp_db_id, ing_name, ing_qty))
                    
                    page_imported += 1
                except Exception as e:
                    logger.debug(f"Fehler bei Blueprint {name}: {e}")
                    continue
            
            imported += page_imported
            logger.info(f"   Seite {page}: {page_imported} Blueprints")
            
            page += 1
        
        logger.info(f"✓ {imported} Blueprints importiert!")
        return imported
    
    def import_items(self):
        """Importiere Items mit Pagination"""
        logger.info("Importiere Items...")
        
        imported = 0
        page = 1
        
        while True:
            url = f"{self.items_url}?page={page}"
            data = self.fetch_json(url)
            
            if not data:
                break
            
            if isinstance(data, dict) and "data" in data:
                items = data["data"]
            elif isinstance(data, list):
                items = data
            else:
                break
            
            if not items or not isinstance(items, list) or len(items) == 0:
                break
            
            page_imported = 0
            
            for item_data in items:
                if not isinstance(item_data, dict):
                    continue
                
                name = item_data.get("name", "Unknown")
                
                location = item_data.get("location", "Unknown")
                if isinstance(location, dict):
                    location = location.get("name", "Unknown")
                location = str(location) if location else "Unknown"
                
                item_type = "OTHER"
                type_str = str(item_data.get("type", "")).lower()
                if "hand" in type_str or "hand_mineable" in type_str:
                    item_type = "HAND_MINEABLE"
                elif "ship" in type_str or "ship_mineable" in type_str:
                    item_type = "SHIP_MINEABLE"
                elif "mission" in type_str or "quest" in type_str:
                    item_type = "NPC_MISSION"
                
                try:
                    query = """
                        INSERT INTO crafting_materials (name, location, mining_type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (name) DO UPDATE 
                        SET location = EXCLUDED.location
                    """
                    self.db.execute_update(query, (name, location, item_type))
                    page_imported += 1
                except Exception as e:
                    logger.debug(f"Fehler bei Item {name}: {e}")
                    continue
            
            imported += page_imported
            logger.info(f"   Seite {page}: {page_imported} Items")
            
            page += 1
        
        logger.info(f"✓ {imported} Items importiert!")
        return imported
    
    def import_missions(self):
        """Importiere Missionen mit Pagination"""
        logger.info("Importiere Missionen...")
        
        imported = 0
        page = 1
        
        while True:
            url = f"{self.missions_url}?page={page}"
            data = self.fetch_json(url)
            
            if not data:
                break
            
            if isinstance(data, dict) and "data" in data:
                missions = data["data"]
            elif isinstance(data, list):
                missions = data
            else:
                break
            
            if not missions or not isinstance(missions, list) or len(missions) == 0:
                break
            
            page_imported = 0
            processed = 0
            
            for mission_data in missions:
                processed += 1
                
                if not isinstance(mission_data, dict):
                    continue
                
                name = mission_data.get("title", mission_data.get("name", "Unknown"))
                
                # WICHTIG: faction kann ein Dict sein!
                faction = mission_data.get("faction", "Unknown")
                if isinstance(faction, dict):
                    faction = faction.get("name", "Unknown")
                faction = str(faction) if faction else "Unknown"
                
                # mission_giver nutzen falls faction nicht vorhanden
                mission_giver = mission_data.get("mission_giver", "Unknown")
                if faction == "Unknown" and mission_giver:
                    faction = mission_giver
                
                mission_type = mission_data.get("type", mission_data.get("mission_type", "Unknown"))
                mission_type = str(mission_type) if mission_type else "Unknown"
                
                # Reward verarbeiten
                reward = mission_data.get("reward", mission_data.get("reward_auc", 0))
                try:
                    reward = int(reward) if reward else 0
                except:
                    reward = 0
                
                xp = mission_data.get("xp", mission_data.get("reward_xp", 0))
                try:
                    xp = int(xp) if xp else 0
                except:
                    xp = 0
                
                # Reputation-Daten - kann Array sein!
                reputation_faction = "Unknown"
                reputation_amount = 0
                
                reputation_gained = mission_data.get("reputation_gained", [])
                if isinstance(reputation_gained, list) and len(reputation_gained) > 0:
                    rep_data = reputation_gained[0]
                    if isinstance(rep_data, dict):
                        reputation_faction = rep_data.get("faction", "Unknown")
                        reputation_faction = str(reputation_faction) if reputation_faction else "Unknown"
                        
                        reputation_amount = rep_data.get("amount", 0)
                        try:
                            reputation_amount = int(reputation_amount)
                        except:
                            reputation_amount = 0
                
                try:
                    query = """
                        INSERT INTO missions 
                        (name, faction, mission_type, reward_auc, reward_xp, reputation_faction, reputation_amount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE 
                        SET faction = EXCLUDED.faction,
                            reputation_faction = EXCLUDED.reputation_faction,
                            reputation_amount = EXCLUDED.reputation_amount
                    """
                    self.db.execute_update(
                        query, 
                        (name, faction, mission_type, reward, xp, reputation_faction, reputation_amount)
                    )
                    page_imported += 1
                except Exception as e:
                    logger.debug(f"Fehler bei Mission {name}: {e}")
                    continue
            
            imported += page_imported
            logger.info(f"   Seite {page}: {page_imported} Missionen")
            
            page += 1
        
        logger.info(f"✓ {imported} Missionen importiert!")
        return imported
