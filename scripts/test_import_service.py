"""Script de test pour l'importation des données depuis l'API GW2."""

import os
import sys
import logging
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import SessionLocal, init_db
from app.services.gw2_import_service import import_all_data
from app.logging_config import get_logger

def setup_logging():
    """Configure le logging pour le script de test."""
    # Configuration du répertoire de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuration du logger avec get_logger
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)
    
    # Ajout d'un gestionnaire de fichier si nécessaire
    log_file = log_dir / "test_import.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    return logger

def test_import_all():
    """Teste l'importation de toutes les données."""
    logger = setup_logging()
    
    # Initialiser la base de données
    logger.info("Initialisation de la base de données...")
    init_db()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        logger.info("Début du test d'importation complète")
        
        # Importer toutes les données
        results = import_all_data(db, language="fr")
        
        # Afficher les résultats
        logger.info("Résultats de l'importation:")
        for endpoint, stats in results.items():
            if isinstance(stats, dict):
                logger.info(f"{endpoint}: {stats}")
            else:
                logger.info(f"{endpoint}: Erreur - {stats}")
        
        logger.info("Test d'importation terminé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du test d'importation: {e}", exc_info=True)
        return False
    finally:
        db.close()

def test_import_specific_service():
    """Teste l'importation d'un service spécifique."""
    logger = setup_logging()
    
    # Initialiser la base de données
    logger.info("Initialisation de la base de données...")
    init_db()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        from app.services.gw2_import_service import ProfessionImportService
        
        logger.info("Début du test d'importation des professions")
        
        # Créer le service d'importation des professions
        service = ProfessionImportService(language="fr")
        
        # Importer les professions
        stats = service.import_all(db)
        
        # Afficher les résultats
        logger.info(f"Résultats de l'importation des professions: {stats}")
        
        # Afficher les professions importées
        from app.models import Profession
        professions = db.query(Profession).all()
        logger.info(f"{len(professions)} professions importées:")
        for prof in professions:
            logger.info(f"- {prof.name} (ID: {prof.id})")
        
        logger.info("Test d'importation des professions terminé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du test d'importation des professions: {e}", exc_info=True)
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Configurer le logging
    logger = setup_logging()
    
    try:
        print("1. Tester l'importation complète")
        print("2. Tester l'importation des professions uniquement")
        
        choice = input("Choisissez une option (1 ou 2): ")
        
        if choice == "1":
            logger.info("Démarrage du test d'importation complète")
            success = test_import_all()
        elif choice == "2":
            logger.info("Démarrage du test d'importation des professions")
            success = test_import_specific_service()
        else:
            logger.error("Option invalide")
            print("\nErreur: Option invalide. Veuillez choisir 1 ou 2.")
            sys.exit(1)
        
        if success:
            msg = "Test réussi! Consultez le fichier logs/test_import.log pour plus de détails."
            logger.info(msg)
            print(f"\n{msg}")
        else:
            msg = "Le test a échoué. Consultez le fichier logs/test_import.log pour plus de détails."
            logger.error(msg)
            print(f"\n{msg}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception("Erreur inattendue lors de l'exécution du test")
        print(f"\nErreur inattendue: {e}\nConsultez le fichier logs/test_import.log pour plus de détails.")
        sys.exit(1)
