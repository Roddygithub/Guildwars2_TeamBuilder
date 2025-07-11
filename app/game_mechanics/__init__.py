"""Package pour la modélisation des mécaniques de jeu GW2.

Ce package contient les classes et fonctions pour modéliser les interactions entre
différents éléments du jeu comme les compétences, les traits, l'équipement, etc.
"""

from .constants import (
    BuffType, ConditionType, BoonType, RoleType, GameMode,
    AttributeType, DamageType, ComboFieldType, ComboFinisherType, SkillCategory
)
from .interactions import InteractionEffect, InteractionAnalyzer, ComboAnalyzer

__all__ = [
    # Constantes
    'BuffType', 'ConditionType', 'BoonType', 'RoleType', 'GameMode',
    'AttributeType', 'DamageType', 'ComboFieldType', 'ComboFinisherType', 'SkillCategory',
    
    # Classes principales
    'InteractionEffect', 'InteractionAnalyzer', 'ComboAnalyzer',
]
