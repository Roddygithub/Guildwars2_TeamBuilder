"""Package contenant les implémentations des algorithmes d'optimisation d'équipe."""

from .base_optimizer import BaseTeamOptimizer
from .simple import optimize_team as simple_optimize_team
from .genetic import optimize_team as genetic_optimize_team
from .pygad_optimizer import optimize_team as pygad_optimize_team

# Exporte la fonction d'optimisation par défaut (version simple)
optimize_team = simple_optimize_team

__all__ = [
    'BaseTeamOptimizer',
    'optimize_team',
    'simple_optimize_team',
    'genetic_optimize_team',
    'pygad_optimize_team'
]
