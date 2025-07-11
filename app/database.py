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

# Configuration spécifique à SQLite
connect_args = {}
engine_config = {
    "url": settings.DATABASE_URL,
    "echo": settings.DEBUG,  # Active l'écho des requêtes SQL en mode debug
    "future": True,  # Active les fonctionnalités futures de SQLAlchemy 2.0
}

if "sqlite" in settings.DATABASE_URL:
    # Configuration spécifique à SQLite
    connect_args["check_same_thread"] = False
    
    # Configuration spécifique pour SQLite en production
    if settings.ENVIRONMENT == "production":
        connect_args["timeout"] = 30
        connect_args["isolation_level"] = "IMMEDIATE"
        # Journalisation en mode WAL pour de meilleures performances
        connect_args.update({
            "timeout": 30,
            "isolation_level": "IMMEDIATE"
        })
    
    # SQLite n'utilise pas de pool de connexions
    engine_config["connect_args"] = connect_args
else:
    # Configuration du pool de connexions pour les autres bases de données (PostgreSQL, etc.)
    engine_config.update({
        "pool_size": 5,  # Taille du pool de connexions
        "max_overflow": 10,  # Connexions supplémentaires autorisées
        "pool_timeout": 30,  # Délai d'attente pour obtenir une connexion (secondes)
        "pool_recycle": 3600,  # Recycle les connexions après 1 heure
        "pool_pre_ping": True,  # Vérifie que la connexion est toujours active
        "connect_args": connect_args
    })

# Création du moteur avec la configuration appropriée
engine = create_engine(**engine_config)

# Configuration de la session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=True,  # Les objets sont expirés après commit
)

# Importer Base depuis le module de base des modèles
from app.models.base import Base


def init_db() -> None:
    """Initialise la base de données et crée les tables si elles n'existent pas.
    
    Cette fonction doit être appelée au démarrage de l'application pour s'assurer
    que le schéma de la base de données est à jour.
    
    Note:
        Cette fonction est synchrone car SQLAlchemy nécessite des opérations synchrones
        pour la création des tables. Pour une utilisation dans un contexte asynchrone,
        utilisez init_async_db() à la place.
    """
    import importlib
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Initialisation synchrone de la base de données...")
    
    try:
        # Import dynamique des modèles pour les enregistrer dans les métadonnées
        importlib.import_module("app.models")
        
        # Créer toutes les tables
        Base.metadata.create_all(bind=engine)
        logger.info("Base de données initialisée avec succès (mode synchrone)")
        
    except Exception as e:
        logger.exception("Erreur lors de l'initialisation de la base de données")
        raise


async def init_async_db() -> None:
    """Version asynchrone de init_db pour les contextes asynchrones.
    
    Cette fonction est une enveloppe autour de init_db() qui peut être attendue.
    Elle est utile pour maintenir la compatibilité avec le code asynchrone.
    """
    import asyncio
    
    # Exécuter l'initialisation synchrone dans un thread séparé
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, init_db)


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
