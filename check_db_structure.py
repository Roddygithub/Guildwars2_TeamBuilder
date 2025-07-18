"""Script pour vérifier la structure complète de la base de données."""
import sqlite3
from pathlib import Path
import json

def check_database_structure(db_path):
    """Affiche la structure complète de la base de données."""
    if not Path(db_path).exists():
        print(f"Erreur: Le fichier de base de données {db_path} n'existe pas.")
        return False
    
    try:
        # Se connecter à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupérer la liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Structure de la base de données {db_path}:")
        print("=" * 80)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * 40)
            
            # Afficher les colonnes de la table
            try:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print("Colonnes:")
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, is_pk = col
                    print(f"  - {col_name} ({col_type}){' PRIMARY KEY' if is_pk else ''} {'NOT NULL' if not_null else ''} {f'DEFAULT {default_val}' if default_val is not None else ''}")
                
                # Afficher les index
                cursor.execute(f"PRAGMA index_list({table_name});")
                indexes = cursor.fetchall()
                if indexes:
                    print("\nIndexes:")
                    for idx in indexes:
                        idx_id, idx_name, is_unique, origin, partial = idx
                        cursor.execute(f"PRAGMA index_info({idx_name});")
                        idx_columns = cursor.fetchall()
                        col_names = [col[2] for col in idx_columns]  # Le nom de la colonne est à l'index 2
                        print(f"  - {idx_name}: {'UNIQUE ' if is_unique else ''}{', '.join(col_names)}")
                
                # Compter le nombre d'entrées
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"\nNombre d'entrées: {count}")
                
                # Afficher un échantillon des données (max 3 lignes)
                if count > 0:
                    print("\nExemple de données:")
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                    sample_data = cursor.fetchall()
                    for i, row in enumerate(sample_data, 1):
                        print(f"  {i}. {row}")
                
            except sqlite3.Error as e:
                print(f"  Erreur lors de la lecture de la table {table_name}: {e}")
            
            print("\n" + "-" * 80)
        
        # Vérifier si la table 'professions' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professions';")
        professions_table = cursor.fetchone()
        
        if not professions_table:
            print("\nATTENTION: La table 'professions' n'existe pas dans la base de données.")
            print("Cela peut causer des problèmes avec l'application.")
            
            # Vérifier si la table existe avec un nom différent (ex: majuscules/minuscules)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND LOWER(name) = 'professions';")
            similar_tables = cursor.fetchall()
            
            if similar_tables:
                print("\nTables similaires trouvées (peut-être une différence de casse):")
                for table in similar_tables:
                    print(f"  - {table[0]}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_path = "gw2_teambuilder.db"
    check_database_structure(db_path)
