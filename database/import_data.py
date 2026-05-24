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
        self.items_url = f"{self.api_base_url}/items"
        self.blueprints_url = f"{self.api_base_url}/blueprints"
        self.missions_url = f"{self.api_base_url}/missions"
    
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
        
        logger.info(f"
