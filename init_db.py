"""Script pour initialiser une nouvelle base de données SQLite pour GuildWars2 TeamBuilder."""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, MetaData, inspect

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Importer les modèles pour s'assurer que toutes les tables sont définies
from app.models.base import Base
from app.models.skill import Skill
from app.models.weapon import Weapon
from app.models.profession import Profession
from app.models.profession_weapon import ProfessionWeaponType
from app.models.specialization import Specialization
from app.models.trait import Trait
from app.models.character import Character

# Configuration de la base de données
DB_PATH = 'gw2_teambuilder.db'
DB_URL = f'sqlite:///{DB_PATH}'

def init_database():
    """Initialise la base de données avec toutes les tables définies dans les modèles."""
    print(f"Initialisation de la base de données à l'emplacement: {os.path.abspath(DB_PATH)}")
    
    # Supprimer le fichier de base de données s'il existe déjà
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"Ancien fichier de base de données supprimé: {DB_PATH}")
        except Exception as e:
            print(f"Erreur lors de la suppression de l'ancienne base de données: {e}")
            return False
    
    try:
        # Créer le moteur SQLAlchemy
        engine = create_engine(DB_URL, echo=True)
        
        # Créer toutes les tables définies dans les modèles
        print("Création des tables...")
        Base.metadata.create_all(engine)
        
        print("Base de données initialisée avec succès!")
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False

def verify_database():
    """Vérifie que la base de données a été correctement initialisée."""
    if not os.path.exists(DB_PATH):
        print(f"Erreur: Le fichier de base de données n'existe pas: {DB_PATH}")
        return False
    
    try:
        engine = create_engine(DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\nTables dans la base de données:")
        for table in tables:
            print(f"- {table}")
            
            # Afficher les colonnes de chaque table
            columns = inspector.get_columns(table)
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de la vérification de la base de données: {e}")
        return False

if __name__ == "__main__":
    print("=== Initialisation de la base de données GuildWars2 TeamBuilder ===\n")
    print(f"Répertoire de travail: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    try:
        # Initialiser la base de données
        print("\nDébut de l'initialisation de la base de données...")
        if init_database():
            print("\n=== Vérification de la base de données ===\n")
            verify_database()
            print("\nBase de données initialisée avec succès!")
        else:
            print("\nÉchec de l'initialisation de la base de données.")
    except Exception as e:
        print(f"\nERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
