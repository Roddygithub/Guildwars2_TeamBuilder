#!/usr/bin/env python3
"""
Script de configuration automatique de Supabase pour Guild Wars 2 Team Builder.

Ce script permet de configurer automatiquement une base de données Supabase avec la structure
de données requise pour l'application.
"""
import os
import sys
import argparse
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Dict, Any, Optional, List
import json
import logging
from urllib.parse import urlparse

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SupabaseConfigurator:
    """Classe pour configurer une base de données Supabase."""
    
    def __init__(self, database_url: str):
        """Initialise le configurateur avec l'URL de la base de données.
        
        Args:
            database_url: URL de connexion à la base de données au format:
                postgresql://user:password@host:port/database
        """
        self.database_url = database_url
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Établit une connexion à la base de données.
        
        Returns:
            bool: True si la connexion a réussi, False sinon.
        """
        try:
            # Extraire les informations de connexion de l'URL
            parsed_url = urlparse(self.database_url)
            
            # S'assurer que le schème est correct
            if parsed_url.scheme not in ('postgresql', 'postgres'):
                logger.error("Le schème de l'URL doit être 'postgresql' ou 'postgres'")
                return False
            
            # Créer le dictionnaire de connexion
            conn_params = {
                'host': parsed_url.hostname,
                'port': parsed_url.port or 5432,
                'user': parsed_url.username,
                'password': parsed_url.password,
                'dbname': parsed_url.path.lstrip('/') or 'postgres',
                'sslmode': 'require'  # Force l'utilisation de SSL
            }
            
            # Établir la connexion
            self.connection = psycopg2.connect(**conn_params)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor()
            logger.info("Connexion à la base de données établie avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à la base de données: {e}")
            self.close()
            return False
    
    def close(self) -> None:
        """Ferme la connexion à la base de données."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Connexion à la base de données fermée")
    
    def execute_sql_file(self, file_path: str) -> bool:
        """Exécute un fichier SQL.
        
        Args:
            file_path: Chemin vers le fichier SQL à exécuter.
            
        Returns:
            bool: True si l'exécution a réussi, False sinon.
        """
        if not os.path.exists(file_path):
            logger.error(f"Le fichier {file_path} n'existe pas")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_commands = f.read()
            
            # Exécuter chaque commande séparément
            for command in sql_commands.split(';'):
                command = command.strip()
                if command:
                    self.cursor.execute(command)
            
            logger.info(f"Fichier SQL exécuté avec succès: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du fichier SQL {file_path}: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Configure la base de données avec la structure requise.
        
        Returns:
            bool: True si la configuration a réussi, False sinon.
        """
        if not self.connection or self.connection.closed != 0:
            logger.error("Aucune connexion active à la base de données")
            return False
        
        try:
            logger.info("Début de la configuration de la base de données...")
            
            # Vérifier si les tables existent déjà
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'professions'
                )
            """)
            tables_exist = self.cursor.fetchone()[0]
            
            if tables_exist:
                logger.warning("Les tables existent déjà dans la base de données")
                if input("Voulez-vous réinitialiser la base de données ? (o/n): ").lower() != 'o':
                    logger.info("Configuration annulée par l'utilisateur")
                    return False
                
                # Supprimer les tables existantes
                logger.info("Suppression des tables existantes...")
                self.cursor.execute("""
                    DROP TABLE IF EXISTS builds CASCADE;
                    DROP TABLE IF EXISTS skills CASCADE;
                    DROP TABLE IF EXISTS specializations CASCADE;
                    DROP TABLE IF EXISTS professions CASCADE;
                    DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
                """)
                logger.info("Anciennes tables supprimées")
            
            # Créer les tables et les fonctions
            logger.info("Création des tables et des fonctions...")
            
            # Création de la fonction pour mettre à jour automatiquement les champs updated_at
            self.cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Table des professions
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS professions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    display_name VARCHAR(50) NOT NULL,
                    icon VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Table des spécialisations
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS specializations (
                    id SERIAL PRIMARY KEY,
                    profession_id INTEGER REFERENCES professions(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    display_name VARCHAR(50) NOT NULL,
                    description TEXT,
                    icon VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(profession_id, name)
                );
            """)
            
            # Table des compétences
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id SERIAL PRIMARY KEY,
                    specialization_id INTEGER REFERENCES specializations(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    icon VARCHAR(100),
                    slot VARCHAR(20),
                    type VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Table des builds sauvegardés
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS builds (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    profession_id INTEGER REFERENCES professions(id) ON DELETE CASCADE,
                    specialization_id INTEGER REFERENCES specializations(id) ON DELETE SET NULL,
                    skills JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    is_public BOOLEAN DEFAULT false,
                    created_by UUID
                );
            """)
            
            # Création des index
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_builds_profession ON builds(profession_id);
                CREATE INDEX IF NOT EXISTS idx_builds_specialization ON builds(specialization_id);
                CREATE INDEX IF NOT EXISTS idx_builds_created_by ON builds(created_by);
                CREATE INDEX IF NOT EXISTS idx_builds_is_public ON builds(is_public);
            """)
            
            # Création des déclencheurs pour mettre à jour automatiquement les champs updated_at
            for table in ['professions', 'specializations', 'skills', 'builds']:
                self.cursor.execute(f"""
                    DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                    CREATE TRIGGER update_{table}_updated_at
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                """)
            
            logger.info("Structure de la base de données créée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de la base de données: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Teste la connexion à la base de données.
        
        Returns:
            bool: True si le test a réussi, False sinon.
        """
        try:
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            logger.info(f"Connexion réussie à PostgreSQL {version[0]}")
            return True
        except Exception as e:
            logger.error(f"Échec de la connexion à la base de données: {e}")
            return False

def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description='Configuration de la base de données Supabase')
    parser.add_argument(
        '--database-url',
        type=str,
        required=True,
        help='URL de connexion à la base de données (ex: postgresql://user:password@host:port/dbname)'
    )
    parser.add_argument(
        '--sql-file',
        type=str,
        help='Fichier SQL supplémentaire à exécuter après la configuration de base'
    )
    return parser.parse_args()

def main():
    """Fonction principale."""
    args = parse_arguments()
    
    # Initialiser le configurateur
    configurator = SupabaseConfigurator(args.database_url)
    
    try:
        # Établir la connexion
        if not configurator.connect():
            return 1
        
        # Tester la connexion
        if not configurator.test_connection():
            return 1
        
        # Configurer la base de données
        if not configurator.setup_database():
            return 1
        
        # Exécuter un fichier SQL supplémentaire si spécifié
        if args.sql_file:
            if not configurator.execute_sql_file(args.sql_file):
                return 1
        
        logger.info("Configuration de la base de données terminée avec succès!")
        return 0
        
    except Exception as e:
        logger.error(f"Une erreur inattendue s'est produite: {e}")
        return 1
    finally:
        # Toujours fermer la connexion
        configurator.close()

if __name__ == "__main__":
    sys.exit(main())
