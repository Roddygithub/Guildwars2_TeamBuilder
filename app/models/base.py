"""Module de base pour les modèles SQLAlchemy."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
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
Base = declarative_base()

def get_db():
    """Générateur de sessions de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
