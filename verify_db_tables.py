"""Script pour vérifier les tables dans la base de données SQLite."""
import sqlite3
import sys
from pathlib import Path

def check_tables(db_path):
    """Affiche toutes les tables de la base de données."""
    try:
        # Se connecter à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer la liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Tables dans la base de données {db_path}:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Afficher les colonnes de la table
            try:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print("Colonnes:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Compter le nombre d'entrées
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"  Nombre d'entrées: {count}")
                
            except sqlite3.Error as e:
                print(f"  Erreur lors de la lecture de la table {table_name}: {e}")
        
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    db_path = "gw2_teambuilder.db"
    if not Path(db_path).exists():
        print(f"Erreur: Le fichier de base de données {db_path} n'existe pas.")
        sys.exit(1)
    
    check_tables(db_path)
