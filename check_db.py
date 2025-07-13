"""Script pour vérifier l'état de la base de données."""
import os
import sqlite3
from pathlib import Path

def check_database():
    """Vérifie l'état de la base de données."""
    # Chemin vers la base de données
    db_path = Path("gw2_teambuilder.db")
    
    # Vérifier si le fichier existe
    if not db_path.exists():
        print(f"La base de données {db_path} n'existe pas.")
        return
    
    print(f"Taille de la base de données: {db_path.stat().st_size} octets")
    
    # Se connecter à la base de données
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Récupérer les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("Aucune table trouvée dans la base de données.")
            return
        
        print("\nTables dans la base de données:")
        for (table,) in tables:
            print(f"- {table}")
            
            # Afficher la structure de la table
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"  Colonnes: {', '.join(col[1] for col in columns)}")
            
            # Compter les entrées
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  Nombre d'entrées: {count}")
            
            # Afficher un échantillon des données pour les petites tables
            if count > 0 and count <= 10:
                cursor.execute(f"SELECT * FROM {table} LIMIT 5;")
                print("  Exemple de données:")
                for row in cursor.fetchall():
                    print(f"    {row}")
        
        # Vérifier les types de compétences si la table existe
        if any('skills' in table for table, in tables):
            print("\nVérification des types de compétences:")
            cursor.execute("SELECT DISTINCT type FROM skills;")
            skill_types = cursor.fetchall()
            print(f"Types de compétences uniques trouvés: {len(skill_types)}")
            for (skill_type,) in skill_types[:10]:  # Afficher les 10 premiers types
                print(f"- {skill_type}")
        
    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database()
