"""
Import von Star Citizen Daten aus der Wiki API
Importiert Blueprints, Items, Missionen direkt von der Star Citizen Wiki API
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
        """Importiere Blueprint-Daten"""
        logger.info("Importiere Blueprints...")
        
        data = self.fetch_json(self.blueprints_url)
        
        if not data:
            logger.error("❌ Blueprints konnten nicht geladen werden")
            return 0
        
        # Daten können in verschiedenen Formaten kommen
        if isinstance(data, dict) and "data" in data:
            blueprints = data["data"]
        elif isinstance(data, list):
            blueprints = data
        else:
            blueprints = data
        
        if not isinstance(blueprints, (list, dict)):
            logger.error("❌ Unerwartetes Blueprint-Format")
            return 0
        
        imported = 0
        
        # Iteriere über Blueprints
        items_iter = blueprints.items() if isinstance(blueprints, dict) else enumerate(blueprints)
        
        for idx, bp_data in items_iter:
            if not isinstance(bp_data, dict):
                continue
            
            name = bp_data.get("name", f"Unknown_{idx}")
            craft_time = bp_data.get("craftTime", bp_data.get("craft_time", 0))
            if isinstance(craft_time, str):
                try:
                    craft_time = int(craft_time)
                except:
                    craft_time = 0
            
            try:
                # Insertiere Blueprint
                query = """
                    INSERT INTO blueprints (name, crafting_time_minutes, source)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE 
                    SET crafting_time_minutes = EXCLUDED.crafting_time_minutes
                """
                self.db.execute_update(query, (name, craft_time, str(idx)))
                
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
                                ing_qty = ingredient.get("quantity", ingredient.get("count", 1))
                                
                                try:
                                    ing_qty = int(ing_qty)
                                except:
                                    ing_qty = 1
                                
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
        
        data = self.fetch_json(self.items_url)
        
        if not data:
            logger.error("❌ Items konnten nicht geladen werden")
            return 0
        
        # Daten können in verschiedenen Formaten kommen
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif isinstance(data, list):
            items = data
        else:
            items = data
        
        if not isinstance(items, (list, dict)):
            logger.error("❌ Unerwartetes Items-Format")
            return 0
        
        imported = 0
        
        # Iteriere über Items
        items_iter = items.items() if isinstance(items, dict) else enumerate(items)
        
        for idx, item_data in items_iter:
            if not isinstance(item_data, dict):
                continue
            
            name = item_data.get("name", f"Unknown_{idx}")
            location = item_data.get("location", item_data.get("found_at", "Unknown"))
            
            # Mining-Type bestimmen
            item_type = "OTHER"
            type_str = item_data.get("type", "").lower()
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
                imported += 1
            except Exception as e:
                logger.debug(f"Fehler bei Item {name}: {e}")
                continue
        
        logger.info(f"✓ {imported} Items importiert!")
        return imported
    
    def import_missions(self):
        """Importiere Missionen"""
        logger.info("Importiere Missionen...")
        
        data = self.fetch_json(self.missions_url)
        
        if not data:
            logger.error("❌ Missionen konnten nicht geladen werden")
            return 0
        
        # Daten können in verschiedenen Formaten kommen
        if isinstance(data, dict) and "data" in data:
            missions = data["data"]
        elif isinstance(data, list):
            missions = data
        else:
            missions = data
        
        if not isinstance(missions, (list, dict)):
            logger.error("❌ Unerwartetes Missions-Format")
            return 0
        
        imported = 0
        processed = 0
        
        # Iteriere über Missionen
        missions_iter = missions.items() if isinstance(missions, dict) else enumerate(missions)
        
        for idx, mission_data in missions_iter:
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"   Verarbeite Mission {processed}...")
            
            if not isinstance(mission_data, dict):
                continue
            
            name = mission_data.get("name", mission_data.get("title", f"Unknown_{idx}"))
            faction = mission_data.get("faction", mission_data.get("giver", "Unknown"))
            mission_type = mission_data.get("type", mission_data.get("mission_type", "Unknown"))
            
            # Rewards verarbeiten
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
        
        logger.info(f"✓ {imported} Missionen importiert!")
        return imported
