"""API endpoints for team analysis from various sources."""
from __future__ import annotations

from typing import List, Union, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl, validator

from app.models.build import BuildData
from app.services.gw2skilleditor_importer import analyze_team, TeamAnalysisResult

router = APIRouter(prefix="/analyze", tags=["analyze"])


class BuildSource(BaseModel):
    """Source d'un build, soit une URL gw2skilleditor, soit un build manuel."""
    type: str = Field(..., description="Type de source: 'url' ou 'manual'")
    data: Union[HttpUrl, Dict[str, Any]] = Field(
        ...,
        description="Soit une URL gw2skilleditor, soit un objet de build manuel"
    )
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ['url', 'manual']:
            raise ValueError("Le type doit être 'url' ou 'manual'")
        return v


class AnalyzeRequest(BaseModel):
    """Modèle de requête pour l'analyse d'équipe."""
    builds: List[BuildSource] = Field(
        ...,
        min_items=5,
        max_items=5,
        description="Liste de 5 builds à analyser (URLs ou définitions manuelles)"
    )
    playstyle: str = Field(
        "zerg",
        description="Contexte de jeu pour l'analyse (zerg, havoc, roaming, gvg)",
        regex="^(zerg|havoc|roaming|gvg)$"
    )


class AnalyzeResponse(TeamAnalysisResult):
    """Response model for team analysis."""
    pass


@router.post(
    "/team",
    response_model=AnalyzeResponse,
    summary="Analyze a team composition",
    description="""
    Analyze a team composition based on build definitions.
    
    This endpoint evaluates the team's buff coverage, role distribution,
    and overall effectiveness for the specified playstyle.
    
    Builds can be provided as:
    - gw2skilleditor URLs
    - Manual build definitions
    """,
    responses={
        200: {"description": "Team analysis results"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_team_endpoint(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a team composition from build definitions."""
    try:
        # Préparer les builds pour l'analyse
        build_data = []
        
        for build_source in request.builds:
            if build_source.type == 'url':
                # C'est une URL gw2skilleditor
                build_data.append(str(build_source.data))
            else:
                # C'est une définition de build manuelle
                # Valider la structure avec le modèle BuildData
                build = BuildData(**build_source.data)
                build_data.append(build.dict())
        
        # Appeler le service d'analyse
        analysis = await analyze_team(build_data)
        
        # Ajouter le playstyle aux métadonnées
        analysis_dict = analysis.dict()
        analysis_dict['metadata'] = analysis_dict.get('metadata', {})
        analysis_dict['metadata']['playstyle'] = request.playstyle
        
        return AnalyzeResponse(**analysis_dict)
        
    except HTTPException:
        # Propager les erreurs HTTP existantes
        raise
    except Exception as e:
        # Gérer les erreurs inattendues
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing the team: {str(e)}"
        )


# Exemple de schéma de réponse pour la documentation
AnalyzeResponse.update_forward_refs()
AnalyzeResponse.__doc__ = """
Résultat de l'analyse d'une équipe.

Attributes:
    team_score: Score global de l'équipe (0.0 à 1.0)
    buff_coverage: Couverture des buffs (0.0 à 1.0)
    role_coverage: Couverture des rôles (0.0 à 1.0)
    strengths: Liste des points forts de l'équipe
    improvement_areas: Liste des points à améliorer
    detailed_breakdown: Détail du scoring par catégorie
"""
