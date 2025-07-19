from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class Playstyle(str, Enum):
    ZERG = "zerg"
    HAVOC = "havoc"
    ROAMING = "roaming"
    GVG = "gvg"

class TeamMember(BaseModel):
    role: str
    profession: str
    build_url: Optional[str] = None
    build_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Détails complets du build généré (armes, compétences, équipement, etc.)"
    )

class TeamComposition(BaseModel):
    members: List[TeamMember]
    score: float
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Détail du score par catégorie (buffs, rôles, pénalités)"
    )
    
class TeamRequest(BaseModel):
    team_size: int = Field(5, ge=1, le=50, description="Taille de l'équipe à générer")
    playstyle: Playstyle = Field(..., description="Style de jeu cible")
    allowed_professions: Optional[List[str]] = Field(
        None,
        description="Liste des professions autorisées (toutes si non spécifié)"
    )
    required_roles: Optional[Dict[str, int]] = Field(
        None,
        description="Rôles requis et leur nombre minimum (ex: {'heal': 1, 'dps': 3})"
    )
    
class TeamResponse(BaseModel):
    team: TeamComposition
    request: TeamRequest
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées sur la génération de l'équipe")
