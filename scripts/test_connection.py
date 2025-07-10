#!/usr/bin/env python3
"""
Script de test de connexion à la base de données Supabase.
"""
import psycopg2
from urllib.parse import quote_plus
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_connection(host, port, database, user, password):
    """Teste la connexion à la base de données."""
    conn = None
    try:
        # Échapper le mot de passe
        safe_password = quote_plus(password)
        
        # Construire la chaîne de connexion
        conn_string = f"host='{host}' port={port} dbname='{database}' user='{user}' password='{safe_password}'"
        
        logger.info("Tentative de connexion avec les paramètres:")
        logger.info(f"- Hôte: {host}")
        logger.info(f"- Port: {port}")
        logger.info(f"- Base de données: {database}")
        logger.info(f"- Utilisateur: {user}")
        
        # Tester la connexion
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        
        # Exécuter une requête simple
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        logger.info("Connexion réussie!")
        logger.info(f"Version de PostgreSQL: {version[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Échec de la connexion: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Paramètres de connexion
    DB_HOST = "db.yhhknatbxmavlyhtugqc.supabase.co"
    DB_PORT = 5432
    DB_NAME = "postgres"
    DB_USER = "postgres"
    DB_PASSWORD = "RNt@2hQZUwZsiq2"  # Nouveau mot de passe
    
    # Tester la connexion
    test_connection(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
