"""Script pour inspecter le contenu de la base de données."""
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.config import settings

# Créer un moteur SQLAlchemy
engine = create_engine(settings.DATABASE_URL)

# Créer une session
Session = sessionmaker(bind=engine)
session = Session()

def list_tables():
    """Affiche la liste des tables dans la base de données."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\nTables dans la base de données:")
    for table in tables:
        print(f"- {table}")
    return tables

def inspect_table(table_name):
    """Affiche les colonnes et un aperçu des données d'une table."""
    inspector = inspect(engine)
    
    # Afficher les colonnes
    columns = inspector.get_columns(table_name)
    print(f"\nStructure de la table '{table_name}':")
    for column in columns:
        print(f"- {column['name']}: {column['type']}")
    
    # Afficher un aperçu des données
    try:
        result = session.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
        rows = result.fetchall()
        
        if rows:
            print(f"\nAperçu des données (5 premières lignes):")
            for row in rows:
                print(row)
        else:
            print("La table est vide.")
    except Exception as e:
        print(f"Erreur lors de la lecture des données: {e}")

def main():
    """Fonction principale."""
    print("Inspection de la base de données...")
    
    # Afficher les tables
    tables = list_tables()
    
    # Demander à l'utilisateur quelle table inspecter
    if tables:
        table_name = input("\nEntrez le nom d'une table à inspecter (ou appuyez sur Entrée pour quitter): ")
        if table_name and table_name in tables:
            inspect_table(table_name)
        else:
            print("Nom de table invalide ou annulation.")
    else:
        print("Aucune table trouvée dans la base de données.")
    
    session.close()

if __name__ == "__main__":
    main()
