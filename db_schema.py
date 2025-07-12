"""Script pour inspecter le schéma de la base de données."""
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, MetaData, Table

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.config import settings

def main():
    """Fonction principale pour inspecter le schéma de la base de données."""
    print("Inspection du schéma de la base de données...")
    
    # Créer un moteur SQLAlchemy
    engine = create_engine(settings.DATABASE_URL)
    
    # Créer un objet d'inspection
    inspector = inspect(engine)
    
    # Obtenir les noms de toutes les tables
    tables = inspector.get_table_names()
    
    if not tables:
        print("Aucune table trouvée dans la base de données.")
        return
    
    print("\nTables trouvées dans la base de données:")
    for table in tables:
        print(f"- {table}")
    
    # Si la table 'skills' existe, examiner sa structure
    if 'skills' in tables:
        print("\nStructure de la table 'skills':")
        columns = inspector.get_columns('skills')
        for column in columns:
            print(f"- {column['name']}: {column['type']}")
        
        # Essayer de compter les entrées
        with engine.connect() as conn:
            try:
                result = conn.execute("SELECT COUNT(*) FROM skills")
                count = result.scalar()
                print(f"\nNombre total d'entrées dans 'skills': {count}")
                
                # Afficher un échantillon des types de compétences
                if count > 0:
                    result = conn.execute("SELECT DISTINCT type FROM skills LIMIT 20")
                    types = [row[0] for row in result]
                    print("\nExemples de types de compétences trouvés:")
                    for t in types:
                        print(f"- {t}")
            except Exception as e:
                print(f"\nErreur lors de la lecture des données: {e}")
    
    # Vérifier s'il y a des données dans d'autres tables
    for table in tables:
        if table != 'skills':
            with engine.connect() as conn:
                try:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    print(f"\nTable '{table}': {count} entrées")
                except Exception as e:
                    print(f"\nErreur lors de la lecture de la table '{table}': {e}")

if __name__ == "__main__":
    main()
