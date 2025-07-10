"""Package contenant les modèles de données de l'application.

Ce package exporte à la fois les modèles Pydantic pour l'API et les modèles SQLAlchemy.
"""

# Import des modèles SQLAlchemy depuis leurs fichiers respectifs
from .profession import Profession
from .specialization import Specialization
from .skill import Skill

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
