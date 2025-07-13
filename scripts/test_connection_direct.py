#!/usr/bin/env python3
"""
Script de test de connexion directe à la base de données Supabase.
"""
import psycopg2
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

def test_direct_connection():
    """Teste une connexion directe avec psycopg2."""
    conn = None
    try:
        # Paramètres de connexion
        db_params = {
            'host': 'db.yhhknatbxmavlyhtugqc.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'RNt@2hQZUwZsiq2',
            'sslmode': 'require'
        }
        
        logger.info("Tentative de connexion directe avec psycopg2...")
        
        # Établir la connexion
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        
        # Exécuter une requête simple
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            logger.info(f"Connexion réussie! Version de PostgreSQL: {version[0]}")
            
            # Tester la création d'une table
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS test_connection (
                        id SERIAL PRIMARY KEY,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                logger.info("Table de test créée avec succès!")
                
                # Insérer des données de test
                cur.execute(
                    "INSERT INTO test_connection (message) VALUES (%s) RETURNING id;",
                    ("Test de connexion réussi!",)
                )
                test_id = cur.fetchone()[0]
                logger.info(f"Donnée de test insérée avec l'ID: {test_id}")
                
                # Lire les données insérées
                cur.execute("SELECT message FROM test_connection WHERE id = %s;", (test_id,))
                result = cur.fetchone()
                logger.info(f"Donnée lue: {result[0]}")
                
                # Nettoyage (optionnel)
                # cur.execute("DROP TABLE IF EXISTS test_connection;")
                
            except Exception as e:
                logger.error(f"Erreur lors de la manipulation de la table: {e}")
                if conn is not None:
                    conn.rollback()
                raise
        
        return True
        
    except Exception as e:
        logger.error(f"Échec de la connexion directe: {e}")
        return False
        
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    test_direct_connection()
