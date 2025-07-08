"""Module de base pour les optimiseurs d'équipe.

Ce module fournit une classe de base abstraite pour les différents algorithmes
d'optimisation de composition d'équipe. Les implémentations spécifiques doivent
hériter de cette classe et implémenter les méthodes abstraites.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence, Tuple, Optional, Dict, Any, TypeVar, Generic

from app.scoring.engine import PlayerBuild
from app.scoring.schema import ScoringConfig, TeamScoreResult

# Type variable pour les paramètres de configuration spécifiques aux optimiseurs
TConfig = TypeVar('TConfig', bound=Dict[str, Any])


class BaseTeamOptimizer(ABC, Generic[TConfig]):
    """Classe de base abstraite pour les optimiseurs d'équipe.
    
    Cette classe définit l'interface commune pour tous les optimiseurs d'équipe
    et fournit des méthodes utilitaires partagées.
    """
    
    def __init__(
        self,
        team_size: int,
        candidates: Sequence[PlayerBuild],
        config: ScoringConfig,
        population_size: int = 200,
        generations: int = 40,
        random_seed: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialise l'optimiseur avec les paramètres de base.
        
        Args:
            team_size: Nombre de joueurs par équipe.
            candidates: Liste des builds candidats parmi lesquels sélectionner.
            config: Configuration du calcul des scores.
            population_size: Taille de la population à chaque génération.
            generations: Nombre de générations à exécuter.
            random_seed: Graine pour la reproductibilité.
            **kwargs: Arguments supplémentaires pour les implémentations spécifiques.
            
        Raises:
            ValueError: Si les paramètres ne sont pas valides.
        """
        self.team_size = team_size
        self.candidates = candidates
        self.config = config
        self.population_size = population_size
        self.generations = generations
        self.random_seed = random_seed
        self.optimizer_config: TConfig = self._init_optimizer_config(**kwargs)
        
        # Validation des entrées
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """Valide les paramètres d'entrée de l'optimiseur.
        
        Raises:
            ValueError: Si les paramètres ne sont pas valides.
        """
        if self.team_size <= 0:
            raise ValueError(f"La taille de l'équipe doit être positive, pas {self.team_size}")
            
        if not self.candidates:
            raise ValueError("La liste des candidats ne peut pas être vide")
            
        if self.team_size > len(self.candidates):
            raise ValueError(
                f"La taille de l'équipe ({self.team_size}) dépasse le "
                f"nombre de candidats ({len(self.candidates)})"
            )
            
        if self.population_size <= 0:
            raise ValueError(
                f"La taille de la population doit être positive, pas {self.population_size}"
            )
            
        if self.generations < 0:
            raise ValueError(
                f"Le nombre de générations ne peut pas être négatif, pas {self.generations}"
            )
    
    @abstractmethod
    def _init_optimizer_config(self, **kwargs: Any) -> TConfig:
        """Initialise la configuration spécifique à l'optimiseur.
        
        Args:
            **kwargs: Arguments de configuration spécifiques à l'optimiseur.
            
        Returns:
            Un dictionnaire de configuration pour l'optimiseur spécifique.
            
        Raises:
            ValueError: Si les arguments de configuration ne sont pas valides.
        """
        pass
    
    @abstractmethod
    def optimize(self) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
        """Exécute l'optimisation et retourne les meilleures solutions.
        
        Returns:
            Une liste de tuples (score, équipe) triée par score décroissant, où :
            - score: Un objet TeamScoreResult contenant le score et les détails.
            - équipe: Une séquence de PlayerBuild représentant la composition d'équipe.
        """
        pass
    
    def _evaluate_team(self, team_indices: Sequence[int]) -> float:
        """Évalue une équipe à partir des indices des candidats.
        
        Args:
            team_indices: Indices des candidats dans l'équipe.
            
        Returns:
            Le score total de l'équipe.
        """
        team = [self.candidates[i] for i in team_indices]
        return score_team(team, self.config).total_score
    
    def _decode_solution(self, solution: Sequence[int]) -> Tuple[TeamScoreResult, Sequence[PlayerBuild]]:
        """Décode une solution en score et équipe.
        
        Args:
            solution: Une solution encodée (généralement des indices).
            
        Returns:
            Un tuple (score, équipe) pour la solution.
        """
        team = [self.candidates[i] for i in solution]
        score_result = score_team(team, self.config)
        return score_result, team
    
    @classmethod
    def optimize_team(
        cls,
        team_size: int,
        candidates: Sequence[PlayerBuild],
        config: ScoringConfig,
        population_size: int = 200,
        generations: int = 40,
        random_seed: Optional[int] = None,
        **kwargs: Any
    ) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
        """Méthode utilitaire pour optimiser une équipe avec des paramètres par défaut.
        
        Args:
            team_size: Nombre de joueurs par équipe.
            candidates: Liste des builds candidats.
            config: Configuration du calcul des scores.
            population_size: Taille de la population. Défaut: 200.
            generations: Nombre de générations. Défaut: 40.
            random_seed: Graine aléatoire. Défaut: None.
            **kwargs: Arguments spécifiques à l'optimiseur.
            
        Returns:
            Liste des meilleures solutions trouvées.
        """
        optimizer = cls(
            team_size=team_size,
            candidates=candidates,
            config=config,
            population_size=population_size,
            generations=generations,
            random_seed=random_seed,
            **kwargs
        )
        return optimizer.optimize()
