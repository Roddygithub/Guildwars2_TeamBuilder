from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Configuration de la base de données
    DATABASE_URL: str = "sqlite:///./gw2_teambuilder.db"
    TEST_DATABASE_URL: str = "sqlite:///./test_teambuilder.db"
    
    # Configuration de l'application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Configuration CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Chargement des variables d'environnement
settings = Settings()

# Configuration spéciale pour les tests
if "pytest" in os.environ.get("PYTEST_CURRENT_TEST", ""):
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    settings.ENVIRONMENT = "testing"

# Configuration pour la production sur Netlify
if os.environ.get("NETLIFY") == "true":
    settings.ENVIRONMENT = "production"
    settings.DEBUG = False
    settings.FRONTEND_URL = os.environ.get("FRONTEND_URL", "")
    settings.ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",") if os.environ.get("ALLOWED_ORIGINS") else []
    
    # Utilisez la base de données PostgreSQL en production
    if "DATABASE_URL" in os.environ:
        # Convertit l'URL de PostgreSQL au format attendu par SQLAlchemy si nécessaire
        db_url = os.environ["DATABASE_URL"]
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        settings.DATABASE_URL = db_url
