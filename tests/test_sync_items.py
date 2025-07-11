"""Tests pour la synchronisation des objets (armes, armures, bijoux) depuis l'API GW2."""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.api.client import GW2APIClient
from app.services.gw2_data_service import GW2DataService

# Configuration du logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"test_sync_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration de la base de données
TEST_DB_URL = "sqlite:///./test_gw2_items.db"
engine = create_engine(TEST_DB_URL, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Créer les tables de la base de données
def init_db():
    """Initialise la base de données de test avec toutes les tables nécessaires."""
    logger.info("Création des tables de la base de données...")
    
    # Importer tous les modèles pour s'assurer que toutes les tables sont créées
    from app.models import (
        Item, ItemStats, ItemStat, 
        Weapon, Armor, Trinket, UpgradeComponent,
        Profession, Specialization, Trait, Skill
    )
    
    # Supprimer toutes les tables existantes
    Base.metadata.drop_all(bind=engine)
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Tables créées avec succès")

async def test_sync_items():
    """Teste la synchronisation des objets depuis l'API GW2."""
    logger.info("Début du test de synchronisation des objets")
    
    db = None
    try:
        # Initialiser la session de base de données
        logger.info("Initialisation de la session de base de données...")
        db = TestingSessionLocal()
        
        # Initialiser le client API et le service de données
        logger.info("Initialisation du client API et du service de données...")
        api_client = GW2APIClient()
        data_service = GW2DataService(db, api_client)
        
        # Synchroniser les statistiques d'objets d'abord (nécessaire pour les objets)
        logger.info("Début de la synchronisation des statistiques d'objets...")
        try:
            stats_result = await data_service.sync_itemstats()
            logger.info(f"Résultat de la synchronisation des statistiques: {stats_result}")
        except Exception as e:
            logger.error(f"Échec de la synchronisation des statistiques: {e}", exc_info=True)
            raise
        
        # Synchroniser les objets
        logger.info("Début de la synchronisation des objets...")
        try:
            items_result = await data_service.sync_items()
            logger.info(f"Résultat de la synchronisation des objets: {items_result}")
        except Exception as e:
            logger.error(f"Échec de la synchronisation des objets: {e}", exc_info=True)
            raise
        
        # Vérifier le nombre d'objets synchronisés
        logger.info("Vérification des objets synchronisés...")
        try:
            total_items = db.query(Item).count()
            weapons = db.query(Weapon).count()
            armors = db.query(Armor).count()
            trinkets = db.query(Trinket).count()
            
            logger.info(f"Total d'objets synchronisés: {total_items}")
            logger.info(f"  - Armes: {weapons}")
            logger.info(f"  - Armures: {armors}")
            logger.info(f"  - Bijoux: {trinkets}")
        except Exception as e:
            logger.error(f"Erreur lors du comptage des objets: {e}", exc_info=True)
            raise
        
        # Vérifier quelques exemples d'objets
        if total_items > 0:
            # Exemple d'arme
            weapon = db.query(Weapon).first()
            if weapon:
                logger.info(f"Exemple d'arme: {weapon.item.name} (ID: {weapon.id}, Type: {weapon.type})")
            
            # Exemple d'armure
            armor = db.query(Armor).first()
            if armor:
                logger.info(f"Exemple d'armure: {armor.item.name} (ID: {armor.id}, Type: {armor.type}, Poids: {armor.weight_class})")
            
            # Exemple de bijou
            trinket = db.query(Trinket).first()
            if trinket:
                logger.info(f"Exemple de bijou: {trinket.item.name} (ID: {trinket.id}, Type: {trinket.type})")
        
        return {
            "status": "success",
            "total_items": total_items,
            "weapons": weapons,
            "armors": armors,
            "trinkets": trinkets,
            "details": items_result
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation des objets: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # Initialiser la base de données
        logger.info("Initialisation de la base de données...")
        init_db()
        
        # Exécuter le test de synchronisation
        logger.info("Lancement du test de synchronisation des objets...")
        try:
            result = asyncio.run(test_sync_items())
            logger.info(f"Test terminé avec succès. Résultat: {result}")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du test: {e}", exc_info=True)
            raise
            
        logger.info(f"Consultez le fichier de log complet pour plus de détails: {log_file.absolute()}")
        print(f"\nTest terminé. Consultez les logs dans: {log_file.absolute()}")
    except Exception as e:
        logger.critical(f"ERREUR CRITIQUE: {e}", exc_info=True)
        print(f"\nERREUR: {e}\nConsultez les logs pour plus de détails: {log_file.absolute()}")
        sys.exit(1)
