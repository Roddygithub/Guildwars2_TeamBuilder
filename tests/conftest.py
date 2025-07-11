"""Configuration partagée pour les tests."""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Configuration des variables d'environnement pour les tests
os.environ["ENV"] = "test"
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Configuration du logger pour les tests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import des dépendances après configuration de l'environnement
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import des dépendances de test
import pytest

# Import des modèles pour créer les tables
from app.models.base import Base

# Import de tous les modèles pour s'assurer que toutes les tables sont créées
from app.models import (
    Profession, Specialization, Trait, Weapon, Skill, Armor, Trinket,
    UpgradeComponent, Rune, Sigil, Relic, Infusion, ItemStats, ItemStat, Item,
    ProfessionWeaponType, ProfessionWeaponSkill, ProfessionArmorType, ProfessionTrinketType
)

# Création du moteur de base de données pour les tests
engine = create_engine(
    os.getenv("DATABASE_URL"),
    connect_args={"check_same_thread": False},
    poolclass=None
)

# Création des tables
Base.metadata.create_all(bind=engine)

# Session de test
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Fournit une session de base de données pour les tests."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
async def gw2_service(db):
    """Fournit une instance de GW2DataService pour les tests."""
    from app.services.gw2_data_service import GW2DataService
    
    # Création du service avec un mock de l'API
    service = GW2DataService(db_session=db)
    
    # Initialisation du service
    await service.initialize()
    
    yield service
    
    # Nettoyage
    await service.close()
