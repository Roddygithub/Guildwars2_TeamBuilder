"""Moteur de notation pour l'évaluation des compositions d'équipe GW2.

Ce module fournit les fonctionnalités pour évaluer et noter les compositions d'équipe
en fonction de divers critères comme la couverture des buffs, l'accomplissement des rôles
et la diversité des professions. Il utilise une approche heuristique pour attribuer
des scores aux compositions d'équipe.

Le module est optimisé pour les performances avec :
- Utilisation de types immuables pour le cache
- Mémoïsation des calculs coûteux
- Structures de données optimisées
- Opérations vectorisées quand c'est possible

Exemple d'utilisation:
    ```python
    from app.scoring.engine import PlayerBuild, score_team
    from app.scoring.schema import ScoringConfig

    # Configuration du scoring
    config = ScoringConfig(...)
    
    # Création d'une équipe de test
    team = [
        PlayerBuild(
            profession_id="Guardian",
            elite_spec="Firebrand",
            buffs={"quickness", "might"},
            roles={"support", "quickness"},
            playstyles={"zerg"}
        ),
        # ... autres builds
    ]
    
    # Calcul du score
    result = score_team(team, config)
    print(f"Score total: {result.total_score:.2f}")
    ```
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field, fields
from functools import lru_cache
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple, Any, TypeVar, cast

# Types de données optimisés
RoleWeights = Dict[str, float]  # Mapping rôle -> poids
BuffWeights = Dict[str, float]  # Mapping buff -> poids
PlayerBuilds = Tuple['PlayerBuild', ...]  # Tuple immuable de builds de joueurs

# Constantes pour les calculs de score
BUFF_COVERAGE_WEIGHT = 0.4
ROLE_COVERAGE_WEIGHT = 0.5
DUPLICATE_PENALTY_WEIGHT = 0.1
DEFAULT_DUPLICATE_THRESHOLD = 2
DEFAULT_PENALTY_PER_EXTRA = 1.0

from app.logging_config import get_logger
from app.scoring.schema import (
    BuffCoverage,
    RoleCoverage,
    ScoringConfig,
    TeamScoreResult,
)

# Initialisation du logger
logger = get_logger(__name__)

# Type variable pour les méthodes de classe
T = TypeVar('T', bound='PlayerBuild')


class PlayerBuild:
    """Représentation immuable d'un build de joueur pour l'évaluation des équipes.
    
    Cette classe est conçue pour être immuable afin de permettre son utilisation 
    comme clé de cache et d'optimiser les performances. L'utilisation de __slots__ 
    améliore les performances en réduisant l'empreinte mémoire et en accélérant 
    l'accès aux attributs.
    
    Attributes:
        profession_id: Identifiant de la profession (ex: 'Guardian')
        buffs: Ensemble des buffs fournis par le build
        roles: Rôles remplis par le build (ex: 'heal', 'dps', 'quickness')
        elite_spec: Spécialisation d'élite (ex: 'Firebrand', 'Dragonhunter').
            Chaîne vide si la profession n'a pas de spé d'élite.
        playstyles: Styles de jeu supportés (ex: 'zerg', 'havoc', 'roaming')
        description: Description du rôle et du gameplay
        weapons: Armes recommandées pour le build
        utilities: Compétences utilitaires recommandées
        
    Example:
        >>> build = PlayerBuild(
        ...     profession_id="Guardian",
        ...     elite_spec="Firebrand",
        ...     buffs={"quickness", "might"},
        ...     roles={"support", "quickness"},
        ...     playstyles={"zerg"},
        ...     description="Heal/Quickness Firebrand",
        ...     weapons=("Mace", "Axe", "Shield"),
        ...     utilities=("Mantra of Potence", "Mantra of Solace")
        ... )
        >>> print(build)
        Guardian (support, quickness)
    """
    __slots__ = [
        '_profession_id', '_elite_spec', '_buffs', '_roles', '_playstyles', 
        '_description', '_weapons', '_utilities'
    ]
    
    def __init__(
        self,
        profession_id: str,
        buffs,
        roles,
        elite_spec: str = "",
        playstyles=None,
        description: str = "",
        weapons=None,
        utilities=None
    ):
        """Initialise un nouveau build de joueur."""
        self._profession_id = profession_id
        self._elite_spec = elite_spec
        self._buffs = frozenset(buffs) if buffs else frozenset()
        self._roles = frozenset(roles) if roles else frozenset()
        self._playstyles = frozenset(playstyles) if playstyles else frozenset()
        self._description = description
        self._weapons = tuple(weapons) if weapons else ()
        self._utilities = tuple(utilities) if utilities else ()
    
    @property
    def profession_id(self) -> str:
        return self._profession_id
        
    @property
    def elite_spec(self) -> str:
        return self._elite_spec
        
    @property
    def buffs(self) -> FrozenSet[str]:
        return self._buffs
        
    @property
    def roles(self) -> FrozenSet[str]:
        return self._roles
        
    @property
    def playstyles(self) -> FrozenSet[str]:
        return self._playstyles
        
    @property
    def description(self) -> str:
        return self._description
        
    @property
    def weapons(self) -> Tuple[str, ...]:
        return self._weapons
        
    @property
    def utilities(self) -> Tuple[str, ...]:
        return self._utilities
    
    def __setattr__(self, name, value):
        """Empêche la modification des attributs après la création."""
        if hasattr(self, f'_{name}') and name != '__dict__':
            raise AttributeError(f"L'attribut {name} est en lecture seule")
        super().__setattr__(name, value)
        
    def __delattr__(self, name):
        """Empêche la suppression des attributs."""
        if hasattr(self, f'_{name}') and name != '__dict__':
            raise AttributeError(f"L'attribut {name} ne peut pas être supprimé")
        super().__delattr__(name)
    
    def __repr__(self) -> str:
        """Représentation technique de l'objet.
        
        Returns:
            Une chaîne représentant l'objet de manière technique.
        """
        spec = f" - {self.elite_spec}" if self.elite_spec else ""
        return f"PlayerBuild({self.profession_id}{spec}, roles={sorted(self.roles)})"
    
    def __str__(self) -> str:
        """Représentation lisible de l'objet.
        
        Returns:
            Une chaîne lisible représentant le build.
        """
        roles = ", ".join(sorted(self.roles))
        return f"{self.profession_id}{f' ({self.elite_spec})' if self.elite_spec else ''} ({roles})"


@lru_cache(maxsize=1024, typed=True)
def _calculate_buff_coverage(
    team: PlayerBuilds, 
    buff_weights: FrozenSet[Tuple[str, float]]
) -> Tuple[float, Dict[str, float], List[BuffCoverage]]:
    """Calcule la couverture des buffs pour une équipe donnée avec mise en cache.
    
    Cette fonction est optimisée pour les performances avec :
    - Utilisation de types immuables pour le cache
    - Opérations sur les ensembles pour des vérifications rapides
    - Pré-allocation des structures de données
    
    Args:
        team: Tuple immuable de builds de joueurs
        buff_weights: Ensemble de tuples (buff, poids) pour le calcul du score
        
    Returns:
        Un tuple contenant :
        - Le score total de couverture des buffs
        - Un dictionnaire de détail par buff
        - Une liste d'objets BuffCoverage pour le rapport détaillé
    """
    """Calcule la couverture des buffs pour une équipe donnée.
    
    Cette fonction est mise en cache avec @lru_cache pour optimiser les performances
    lors d'appels répétés avec les mêmes paramètres.
    
    Args:
        team: Tuple immuable de builds de joueurs
        buff_weights: Ensemble de tuples (buff, poids) pour le calcul du score
        
    Returns:
        Un tuple contenant:
        - Le score total de couverture des buffs
        - Un dictionnaire de détail par buff
        - Une liste d'objets BuffCoverage pour le rapport détaillé
        
    Note:
        La fonction est décorée avec @lru_cache, donc les paramètres doivent être hashables.
        C'est pourquoi nous utilisons des tuples et frozenset plutôt que des listes/sets.
    """
    # Création d'un ensemble de tous les buffs uniques de l'équipe
    # Utilisation d'une compréhension d'ensemble pour une meilleure performance
    team_buffs = frozenset().union(*(p.buffs for p in team))
    
    buff_items: List[BuffCoverage] = []
    buff_breakdown: Dict[str, float] = {}
    buff_total = 0.0
    
    # Calcul du score pour chaque buff
    for buff, weight in buff_weights:
        covered = buff in team_buffs
        score = weight if covered else 0.0
        buff_breakdown[buff] = score
        buff_items.append(BuffCoverage(buff=buff, covered=covered, weight=weight))
        buff_total += score
        
    return buff_total, buff_breakdown, buff_items

@lru_cache(maxsize=1024, typed=True)
def _calculate_role_coverage(
    team: PlayerBuilds, 
    role_weights: FrozenSet[Tuple[str, float, int]]
) -> Tuple[float, Dict[str, float], List[RoleCoverage]]:
    """Calcule la couverture des rôles pour une équipe donnée avec mise en cache.
    
    Optimisations :
    - Utilisation de compteurs pour un décompte efficace
    - Pré-allocation des structures de données
    - Opérations vectorisées pour le calcul des scores
    
    Args:
        team: Tuple immuable de builds de joueurs
        role_weights: Ensemble de tuples (rôle, poids, nombre_requis)
        
    Returns:
        Un tuple contenant :
        - Le score total de couverture des rôles
        - Un dictionnaire de détail par rôle
        - Une liste d'objets RoleCoverage pour le rapport détaillé
    """
    """Calcule la couverture des rôles pour une équipe donnée.
    
    Cette fonction évalue dans quelle mesure une équipe remplit les rôles requis
    et calcule un score basé sur la configuration des poids.
    
    Args:
        team: Tuple immuable de builds de joueurs
        role_weights: Ensemble de tuples (rôle, poids, nombre_requis) pour le calcul
            
    Returns:
        Un tuple contenant:
        - Le score total de couverture des rôles
        - Un dictionnaire de détail par rôle
        - Une liste d'objets RoleCoverage pour le rapport détaillé
        
    Note:
        Le score pour chaque rôle est calculé comme suit:
        - Si le rôle est couvert (fulfilled >= required): score = poids
        - Sinon: score = poids * (fulfilled / required)
        
        Le score total est la somme des scores de chaque rôle.
    """
    # Comptage des rôles en une seule passe avec un dictionnaire
    role_counts: Dict[str, int] = {}
    for player in team:
        for role in player.roles:
            role_counts[role] = role_counts.get(role, 0) + 1
    
    role_items: List[RoleCoverage] = []
    role_breakdown: Dict[str, float] = {}
    role_total = 0.0
    
    # Calcul du score pour chaque rôle
    for role, weight, required in role_weights:
        fulfilled = role_counts.get(role, 0)
        
        # Calcul du ratio de couverture (ne peut pas dépasser 1.0)
        ratio = min(1.0, fulfilled / required) if required > 0 else 1.0
        score = weight * ratio
        
        role_breakdown[role] = score
        # Calcul de si le rôle est suffisamment couvert
        is_fulfilled = fulfilled >= required if required > 0 else True
        
        role_items.append(RoleCoverage(
            role=role,
            fulfilled_count=fulfilled,
            required_count=required,
            fulfilled=is_fulfilled,
            weight=weight  # Utilisation du poids fourni dans les paramètres
        ))
        role_total += score
        
    return role_total, role_breakdown, role_items

@lru_cache(maxsize=1024, typed=True)
def _calculate_duplicate_penalty(
    team: PlayerBuilds, 
    threshold: int = DEFAULT_DUPLICATE_THRESHOLD, 
    penalty_per_extra: float = DEFAULT_PENALTY_PER_EXTRA
) -> float:
    """Calcule la pénalité pour les doublons de profession avec mise en cache.
    
    Optimisations :
    - Utilisation de Counter pour un décompte efficace
    - Paramètres par défaut pour éviter les calculs redondants
    
    Args:
        team: Tuple immuable de builds de joueurs
        threshold: Nombre maximum autorisé de chaque profession avant pénalité
        penalty_per_extra: Pénalité pour chaque occurrence supplémentaire
        
    Returns:
        La pénalité totale à soustraire du score
    """
    """Calcule la pénalité pour les doublons de profession.
    
    Cette fonction applique une pénalité pour chaque occurrence d'une profession
    au-delà du seuil spécifié. Par exemple, avec un seuil de 2, la troisième
    occurrence d'une profession déclenche une pénalité.
    
    Args:
        team: Tuple immuable de builds de joueurs
        threshold: Nombre maximum autorisé de chaque profession avant pénalité
        penalty_per_extra: Pénalité pour chaque occurrence supplémentaire
        
    Returns:
        La pénalité totale à soustraire du score
        
    Example:
        >>> team = [...]  # 3 Guardians et 2 Warriors
        >>> # Avec threshold=2 et penalty_per_extra=1.0
        >>> # Pénalité = (3 - 2) * 1.0 + (2 - 2) * 1.0 = 1.0
        >>> penalty = _calculate_duplicate_penalty(team, 2, 1.0)
        >>> print(penalty)
        1.0
    """
    # Si le seuil est 0 ou la pénalité est nulle, retourner 0 immédiatement
    if not threshold or penalty_per_extra <= 0:
        return 0.0
        
    # Comptage des occurrences de chaque profession
    profession_counts: Dict[str, int] = {}
    for player in team:
        prof = player.profession_id
        profession_counts[prof] = profession_counts.get(prof, 0) + 1
    
    # Calcul de la pénalité totale
    return sum(
        max(0, count - threshold) * penalty_per_extra
        for count in profession_counts.values()
    )

def score_team(team: Iterable[PlayerBuild], config: ScoringConfig) -> TeamScoreResult:
    """Calcule le score d'une équipe en fonction de sa composition.
    
    Cette fonction évalue une équipe selon trois critères principaux :
    1. Couverture des buffs requis (40% du score total)
    2. Couverture des rôles nécessaires (50% du score total)
    3. Pénalités pour les doublons de profession (10% du score total)
    
    Optimisations de performance :
    - Conversion précoce en tuple pour la mise en cache
    - Pré-calcul des structures de données immuables
    - Utilisation de types natifs pour les opérations critiques
    - Vérification des préconditions avant les calculs coûteux
    
    Args:
        team: Itérable de PlayerBuild représentant l'équipe à évaluer
        config: Configuration du calcul des scores (poids, pénalités, etc.)
        
    Returns:
        Un objet TeamScoreResult contenant :
        - Le score total (0.0 à 1.0)
        - Le détail des scores par catégorie
        - Les informations de couverture pour le débogage
        
    Raises:
        TypeError: Si les types des paramètres sont incorrects
        ValueError: Si la configuration est invalide
        
    Example:
        >>> from app.scoring.schema import ScoringConfig, BuffWeight, RoleWeight
        >>> 
        >>> # Configuration de test
        >>> config = ScoringConfig(
        ...     buff_weights={
        ...         "quickness": BuffWeight(weight=2.0, description="Quickness support"),
        ...         "alacrity": BuffWeight(weight=2.0, description="Alacrity support"),
        ...     },
        ...     role_weights={
        ...         "heal": RoleWeight(weight=2.0, required_count=1, description="Healer"),
        ...         "dps": RoleWeight(weight=1.0, required_count=3, description="DPS"),
        ...     }
        ... )
        >>> 
        >>> # Équipe de test
        >>> team = [...]  # Liste de PlayerBuild
        >>> 
        >>> # Calcul du score
        >>> result = score_team(team, config)
        >>> print(f"Score total: {result.total_score:.2f}")
    """
    # Vérification des préconditions (optimisation: échec rapide)
    if not team:
        return TeamScoreResult(
            total_score=1.0,  # Score par défaut pour une équipe vide
            buff_score=1.0,   # Score de buffs parfait pour une équipe vide
            role_score=1.0,   # Score de rôles parfait pour une équipe vide
            duplicate_penalty=0.0,  # Aucune pénalité pour une équipe vide
            buff_breakdown={},  # Aucun buff à lister
            role_breakdown={},  # Aucun rôle à lister
            buff_coverage=[],   # Aucune couverture de buff
            role_coverage=[]    # Aucune couverture de rôle
        )
        
    # Conversion en tuple pour l'immutabilité (nécessaire pour le cache)
    team_tuple = tuple(team)
    
    # Préparation des données pour le cache
    buff_weights_fs = frozenset((k, v.weight) for k, v in config.buff_weights.items())
    role_weights_fs = frozenset(
        (k, v.weight, v.required_count) 
        for k, v in config.role_weights.items()
    )
    
    # Calcul des composants du score (avec mise en cache)
    buff_score, buff_breakdown, buff_coverage = _calculate_buff_coverage(
        team_tuple, buff_weights_fs
    )
    
    role_score, role_breakdown, role_coverage = _calculate_role_coverage(
        team_tuple, role_weights_fs
    )
    
    # Application des pénalités pour doublons
    duplicate_penalty = 0.0
    if config.duplicate_penalty:
        duplicate_penalty = _calculate_duplicate_penalty(
            team_tuple,
            config.duplicate_penalty.threshold,
            config.duplicate_penalty.penalty_per_extra
        )
    
    # Calcul du score total pondéré
    total_score = max(0.0, min(1.0, (
        (buff_score * BUFF_COVERAGE_WEIGHT) +
        (role_score * ROLE_COVERAGE_WEIGHT) -
        (duplicate_penalty * DUPLICATE_PENALTY_WEIGHT)
    )))
    
    # Normalisation des scores entre 0 et 1 pour buff_score et role_score
    normalized_buff_score = max(0.0, min(1.0, buff_score / len(buff_weights_fs) if buff_weights_fs else 0.0))
    normalized_role_score = max(0.0, min(1.0, role_score / len(role_weights_fs) if role_weights_fs else 0.0))
    
    return TeamScoreResult(
        total_score=total_score,
        buff_score=normalized_buff_score,
        role_score=normalized_role_score,
        duplicate_penalty=duplicate_penalty,
        buff_breakdown=dict(buff_breakdown),
        role_breakdown=dict(role_breakdown),
        buff_coverage=buff_coverage,
        role_coverage=role_coverage
    )
    # Validation des entrées
    if not isinstance(team, Iterable):
        raise TypeError("L'équipe doit être un itérable de PlayerBuild")
    
    # Conversion en tuple pour le cache et optimisation
    # Utilisation d'une compréhension pour forcer l'itération une seule fois
    team_list = list(team)
    team_tuple = tuple(team_list)
    
    # Validation que tous les éléments sont des PlayerBuild
    if not all(isinstance(p, PlayerBuild) for p in team_list):
        raise TypeError("Tous les éléments de l'équipe doivent être des instances de PlayerBuild")
    
    # Préparation des données pour le cache
    # Utilisation de frozenset pour les poids pour permettre la mise en cache
    buff_weights = frozenset(
        (b, float(w.weight)) 
        for b, w in config.buff_weights.items()
    )
    role_weights = frozenset(
        (r, float(rw.weight), rw.required_count) 
        for r, rw in config.role_weights.items()
    )
    
    # Calcul des différentes parties du score
    # Ces appels utilisent le cache LRU pour les calculs répétitifs
    buffs_total, buff_breakdown, buff_coverage = _calculate_buff_coverage(
        team_tuple, buff_weights
    )
    
    roles_total, role_breakdown, role_coverage = _calculate_role_coverage(
        team_tuple, role_weights
    )
    
    # Calcul de la pénalité pour les doublons
    dup_penalty = 0.0
    if config.duplicate_penalty:
        dup_penalty = _calculate_duplicate_penalty(
            team_tuple,
            config.duplicate_penalty.threshold,
            config.duplicate_penalty.penalty_per_extra
        )
    
    # Score final = buffs + rôles - pénalités
    total_score = buffs_total + roles_total - dup_penalty
    
    # Logging des résultats détaillés en mode DEBUG
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Score calculé - Buffs: %.2f, Rôles: %.2f, Pénalité: -%.2f, Total: %.2f",
            buffs_total, roles_total, dup_penalty, total_score
        )
        
        # Détail des buffs manquants
        missing_buffs = [
            b for b, cov in zip(config.buff_weights.keys(), buff_coverage) 
            if not cov.covered
        ]
        if missing_buffs:
            logger.debug("Buffs manquants: %s", ", ".join(missing_buffs))
    
    # Création et retour du résultat
    return TeamScoreResult(
        total_score=total_score,
        buff_breakdown=buff_breakdown,
        role_breakdown=role_breakdown,
        duplicate_penalty=dup_penalty,
        buff_coverage=buff_coverage,
        role_coverage=role_coverage,
    )
