"""Module de base pour les modèles SQLAlchemy."""

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, DateTime, func
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Créer le moteur SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gw2_team_builder.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

# Créer une session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour tous les modèles
class BaseModel:
    """Classe de base pour tous les modèles avec des champs communs."""
    
    # Ces champs seront ajoutés à toutes les classes qui héritent de Base
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    @declared_attr
    def __tablename__(cls):
        """Génère automatiquement le nom de la table en snake_case."""
        return cls.__name__.lower()

# Créer la classe de base avec SQLAlchemy
Base = declarative_base(cls=BaseModel)

def get_db():
    """Générateur de sessions de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
