"""Script pour vérifier et réparer la base de données SQLite."""
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

def check_database_integrity(db_path):
    """Vérifie l'intégrité de la base de données SQLite."""
    print(f"Vérification de l'intégrité de la base de données: {db_path}")
    
    if not os.path.exists(db_path):
        print("La base de données n'existe pas.")
        return False
    
    try:
        # Vérifier l'intégrité de la base de données
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Exécuter une commande PRAGMA pour vérifier l'intégrité
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        
        if result and result[0] == 'ok':
            print("La base de données est intègre.")
            return True
        else:
            print(f"Problème d'intégrité détecté: {result}")
            return False
            
    except sqlite3.Error as e:
        print(f"Erreur lors de la vérification de l'intégrité: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def repair_database(db_path):
    """Tente de réparer la base de données SQLite."""
    print(f"Tentative de réparation de la base de données: {db_path}")
    
    # Créer une sauvegarde de la base de données actuelle
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Sauvegarde créée: {backup_path}")
    except Exception as e:
        print(f"Échec de la création de la sauvegarde: {e}")
        return False
    
    try:
        # Essayer de réparer la base de données en la recréant
        conn_old = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
        conn_new = sqlite3.connect(db_path)
        
        # Exécuter la commande de sauvegarde
        conn_old.backup(conn_new)
        
        print("Base de données réparée avec succès.")
        return True
        
    except sqlite3.Error as e:
        print(f"Échec de la réparation: {e}")
        return False
    finally:
        if 'conn_old' in locals():
            conn_old.close()
        if 'conn_new' in locals():
            conn_new.close()

def create_new_database(db_path):
    """Crée une nouvelle base de données vide."""
    print(f"Création d'une nouvelle base de données: {db_path}")
    
    # Supprimer l'ancien fichier s'il existe
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"Échec de la suppression de l'ancienne base de données: {e}")
            return False
    
    try:
        # Créer une nouvelle base de données vide
        conn = sqlite3.connect(db_path)
        conn.close()
        print("Nouvelle base de données créée avec succès.")
        return True
    except Exception as e:
        print(f"Échec de la création de la nouvelle base de données: {e}")
        return False

def main():
    """Fonction principale."""
    db_path = "gw2_teambuilder.db"
    
    # Vérifier si la base de données existe
    if not os.path.exists(db_path):
        print(f"La base de données {db_path} n'existe pas.")
        if input("Voulez-vous créer une nouvelle base de données ? (o/n): ").lower() == 'o':
            if create_new_database(db_path):
                print("Veuvez exécuter le script d'initialisation pour créer les tables.")
        return
    
    # Vérifier l'intégrité
    if check_database_integrity(db_path):
        print("Aucune action nécessaire, la base de données semble en bon état.")
        return
    
    # Tenter de réparer
    if input("Voulez-vous tenter de réparer la base de données ? (o/n): ").lower() == 'o':
        if repair_database(db_path):
            print("La base de données a été réparée avec succès.")
        else:
            print("La réparation a échoué.")
            if input("Voulez-vous créer une nouvelle base de données ? (o/n): ").lower() == 'o':
                create_new_database(db_path)
    else:
        print("Aucune action effectuée.")

if __name__ == "__main__":
    main()
