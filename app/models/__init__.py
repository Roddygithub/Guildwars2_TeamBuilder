"""Package contenant les modèles de données de l'application.

Ce package exporte à la fois les modèles Pydantic pour l'API et les modèles SQLAlchemy.
"""

# Import des modèles SQLAlchemy depuis le module racine
import sys
from pathlib import Path

# Ajout du répertoire parent au chemin de recherche Python pour permettre l'import du module racine
sys.path.append(str(Path(__file__).parent.parent))

# Import des modèles SQLAlchemy depuis le module racine
from app.models import Profession, Specialization, Skill

# Import des modèles Pydantic pour l'API
from .team import TeamRequest, TeamResponse, TeamComposition, TeamMember, Playstyle

__all__ = [
    # Modèles SQLAlchemy
    'Profession',
    'Specialization',
    'Skill',
    
    # Modèles Pydantic pour l'API
    'TeamRequest',
    'TeamResponse',
    'TeamComposition',
    'TeamMember',
    'Playstyle'
]
