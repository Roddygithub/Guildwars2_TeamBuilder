"""Modèles pour la représentation des builds de personnages."""
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


class ProfessionType(str, Enum):
    """Types de professions disponibles dans Guild Wars 2."""
    ELEMENTALIST = "elementalist"
    ENGINEER = "engineer"
    GUARDIAN = "guardian"
    MESMER = "mesmer"
    NECROMANCER = "necromancer"
    RANGER = "ranger"
    REVENANT = "revenant"
    THIEF = "thief"
    WARRIOR = "warrior"


class RoleType(str, Enum):
    """Types de rôles possibles pour un build."""
    DPS = "dps"
    HEAL = "heal"
    QUICKNESS = "quickness"
    ALACRITY = "alacrity"
    SUPPORT = "support"
    TANK = "tank"


class TraitLine(BaseModel):
    """Ligne de traits pour une spécialisation."""
    id: int = Field(..., description="ID de la spécialisation")
    name: str = Field(..., description="Nom de la spécialisation")
    traits: List[int] = Field(..., description="IDs des traits sélectionnés")


class EquipmentItem(BaseModel):
    """Équipement d'un personnage."""
    id: int = Field(..., description="ID de l'objet")
    name: str = Field(..., description="Nom de l'objet")
    infusions: Optional[List[int]] = Field(default_factory=list, description="IDs des infusions")
    upgrades: Optional[List[int]] = Field(default_factory=list, description="IDs des améliorations")


class BuildData(BaseModel):
    """Représente un build de personnage complet."""
    # Informations de base
    name: str = Field(..., description="Nom du build")
    profession: ProfessionType = Field(..., description="Profession du personnage")
    role: RoleType = Field(..., description="Rôle principal du build")
    
    # Spécialisations et compétences
    specializations: List[TraitLine] = Field(..., min_items=3, max_items=3, 
                                          description="Les trois spécialisations du build")
    skills: List[int] = Field(..., min_items=5, max_items=5, 
                            description="IDs des compétences équipées")
    
    # Équipement
    equipment: Dict[str, EquipmentItem] = Field(..., description="Équipement du personnage")
    
    # Métadonnées
    description: Optional[str] = Field(None, description="Description du build")
    source: Optional[HttpUrl] = Field(None, description="URL de la source du build")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Heal Firebrand",
                "profession": "guardian",
                "role": "heal",
                "specializations": [
                    {"id": 46, "name": "Zeal", "traits": [909, 914, 909]},
                    {"id": 27, "name": "Honor", "traits": [915, 908, 894]},
                    {"id": 62, "name": "Firebrand", "traits": [904, 0, 0]}
                ],
                "skills": [62561, 9153, 0, 0, 0],
                "equipment": {
                    "Helm": {"id": 48033, "name": "Harrier's Wreath of the Diviner", "infusions": []},
                    "Shoulders": {"id": 48034, "name": "Harrier's Pauldrons of the Diviner", "infusions": []},
                    # ... autres pièces d'équipement
                },
                "description": "Heal Firebrand avec Quickness",
                "source": "https://lucky-noobs.com/builds/view/12345"
            }
        }
