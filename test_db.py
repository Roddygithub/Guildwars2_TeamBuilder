"""Script de test pour la base de données."""
import sys
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.database import SessionLocal, init_db
from app.models.skill import Skill

def main():
    """Fonction principale pour tester la connexion à la base de données."""
    print("Initialisation de la base de données...")
    init_db()
    
    print("Création d'une session de base de données...")
    db = SessionLocal()
    
    try:
        print("Vérification de la connexion à la base de données...")
        # Exécuter une requête simple pour vérifier la connexion
        count = db.query(Skill).count()
        print(f"Nombre de compétences dans la base de données: {count}")
        
        # Afficher les 5 premières compétences (si elles existent)
        if count > 0:
            print("\n5 premières compétences:")
            for skill in db.query(Skill).limit(5).all():
                print(f"- {skill.name} (ID: {skill.id})")
        else:
            print("Aucune compétence trouvée dans la base de données.")
            print("Veuillez exécuter les migrations et charger les données de test.")
            
    except Exception as e:
        print(f"Erreur lors de l'accès à la base de données: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\nFermeture de la connexion à la base de données.")

if __name__ == "__main__":
    main()
