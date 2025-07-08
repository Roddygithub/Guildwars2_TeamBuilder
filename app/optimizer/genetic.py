"""Optimiseur d'équipes utilisant un algorithme génétique avec DEAP.

Ce module implémente un algorithme génétique pour trouver des compositions d'équipe
optimales à partir d'un ensemble de builds candidats. Il utilise la bibliothèque
DEAP (Distributed Evolutionary Algorithms in Python) pour l'implémentation des
opérateurs génétiques (sélection, croisement, mutation).

Exemple d'utilisation:
    ```python
    config = ScoringConfig(...)
    candidates = [...]  # Liste de PlayerBuild
    
    # Créer et exécuter l'optimiseur
    optimizer = DEAPOptimizer(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=200,
        generations=50
    )
    best_teams = optimizer.optimize()
    
    # Ou utiliser la méthode utilitaire
    best_teams = DEAPOptimizer.optimize_team(
        team_size=5,
        candidates=candidates,
        config=config
    )
    ```
"""
from __future__ import annotations

import random
from typing import List, Sequence, Tuple, Any, Dict, TypeVar, cast

from deap import base, creator, tools

from app.optimizer.base_optimizer import BaseTeamOptimizer
from app.scoring.engine import PlayerBuild, score_team
from app.scoring.schema import ScoringConfig, TeamScoreResult

# Création des types DEAP (uniquement s'ils n'existent pas déjà)
try:
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
except RuntimeError:
    # Les types existent déjà
    pass

# Type pour la configuration spécifique à DEAP
DEAPConfig = Dict[str, Any]


class DEAPOptimizer(BaseTeamOptimizer[DEAPConfig]):
    """Optimiseur d'équipe utilisant l'algorithme génétique DEAP.
    
    Cet optimiseur utilise la bibliothèque DEAP pour implémenter un algorithme
    génétique avec sélection par tournoi, croisement à deux points et mutation uniforme.
    """
    
    def _init_optimizer_config(self, **kwargs: Any) -> DEAPConfig:
        """Initialise la configuration spécifique à DEAP.
        
        Args:
            **kwargs: Arguments de configuration pour DEAP.
                - cx_pb: Probabilité de croisement (défaut: 0.8).
                - mut_pb: Probabilité de mutation (défaut: 0.2).
                - tournsize: Taille du tournoi pour la sélection (défaut: 3).
                
        Returns:
            Un dictionnaire de configuration pour DEAP.
            
        Raises:
            ValueError: Si les probabilités ne sont pas dans [0, 1].
        """
        config: DEAPConfig = {
            'cx_pb': kwargs.pop('cx_pb', 0.8),
            'mut_pb': kwargs.pop('mut_pb', 0.2),
            'tournsize': kwargs.pop('tournsize', 3),
        }
        
        # Validation des probabilités
        if not 0 <= config['cx_pb'] <= 1 or not 0 <= config['mut_pb'] <= 1:
            raise ValueError("Les probabilités doivent être entre 0 et 1")
            
        return config
    
    def _make_toolbox(self, rand: random.Random) -> base.Toolbox:
        """Crée et configure une boîte à outils DEAP.
        
        Args:
            rand: Générateur de nombres aléatoires.
            
        Returns:
            Une instance de `deap.base.Toolbox` configurée.
        """
        toolbox = base.Toolbox()

        # Attribut : index aléatoire dans la liste des candidats
        toolbox.register("attr_idx", rand.randrange, len(self.candidates))

        # Individu : liste d'indices (peut contenir des doublons -> pénalisés)
        toolbox.register(
            "individual", 
            tools.initRepeat, 
            creator.Individual, 
            toolbox.attr_idx, 
            n=self.team_size
        )
        
        # Population : liste d'individus
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        # Configuration des opérateurs génétiques
        toolbox.register("evaluate", self._evaluate_individual)
        toolbox.register("mate", tools.cxTwoPoint)  # Croisement à deux points
        
        # Mutation uniforme d'entiers
        toolbox.register(
            "mutate", 
            tools.mutUniformInt, 
            low=0, 
            up=len(self.candidates) - 1, 
            indpb=1.0 / self.team_size  # Probabilité de mutation par gène
        )
        
        # Sélection par tournoi
        toolbox.register("select", tools.selTournament, 
                        tournsize=self.optimizer_config['tournsize'])
        
        return toolbox
    
    def _evaluate_individual(self, individual: Sequence[int]) -> Tuple[float]:
        """Évalue un individu en calculant le score de l'équipe correspondante.
        
        Args:
            individual: Un individu (liste d'indices pointant vers des candidats).
            
        Returns:
            Un tuple contenant le score total de l'équipe (pour compatibilité DEAP).
        """
        return (self._evaluate_team(individual),)
    
    def optimize(self) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
        """Exécute l'optimisation et retourne les meilleures solutions.
        
        Returns:
            Une liste de tuples (score, équipe) triée par score décroissant.
        """
        # Initialisation du générateur aléatoire
        rand = random.Random(self.random_seed)
        
        # Création de la boîte à outils DEAP
        toolbox = self._make_toolbox(rand)
        cx_pb = self.optimizer_config['cx_pb']
        mut_pb = self.optimizer_config['mut_pb']
        
        # Création de la population initiale
        population = toolbox.population(n=self.population_size)
        
        # Évaluation de la population initiale
        fitnesses = list(map(toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        
        # Évolution de la population
        for gen in range(self.generations):
            # Sélection des parents
            offspring = toolbox.select(population, len(population))
            
            # Clonage des individus sélectionnés
            offspring = list(map(toolbox.clone, offspring))
            
            # Application des opérateurs génétiques
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                # Croisement
                if rand.random() < cx_pb:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
            
            for mutant in offspring:
                # Mutation
                if rand.random() < mut_pb:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
            
            # Évaluation des nouveaux individus
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # Remplacement de la population
            population[:] = offspring
        
        # Récupération des meilleures solutions
        best_individuals = tools.selBest(population, k=min(10, self.population_size))
        
        # Conversion des solutions en résultats
        results = [self._decode_solution(ind) for ind in best_individuals]
        
        # Tri par score décroissant
        results.sort(key=lambda x: x[0].total_score, reverse=True)
        
        return results

    @classmethod
    def optimize_team(
        cls,
        team_size: int,
        candidates: Sequence[PlayerBuild],
        config: ScoringConfig,
        population_size: int = 200,
        generations: int = 50,
        top_n: int = 10,
        random_seed: int | None = None,
        **kwargs: Any
    ) -> List[Tuple[TeamScoreResult, List[PlayerBuild]]]:
        """Méthode utilitaire pour optimiser une équipe en une seule étape.
        
        Args:
            team_size: Taille de l'équipe à former.
            candidates: Liste des builds candidats.
            config: Configuration du calcul des scores.
            population_size: Taille de la population pour l'algorithme génétique.
            generations: Nombre de générations à exécuter.
            top_n: Nombre de meilleures équipes à retourner.
            random_seed: Graine aléatoire pour la reproductibilité.
            **kwargs: Arguments supplémentaires pour la configuration de l'optimiseur.
            
        Returns:
            Une liste de tuples (score, équipe) triée par score décroissant.
        """
        optimizer = cls(
            team_size=team_size,
            candidates=candidates,
            config=config,
            population_size=population_size,
            generations=generations,
            top_n=top_n,
            random_seed=random_seed,
            **kwargs
        )
        return optimizer.optimize()


# Export des symboles du module
__all__ = ['DEAPOptimizer', 'optimize_team']

# Alias de la méthode de classe au niveau du module pour une utilisation directe
optimize_team = DEAPOptimizer.optimize_team
