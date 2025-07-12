"""Script pour vérifier le contenu de la base de données."""
import os
import sqlite3
from tabulate import tabulate

def check_database(db_path):
    """Affiche le contenu de toutes les tables de la base de données."""
    if not os.path.exists(db_path):
        print(f"Erreur: Le fichier de base de données {db_path} n'existe pas.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer la liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n=== Tables trouvées dans {db_path} ===")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 7))
            
            try:
                # Récupérer les données de la table
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
                rows = cursor.fetchall()
                
                # Récupérer les noms des colonnes
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [column[1] for column in cursor.fetchall()]
                
                if rows:
                    print(tabulate(rows, headers=columns, tablefmt="grid"))
                else:
                    print("Aucune donnée trouvée.")
                
                # Afficher le nombre total de lignes
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"\nTotal: {count} enregistrement(s)")
                
            except sqlite3.Error as e:
                print(f"Erreur lors de la lecture de la table {table_name}: {e}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données: {e}")

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "gw2_teambuilder.db")
    check_database(db_path)
