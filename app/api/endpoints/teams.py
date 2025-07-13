from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import random
import logging
from datetime import datetime, timezone
from ...models.team import TeamRequest, TeamResponse, TeamComposition, TeamMember, Playstyle
from ...scoring.engine import score_team, PlayerBuild
from ...scoring.schema import ScoringConfig, BuffWeight, RoleWeight, DuplicatePenalty, TeamScoreResult
from ...scoring.constants import GameMode, Role, Profession
from ...optimizer.simple import optimize as optimize_team

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])

# Configuration de scoring par défaut
_DEFAULT_CONFIG = ScoringConfig(
    buff_weights={
        "quickness": BuffWeight(weight=2.0, description="Augmente la vitesse d'attaque"),
        "alacrity": BuffWeight(weight=2.0, description="Réduit les temps de recharge"),
        "might": BuffWeight(weight=1.5, description="Augmente les dégâts"),
        "fury": BuffWeight(weight=1.0, description="Augmente la chance de coup critique"),
        "protection": BuffWeight(weight=1.0, description="Réduit les dégâts reçus"),
        "stability": BuffWeight(weight=1.5, description="Immunise contre les contrôles"),
        "aegis": BuffWeight(weight=1.0, description="Blocage du prochain coup"),
        "resistance": BuffWeight(weight=0.8, description="Réduit la durée des altérations"),
        "regeneration": BuffWeight(weight=0.5, description="Soigne au fil du temps"),
        "swiftness": BuffWeight(weight=0.3, description="Augmente la vitesse de déplacement"),
    },
    role_weights={
        "heal": RoleWeight(weight=2.0, required_count=1, description="Soigneur principal"),
        "quickness": RoleWeight(weight=2.0, required_count=1, description="Fournisseur de Quickness"),
        "alacrity": RoleWeight(weight=2.0, required_count=1, description="Fournisseur d'Alacrity"),
        "dps": RoleWeight(weight=1.0, required_count=2, description="Dégâts purs"),
        "support": RoleWeight(weight=1.5, required_count=1, description="Support secondaire"),
        "tank": RoleWeight(weight=1.2, required_count=1, description="Tank"),
    },
    duplicate_penalty=DuplicatePenalty(
        threshold=1,
        penalty_per_extra=0.5,
        enabled=True
    )
)

def _format_team_members(team: List[PlayerBuild]) -> List[TeamMember]:
    """Convertit une liste de PlayerBuild en une liste de TeamMember pour la réponse API."""
    members = []
    for member in team:
        # Créer une description plus lisible pour le rôle
        role_descriptions = {
            "heal": "Soins",
            "quickness": "Quickness",
            "alacrity": "Alacrity",
            "dps": "Dégâts",
            "support": "Support",
            "tank": "Tank",
            "bunker": "Défense"
        }
        
        roles = [role_descriptions.get(role, role.capitalize()) for role in member.roles]
        
        members.append(TeamMember(
            role=", ".join(roles),
            profession=f"{member.elite_spec if member.elite_spec else member.profession_id}",
            build_url=f"#"  # À remplacer par une URL réelle si disponible
        ))
    return members


def _format_score_breakdown(score_result: TeamScoreResult) -> Dict[str, float]:
    """Formate les détails du score pour la réponse API."""
    return {
        "buff_coverage": score_result.buff_score,
        "role_coverage": score_result.role_score,
        "duplicate_penalty": score_result.duplicate_penalty,
        "total": score_result.total_score
    }

@router.post("/generate", response_model=TeamResponse)
async def generate_team(
    request: TeamRequest,
    background_tasks: BackgroundTasks
) -> TeamResponse:
    """Génère une ou plusieurs compositions d'équipe optimisées.
    
    Args:
        request: La demande de génération d'équipe.
        background_tasks: Tâches d'arrière-plan pour le traitement asynchrone.
        
    Returns:
        Une réponse contenant les équipes optimisées et leurs scores.
        
    Raises:
        HTTPException: En cas d'erreur lors de la génération de l'équipe.
    """
    try:
        logger.info(f"Génération d'une équipe de {request.team_size} joueurs pour le style de jeu: {request.playstyle}")
        
        # 1. Valider la requête
        if request.team_size < 1 or request.team_size > 50:
            raise HTTPException(
                status_code=400,
                detail="La taille de l'équipe doit être comprise entre 1 et 50 joueurs."
            )
        
        # 2. Utiliser l'optimiseur pour générer les meilleures équipes
        # On génère 1000 échantillons et on garde les 3 meilleures équipes
        logger.info(f"Démarrage de l'optimisation pour une équipe de {request.team_size} joueurs...")
        try:
            results = optimize_team(
                team_size=request.team_size,
                samples=1000,
                top_n=3,  # Retourner les 3 meilleures équipes
                config=_DEFAULT_CONFIG,
                random_seed=42  # Pour la reproductibilité
            )
            logger.info(f"Optimisation terminée. {len(results) if results else 0} équipes générées.")
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation: {str(e)}", exc_info=True)
            raise
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="Aucune équipe valide n'a pu être générée avec les paramètres fournis."
            )
        
        # 3. Formater les équipes pour la réponse
        team_compositions = []
        for score_result, team in results:
            team_composition = TeamComposition(
                members=_format_team_members(team),
                score=score_result.total_score,
                score_breakdown=_format_score_breakdown(score_result)
            )
            team_compositions.append(team_composition)
        
        # 4. Retourner la réponse
        return TeamResponse(
            teams=team_compositions,
            request=request,
            metadata={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "version": "0.1.0",
                "notes": "Généré avec l'optimiseur simple. Les builds sont basés sur des profils types."
            }
        )
        
    except HTTPException:
        # On laisse passer les exceptions HTTP déjà gérées
        raise
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'équipe: {str(e)}", exc_info=True)
        # Afficher plus de détails sur l'erreur
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Détails de l'erreur: {error_details}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Une erreur est survenue lors de la génération de l'équipe",
                "details": str(e),
                "traceback": error_details.split('\n')
            }
        )
