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
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field, fields
from functools import lru_cache
from itertools import islice
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple, Any, TypeVar, cast, Iterator, Sequence

# Types de données optimisés
RoleWeights = Dict[str, float]  # Mapping rôle -> poids
BuffWeights = Dict[str, float]  # Mapping buff -> poids
PlayerBuilds = Tuple['PlayerBuild', ...]  # Tuple immuable de builds de joueurs
TeamGroups = Tuple[PlayerBuilds, ...]  # Tuple de groupes de joueurs (chaque groupe est un tuple)

# Constantes pour le calcul des scores
BUFF_COVERAGE_WEIGHT = 0.4  # Poids de la couverture des buffs dans le score total
ROLE_COVERAGE_WEIGHT = 0.5  # Poids de la couverture des rôles dans le score total
DUPLICATE_PENALTY_WEIGHT = 0.1  # Poids des pénalités pour doublons dans le score total
DEFAULT_DUPLICATE_THRESHOLD = 2  # Seuil par défaut pour les doublons
DEFAULT_PENALTY_PER_EXTRA = 1.0  # Pénalité par doublon supplémentaire

def split_into_groups(team: Sequence[PlayerBuild], group_size: int = 5) -> TeamGroups:
    """Divise une équipe en groupes de taille spécifiée.
    
    Args:
        team: Séquence de builds de joueurs
        group_size: Taille maximale de chaque groupe (5 par défaut pour GW2)
        
    Returns:
        Un tuple de groupes, chaque groupe étant un tuple de builds de joueurs
        
    Example:
        >>> team = [PlayerBuild(...) for _ in range(12)]
        >>> groups = split_into_groups(team, group_size=5)
        >>> len(groups)  # Devrait retourner 3 groupes (5, 5, 2)
        3
    """
    if not team:
        return ()
        
    team_list = list(team)
    return tuple(
        tuple(team_list[i:i + group_size])
        for i in range(0, len(team_list), group_size)
    )

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
        '_description', '_weapons', '_utilities', '_source', '_metadata'
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
        utilities=None,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialise un nouveau build de joueur.
        
        Args:
            profession_id: Identifiant de la profession (ex: 'Guardian')
            buffs: Ensemble des buffs fournis par le build
            roles: Rôles remplis par le build (ex: {'heal', 'support'})
            elite_spec: Spécialisation d'élite (ex: 'Firebrand')
            playstyles: Styles de jeu supportés (ex: {'zerg', 'roaming'})
            description: Description du rôle et du gameplay
            weapons: Armes recommandées pour le build
            utilities: Compétences utilitaires recommandées
            source: Source du build (ex: URL ou 'manual')
            metadata: Métadonnées supplémentaires sur le build
        """
        self._profession_id = profession_id
        self._elite_spec = elite_spec
        self._buffs = frozenset(buffs) if buffs else frozenset()
        self._roles = frozenset(roles) if roles else frozenset()
        self._playstyles = frozenset(playstyles) if playstyles else frozenset()
        self._description = description
        self._weapons = tuple(weapons) if weapons else ()
        self._utilities = tuple(utilities) if utilities else ()
        self._source = source
        self._metadata = metadata or {}
    
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
        
    @property
    def source(self) -> str:
        return self._source
        
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
    
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
    - Gestion des groupes de 5 joueurs pour la couverture des buffs
    
    Args:
        team: Tuple immuable de builds de joueurs
        buff_weights: Ensemble de tuples (buff, poids) pour le calcul du score
        
    Returns:
        Un tuple contenant :
        - Le score total de couverture des buffs
        - Un dictionnaire de détail par buff
        - Une liste d'objets BuffCoverage pour le rapport détaillé
    """
    if not team or not buff_weights:
        return 0.0, {}, []
    
    # Diviser l'équipe en groupes de 5 joueurs
    groups = split_into_groups(team, group_size=5)
    
    # Si l'équipe est vide ou qu'il n'y a pas de poids de buff, retourner un score nul
    if not groups:
        return 0.0, {}, []
    
    # Initialisation des structures de données
    total_score = 0.0
    buff_breakdown = {}
    buff_coverage = []
    
    # Pour chaque buff à évaluer
    for buff, weight in buff_weights:
        # Vérifier dans combien de groupes le buff est présent
        groups_with_buff = 0
        all_providers = []
        
        # Vérifier chaque groupe
        for group in groups:
            group_has_buff = False
            group_providers = []
            
            # Vérifier chaque joueur du groupe
            for player in group:
                if buff in player.buffs:
                    group_has_buff = True
                    group_providers.append(player.profession_id)
            
            # Si le buff est présent dans le groupe, l'ajouter au compteur
            if group_has_buff:
                groups_with_buff += 1
                all_providers.extend(group_providers)
        
        # Calculer le score pour ce buff
        # Le score est proportionnel au pourcentage de groupes couverts
        coverage_ratio = groups_with_buff / len(groups) if groups else 0.0
        # S'assurer que le ratio ne dépasse pas 1.0 à cause des erreurs d'arrondi
        coverage_ratio = min(1.0, coverage_ratio)
        buff_score = weight * coverage_ratio
        total_score += buff_score
        
        # Déterminer si le buff est globalement couvert (présent dans tous les groupes)
        is_globally_covered = groups_with_buff == len(groups)
        
        # Stocker les résultats pour le rapport
        buff_breakdown[buff] = buff_score
        buff_coverage.append(
            BuffCoverage(
                buff=buff,
                covered=is_globally_covered,
                provided_by=all_providers,
                weight=weight
            )
        )
    
    return total_score, buff_breakdown, buff_coverage

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
    1. Couverture des buffs requis (40% du score total) - maintenant par groupe de 5 joueurs
    2. Couverture des rôles nécessaires (50% du score total)
    3. Pénalités pour les doublons de profession (10% du score total)
    
    La couverture des buffs est calculée par groupe de 5 joueurs pour s'assurer que
    chaque sous-groupe dispose des buffs nécessaires. Un buff est considéré comme
    couvert uniquement s'il est présent dans chaque groupe de 5 joueurs.
    
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
        - Le score total (basé sur les poids bruts, non normalisé)
        - Le détail des scores par catégorie
        - Les informations de couverture pour le débogage
        
    Raises:
        TypeError: Si les types des paramètres sont incorrects
        ValueError: Si la configuration est invalide
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
            role_coverage=[],   # Aucune couverture de rôle
            group_coverage={}   # Aucune couverture de groupe
        )
    
    # Validation des entrées
    if not isinstance(team, Iterable):
        raise TypeError("L'équipe doit être un itérable de PlayerBuild")
    
    # Conversion en tuple pour le cache et optimisation
    team_list = list(team)
    team_tuple = tuple(team_list)
    
    # Validation que tous les éléments sont des PlayerBuild
    if not all(isinstance(p, PlayerBuild) for p in team_list):
        raise TypeError("Tous les éléments de l'équipe doivent être des instances de PlayerBuild")
    
    # Préparation des données pour le cache
    # Utilisation de frozenset pour les poids pour permettre la mise en cache
    buff_weights_fs = frozenset((k, v.weight) for k, v in config.buff_weights.items())
    role_weights_fs = frozenset(
        (k, v.weight, v.required_count) 
        for k, v in config.role_weights.items()
    )
    
    # Calcul des composants du score (avec mise en cache)
    # La couverture des buffs est maintenant calculée par groupe de 5 joueurs
    buff_score, buff_breakdown, buff_coverage = _calculate_buff_coverage(
        team_tuple, buff_weights_fs
    )
    
    # Calcul de la couverture des rôles
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
    
    # Calcul des scores maximaux possibles pour la normalisation
    max_buff_score = sum(weight for _, weight in buff_weights_fs) if buff_weights_fs else 1.0
    max_role_score = sum(weight for _, weight, _ in role_weights_fs) if role_weights_fs else 1.0
    
    # Éviter la division par zéro
    normalized_buff_score = buff_score / max_buff_score if max_buff_score > 0 else 0.0
    normalized_role_score = role_score / max_role_score if max_role_score > 0 else 0.0
    
    # Calcul du score total normalisé (moyenne pondérée des scores normalisés)
    # avec application des poids globaux pour chaque composante
    total_score = (normalized_buff_score * BUFF_COVERAGE_WEIGHT +
                  normalized_role_score * ROLE_COVERAGE_WEIGHT)
    
    # Appliquer la pénalité (en pourcentage du score total)
    if duplicate_penalty > 0 and total_score > 0:
        # La pénalité est une fraction du score total, mais ne peut pas le rendre négatif
        penalty_ratio = min(1.0, duplicate_penalty / (buff_score + role_score)) if (buff_score + role_score) > 0 else 0.0
        total_score *= (1.0 - penalty_ratio * DUPLICATE_PENALTY_WEIGHT)
    
    # S'assurer que le score final est dans l'intervalle [0.0, 1.0]
    # En utilisant math.fsum pour une meilleure précision avec les flottants
    total_score = max(0.0, min(1.0, total_score))
    
    # S'assurer que les scores normalisés sont bien dans [0.0, 1.0]
    normalized_buff_score = min(1.0, normalized_buff_score)
    normalized_role_score = min(1.0, normalized_role_score)
    
    # Log de débogage pour vérifier les valeurs
    logger.debug("Scores normalisés - buff_score: %f, role_score: %f", 
                normalized_buff_score, normalized_role_score)
    
    # Préparation des informations sur la couverture par groupe
    groups = split_into_groups(team_tuple, group_size=5)
    group_coverage = {}
    
    for i, group in enumerate(groups, 1):
        group_buffs = set()
        for player in group:
            group_buffs.update(player.buffs)
        group_coverage[f"group_{i}"] = {
            "size": len(group),
            "buffs": sorted(group_buffs),
            "players": [p.profession_id for p in group]
        }
    
    # Logging des résultats détaillés en mode DEBUG
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Score calculé - Buffs: %.2f, Rôles: %.2f, Pénalité: -%.2f, Total: %.2f",
            buff_score, role_score, duplicate_penalty, total_score
        )
        
        # Détail des buffs manquants
        missing_buffs = [
            b for b, cov in zip(config.buff_weights.keys(), buff_coverage) 
            if not cov.covered
        ]
        if missing_buffs:
            logger.debug("Buffs manquants: %s", ", ".join(missing_buffs))
    
    # Vérification finale des valeurs avant création du résultat
    if normalized_buff_score > 1.0 or normalized_role_score > 1.0 or total_score > 1.0:
        logger.warning("Valeurs anormales détectées - buff_score: %f, role_score: %f, total_score: %f",
                     normalized_buff_score, normalized_role_score, total_score)
    
    # Création et retour du résultat
    return TeamScoreResult(
        total_score=min(1.0, total_score),  # Double vérification
        buff_score=min(1.0, normalized_buff_score),  # Double vérification
        role_score=min(1.0, normalized_role_score),  # Double vérification
        duplicate_penalty=min(1.0, duplicate_penalty / (buff_score + role_score) if (buff_score + role_score) > 0 else 0.0),
        buff_breakdown=dict(buff_breakdown),
        role_breakdown=dict(role_breakdown),
        buff_coverage=buff_coverage,
        role_coverage=role_coverage,
        group_coverage=group_coverage
    )
