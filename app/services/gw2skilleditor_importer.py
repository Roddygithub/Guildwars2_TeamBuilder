"""
Service pour importer et analyser des builds d'équipe à partir de différents formats.
"""
from typing import List, Dict, Any, Optional, Union
import re
import httpx
from pydantic import BaseModel, HttpUrl, ValidationError
from fastapi import HTTPException

from app.models.team import TeamMember, TeamComposition, Playstyle
from app.models.build import BuildData
from app.scoring.engine import score_team, PlayerBuild
from app.services.build_importer import BuildImporter

class BuildAnalysisResult(BaseModel):
    """Modèle représentant l'analyse d'un build."""
    build: PlayerBuild
    source: str = "manual"  # 'manual' ou 'gw2skilleditor'

class TeamAnalysisResult(BaseModel):
    """Résultat de l'analyse d'une équipe."""
    team_score: float = Field(..., ge=0.0, le=1.0, description="Score global de l'équipe (0.0 à 1.0)")
    buff_coverage: float = Field(..., ge=0.0, le=1.0, description="Couverture des buffs (0.0 à 1.0)")
    role_coverage: float = Field(..., ge=0.0, le=1.0, description="Couverture des rôles (0.0 à 1.0)")
    strengths: List[str] = Field(default_factory=list, description="Points forts de l'équipe")
    improvement_areas: List[str] = Field(default_factory=list, description="Points à améliorer")
    detailed_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Détail du scoring")
    suggested_improvements: List[Dict[str, Any]] = Field(default_factory=list, description="Suggestions d'amélioration")

# Expression régulière pour extraire l'ID d'un lien gw2skilleditor
GW2SKILLEDITOR_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?lucky-noobs\.com/builds/view/(\d+)',
    re.IGNORECASE
)

async def parse_gw2skilleditor_url(url: str) -> Optional[str]:
    """Extrait l'ID de build d'une URL gw2skilleditor.
    
    Args:
        url: L'URL du build gw2skilleditor
        
    Returns:
        L'ID du build, ou None si l'URL n'est pas valide
    """
    match = GW2SKILLEDITOR_URL_PATTERN.match(url.strip())
    return match.group(1) if match else None

async def fetch_build_data(build_id: str) -> Dict[str, Any]:
    """Récupère les données d'un build à partir de son ID.
    
    Note: Cette fonction est un exemple et devra être adaptée en fonction de l'API réelle
    de gw2skilleditor ou de la méthode de scraping nécessaire.
    
    Args:
        build_id: L'ID du build à récupérer
        
    Returns:
        Un dictionnaire contenant les données du build
        
    Raises:
        HTTPException: Si la récupération échoue
    """
    # TODO: Implémenter la récupération des données réelles
    # Ceci est un exemple avec une API fictive
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.lucky-noobs.com/builds/{build_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du build {build_id}: {str(e)}"
        )

async def parse_build_data(raw_data: Dict[str, Any]) -> Gw2SkilleditorBuild:
    """Parse les données brutes d'un build en un objet structuré.
    
    Args:
        raw_data: Les données brutes du build
        
    Returns:
        Un objet Gw2SkilleditorBuild structuré
        
    Raises:
        ValidationError: Si les données ne sont pas valides
    """
    # TODO: Adapter cette fonction en fonction de la structure réelle des données
    return Gw2SkilleditorBuild(
        build_id=raw_data.get("id", ""),
        profession=raw_data.get("profession", "").lower(),
        specialization=raw_data.get("specialization", "").lower(),
        skills=raw_data.get("skills", []),
        traits=raw_data.get("traits", {}),
        equipment=raw_data.get("equipment", {})
    )

async def analyze_team(builds: List[Union[Dict[str, Any], str]]) -> TeamAnalysisResult:
    """Analyse une équipe à partir d'une liste de builds.
    
    Args:
        builds: Liste de builds, soit sous forme de dictionnaires, soit d'URLs gw2skilleditor
        
    Returns:
        Un objet TeamAnalysisResult contenant l'analyse de l'équipe
        
    Raises:
        HTTPException: Si l'analyse échoue
    """
    if len(builds) != 5:
        raise HTTPException(
            status_code=400,
            detail="L'analyse d'équipe nécessite exactement 5 builds"
        )
    
    # Convertir les builds en objets PlayerBuild
    player_builds = []
    analysis_results = []
    
    for build_data in builds:
        try:
            if isinstance(build_data, str):
                # C'est une URL gw2skilleditor
                build = BuildImporter.from_gw2skilleditor_url(build_data)
                analysis_results.append(BuildAnalysisResult(
                    build=build,
                    source="gw2skilleditor"
                ))
            else:
                # C'est un dictionnaire de données de build
                build = BuildImporter.from_dict(build_data)
                analysis_results.append(BuildAnalysisResult(
                    build=build,
                    source="manual"
                ))
            
            player_builds.append(build)
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de l'import du build: {str(e)}"
            )
    
    # Créer une composition d'équipe
    team = TeamComposition(
        members=[],  # Les membres ne sont plus nécessaires directement
        score=0.0  # Le score sera calculé par le moteur
    )
    
    # Utiliser le moteur de scoring existant
    scoring_result = score_team(
        team=player_builds,  # On passe directement les builds
        config={
            "playstyle": Playstyle.ZERG,  # À adapter selon le contexte
            "required_buffs": ["might", "quickness", "alacrity", "fury", "protection"],
            "required_roles": ["heal", "dps", "support"]
        }
    )
    
    # Analyser les résultats
    strengths = []
    improvement_areas = []
    
    # Analyse de la couverture des buffs
    buff_coverage = scoring_result.buff_score
    if buff_coverage > 0.8:
        strengths.append("Excellente couverture des buffs")
    elif buff_coverage < 0.5:
        improvement_areas.append("Couverture des buffs insuffisante")
    
    # Analyse de la répartition des rôles
    role_coverage = scoring_result.role_score
    if role_coverage > 0.8:
        strengths.append("Bonne répartition des rôles")
    elif role_coverage < 0.5:
        improvement_areas.append("Répartition des rôles à améliorer")
    
    # Vérifier les buffs manquants
    missing_buffs = [
        buff for buff, coverage in scoring_result.buff_breakdown.items() 
        if coverage.get("score", 0) < 0.5
    ]
    if missing_buffs:
        improvement_areas.append(f"Buffs manquants ou insuffisants: {', '.join(missing_buffs)}")
    
    # Construire le résultat
    return TeamAnalysisResult(
        team_score=scoring_result.total_score,
        buff_coverage=buff_coverage,
        role_coverage=role_coverage,
        strengths=strengths,
        improvement_areas=improvement_areas,
        detailed_breakdown={
            "buff_breakdown": scoring_result.buff_breakdown,
            "role_breakdown": scoring_result.role_breakdown,
            "group_coverage": scoring_result.group_coverage,
            "builds_analysis": [
                {
                    "profession": build.build.profession_id,
                    "role": build.build.role,
                    "buffs": build.build.buffs,
                    "source": build.source
                }
                for build in analysis_results
            ]
        }
    )
