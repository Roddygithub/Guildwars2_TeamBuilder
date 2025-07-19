import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.models.team import TeamRequest, TeamResponse, TeamMember, TeamComposition
from app.optimizer.simple import optimize as optimize_team
from app.optimizer.build_generator import (
    select_weapons_for_build,
    select_skills_for_build,
    select_equipment_for_build,
    BuildRole
)
from app.scoring.engine import PlayerBuild
from app.scoring.schema import (
    BuffWeight,
    DuplicatePenalty,
    RoleWeight,
    ScoringConfig,
    TeamScoreResult,
)
from app.database import SessionLocal

# Configuration du logger
logger = logging.getLogger(__name__)

# Le préfixe est maintenant géré dans app/api/endpoints/__init__.py
router = APIRouter(tags=["teams"])

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

def _determine_build_role(roles: List[str]) -> BuildRole:
    """Détermine le rôle principal du build à partir des rôles fournis."""
    role_map = {
        'heal': BuildRole.HEALER,
        'quickness': BuildRole.QUICKNESS_SUPPORT,
        'alacrity': BuildRole.ALACRITY_SUPPORT,
        'tank': BuildRole.TANK,
        'dps': BuildRole.POWER_DPS,  # Par défaut, on considère DPS puissance
        'condition': BuildRole.CONDITION_DPS,
        'hybrid': BuildRole.HYBRID
    }
    
    # Parcourir les rôles par ordre de priorité
    for role in ['heal', 'quickness', 'alacrity', 'tank', 'condition', 'hybrid', 'dps']:
        if role in roles:
            return role_map[role]
    
    # Par défaut, on retourne DPS puissance
    return BuildRole.POWER_DPS

def _get_stat_priority(build_role: BuildRole) -> List[str]:
    """Détermine la priorité des statistiques en fonction du rôle."""
    if build_role == BuildRole.POWER_DPS:
        return ["Power", "Precision", "Ferocity", "Critical Damage"]
    elif build_role == BuildRole.CONDITION_DPS:
        return ["Condition Damage", "Expertise", "Precision", "Power"]
    elif build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        return ["Healing Power", "Concentration", "Boon Duration", "Vitality"]
    elif build_role == BuildRole.TANK:
        return ["Toughness", "Vitality", "Healing Power", "Concentration"]
    else:  # HYBRID
        return ["Power", "Precision", "Ferocity", "Vitality"]

def _generate_basic_rotation(profession: str, elite_spec: Optional[str], 
                           build_role: BuildRole, weapons: List[Dict[str, Any]]) -> List[str]:
    """Génère une rotation de base basée sur la profession, la spécialisation et le rôle.
    
    Args:
        profession: La profession du personnage
        elite_spec: La spécialisation d'élite (optionnelle)
        build_role: Le rôle du build
        weapons: Liste des armes équipées
        
    Returns:
        Une liste d'étapes de rotation
    """
    # Rotation de base générique
    rotation = [
        "Utilisez vos compétences de contrôle pour interrompre les attaques ennemies",
        "Maintenez les buffs de groupe (si votre rôle le permet)",
        "Adaptez votre rotation en fonction des mécaniques de combat"
    ]
    
    # Ajouter des conseils spécifiques au rôle
    if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        rotation.insert(0, "Priorité aux compétences de soin et de support")
    elif build_role == BuildRole.TANK:
        rotation.insert(0, "Gardez l'attention des ennemis sur vous")
        rotation.insert(1, "Utilisez vos compétences défensives pour survivre")
    else:  # DPS
        rotation.insert(0, "Maximisez vos dégâts tout en évitant les attaques ennemies")
    
    return rotation

def _generate_build_details(member: PlayerBuild) -> dict:
    """Génère les détails d'un build personnalisé basé sur la profession et les rôles.
    
    Args:
        member: Le PlayerBuild contenant les informations de base
        
    Returns:
        Un dictionnaire contenant les détails du build généré
    """
    try:
        # Déterminer le rôle principal du build
        build_role = _determine_build_role(member.roles)
        
        # Déterminer la priorité des statistiques
        stat_priority = _get_stat_priority(build_role)
        
        # Créer une session de base de données
        db = SessionLocal()
        
        try:
            # 1. Sélectionner les armes
            weapons = select_weapons_for_build(
                profession=member.profession_id,
                elite_spec=member.elite_spec,
                build_role=build_role,
                session=db
            )
            
            # 2. Sélectionner les compétences
            skills = select_skills_for_build(
                profession=member.profession_id,
                elite_spec=member.elite_spec,
                weapons=[w['type'] for w in weapons],
                build_role=build_role,
                session=db
            )
            
            # 3. Sélectionner l'équipement
            equipment = select_equipment_for_build(
                profession=member.profession_id,
                elite_spec=member.elite_spec,
                build_role=build_role,
                stat_priority=stat_priority,
                session=db
            )
            
            # 4. Générer une rotation de base
            rotation = _generate_basic_rotation(
                profession=member.profession_id,
                elite_spec=member.elite_spec,
                build_role=build_role,
                weapons=weapons
            )
            
            # 5. Construire la réponse finale
            build_details = {
                "profession": member.profession_id,
                "elite_spec": member.elite_spec,
                "roles": member.roles,
                "build_role": build_role.value,
                "weapons": weapons,
                "skills": skills,
                "equipment": equipment,
                "stats_priority": stat_priority,
                "rotation": rotation,
                "consumables": {
                    "food": equipment.get('Food', {}).get('name', 'Nourriture recommandée non trouvée'),
                    "utility": equipment.get('Utility', {}).get('name', 'Utilitaire recommandé non trouvé'),
                    "rune": equipment.get('Rune', {}).get('name', 'Rune recommandée non trouvée')
                }
            }
            
            return build_details
            
        except Exception as e:
            logger.error(
                "Erreur lors de la génération du build pour %s (%s): %s",
                member.profession_id,
                member.elite_spec or "Pas de spécialisation",
                str(e)
            )
            logger.error(traceback.format_exc())
            
            # En cas d'erreur, retourner une structure de base avec les informations disponibles
            return {
                "profession": member.profession_id,
                "elite_spec": member.elite_spec,
                "roles": member.roles,
                "build_role": build_role.value,
                "weapons": [],
                "skills": [],
                "equipment": {},
                "stats_priority": stat_priority,
                "rotation": [],
                "error": f"Erreur lors de la génération du build: {str(e)}"
            }
            
        finally:
            # Toujours fermer la session de base de données
            db.close()
            
    except Exception as e:
        logger.error(
            "Erreur critique lors de la génération du build: %s",
            str(e)
        )
        logger.error(traceback.format_exc())
        
        # En cas d'erreur critique, retourner une structure minimale
        return {
            "profession": member.profession_id if hasattr(member, 'profession_id') else "Inconnu",
            "elite_spec": member.elite_spec if hasattr(member, 'elite_spec') else None,
            "roles": member.roles if hasattr(member, 'roles') else [],
            "error": f"Erreur critique lors de la génération du build: {str(e)}"
        }

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
        
        # Générer les détails du build personnalisé
        build_details = _generate_build_details(member)
        
        # Pour l'instant, on utilise "#" comme URL, mais on pourrait générer une page de détail
        # avec les informations du build dans le futur
        build_url = "#"
        
        members.append(TeamMember(
            role=", ".join(roles),
            profession=f"{member.elite_spec if member.elite_spec else member.profession_id}",
            build_url=build_url,
            build_details=build_details  # On ajoute les détails du build à l'objet membre
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
) -> TeamResponse:
    """Génère une ou plusieurs compositions d'équipe optimisées.
    
    Args:
        request: La demande de génération d'équipe.
        
    Returns:
        Une réponse contenant les équipes optimisées et leurs scores.
        
    Raises:
        HTTPException: En cas d'erreur lors de la génération de l'équipe.
    """
    import traceback
    try:
        logger.info("=== DÉBUT DE LA GÉNÉRATION D'ÉQUIPE ===")
        logger.info("Requête reçue : %s", request.dict())
        logger.info(
            "Génération d'une équipe de %s joueurs pour le style de jeu: %s",
            request.team_size,
            request.playstyle
        )
        
        # 1. Valider la requête
        if request.team_size < 1 or request.team_size > 50:
            raise HTTPException(
                status_code=400,
                detail="La taille de l'équipe doit être comprise entre 1 et 50 joueurs."
            )
        
        # 2. Utiliser l'optimiseur pour générer la meilleure équipe
        # On génère 1000 échantillons et on garde uniquement la meilleure équipe
        logger.info(
            "Démarrage de l'optimisation pour une équipe de %s joueurs...",
            request.team_size
        )
        try:
            logger.info("Appel à optimize_team avec les paramètres suivants :")
            logger.info("- team_size: %s", request.team_size)
            logger.info("- samples: 1000")
            logger.info("- top_n: 1 (uniquement la meilleure équipe)")
            # Éviter la sérialisation complète de _DEFAULT_CONFIG qui peut contenir des références circulaires
            config_info = {
                'buff_weights': list(_DEFAULT_CONFIG.buff_weights.keys()) if hasattr(_DEFAULT_CONFIG, 'buff_weights') else [],
                'role_weights': list(_DEFAULT_CONFIG.role_weights.keys()) if hasattr(_DEFAULT_CONFIG, 'role_weights') else [],
                'duplicate_penalty': {
                    'enabled': _DEFAULT_CONFIG.duplicate_penalty.enabled if hasattr(_DEFAULT_CONFIG.duplicate_penalty, 'enabled') else False,
                    'threshold': _DEFAULT_CONFIG.duplicate_penalty.threshold if hasattr(_DEFAULT_CONFIG.duplicate_penalty, 'threshold') else 1,
                    'penalty_per_extra': _DEFAULT_CONFIG.duplicate_penalty.penalty_per_extra if hasattr(_DEFAULT_CONFIG.duplicate_penalty, 'penalty_per_extra') else 0.5
                } if hasattr(_DEFAULT_CONFIG, 'duplicate_penalty') and _DEFAULT_CONFIG.duplicate_penalty is not None else {}
            }
            logger.info("- config: %s", config_info)
            
            # Optimiser pour trouver la meilleure équipe
            # On génère 1000 échantillons mais on ne garde que la meilleure équipe
            results = optimize_team(
                team_size=request.team_size,
                samples=1000,
                top_n=1,  # On ne veut que la meilleure équipe
                config=_DEFAULT_CONFIG,
                random_seed=42  # Pour la reproductibilité
            )
            
            logger.info(
                "Optimisation terminée. %s équipes générées.",
                len(results) if results else 0
            )
            
            if results:
                logger.info("Exemple de résultat : %s", str(results[0][0]) if len(results) > 0 else "Aucun résultat")
                
        except Exception as e:
            logger.error("=== ERREUR LORS DE L'OPTIMISATION ===")
            logger.error("Type d'erreur: %s", type(e).__name__)
            logger.error("Message d'erreur: %s", str(e))
            logger.error("Stack trace complète:\n%s", traceback.format_exc())
            logger.error("=== FIN DU LOG D'ERREUR ===")
            
            raise HTTPException(
                status_code=500,
                detail="Une erreur est survenue lors de l'optimisation de l'équipe"
            ) from e
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="Aucune équipe valide n'a pu être générée avec les paramètres fournis."
            )
        
        # 3. Prendre uniquement la meilleure équipe
        best_score, best_team = results[0] if results else (None, None)
        
        if not best_team:
            raise HTTPException(
                status_code=404,
                detail="Aucune équipe valide n'a pu être générée avec les paramètres fournis."
            )
        
        # 4. Formater la meilleure équipe pour la réponse
        team_composition = TeamComposition(
            members=_format_team_members(best_team),
            score=best_score.total_score,
            score_breakdown=_format_score_breakdown(best_score)
        )
        
        # 5. Créer les métadonnées de réponse
        metadata: Dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "0.1.0",
            "notes": "Équipe optimisée générée avec l'optimiseur avancé. Les builds sont basés sur des profils types optimisés pour le style de jeu.",
            "total_teams_evaluated": 1000,  # Nombre d'équipes évaluées
            "optimization_time_ms": 0,      # À implémenter: mesurer le temps d'optimisation
            "build_details_available": True # Indique que des détails de build sont disponibles
        }
        
        # 6. Retourner la réponse avec la meilleure équipe
        return TeamResponse(
            team=team_composition,
            request=request,
            metadata=metadata
        )
        
    except HTTPException as http_exc:
        # On laisse passer les exceptions HTTP déjà gérées
        logger.debug(
            "Exception HTTP interceptée: %s",
            str(http_exc)
        )
        raise
        
    except Exception as e:
        error_details = str(e)
        logger.error(
            "Erreur lors de la génération de l'équipe: %s",
            error_details,
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                'error': "Une erreur est survenue lors de la génération de l'équipe",
                'details': error_details,
                'traceback': traceback.format_exc().split('\n')
            }
        ) from e
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Une erreur est survenue lors de la génération de l'équipe",
                "details": str(e),
                "traceback": error_details.split('\n')
            }
        )

# Export du routeur pour une utilisation dans __init__.py
__all__ = ["router"]
