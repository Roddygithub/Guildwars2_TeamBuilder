"""Script pour tester la synchronisation des statistiques d'objets."""

import asyncio
import logging
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.services.gw2_data_service import GW2DataService
from app.database import SessionLocal, Base, engine

# Importer tous les modèles pour s'assurer qu'ils sont enregistrés auprès de Base.metadata
# avant d'appeler create_all()
from app.models import (
    Item, ItemStats, ItemStat,  # Modèles de base pour les statistiques d'objets
    Weapon, Armor, Trinket, UpgradeComponent,  # Modèles d'objets
    Profession, ProfessionWeaponType, ProfessionArmorType, ProfessionTrinketType  # Modèles de profession
)

# Créer un dossier de logs s'il n'existe pas
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# Configuration du logging
log_file = log_dir / f'test_sync_itemstats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.DEBUG,  # Niveau de log global
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Sortie console
        logging.FileHandler(log_file, encoding='utf-8')  # Fichier de log
    ]
)

# Configuration spécifique pour SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.WARNING)  # Réduire le bruit de urllib3

logger = logging.getLogger(__name__)

# Afficher le fichier de log pour faciliter le débogage
log_path = str(log_file.absolute())
logger.info(f"Les logs complets sont enregistrés dans : {log_path}")
print(f"\n=== FICHIER DE LOG : {log_path} ===\n")

# Fonction pour afficher la fin du fichier de log
def print_tail_log():
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Afficher les 50 dernières lignes ou moins si le fichier est plus petit
            print("\n=== DERNIÈRES LIGNES DU FICHIER DE LOG ===")
            for line in lines[-50:]:
                print(line, end='')
            print("\n=== FIN DU FICHIER DE LOG ===\n")
    except Exception as e:
        print(f"Impossible de lire le fichier de log: {e}")

# Enregistrer la fonction pour l'appeler en cas d'erreur
import atexit
atexit.register(print_tail_log)

def init_db():
    """Initialise la base de données de manière synchrone."""
    # Créer toutes les tables de manière synchrone
    Base.metadata.create_all(bind=engine)
    return SessionLocal()

async def main():
    """Fonction principale pour tester la synchronisation des statistiques d'objets."""
    logger.info("Initialisation de la base de données...")
    db = init_db()
    
    service = None
    try:
        # Initialiser le service
        logger.info("Initialisation du service...")
        service = GW2DataService()
        
        # Activer le mode debug pour le client API
        service._api.debug = True
        
        # Démarrer la synchronisation
        logger.info("Démarrage de la synchronisation des statistiques d'objets...")
        
        # Récupérer d'abord les IDs des statistiques d'objets
        itemstat_ids = await service._api.get('/v2/itemstats')
        logger.info(f"Nombre total de statistiques d'objets à synchroniser: {len(itemstat_ids) if itemstat_ids else 0}")
        
        # Exécuter la synchronisation complète
        result = await service.sync_itemstats()
        
        # Si des erreurs se sont produites, essayer de les identifier
        if result.get('errors', 0) > 0:
            logger.warning(f"{result['errors']} erreurs détectées lors de la synchronisation")
            
            # Essayer d'identifier les IDs problématiques
            existing_stats = {stat.id for stat in db.query(ItemStats).all()}
            missing_ids = [iid for iid in itemstat_ids if iid not in existing_stats]
            
            if missing_ids:
                logger.warning(f"IDs des statistiques manquantes: {missing_ids}")
                
                # Essayer de récupérer les détails des statistiques manquantes une par une
                for stat_id in missing_ids:
                    try:
                        logger.info(f"\nTentative de récupération de la statistique ID: {stat_id}")
                        stat_data = await service._api.get(f"/v2/itemstats/{stat_id}")
                        logger.info(f"Données brutes pour l'ID {stat_id}: {stat_data}")
                        
                        # Essayer de traiter manuellement cette statistique
                        try:
                            stat = await service._process_itemstat_data(stat_data)
                            logger.info(f"Traitement réussi pour l'ID {stat_id}")
                        except Exception as proc_err:
                            logger.error(f"Échec du traitement pour l'ID {stat_id}: {str(proc_err)}")
                            logger.debug(f"Traceback: {traceback.format_exc()}")
                            
                    except Exception as api_err:
                        logger.error(f"Erreur API pour l'ID {stat_id}: {str(api_err)}")
        
        logger.info(f"Résultat final de la synchronisation: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors de la synchronisation: {str(e)}\n"
        error_msg += f"Type d'erreur: {type(e).__name__}\n"
        error_msg += f"Traceback complète:\n{traceback.format_exc()}"
        
        logger.error(error_msg)
        print("\n=== ERREUR DÉTECTÉE ===")
        print(error_msg)
        print("======================\n")
        
        # Afficher les informations sur les erreurs individuelles si disponibles
        if hasattr(e, 'errors') and isinstance(e.errors, list):
            print("=== ERREURS INDIVIDUELLES ===")
            for i, err in enumerate(e.errors[:10], 1):  # Augmenté à 10 erreurs
                print(f"\nErreur {i}:")
                print(f"  Type: {type(err).__name__}")
                print(f"  Message: {str(err)}")
                if hasattr(err, '__traceback__'):
                    print(f"  Traceback: {traceback.format_tb(err.__traceback__)}")
                
                # Afficher plus de détails pour les erreurs spécifiques
                if hasattr(err, 'args') and err.args:
                    print(f"  Arguments: {err.args}")
                
                # Si c'est une erreur de validation, afficher les détails
                if hasattr(err, 'errors') and isinstance(err.errors, dict):
                    print("  Erreurs de validation:")
                    for field, field_errors in err.errors.items():
                        print(f"    - {field}: {field_errors}")
            
            if len(e.errors) > 10:
                print(f"\n... et {len(e.errors) - 10} autres erreurs")
            print("\n" + "="*60 + "\n")
        
        return {"status": "error", "message": str(e), "error_type": type(e).__name__}
    finally:
        if db:
            db.close()
        if service and hasattr(service, 'close'):
            await service.close()

def print_log_file():
    """Affiche les 50 dernières lignes du fichier de log dans la console."""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("\n" + "="*80)
            print(f"50 DERNIÈRES LIGNES DU FICHIER DE LOG: {log_path}")
            print("="*80)
            # Afficher les 50 dernières lignes ou moins si le fichier est plus petit
            for line in lines[-50:]:
                print(line, end='')
            print("\n" + "="*80 + "\n")
    except Exception as e:
        print(f"\nImpossible de lire le fichier de log: {e}\n")

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
