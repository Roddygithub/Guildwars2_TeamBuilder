"""Package contenant les fonctionnalités de calcul de score pour les builds et compositions d'équipe GW2.

Ce package fournit des outils pour évaluer et noter les builds de personnages et les compositions d'équipe
en fonction de divers critères de performance et de synergie.
"""

from .engine import PlayerBuild, score_team
from .scorer import BuildScorer, BuildEvaluation
from .schema import ScoringConfig, TeamScoreResult
from .metrics import (
    MetricType, MetricResult,
    BaseMetric, AttributeScoreMetric, BoonUptimeMetric, ConditionDamageMetric
)

__all__ = [
    # Anciennes exportations
    'PlayerBuild',
    'ScoringConfig',
    'TeamScoreResult',
    'score_team',
    
    # Nouvelles exportations
    'BuildScorer',
    'BuildEvaluation',
    'MetricType',
    'MetricResult',
    'BaseMetric',
    'AttributeScoreMetric',
    'BoonUptimeMetric',
    'ConditionDamageMetric',
]
