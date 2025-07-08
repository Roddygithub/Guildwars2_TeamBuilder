"""Optimiseur d'équipes utilisant un algorithme génétique avec PyGAD.

Ce module implémente un algorithme génétique pour trouver des compositions d'équipe
optimales à partir d'un ensemble de builds candidats. Il utilise la bibliothèque
PyGAD (Python Genetic Algorithm) qui offre une interface simple et efficace pour
l'implémentation d'algorithmes génétiques.

Exemple d'utilisation:
    ```python
    config = ScoringConfig(...)
    candidates = [...]  # Liste de PlayerBuild
    
    # Créer et exécuter l'optimiseur
    optimizer = PyGADOptimizer(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=200,
        generations=50
    )
    best_teams = optimizer.optimize()
    
    # Ou utiliser la méthode utilitaire
    best_teams = optimize_team(
        team_size=5,
        candidates=candidates,
        config=config
    )
    ```
"""
from __future__ import annotations

from typing import List, Sequence, Tuple, Optional, Dict, Any, cast
import numpy as np
import pygad

from app.optimizer.base_optimizer import BaseTeamOptimizer
from app.scoring.engine import PlayerBuild, score_team
from app.scoring.schema import ScoringConfig, TeamScoreResult

# Type pour la configuration spécifique à PyGAD
PyGADConfig = Dict[str, Any]


class PyGADOptimizer(BaseTeamOptimizer[PyGADConfig]):
    """Optimiseur d'équipe utilisant l'algorithme génétique PyGAD.
    
    Cet optimiseur utilise la bibliothèque PyGAD pour implémenter un algorithme
    génétique avec sélection par tournoi, croisement à deux points et mutation uniforme.
    """
    
    def _init_optimizer_config(self, **kwargs: Any) -> PyGADConfig:
        """Initialise la configuration spécifique à PyGAD.
        
        Args:
            **kwargs: Arguments de configuration pour PyGAD.
                - crossover_probability: Probabilité de croisement (défaut: 0.8).
                - mutation_probability: Probabilité de mutation (défaut: 0.2).
                - num_parents_mating: Nombre de parents pour la reproduction (défaut: population_size//2).
                - keep_elitism: Nombre de meilleures solutions à conserver (défaut: 1).
                
        Returns:
            Un dictionnaire de configuration pour PyGAD.
            
        Raises:
            ValueError: Si les probabilités ne sont pas dans [0, 1].
        """
        config: PyGADConfig = {
            'crossover_probability': kwargs.pop('crossover_probability', 0.8),
            'mutation_probability': kwargs.pop('mutation_probability', 0.2),
            'num_parents_mating': kwargs.pop('num_parents_mating', self.population_size // 2),
            'keep_elitism': kwargs.pop('keep_elitism', 1),
        }
        
        # Validation des probabilités
        if not 0 <= config['crossover_probability'] <= 1 or not 0 <= config['mutation_probability'] <= 1:
            raise ValueError("Les probabilités doivent être entre 0 et 1")
            
        return config
    
    def _fitness_func(self, ga_instance: pygad.GA, solution: np.ndarray, solution_idx: int) -> float:
        """Fonction de fitness pour PyGAD.
        
        Args:
            ga_instance: Instance de l'algorithme génétique PyGAD.
            solution: Solution encodée (indices des candidats).
            solution_idx: Index de la solution dans la population.
            
        Returns:
            Le score de fitness de la solution.
        """
        # Conversion des indices en entiers et évaluation de l'équipe
        team_indices = solution.astype(int)
        return self._evaluate_team(team_indices)
    
    def optimize(self) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
        """Exécute l'optimisation et retourne les meilleures solutions.
        
        Returns:
            Une liste de tuples (score, équipe) triée par score décroissant.
        """
        # Configuration de PyGAD
        ga_instance = pygad.GA(
            num_generations=self.generations,
            num_parents_mating=self.optimizer_config['num_parents_mating'],
            fitness_func=self._fitness_func,
            sol_per_pop=self.population_size,
            num_genes=self.team_size,
            gene_space=range(len(self.candidates)),
            gene_type=int,
            keep_elitism=self.optimizer_config['keep_elitism'],
            crossover_probability=self.optimizer_config['crossover_probability'],
            mutation_probability=self.optimizer_config['mutation_probability'],
            random_seed=self.random_seed,
            suppress_warnings=True,
            save_solutions=False,
        )
        
        # Exécution de l'algorithme génétique
        ga_instance.run()
        
        # Récupération des meilleures solutions
        num_results = self.optimizer_config['keep_elitism'] * 2 or 5
        best_solutions = ga_instance.best_solutions(num_results)
        
        # Conversion des solutions en résultats
        results = []
        for solution, _, _ in best_solutions:
            team_indices = solution.astype(int)
            results.append(self._decode_solution(team_indices))
        
        # Tri par score décroissant et élimination des doublons
        unique_results = {tuple(sorted(p[1], key=id)): p for p in results}.values()
        sorted_results = sorted(unique_results, key=lambda x: x[0].total_score, reverse=True)
        
        return list(sorted_results)


def optimize_team(
    team_size: int,
    candidates: Sequence[PlayerBuild],
    config: ScoringConfig,
    population_size: int = 200,
    generations: int = 40,
    random_seed: Optional[int] = None,
) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
    """Optimise la composition d'équipe avec des paramètres par défaut raisonnables.
    
    Cette fonction est un wrapper pratique autour de `optimize_genetic` avec des valeurs
    par défaut adaptées à la plupart des cas d'utilisation.
    
    Args:
        team_size: Nombre de joueurs par équipe.
        candidates: Liste des builds candidats parmi lesquels sélectionner.
        config: Configuration du calcul des scores.
        population_size: Taille de la population à chaque génération. Défaut: 200.
        generations: Nombre de générations à exécuter. Défaut: 40.
        random_seed: Graine pour le générateur de nombres aléatoires. Défaut: None.
        
    Returns:
        Une liste de tuples (score, équipe) triée par score décroissant.
        
    Example:
        >>> config = ScoringConfig(...)
        >>> candidates = [...]  # Liste de PlayerBuild
        >>> 
        >>> # Utilisation avec les paramètres par défaut
        >>> best_teams = optimize_team(
        ...     team_size=5,
        ...     candidates=candidates,
        ...     config=config
        ... )
    """
    optimizer = PyGADOptimizer(
        team_size=team_size,
        candidates=candidates,
        config=config,
        population_size=population_size,
        generations=generations,
        random_seed=random_seed,
    )
    return optimizer.optimize()


# Export des symboles du module
__all__ = ['PyGADOptimizer', 'optimize_team']

# Alias de la fonction au niveau du module pour une utilisation directe
optimize_team = PyGADOptimizer.optimize_team
