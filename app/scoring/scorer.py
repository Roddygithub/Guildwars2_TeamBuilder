"""Système de scoring avancé pour les builds GW2.

Ce module fournit une classe BuildScorer qui permet d'évaluer des builds de personnages
en utilisant diverses métriques de performance et de synergie.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
import logging

from app.game_mechanics import (
    RoleType, GameMode, BuffType, ConditionType, BoonType, 
    AttributeType, DamageType, SkillCategory
)
from app.models import (
    Profession, Specialization, Skill, Trait, 
    Weapon, Armor, Trinket, UpgradeComponent
)

from .metrics import (
    BaseMetric, MetricType, MetricResult,
    AttributeScoreMetric, BoonUptimeMetric, ConditionDamageMetric
)

logger = logging.getLogger(__name__)

@dataclass
class BuildEvaluation:
    """Résultat de l'évaluation d'un build."""
    total_score: float = 0.0
    metric_results: Dict[MetricType, MetricResult] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'évaluation en dictionnaire pour la sérialisation."""
        return {
            "total_score": self.total_score,
            "metrics": {
                metric_type.value: {
                    "value": result.value,
                    "weight": result.weight,
                    "weighted_value": result.weighted_value,
                    "details": result.details
                }
                for metric_type, result in self.metric_results.items()
            },
            "details": self.details
        }

class BuildScorer:
    """Classe pour évaluer et noter les builds GW2.
    
    Cette classe utilise un ensemble de métriques pour évaluer la qualité et l'efficacité
d'un build de personnage selon différents critères (dégâts, survie, soutien, etc.).
    """
    
    def __init__(
        self,
        game_mode: GameMode = GameMode.PVE,
        role: Optional[RoleType] = None,
        custom_metrics: Optional[List[BaseMetric]] = None,
        default_metric_weights: Optional[Dict[MetricType, float]] = None
    ):
        """Initialise le système de scoring.
        
        Args:
            game_mode: Mode de jeu pour lequel évaluer les builds
            role: Rôle cible pour l'évaluation (influence le poids des métriques)
            custom_metrics: Liste personnalisée de métriques à utiliser
            default_metric_weights: Poids personnalisés pour les métriques par défaut
        """
        self.game_mode = game_mode
        self.role = role
        
        # Définir les poids par défaut des métriques selon le rôle
        self.default_metric_weights = self._get_default_weights(role)
        
        # Mettre à jour avec les poids personnalisés si fournis
        if default_metric_weights:
            self.default_metric_weights.update(default_metric_weights)
        
        # Initialiser les métriques
        self.metrics = self._initialize_metrics(custom_metrics)
    
    def _get_default_weights(self, role: Optional[RoleType]) -> Dict[MetricType, float]:
        """Définit les poids par défaut des métriques selon le rôle."""
        # Poids de base (neutres)
        weights = {
            MetricType.ATTRIBUTE_SCORE: 1.0,
            MetricType.BOON_UPTIME: 1.0,
            MetricType.CONDITION_DAMAGE: 1.0,
            MetricType.DIRECT_DAMAGE: 1.0,
            MetricType.HEALING_OUTPUT: 1.0,
            MetricType.SURVIVABILITY: 1.0,
            MetricType.BOON_SYNERGY: 0.8,
            MetricType.CONDITION_SYNERGY: 0.8,
            MetricType.COMBO_POTENTIAL: 0.6,
            MetricType.ROTATION_EFFICIENCY: 0.7,
            MetricType.TEAM_SYNERGY: 0.9,
            MetricType.EASE_OF_USE: 0.5,
            MetricType.FLEXIBILITY: 0.6,
            MetricType.CONSISTENCY: 0.7,
        }
        
        # Ajuster les poids selon le rôle
        if role == RoleType.DPS:
            weights.update({
                MetricType.DIRECT_DAMAGE: 2.0,
                MetricType.CONDITION_DAMAGE: 2.0,
                MetricType.ROTATION_EFFICIENCY: 1.0,
                MetricType.SURVIVABILITY: 0.5,
                MetricType.HEALING_OUTPUT: 0.2,
            })
        elif role == RoleType.HEALER:
            weights.update({
                MetricType.HEALING_OUTPUT: 2.5,
                MetricType.BOON_UPTIME: 2.0,
                MetricType.SURVIVABILITY: 1.5,
                MetricType.TEAM_SYNERGY: 1.5,
                MetricType.DIRECT_DAMAGE: 0.2,
                MetricType.CONDITION_DAMAGE: 0.1,
            })
        elif role == RoleType.SUPPORT:
            weights.update({
                MetricType.BOON_UPTIME: 2.5,
                MetricType.TEAM_SYNERGY: 2.0,
                MetricType.HEALING_OUTPUT: 1.5,
                MetricType.SURVIVABILITY: 1.2,
                MetricType.DIRECT_DAMAGE: 0.8,
                MetricType.CONDITION_DAMAGE: 0.5,
            })
        elif role == RoleType.TANK:
            weights.update({
                MetricType.SURVIVABILITY: 2.5,
                MetricType.BOON_UPTIME: 1.5,
                MetricType.TEAM_SYNERGY: 1.5,
                MetricType.HEALING_OUTPUT: 0.8,
                MetricType.DIRECT_DAMAGE: 0.5,
                MetricType.CONDITION_DAMAGE: 0.3,
            })
        
        return weights
    
    def _initialize_metrics(self, custom_metrics: Optional[List[BaseMetric]] = None) -> List[BaseMetric]:
        """Initialise les métriques à utiliser pour l'évaluation."""
        if custom_metrics:
            return custom_metrics
        
        # Utiliser les métriques par défaut avec les poids appropriés
        metrics = [
            AttributeScoreMetric(weight=self.default_metric_weights[MetricType.ATTRIBUTE_SCORE]),
            BoonUptimeMetric(weight=self.default_metric_weights[MetricType.BOON_UPTIME]),
            ConditionDamageMetric(weight=self.default_metric_weights[MetricType.CONDITION_DAMAGE]),
            # TODO: Ajouter d'autres métriques par défaut
        ]
        
        return metrics
    
    def evaluate_build(
        self,
        profession: Profession,
        specializations: List[Specialization],
        skills: List[Skill],
        weapons: List[Weapon],
        armor: List[Armor],
        trinkets: List[Trinket],
        upgrades: List[UpgradeComponent],
        context: Optional[Dict[str, Any]] = None
    ) -> BuildEvaluation:
        """Évalue un build complet et retourne un score détaillé.
        
        Args:
            profession: La profession du personnage
            specializations: Les spécialisations choisies (2-3)
            skills: Les compétences sélectionnées (soin, utilitaires, élite)
            weapons: Les armes équipées (1-2 jeux)
            armor: Les pièces d'armure équipées
            trinkets: Les bijoux équipés
            upgrades: Les améliorations (runes, cachets, etc.)
            context: Contexte supplémentaire pour l'évaluation
            
        Returns:
            Un objet BuildEvaluation contenant le score et les détails
        """
        evaluation = BuildEvaluation()
        context = context or {}
        
        # Évaluer le build avec chaque métrique
        for metric in self.metrics:
            try:
                result = metric.evaluate(
                    profession=profession,
                    specializations=specializations,
                    skills=skills,
                    weapons=weapons,
                    armor=armor,
                    trinkets=trinkets,
                    upgrades=upgrades,
                    game_mode=self.game_mode,
                    role=self.role,
                    **context
                )
                
                # Stocker le résultat
                evaluation.metric_results[metric.metric_type] = result
                evaluation.total_score += result.weighted_value
                
            except Exception as e:
                logger.error(
                    f"Erreur lors de l'évaluation avec la métrique {metric.__class__.__name__}: {e}",
                    exc_info=True
                )
        
        # Normaliser le score total (optionnel)
        evaluation.total_score = self._normalize_score(evaluation.total_score)
        
        # Ajouter des détails supplémentaires
        evaluation.details.update({
            "profession": profession.name,
            "specializations": [s.name for s in specializations],
            "role": self.role.value if self.role else "Aucun rôle spécifique",
            "game_mode": self.game_mode.value,
        })
        
        return evaluation
    
    def _normalize_score(self, raw_score: float) -> float:
        """Normalise le score brut dans une plage plus standard (0-1000)."""
        # Cette implémentation est un exemple et peut être ajustée
        # selon la distribution attendue des scores
        return min(1000.0, max(0.0, raw_score * 10))  # Ajuster le facteur selon les besoins
    
    def compare_builds(
        self, 
        build1: Dict[str, Any], 
        build2: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compare deux builds et retourne une analyse détaillée.
        
        Args:
            build1: Premier build à comparer (doit contenir les mêmes clés que les arguments de evaluate_build)
            build2: Deuxième build à comparer
            context: Contexte supplémentaire pour l'évaluation
            
        Returns:
            Un dictionnaire contenant les scores et une comparaison détaillée
        """
        # Évaluer les deux builds
        eval1 = self.evaluate_build(**build1, context=context)
        eval2 = self.evaluate_build(**build2, context=context)
        
        # Préparer la comparaison
        comparison = {
            "build1": {
                "score": eval1.total_score,
                "metrics": {k.value: v.weighted_value for k, v in eval1.metric_results.items()}
            },
            "build2": {
                "score": eval2.total_score,
                "metrics": {k.value: v.weighted_value for k, v in eval2.metric_results.items()}
            },
            "differences": {}
        }
        
        # Calculer les différences entre les métriques communes
        common_metrics = set(eval1.metric_results.keys()) & set(eval2.metric_results.keys())
        for metric in common_metrics:
            diff = eval1.metric_results[metric].weighted_value - eval2.metric_results[metric].weighted_value
            comparison["differences"][metric.value] = {
                "difference": diff,
                "build1_value": eval1.metric_results[metric].weighted_value,
                "build2_value": eval2.metric_results[metric].weighted_value,
                "metric_name": metric.value
            }
        
        # Déterminer le build gagnant
        if eval1.total_score > eval2.total_score + 10:  # Seuil pour éviter les égalités trop proches
            comparison["winner"] = "build1"
            comparison["winner_margin"] = eval1.total_score - eval2.total_score
        elif eval2.total_score > eval1.total_score + 10:
            comparison["winner"] = "build2"
            comparison["winner_margin"] = eval2.total_score - eval1.total_score
        else:
            comparison["winner"] = "tie"
            comparison["winner_margin"] = abs(eval1.total_score - eval2.total_score)
        
        return comparison
