"""Métriques de base pour l'évaluation des builds GW2."""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum, auto
import math

from app.game_mechanics import (
    RoleType, GameMode, BuffType, ConditionType, BoonType, 
    AttributeType, DamageType, SkillCategory, ComboFieldType, ComboFinisherType
)
from app.models import (
    Profession, Specialization, Skill, Trait, 
    Weapon, Armor, Trinket, UpgradeComponent
)

class MetricType(Enum):
    """Types de métriques disponibles pour l'évaluation des builds."""
    # Métriques de base
    ATTRIBUTE_SCORE = "attribute_score"
    BOON_UPTIME = "boon_uptime"
    CONDITION_DAMAGE = "condition_damage"
    DIRECT_DAMAGE = "direct_damage"
    HEALING_OUTPUT = "healing_output"
    SURVIVABILITY = "survivability"
    
    # Métriques avancées
    BOON_SYNERGY = "boon_synergy"
    CONDITION_SYNERGY = "condition_synergy"
    COMBO_POTENTIAL = "combo_potential"
    ROTATION_EFFICIENCY = "rotation_efficiency"
    TEAM_SYNERGY = "team_synergy"
    
    # Métriques de qualité de vie
    EASE_OF_USE = "ease_of_use"
    FLEXIBILITY = "flexibility"
    CONSISTENCY = "consistency"

@dataclass
class MetricResult:
    """Résultat d'une métrique d'évaluation."""
    metric_type: MetricType
    value: float
    weight: float = 1.0
    details: Optional[Dict[str, Any]] = None
    
    @property
    def weighted_value(self) -> float:
        """Valeur pondérée de la métrique."""
        return self.value * self.weight

class BaseMetric:
    """Classe de base pour les métriques d'évaluation."""
    
    def __init__(self, weight: float = 1.0, **kwargs):
        self.weight = weight
        self.metric_type = MetricType(kwargs.get('metric_type', 'attribute_score'))
    
    def evaluate(
        self,
        profession: Profession,
        specializations: List[Specialization],
        skills: List[Skill],
        weapons: List[Weapon],
        armor: List[Armor],
        trinkets: List[Trinket],
        upgrades: List[UpgradeComponent],
        game_mode: GameMode = GameMode.PVE,
        role: Optional[RoleType] = None,
        **kwargs
    ) -> MetricResult:
        """Évalue la métrique pour un build donné."""
        raise NotImplementedError("La méthode evaluate doit être implémentée par les sous-classes")

class AttributeScoreMetric(BaseMetric):
    """Évalue le score d'attributs d'un build."""
    
    def __init__(self, **kwargs):
        super().__init__(metric_type=MetricType.ATTRIBUTE_SCORE, **kwargs)
        
    def evaluate(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE, role=None, **kwargs):
        # Calculer les attributs de base
        attributes = self._calculate_attributes(profession, specializations, weapons, armor, trinkets, upgrades)
        
        # Calculer un score global basé sur le rôle
        score = self._calculate_role_based_score(attributes, role)
        
        return MetricResult(
            metric_type=self.metric_type,
            value=score,
            weight=self.weight,
            details={"attributes": attributes}
        )
    
    def _calculate_attributes(self, profession, specializations, weapons, armor, trinkets, upgrades) -> Dict[AttributeType, int]:
        """Calcule les attributs totaux du build."""
        # TODO: Implémenter le calcul des attributs à partir de l'équipement, des runes, etc.
        attributes = {
            AttributeType.POWER: 1000,
            AttributeType.PRECISION: 1000,
            AttributeType.TOUGHNESS: 1000,
            AttributeType.VITALITY: 1000,
            AttributeType.CONCENTRATION: 0,
            AttributeType.CONDITION_DAMAGE: 0,
            AttributeType.EXPERTISE: 0,
            AttributeType.FEROCITY: 0,
            AttributeType.HEALING_POWER: 0,
        }
        
        # Appliquer les bonus des spécialisations
        for spec in specializations:
            # TODO: Ajouter les bonus d'attributs des traits sélectionnés
            pass
        
        # Appliquer les bonus de l'équipement
        for item in [*armor, *trinkets, *upgrades]:
            # TODO: Ajouter les attributs de l'équipement
            pass
        
        return attributes
    
    def _calculate_role_based_score(self, attributes: Dict[AttributeType, int], role: Optional[RoleType]) -> float:
        """Calcule un score basé sur les attributs et le rôle."""
        if role is None:
            # Si aucun rôle n'est spécifié, calculer un score équilibré
            return sum(attributes.values()) / len(attributes)
        
        # Poids des attributs par rôle
        role_weights = {
            RoleType.HEALER: {
                AttributeType.HEALING_POWER: 2.0,
                AttributeType.CONCENTRATION: 1.8,
                AttributeType.VITALITY: 1.2,
                AttributeType.TOUGHNESS: 1.0,
                AttributeType.POWER: 0.5,
                AttributeType.PRECISION: 0.3,
                AttributeType.FEROCITY: 0.2,
                AttributeType.CONDITION_DAMAGE: 0.1,
                AttributeType.EXPERTISE: 0.1,
            },
            RoleType.DPS: {
                AttributeType.POWER: 2.0,
                AttributeType.PRECISION: 1.8,
                AttributeType.FEROCITY: 1.6,
                AttributeType.CONDITION_DAMAGE: 1.4,
                AttributeType.EXPERTISE: 1.2,
                AttributeType.VITALITY: 0.8,
                AttributeType.TOUGHNESS: 0.5,
                AttributeType.HEALING_POWER: 0.1,
                AttributeType.CONCENTRATION: 0.1,
            },
            RoleType.SUPPORT: {
                AttributeType.CONCENTRATION: 2.0,
                AttributeType.HEALING_POWER: 1.8,
                AttributeType.VITALITY: 1.2,
                AttributeType.TOUGHNESS: 1.0,
                AttributeType.POWER: 0.6,
                AttributeType.PRECISION: 0.4,
                AttributeType.FEROCITY: 0.3,
                AttributeType.CONDITION_DAMAGE: 0.2,
                AttributeType.EXPERTISE: 0.2,
            },
            RoleType.TANK: {
                AttributeType.TOUGHNESS: 2.5,
                AttributeType.VITALITY: 2.0,
                AttributeType.HEALING_POWER: 1.0,
                AttributeType.CONCENTRATION: 0.8,
                AttributeType.POWER: 0.5,
                AttributeType.PRECISION: 0.3,
                AttributeType.FEROCITY: 0.2,
                AttributeType.CONDITION_DAMAGE: 0.1,
                AttributeType.EXPERTISE: 0.1,
            },
        }
        
        # Utiliser les poids du rôle spécifié (par défaut à DPS si non trouvé)
        weights = role_weights.get(role, role_weights[RoleType.DPS])
        
        # Calculer le score pondéré
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
            
        weighted_sum = sum(attributes[attr] * weight for attr, weight in weights.items())
        return weighted_sum / total_weight

class BoonUptimeMetric(BaseMetric):
    """Évalue la couverture des buffs (boons) d'un build."""
    
    def __init__(self, **kwargs):
        super().__init__(metric_type=MetricType.BOON_UPTIME, **kwargs)
    
    def evaluate(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE, role=None, **kwargs):
        # Analyser les sources de buffs dans le build
        boon_sources = self._analyze_boon_sources(profession, specializations, skills, weapons)
        
        # Estimer le taux de couverture pour chaque buff important
        boon_uptimes = self._estimate_boon_uptimes(boon_sources, role)
        
        # Calculer un score global de couverture des buffs
        avg_uptime = sum(boon_uptimes.values()) / len(boon_uptimes) if boon_uptimes else 0.0
        
        return MetricResult(
            metric_type=self.metric_type,
            value=avg_uptime,
            weight=self.weight,
            details={"boon_uptimes": boon_uptimes}
        )
    
    def _analyze_boon_sources(self, profession, specializations, skills, weapons) -> Dict[BoonType, List[Dict]]:
        """Analyse les sources de buffs dans le build."""
        boon_sources = {boon: [] for boon in BoonType}
        
        # Analyser les compétences
        for skill in skills:
            # TODO: Extraire les buffs appliqués par la compétence
            # Cela nécessite d'analyser les 'facts' de l'API GW2
            pass
        
        # Analyser les traits
        for spec in specializations:
            # TODO: Extraire les buffs fournis par les traits
            pass
        
        # Analyser les armes
        for weapon in weapons:
            # TODO: Extraire les buffs liés aux compétences d'arme
            pass
        
        return boon_sources
    
    def _estimate_boon_uptimes(self, boon_sources: Dict[BoonType, List[Dict]], role: Optional[RoleType]) -> Dict[BoonType, float]:
        """Estime les taux de couverture des buffs."""
        # Buffs importants à évaluer (avec priorités selon le rôle)
        important_boons = {
            BoonType.QUICKNESS: 1.0,
            BoonType.ALACRITY: 1.0,
            BoonType.MIGHT: 0.8,
            BoonType.FURY: 0.8,
            BoonType.PROTECTION: 0.7,
            BoonType.REGENERATION: 0.6,
            BoonType.SWIFTNESS: 0.4,
            BoonType.VIGOR: 0.4,
            BoonType.AEGIS: 0.3,
            BoonType.STABILITY: 0.3,
        }
        
        # Ajuster les priorités selon le rôle
        if role in [RoleType.HEALER, RoleType.SUPPORT, RoleType.BOON_SUPPORT]:
            for boon in important_boons:
                important_boons[boon] *= 1.5  # Les buffs sont plus importants pour les rôles de soutien
        
        # Estimer les taux de couverture
        uptimes = {}
        for boon, sources in boon_sources.items():
            if not sources:
                uptimes[boon] = 0.0
                continue
            
            # Estimation simplifiée : plus il y a de sources, meilleure est la couverture
            # (à affiner avec une analyse plus poussée des temps de recharge, etc.)
            source_count = len(sources)
            uptime = min(1.0, 0.2 * source_count)  # Jusqu'à 100% avec 5 sources
            uptimes[boon] = uptime * important_boons.get(boon, 0.5)
        
        return uptimes

class ConditionDamageMetric(BaseMetric):
    """Évalue le potentiel de dégâts de conditions d'un build."""
    
    def __init__(self, **kwargs):
        super().__init__(metric_type=MetricType.CONDITION_DAMAGE, **kwargs)
    
    def evaluate(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE, role=None, **kwargs):
        # Vérifier si le build est orienté dégâts de conditions
        if not self._is_condition_build(specializations, skills, weapons):
            return MetricResult(
                metric_type=self.metric_type,
                value=0.0,
                weight=0.0,  # Pas de pénalité pour les builds non-condition
                details={"is_condition_build": False}
            )
        
        # Analyser les types de conditions appliqués
        condition_types = self._analyze_condition_types(skills, weapons, specializations)
        
        # Estimer le DPS des conditions
        condition_dps = self._estimate_condition_dps(condition_types, specializations, trinkets, upgrades)
        
        return MetricResult(
            metric_type=self.metric_type,
            value=condition_dps,
            weight=self.weight,
            details={
                "is_condition_build": True,
                "condition_types": {c.name: v for c, v in condition_types.items()},
                "estimated_dps": condition_dps
            }
        )
    
    def _is_condition_build(self, specializations, skills, weapons) -> bool:
        """Détermine si le build est orienté dégâts de conditions."""
        # Vérifier les spécialisations pour des traits améliorant les conditions
        for spec in specializations:
            # TODO: Vérifier si la spécialisation contient des traits de condition
            pass
        
        # Vérifier les compétences pour des applications de conditions
        for skill in skills:
            # TODO: Vérifier si la compétence applique des conditions
            pass
        
        # Vérifier les armes pour des compétences de condition
        for weapon in weapons:
            # TODO: Vérifier si l'arme est typiquement utilisée pour les builds condition
            pass
        
        # Par défaut, supposer que ce n'est pas un build condition
        return False
    
    def _analyze_condition_types(self, skills, weapons, specializations) -> Dict[ConditionType, float]:
        """Analyse les types de conditions appliqués par le build."""
        condition_stacks = {cond: 0.0 for cond in ConditionType}
        
        # Analyser les compétences
        for skill in skills:
            # TODO: Extraire les conditions appliquées par la compétence
            # et estimer le nombre de stacks par seconde
            pass
        
        # Analyser les armes
        for weapon in weapons:
            # TODO: Extraire les conditions appliquées par les compétences d'arme
            pass
        
        # Analyser les traits de spécialisation
        for spec in specializations:
            # TODO: Ajouter les bonus de condition des traits
            pass
        
        return {k: v for k, v in condition_stacks.items() if v > 0}
    
    def _estimate_condition_dps(self, condition_types: Dict[ConditionType, float], specializations, trinkets, upgrades) -> float:
        """Estime le DPS des conditions appliquées."""
        # Dégâts de base par type de condition (par stack par seconde)
        base_damage = {
            ConditionType.BLEEDING: 110,
            ConditionType.BURNING: 400,
            ConditionType.CONFUSION: 200,  # Varie selon l'activité de la cible
            ConditionType.POISON: 100,
            ConditionType.TORMENT: 220,  # Plus élevé si la cible bouge
        }
        
        # Calculer le DPS total
        total_dps = 0.0
        for cond, stacks in condition_types.items():
            if cond in base_damage:
                # Ajuster les dégâts en fonction des attributs (Condition Damage, Expertise)
                # TODO: Prendre en compte les attributs du personnage
                damage_multiplier = 1.0
                total_dps += base_damage[cond] * stacks * damage_multiplier
        
        return total_dps
