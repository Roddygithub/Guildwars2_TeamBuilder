"""Configuration de la base de données SQLAlchemy pour GW2 Team Builder.

Ce module configure la connexion à la base de données avec un pool de connexions,
des timeouts et d'autres optimisations de performance.
"""
import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from .config import settings

# Configuration du pool de connexions
pool_config = {
    "pool_size": 5,  # Taille du pool de connexions
    "max_overflow": 10,  # Connexions supplémentaires autorisées
    "pool_timeout": 30,  # Délai d'attente pour obtenir une connexion (secondes)
    "pool_recycle": 3600,  # Recycle les connexions après 1 heure
    "pool_pre_ping": True,  # Vérifie que la connexion est toujours active
}

# Configuration spécifique à SQLite
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False
    # Configuration spécifique pour SQLite en production
    if settings.ENVIRONMENT == "production":
        connect_args["timeout"] = 30
        # Journalisation en mode WAL pour de meilleures performances
        connect_args["isolation_level"] = "IMMEDIATE"

# Création du moteur avec un pool de connexions et des optimisations
engine = create_engine(
    settings.DATABASE_URL,
    **pool_config,
    connect_args=connect_args if connect_args else {},
    echo=settings.DEBUG,  # Active l'écho des requêtes SQL en mode debug
    future=True  # Active les fonctionnalités futures de SQLAlchemy 2.0
)

# Configuration de la session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=True,  # Les objets sont expirés après commit
)

# Base pour les modèles
Base = declarative_base()


def init_db() -> None:
    """Initialise la base de données et crée les tables si elles n'existent pas.
    
    Cette fonction doit être appelée au démarrage de l'application pour s'assurer
    que le schéma de la base de données est à jour.
    """
    import importlib
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Initialisation de la base de données...")
    
    try:
        # Import dynamique des modèles pour les enregistrer dans les métadonnées
        importlib.import_module("app.models")
        
        # Création des tables
        Base.metadata.create_all(bind=engine)
        logger.info("Base de données initialisée avec succès")
        
    except Exception as e:
        logger.exception("Erreur lors de l'initialisation de la base de données")
        raise


def get_db() -> Generator[Session, None, None]:
    """Fournit une session de base de données pour les dépendances FastAPI.
    
    Utilisation:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Configuration spécifique pour SQLite pour améliorer les performances
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Active les clés étrangères et d'autres optimisations SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")  # Active les clés étrangères
        cursor.execute("PRAGMA journal_mode=WAL")  # Améliore les performances en écriture
        cursor.execute("PRAGMA synchronous=NORMAL")  # Meilleur compromis perf/fiabilité
        cursor.execute("PRAGMA cache_size=-2000")  # Taille du cache en nombre de pages (env. 2MB)
        cursor.close()
