"""Script pour vérifier et corriger les types de compétences invalides dans la base de données."""
import sys
from pathlib import Path
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.config import settings
from app.models.skill import Skill, SkillType

# URL de la base de données SQLite
DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "")

def check_skill_types():
    """Vérifie et affiche les types de compétences invalides dans la base de données."""
    # Créer une connexion SQLite brute pour l'inspection
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Récupérer les valeurs uniques du champ 'type' dans la table skills
        cursor.execute("SELECT DISTINCT type FROM skills")
        types = cursor.fetchall()
        
        print("Types de compétences trouvés dans la base de données:")
        for (skill_type,) in types:
            print(f"- {skill_type} (valide: {skill_type in [t.value for t in SkillType]})")
        
        # Compter les compétences avec des types invalides
        cursor.execute("""
            SELECT COUNT(*) 
            FROM skills 
            WHERE type NOT IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [t.value for t in SkillType])
        
        invalid_count = cursor.fetchone()[0]
        print(f"\nNombre total de compétences avec des types invalides: {invalid_count}")
        
        # Afficher un échantillon des compétences avec des types invalides
        if invalid_count > 0:
            print("\nExemple de compétences avec des types invalides:")
            cursor.execute("""
                SELECT id, name, type 
                FROM skills 
                WHERE type NOT IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                LIMIT 5
            """, [t.value for t in SkillType])
            
            for skill_id, name, skill_type in cursor.fetchall():
                print(f"- ID: {skill_id}, Nom: {name}, Type invalide: {skill_type}")
    
    finally:
        conn.close()

def fix_skill_types():
    """Tente de corriger les types de compétences invalides dans la base de données."""
    # Créer une connexion SQLite brute pour la mise à jour
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Récupérer les compétences avec des types invalides
        cursor.execute("""
            SELECT id, name, type 
            FROM skills 
            WHERE type NOT IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [t.value for t in SkillType])
        
        invalid_skills = cursor.fetchall()
        
        if not invalid_skills:
            print("Aucune compétence avec un type invalide trouvée.")
            return
        
        print(f"Tentative de correction de {len(invalid_skills)} compétences avec des types invalides...")
        
        # Dictionnaire pour mapper les types invalides vers des types valides
        type_mapping = {
            'Profession': 'Weapon',  # Supposition que 'Profession' devrait être 'Weapon'
            'Profession Skills': 'Weapon',
            'Healing': 'Heal',
            'Elite Skills': 'Elite',
            'Downed Skills': 'Downed'
        }
        
        updated_count = 0
        
        for skill_id, name, skill_type in invalid_skills:
            # Essayer de trouver un type valide dans le mapping
            new_type = type_mapping.get(skill_type)
            
            if new_type and new_type in [t.value for t in SkillType]:
                # Mettre à jour le type de la compétence
                cursor.execute(
                    "UPDATE skills SET type = ? WHERE id = ?",
                    (new_type, skill_id)
                )
                print(f"Corrigé: ID {skill_id} - '{skill_type}' -> '{new_type}'")
                updated_count += 1
            else:
                print(f"Avertissement: Aucun type valide trouvé pour '{skill_type}' (ID: {skill_id}, Nom: {name})")
        
        # Valider les changements
        conn.commit()
        print(f"\n{updated_count} compétences mises à jour avec succès.")
        
        # Vérifier s'il reste des types invalides
        cursor.execute("""
            SELECT COUNT(*) 
            FROM skills 
            WHERE type NOT IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [t.value for t in SkillType])
        
        remaining = cursor.fetchone()[0]
        print(f"\nNombre de compétences avec des types toujours invalides: {remaining}")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la mise à jour des types de compétences: {e}")
        raise
    finally:
        conn.close()

def main():
    """Fonction principale."""
    print("Vérification des types de compétences dans la base de données...\n")
    
    # Afficher les types de compétences actuels
    check_skill_types()
    
    # Demander à l'utilisateur s'il souhaite corriger les types invalides
    if input("\nVoulez-vous tenter de corriger les types invalides ? (o/n): ").lower() == 'o':
        fix_skill_types()
        
        # Afficher à nouveau les types après correction
        print("\nVérification après correction:")
        check_skill_types()

if __name__ == "__main__":
    main()
