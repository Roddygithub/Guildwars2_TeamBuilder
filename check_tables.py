import sqlite3
import os

def list_tables(db_path):
    """Liste toutes les tables de la base de données SQLite."""
    if not os.path.exists(db_path):
        print(f"Erreur: Le fichier de base de données {db_path} n'existe pas.")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer la liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        print("Tables dans la base de données:")
        for table in tables:
            print(f"- {table[0]}")
            
            # Afficher les colonnes de chaque table
            cursor.execute(f"PRAGMA table_info({table[0]});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
            print()
            
        return [table[0] for table in tables]
        
    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_path = "gw2_teambuilder.db"
    print(f"Vérification de la base de données: {os.path.abspath(db_path)}")
    tables = list_tables(db_path)
    
    if tables:
        print(f"\nTotal de {len(tables)} tables trouvées.")
    else:
        print("Aucune table trouvée ou erreur lors de la connexion.")
