"""
Datenbankverbindung für mobiGlas Bot
Verwaltet die Verbindung zu PostgreSQL
"""

import psycopg2
from psycopg2 import pool
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    """Verwaltet die PostgreSQL Datenbankverbindung"""
    
    def __init__(self):
        """Initialisiere die Datenbankverbindung"""
        try:
            # Verbindungs-Pool für mehrere gleichzeitige Anfragen
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # Minimale Verbindungen
                20,  # Maximale Verbindungen
                DATABASE_URL
            )
            logger.info("✓ Datenbankverbindung erfolgreich aufgebaut!")
        except psycopg2.Error as e:
            logger.error(f"❌ Fehler beim Verbinden zur Datenbank: {e}")
            raise
    
    def get_connection(self):
        """Hole eine Verbindung aus dem Pool"""
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Gib eine Verbindung an den Pool zurück"""
        if conn:
            self.connection_pool.putconn(conn)
    
    def execute_query(self, query, params=None):
        """
        Führe eine SQL-Query aus (SELECT)
        
        Args:
            query: SQL-Query
            params: Parameter für die Query
        
        Returns:
            Liste mit Ergebnissen
        """
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return results
        except psycopg2.Error as e:
            logger.error(f"❌ Fehler bei Query-Ausführung: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.return_connection(conn)
    
    def execute_update(self, query, params=None):
        """
        Führe eine SQL-Query aus (INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL-Query
            params: Parameter für die Query
        
        Returns:
            True wenn erfolgreich, False wenn Fehler
        """
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            logger.debug(f"✓ Query erfolgreich ausgeführt: {query[:50]}...")
            return True
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"❌ Fehler bei Update: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            self.return_connection(conn)
    
    def create_tables(self):
        """Erstelle alle notwendigen Datenbank-Tabellen"""
        logger.info("Erstelle Datenbank-Tabellen...")
        
        queries = [
            # Blueprints / Rezepte
            """
            CREATE TABLE IF NOT EXISTS blueprints (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                crafting_time_minutes INT DEFAULT 0,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Zutaten für Blueprints
            """
            CREATE TABLE IF NOT EXISTS blueprint_ingredients (
                id SERIAL PRIMARY KEY,
                blueprint_id INT NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
                ingredient_name VARCHAR(255) NOT NULL,
                quantity INT DEFAULT 1,
                UNIQUE(blueprint_id, ingredient_name)
            );
            """,
            
            # Crafting-Materialien
            """
            CREATE TABLE IF NOT EXISTS crafting_materials (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                location VARCHAR(255),
                mining_type VARCHAR(50) DEFAULT 'OTHER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Missionen
            """
            CREATE TABLE IF NOT EXISTS missions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                faction VARCHAR(255),
                mission_type VARCHAR(100),
                reward_auc INT,
                reward_xp INT,
                reputation_rank VARCHAR(100),
                reputation_xp INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # User-Inventar
            """
            CREATE TABLE IF NOT EXISTS user_blueprints (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                blueprint_id INT NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, blueprint_id)
            );
            """
        ]
        
        for query in queries:
            self.execute_update(query)
        
        logger.info("✓ Alle Tabellen erstellt!")
    
    def close(self):
        """Schließe alle Verbindungen im Pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Datenbankverbindungen geschlossen.")


# Globale Instanz
db = None

def init_database():
    """Initialisiere die Datenbank"""
    global db
    db = Database()
    db.create_tables()
    return db

def get_db():
    """Hole die globale Datenbank-Instanz"""
    global db
    if db is None:
        db = init_database()
    return db
