"""Package pour la génération de builds GW2 basée sur des contraintes.

Ce package contient les classes et fonctions pour générer des builds optimaux
en utilisant un solveur de contraintes et un système de scoring avancé.
"""

from .constraints import (
    BuildConstraint, ConstraintViolation, ConstraintViolationSeverity,
    RoleConstraint, BoonCoverageConstraint, ConditionCoverageConstraint,
    WeaponProficiencyConstraint, AttributeThresholdConstraint, BuildValidator
)
from .solver import BuildGenerator, BuildSolution

__all__ = [
    # Classes principales
    'BuildGenerator', 'BuildSolution',
    
    # Contraintes
    'BuildConstraint', 'ConstraintViolation', 'ConstraintViolationSeverity',
    'RoleConstraint', 'BoonCoverageConstraint', 'ConditionCoverageConstraint',
    'WeaponProficiencyConstraint', 'AttributeThresholdConstraint', 'BuildValidator',
]
