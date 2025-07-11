"""Script pour sauvegarder et réinitialiser la base de données.

Ce script effectue les opérations suivantes :
1. Crée une sauvegarde de la base de données existante
2. Supprime la base de données existante
3. Recrée le schéma de la base de données
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

def backup_database():
    """Crée une sauvegarde de la base de données existante."""
    db_path = Path("gw2_teambuilder.db")
    if not db_path.exists():
        print("Aucune base de données existante à sauvegarder.")
        return
    
    # Créer le répertoire de sauvegarde s'il n'existe pas
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Créer un nom de fichier de sauvegarde avec un horodatage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"gw2_teambuilder_backup_{timestamp}.db"
    
    try:
        # Copier le fichier de base de données
        shutil.copy2(db_path, backup_path)
        print(f"Sauvegarde créée : {backup_path}")
    except Exception as e:
        print(f"Erreur lors de la création de la sauvegarde : {e}")
        raise

def delete_database():
    """Supprime la base de données existante."""
    db_path = Path("gw2_teambuilder.db")
    if db_path.exists():
        try:
            db_path.unlink()
            print("Ancienne base de données supprimée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la suppression de la base de données : {e}")
            raise
    else:
        print("Aucune base de données existante à supprimer.")

def recreate_schema():
    """Recrée le schéma de la base de données."""
    from app.database import engine, Base, init_db
    
    print("Création du schéma de la base de données...")
    try:
        # Importer tous les modèles pour s'assurer qu'ils sont enregistrés
        from app import models  # noqa: F401
        
        # Créer toutes les tables
        Base.metadata.create_all(bind=engine)
        print("Schéma de la base de données recréé avec succès.")
    except Exception as e:
        print(f"Erreur lors de la création du schéma : {e}")
        raise

def main():
    """Fonction principale."""
    print("=== Réinitialisation de la base de données ===")
    print("Cette opération va :")
    print("1. Créer une sauvegarde de la base de données existante")
    print("2. Supprimer la base de données existante")
    print("3. Recréer le schéma de la base de données")
    print("")
    
    confirmation = input("Êtes-vous sûr de vouloir continuer ? (o/n) ").strip().lower()
    if confirmation != 'o':
        print("Opération annulée.")
        return
    
    try:
        # 1. Sauvegarder la base de données existante
        print("\n=== Étape 1/3 : Sauvegarde de la base de données existante ===")
        backup_database()
        
        # 2. Supprimer l'ancienne base de données
        print("\n=== Étape 2/3 : Suppression de l'ancienne base de données ===")
        delete_database()
        
        # 3. Recréer le schéma
        print("\n=== Étape 3/3 : Création du nouveau schéma ===")
        recreate_schema()
        
        print("\n=== Opération terminée avec succès ===")
        print("La base de données a été réinitialisée avec le nouveau schéma.")
        print("Une sauvegarde de l'ancienne base de données a été créée dans le dossier 'backup'.")
        
    except Exception as e:
        print(f"\n=== ERREUR ===\nUne erreur est survenue : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
