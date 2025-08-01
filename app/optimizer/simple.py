"""Optimiseur simple qui échantillonne des équipes aléatoires et conserve les meilleures.

Ce module fournit une implémentation de référence pour l'optimisation d'équipes
en utilisant une approche par échantillonnage aléatoire. Il est conçu comme une
solution de base avant de passer à des algorithmes plus sophistiqués comme les
algorithmes génétiques.

Exemple d'utilisation:
    ```python
    config = ScoringConfig(...)
    best_teams = optimize(
        team_size=5,
        samples=1000,
        top_n=5,
        config=config
    )
    ```
"""
from __future__ import annotations

import itertools
import random
from typing import List, Sequence, Tuple

from sqlalchemy.orm import Session

from app.database import SessionLocal
# Import du modèle Profession depuis le module racine
import sys
from pathlib import Path
# Ajout du répertoire parent au chemin de recherche Python
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models import Profession  # Import direct du modèle SQLAlchemy
from app.scoring.engine import PlayerBuild, score_team
from app.scoring.schema import ScoringConfig, TeamScoreResult

#: Dictionnaire de correspondance entre les professions et leurs métadonnées (buffs et rôles par défaut).
#: Format: {"NomProfession": (set(buffs), set(roles))}
_PROFESSION_METADATA = {
    "Guardian": ({"quickness", "might"}, {"heal", "quickness"}),
    "Warrior": ({"might"}, {"dps"}),
    "Revenant": ({"alacrity", "might"}, {"dps", "alacrity"}),
    "Ranger": (set(), {"dps"}),
    "Thief": (set(), {"dps"}),
    "Engineer": ({"quickness"}, {"dps", "quickness"}),
    "Necromancer": (set(), {"dps"}),
    "Elementalist": (set(), {"dps"}),
    "Mesmer": ({"alacrity"}, {"heal", "alacrity"}),
}


def _default_candidates(db: Session) -> List[PlayerBuild]:
    """Génère une liste de builds par défaut pour chaque profession.
    
    Args:
        db: Session SQLAlchemy pour accéder à la base de données.
        
    Returns:
        Une liste de PlayerBuild, un pour chaque profession dans la base de données,
        avec des buffs et des rôles par défaut basés sur _PROFESSION_METADATA.
        
    Example:
        >>> with SessionLocal() as session:
        ...     builds = _default_candidates(session)
        ...     assert len(builds) > 0
        ...     assert all(isinstance(build, PlayerBuild) for build in builds)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Début de la récupération des professions depuis la base de données...")
        
        # Vérifier si la table existe
        from sqlalchemy import inspect
        inspector = inspect(db.get_bind())
        if 'professions' not in inspector.get_table_names():
            logger.error("La table 'professions' n'existe pas dans la base de données.")
            raise ValueError("La table 'professions' n'existe pas dans la base de données.")
        
        # Récupérer toutes les professions
        professions = db.query(Profession).all()
        logger.info(f"{len(professions)} professions récupérées depuis la base de données.")
        
        if not professions:
            logger.warning("Aucune profession trouvée dans la base de données. Utilisation des valeurs par défaut.")
            # Retourner des valeurs par défaut si la base est vide
            return [
                PlayerBuild(
                    profession_id=prof_name.lower(),
                    buffs=buffs,
                    roles=roles,
                    description=f"Build par défaut pour {prof_name}"
                )
                for prof_name, (buffs, roles) in _PROFESSION_METADATA.items()
            ]
        
        # Créer les builds pour chaque profession
        builds: List[PlayerBuild] = []
        for prof in professions:
            try:
                buffs, roles = _PROFESSION_METADATA.get(prof.name, (set(), {"dps"}))
                build = PlayerBuild(
                    profession_id=prof.id,
                    buffs=buffs,
                    roles=roles,
                    description=f"Build pour {prof.name}"
                )
                builds.append(build)
                logger.debug(f"Build créé pour {prof.name} avec {len(buffs)} buffs et {len(roles)} rôles.")
            except Exception as e:
                logger.error(f"Erreur lors de la création du build pour {prof.name}: {str(e)}")
                continue
        
        logger.info(f"{len(builds)} builds créés avec succès.")
        return builds
        
    except Exception as e:
        logger.error(f"Erreur critique dans _default_candidates: {str(e)}", exc_info=True)
        # En cas d'échec, retourner des valeurs par défaut
        return [
            PlayerBuild(
                profession_id=prof_name.lower(),
                buffs=buffs,
                roles=roles,
                description=f"Build par défaut pour {prof_name} (fallback)"
            )
            for prof_name, (buffs, roles) in _PROFESSION_METADATA.items()
        ]


def optimize_team(
    team_size: int,
    samples: int,
    top_n: int,
    config: ScoringConfig,
    candidates: Sequence[PlayerBuild] | None = None,
    random_seed: int | None = None,
) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
    """Alias pour la fonction optimize pour maintenir la compatibilité.
    
    Voir la documentation de la fonction optimize pour plus de détails.
    """
    return optimize(team_size, samples, top_n, config, candidates, random_seed)


def optimize(
    team_size: int,
    samples: int,
    top_n: int,
    config: ScoringConfig,
    candidates: Sequence[PlayerBuild] | None = None,
    random_seed: int | None = None,
) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
    """Trouve les meilleures équipes en échantillonnant des combinaisons aléatoires.
    
    Cette fonction évalue plusieurs combinaisons de builds et retourne les `top_n`
    équipes ayant les meilleurs scores selon la configuration fournie.
    
    Args:
        team_size: Nombre de joueurs par équipe.
        samples: Nombre maximum de combinaisons à évaluer.
        top_n: Nombre d'équipes à retourner (les mieux notées).
        config: Configuration du calcul des scores.
        candidates: Liste optionnelle de builds candidats. Si None, utilise les builds par défaut.
        random_seed: Graine pour le générateur de nombres aléatoires (pour la reproductibilité).
        
    Returns:
        Une liste de tuples (score, équipe) triée par score décroissant, où :
        - score: Un objet TeamScoreResult contenant le score et les détails de l'évaluation.
        - équipe: Une séquence de PlayerBuild représentant la composition d'équipe.
        
    Raises:
        ValueError: Si le nombre de candidats est insuffisant pour former une équipe.
        
    Example:
        >>> config = ScoringConfig(...)
        >>> # Trouver les 3 meilleures équipes de 5 joueurs parmi 1000 échantillons
        >>> best_teams = optimize(5, 1000, 3, config)
        >>> for score, team in best_teams:
        ...     print(f"Score: {score.total_score:.2f}")
        ...     print(f"  Composition: {[p.profession_id for p in team]}")
    """
    if random_seed is not None:
        random.seed(random_seed)

    with SessionLocal() as db:
        if candidates is None:
            candidates = _default_candidates(db)

    if len(candidates) < team_size:
        raise ValueError("Not enough candidate builds to form a team.")

    best: List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]] = []

    # Si le nombre total de combinaisons est raisonnable, on les évalue toutes
    # Sinon, on se limite à un échantillon aléatoire
    total_combos = itertools.combinations(candidates, team_size)
    
    # Limite pour éviter les boucles trop longues
    limit = min(5000, samples)  # Ne pas dépasser 5000 évaluations
    
    for i, combo in enumerate(total_combos):
        if i >= limit:
            break
            
        team = list(combo)
        result = score_team(team, config)
        best.append((result, team))

    # Trie par score décroissant et retourne les top_n meilleures équipes
    best.sort(key=lambda x: x[0].total_score, reverse=True)
    return best[:top_n]
