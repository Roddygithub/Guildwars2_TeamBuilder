"""
Schémas Pydantic pour les réponses d'API liées aux builds.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PlayerBuildResponse(BaseModel):
    """Modèle de réponse pour un build de joueur.
    
    Ce modèle est utilisé pour sérialiser les objets PlayerBuild en réponse API.
    """
    profession_id: str = Field(..., description="Identifiant de la profession (ex: 'Guardian')")
    elite_spec: str = Field(default="", description="Spécialisation d'élite (ex: 'Firebrand')")
    buffs: List[str] = Field(default_factory=list, description="Liste des buffs fournis par le build")
    roles: List[str] = Field(default_factory=list, description="Rôles remplis par le build")
    playstyles: List[str] = Field(default_factory=list, description="Styles de jeu supportés")
    description: str = Field(default="", description="Description du rôle et du gameplay")
    weapons: List[str] = Field(default_factory=list, description="Armes recommandées pour le build")
    utilities: List[str] = Field(default_factory=list, description="Compétences utilitaires recommandées")
    source: str = Field(default="", description="Source du build (ex: URL ou 'manual')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées supplémentaires")

    class Config:
        json_schema_extra = {
            "example": {
                "profession_id": "Guardian",
                "elite_spec": "Firebrand",
                "buffs": ["quickness", "might"],
                "roles": ["support", "quickness"],
                "playstyles": ["zerg"],
                "description": "Heal/Quickness Firebrand",
                "weapons": ["Mace", "Axe", "Shield"],
                "utilities": ["Mantra of Potence", "Mantra of Solace"],
                "source": "https://example.com/builds/firebrand",
                "metadata": {"author": "GW2 Team Builder"}
            }
        }


def player_build_to_response(player_build) -> 'PlayerBuildResponse':
    """Convertit un objet PlayerBuild en PlayerBuildResponse.
    
    Args:
        player_build: Instance de PlayerBuild à convertir
        
    Returns:
        Une instance de PlayerBuildResponse
    """
    # Extraire les rôles de l'ensemble vers une liste
    roles = list(player_build.roles) if hasattr(player_build, 'roles') else []
    
    # Extraire les buffs de l'ensemble vers une liste
    buffs = list(player_build.buffs) if hasattr(player_build, 'buffs') else []
    
    # Extraire les métadonnées si elles existent
    metadata = {}
    if hasattr(player_build, 'metadata') and player_build.metadata:
        metadata = player_build.metadata
    
    # Créer et retourner la réponse
    return PlayerBuildResponse(
        profession_id=getattr(player_build, 'profession_id', ''),
        elite_spec=getattr(player_build, 'elite_spec', ''),
        buffs=buffs,
        roles=roles,
        playstyles=list(getattr(player_build, 'playstyles', [])),
        description=getattr(player_build, 'description', ''),
        weapons=list(getattr(player_build, 'weapons', [])),
        utilities=list(getattr(player_build, 'utilities', [])),
        source=getattr(player_build, 'source', ''),
        metadata=metadata
    )
