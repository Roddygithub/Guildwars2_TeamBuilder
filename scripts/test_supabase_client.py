#!/usr/bin/env python3
"""
Script de test du client Supabase pour Guild Wars 2 Team Builder.
"""
import os
import sys
import logging
from supabase import create_client, Client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_supabase_connection():
    """Teste la connexion à Supabase avec le client officiel."""
    try:
        # URL et clé de l'API Supabase
        SUPABASE_URL = "https://yhhknatbxmavlyhtugqc.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InloaGtuYXRieG1hdmx5aHR1Z3FjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIwODk3NjQsImV4cCI6MjA2NzY2NTc2NH0.cBn_L1UFzRHn_z_xWiy2_PuqVHQ73cD_ODCG7CAh-Qo"
        
        logger.info("Tentative de connexion à Supabase...")
        
        # Créer le client Supabase
        logger.info("Création du client Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Client Supabase créé avec succès")
        
        # Créer une table de test si elle n'existe pas
        table_name = "test_connection"
        logger.info(f"Vérification de la table {table_name}...")
        
        # Tester l'insertion d'une donnée dans la table
        try:
            # Essayer d'insérer des données
            test_data = {
                "name": "Test",
                "description": "Test de connexion",
                "status": "active"
            }
            
            logger.info(f"Tentative d'insertion dans la table {table_name}...")
            response = supabase.table(table_name).insert(test_data).execute()
            
            if hasattr(response, 'data') and response.data:
                logger.info(f"✅ Donnée insérée avec succès: {response.data}")
                
                # Lire les données insérées
                logger.info("Lecture des données insérées...")
                result = supabase.table(table_name).select("*").eq("name", "Test").execute()
                logger.info(f"Données lues: {result.data}")
                
                # Mettre à jour les données
                logger.info("Mise à jour des données...")
                update_data = {"status": "completed"}
                update_result = supabase.table(table_name).update(update_data).eq("name", "Test").execute()
                logger.info(f"Donnée mise à jour: {update_result.data}")
                
                # Supprimer les données de test
                logger.info("Suppression des données de test...")
                delete_result = supabase.table(table_name).delete().eq("name", "Test").execute()
                logger.info(f"Données supprimées: {delete_result.data}")
                
                logger.info("✅ Tous les tests CRUD ont réussi!")
            else:
                logger.warning("⚠️ Aucune donnée retournée après insertion")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors des opérations CRUD: {e}")
            logger.info("Tentative de création de la table...")
            
            # Créer la table via l'API REST (si vous avez les permissions)
            try:
                # Créer la table via SQL (nécessite les bonnes permissions)
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
                
                # Exécuter le SQL via l'API REST (si vous avez les permissions)
                # Note: Cette méthode peut ne pas fonctionner selon les permissions
                create_result = supabase.rpc('execute_sql', {'query': create_table_sql}).execute()
                logger.info(f"Table {table_name} créée avec succès")
                
                # Réessayer l'insertion après création de la table
                logger.info("Nouvelle tentative d'insertion...")
                response = supabase.table(table_name).insert(test_data).execute()
                logger.info(f"Donnée insérée après création de la table: {response.data}")
                
            except Exception as create_error:
                logger.error(f"❌ Impossible de créer la table: {create_error}")
                logger.info("""
                Pour résoudre ce problème :
                1. Connectez-vous à l'interface Supabase
                2. Allez dans l'éditeur SQL
                3. Exécutez la requête SQL suivante :
                
                CREATE TABLE IF NOT EXISTS test_connection (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """)
        
        return True
        
    except Exception as e:
        logger.error(f"Échec de la connexion à Supabase: {e}")
        return False

if __name__ == "__main__":
    # Installer la dépendance si nécessaire
    try:
        import supabase
    except ImportError:
        logger.info("Installation de la dépendance 'supabase'...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
        
    test_supabase_connection()
