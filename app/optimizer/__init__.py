"""
Package contenant les implémentations des algorithmes d'optimisation d'équipe.

Ce module fournit une interface unifiée pour différents algorithmes d'optimisation
utilisés pour générer des équipes optimales dans Guild Wars 2.
"""

from .base_optimizer import BaseTeamOptimizer
from .simple import optimize_team as simple_optimize_team

# Les modules suivants sont désactivés car non utilisés dans l'approche actuelle :
# - genetic_optimizer
# - pygad_optimizer

# Exporte la fonction d'optimisation par défaut (version simple)
optimize_team = simple_optimize_team

__all__ = [
    'BaseTeamOptimizer',
    'optimize_team',
    'simple_optimize_team',
    # Modules désactivés :
    # 'genetic_optimize_team',
    # 'pygad_optimize_team'
]
