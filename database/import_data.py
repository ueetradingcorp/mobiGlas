"""
Import von Star Citizen Daten aus der Wiki API
Optimiert mit Filtern und dynamischer Version-Abfrage mit Fallback
"""

import json
import logging
import requests
from database.db_connection import get_db

logger = logging.getLogger(__name__)

# Blacklist: Commodities die NICHT als Crafting-Zutaten importiert werden sollen
EXCLUDED_COMMODITIES = {
    "Altruciatoxin",
    "Carinite",
    "Compboard",
    "Construction Materials",
    "Decari Pod",
    "Degnous Root",
    "E'tam",
    "Fotia Seedpod",
    "Fresh Food",
    "Golden Medmon",
    "Heart of the Woods",
    "Jaclium (Ore)",
    "Lindinium (Ore)",
    "Maze",
    "Neograph",
    "Neon",
    "Organics",
    "<= PLACEHOLDER =>",
    "Prota",
    "Pingala Seeds",
    "Pitambu",
    "Ranta Dung",
    "Raw Ouratite",
    "Recycled Material Composite",
    "Revenant Pod",
    "SLAM",
    "Sunset Berries",
    "Tungsten (Ore)",
    "WiDoW",
    "Nitrogen",
}

# Mapping: Ort-Name → (System, Typ)
LOCATION_MAPPING = {
    # Systeme
    "Stanton System": ("Stanton", "System"),
    "Pyro System": ("Pyro", "System"),
    "Nyx System": ("Nyx", "System"),
    
    # Planeten
    "Hurston": ("Stanton", "Planet"),
    "Crusader": ("Stanton", "Planet"),
    "ArcCorp": ("Stanton", "Planet"),
    "microTech": ("Stanton", "Planet"),
    
    # Monde
    "Aberdeen": ("Stanton", "Moon"),
    "Arial": ("Stanton", "Moon"),
    "Calliope": ("Stanton", "Moon"),
    "Cellin": ("Stanton", "Moon"),
    "Clio": ("Stanton", "Moon"),
    "Daymar": ("Stanton", "Moon"),
    "Euterpe": ("Stanton", "Moon"),
    "Ita": ("Stanton", "Moon"),
    "Lyria": ("Stanton", "Moon"),
    "Magda": ("Stanton", "Moon"),
    "Wala": ("Stanton", "Moon"),
    "Yela": ("Stanton", "Moon"),
    
    # Asteroiden/Mining Bases
    "Mining Base #01K-I43": ("Stanton", "Asteroid"),
    "Mining Base #0YX-O7Z": ("Stanton", "Asteroid"),
    "Mining Base #1XA-3GI": ("Stanton", "Asteroid"),
    "Mining Base #365-YNZ": ("Stanton", "Asteroid"),
    "Mining Base #4PI-3YY": ("Stanton", "Asteroid"),
    "Mining Base #4R0-NVX": ("Stanton", "Asteroid"),
    "Mining Base #51F-OGH": ("Stanton", "Asteroid"),
    "Mining Base #5U5-TLC": ("Stanton", "Asteroid"),
    "Mining Base #6IN-P02": ("Stanton", "Asteroid"),
    "Mining Base #74H-2DO": ("Stanton", "Asteroid"),
    "Mining Base #7IQ-29Q": ("Stanton", "Asteroid"),
    "Mining Base #7LI-0OA": ("Stanton", "Asteroid"),
    "Mining Base #7YH-JX7": ("Stanton", "Asteroid"),
    "Mining Base #8CG-OSA": ("Stanton", "Asteroid"),
    "Mining Base #8PV-WNE": ("Stanton", "Asteroid"),
    "Mining Base #A73-HTJ": ("Stanton", "Asteroid"),
    "Mining Base #AL5-XPD": ("Stanton", "Asteroid"),
    "Mining Base #BBR-4JQ": ("Stanton", "Asteroid"),
    "Mining Base #BRE-582": ("Stanton", "Asteroid"),
    "Mining Base #BSK-IJ5": ("Stanton", "Asteroid"),
    "Mining Base #CVF-T6H": ("Stanton", "Asteroid"),
    "Mining Base #CZW-RRY": ("Stanton", "Asteroid"),
    "Mining Base #E38-S5G": ("Stanton", "Asteroid"),
    "Mining Base #GO4-CH0": ("Stanton", "Asteroid"),
    "Mining Base #IGB-FXW": ("Stanton", "Asteroid"),
    "Mining Base #IO3-H1F": ("Stanton", "Asteroid"),
    "Mining Base #JUG-0KZ": ("Stanton", "Asteroid"),
    "Mining Base #LBP-UN5": ("Stanton", "Asteroid"),
    "Mining Base #N6J-XKH": ("Stanton", "Asteroid"),
    "Mining Base #ODD-E9B": ("Stanton", "Asteroid"),
    "Mining Base #OYV-JKE": ("Stanton", "Asteroid"),
    "Mining Base #Q4U-I20": ("Stanton", "Asteroid"),
    "Mining Base #Q9Q-090": ("Stanton", "Asteroid"),
    "Mining Base #QXS-NBS": ("Stanton", "Asteroid"),
    "Mining Base #R08-Y3K": ("Stanton", "Asteroid"),
    "Mining Base #R75-5PZ": ("Stanton", "Asteroid"),
    "Mining Base #R7J-WJ7": ("Stanton", "Asteroid"),
    "Mining Base #RCD-OB3": ("Stanton", "Asteroid"),
    "Mining Base #RSV-8HL": ("Stanton", "Asteroid"),
    "Mining Base #SAG-2UN": ("Stanton", "Asteroid"),
    "Mining Base #U5X-NGQ": ("Stanton", "Asteroid"),
    "Mining Base #UDK-IJX": ("Stanton", "Asteroid"),
    "Mining Base #URB-H3V": ("Stanton", "Asteroid"),
    "Mining Base #UU6-1EI": ("Stanton", "Asteroid"),
    "Mining Base #W79-2H7": ("Stanton", "Asteroid"),
    "Mining Base #WUO-ZRU": ("Stanton", "Asteroid"),
    "Mining Base #X92-IVA": ("Stanton", "Asteroid"),
    "Mining Base #XJZ-JR2": ("Stanton", "Asteroid"),
    "Mining Base #YTO-GLQ": ("Stanton", "Asteroid"),
    "Mining Base #Z48-013": ("Stanton", "Asteroid"),
    "Stanton": ("Stanton", "Star"),
}

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
        self.game_version = None
        
        # API Endpoints
        self.game_versions_url = f"{self.api_base_url}/api/game-versions"
        self.blueprints_url = f"{self.api_base_url}/api/blueprints"
        self.commodities_url = f"{self.api_base_url}/api/commodities"
        self.missions_url = f"{self.api_base_url}/api/missions"
        
        # Hole Game-Version beim Initialisieren
        self._init_game_version()
    
    def _init_game_version(self):
        """Initialisiere Game-Version beim Konstruktor"""
        self.game_version = self.get_game_version()
    
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
    
    def get_game_version(self):
        """Hole die aktuelle Standard Game-Version"""
        logger.info("Ermittle aktuelle Game-Version...")
        
        url = f"{self.game_versions_url}/default"
        data = self.fetch_json(url)
        
        if data:
            logger.info(f"Response von {url}: {json.dumps(data, indent=2)[:500]}")
        
        if not data or not isinstance(data, dict):
            logger.warning("⚠️ Game-Version-API antwortete nicht wie erwartet")
            logger.info("Nutze Fallback-Version: 4.8.0-LIVE.11875683")
            return "4.8.0-LIVE.11875683"
        
        version = data.get("code", None)
        if not version:
            version = data.get("version", None)
        if not version:
            version = data.get("name", None)
        
        if version:
            logger.info(f"✓ Game-Version ermittelt: {version}")
            return version
        
        logger.warning("⚠️ Konnte Version nicht aus Response extrahieren")
        logger.info("Nutze Fallback-Version: 4.8.0-LIVE.11875683")
        return "4.8.0-LIVE.11875683"
    
    def import_blueprints(self):
        """Importiere Blueprint-Daten mit Pagination"""
        logger.info("Importiere Blueprints...")
        logger.info(f"Verwende Game-Version: {self.game_version}")
        
        imported = 0
        page = 1
        
        while True:
            url = f"{self.blueprints_url}?page[number]={page}&page[size]=200&version={self.game_version}"
            data = self.fetch_json(url)
            
            if not data:
                break
            
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
                
                name = bp_data.get("output_name", None)
                if not name or name == "Unknown":
                    name = bp_data.get("name", None)
                
                if not name:
                    continue
                
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
            
            if len(blueprints) < 200:
                break
            
            page += 1
        
        logger.info(f"✓ {imported} Blueprints importiert!")
        return imported
    
    def import_commodities(self):
        """Importiere Commodities mit Pagination - nur echte Crafting-Zutaten!"""
        logger.info("Importiere Commodities...")
        logger.info(f"Verwende Game-Version: {self.game_version}")
        
        imported = 0
        page = 1
        
        while True:
            url = f"{self.commodities_url}?page[number]={page}&page[size]=200&version={self.game_version}&filter[mineable]=true"
            data = self.fetch_json(url)
            
            if not data:
                break
            
            if isinstance(data, dict) and "data" in data:
                commodities = data["data"]
            elif isinstance(data, list):
                commodities = data
            else:
                break
            
            if not commodities or not isinstance(commodities, list) or len(commodities) == 0:
                break
            
            page_imported = 0
            
            for commodity_data in commodities:
                if not isinstance(commodity_data, dict):
                    continue
                
                name = commodity_data.get("name", "Unknown")
                
                # BLACKLIST: Skip ausgeschlossene Items
                if name in EXCLUDED_COMMODITIES:
                    logger.debug(f"Skip {name} (in Blacklist)")
                    continue
                
                # Sammle ALLE Fundorte
                locations_list = []
                
                locations = commodity_data.get("locations", [])
                if locations and isinstance(locations, list):
                    for loc in locations:
                        if isinstance(loc, dict):
                            loc_name = loc.get("name", "Unbekannt")
                        else:
                            loc_name = str(loc)
                        locations_list.append(loc_name)
                
                # Fallback: systems
                if not locations_list:
                    systems = commodity_data.get("systems", [])
                    if systems and isinstance(systems, list):
                        for sys in systems:
                            if isinstance(sys, dict):
                                sys_name = sys.get("name", "Unbekannt")
                            else:
                                sys_name = str(sys)
                            locations_list.append(sys_name)
                
                # Sortiere Fundorte nach Typ (System → Planet → Moon → Asteroid)
                location = self._sort_locations(locations_list)
                location = str(location) if location else "Unbekannt"
                
                # Bestimme Mining-Type
                item_type = "SHIP_MINEABLE"  # Standard
                
                if commodity_data.get("has_fps_mineables") or commodity_data.get("has_ground_vehicle_mineables"):
                    item_type = "HAND_MINEABLE"
                elif commodity_data.get("has_harvestables"):
                    item_type = "HAND_MINEABLE"
                
                try:
                    query = """
                        INSERT INTO crafting_materials (name, location, mining_type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (name) DO UPDATE 
                        SET location = EXCLUDED.location,
                            mining_type = EXCLUDED.mining_type
                    """
                    self.db.execute_update(query, (name, location, item_type))
                    page_imported += 1
                except Exception as e:
                    logger.debug(f"Fehler bei Commodity {name}: {e}")
                    continue
            
            imported += page_imported
            logger.info(f"   Seite {page}: {page_imported} Commodities")
            
            if len(commodities) < 200:
                break
            
            page += 1
        
        logger.info(f"✓ {imported} Commodities importiert!")
        return imported
    
    def _sort_locations(self, locations_list):
        """Sortiere Fundorte nach Typ: System → Planet → Moon → Asteroid"""
        if not locations_list:
            return "Unbekannt"
        
        # Kategorisiere Fundorte
        systems = []
        planets = []
        moons = []
        asteroids = []
        others = []
        
        for loc in locations_list:
            if loc in LOCATION_MAPPING:
                sys, loc_type = LOCATION_MAPPING[loc]
                
                if loc_type == "System":
                    systems.append(loc)
                elif loc_type == "Planet":
                    planets.append(loc)
                elif loc_type == "Moon":
                    moons.append(loc)
                elif loc_type == "Asteroid":
                    asteroids.append(loc)
                else:
                    others.append(loc)
            else:
                others.append(loc)
        
        # Sortiere jede Kategorie alphabetisch
        systems.sort()
        planets.sort()
        moons.sort()
        asteroids.sort()
        others.sort()
        
        # Kombiniere in Reihenfolge
        sorted_locations = systems + planets + moons + asteroids + others
        
        return ", ".join(sorted_locations)
    
    def import_missions(self):
        """Importiere Missionen mit Pagination - nur veröffentlichte Blueprint-Missionen"""
        logger.info("Importiere Missionen...")
        logger.info(f"Verwende Game-Version: {self.game_version}")
        
        imported = 0
        page = 1
        
        while True:
            url = f"{self.missions_url}?page[number]={page}&page[size]=200&version={self.game_version}&filter[include_unreleased]=false&filter[has_blueprints]=true"
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
            
            for mission_data in missions:
                if not isinstance(mission_data, dict):
                    continue
                
                name = mission_data.get("title", mission_data.get("name", "Unknown"))
                
                faction = mission_data.get("faction", "Unknown")
                if isinstance(faction, dict):
                    faction = faction.get("name", "Unknown")
                faction = str(faction) if faction else "Unknown"
                
                mission_giver = mission_data.get("mission_giver", "Unknown")
                if faction == "Unknown" and mission_giver:
                    faction = mission_giver
                
                mission_type = mission_data.get("type", mission_data.get("mission_type", "Unknown"))
                mission_type = str(mission_type) if mission_type else "Unknown"
                
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
            
            if len(missions) < 200:
                break
            
            page += 1
        
        logger.info(f"✓ {imported} Missionen importiert!")
        return imported
