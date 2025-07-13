"""Contraintes pour le générateur de builds GW2."""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum, auto
import logging

from app.game_mechanics import (
    RoleType, GameMode, BuffType, ConditionType, BoonType, 
    AttributeType, DamageType, SkillCategory
)
from app.models import (
    Profession, Specialization, Skill, Trait, 
    Weapon, Armor, Trinket, UpgradeComponent
)

logger = logging.getLogger(__name__)

class ConstraintViolationSeverity(Enum):
    """Niveaux de sévérité pour les violations de contraintes."""
    ERROR = auto()    # Le build est invalide
    WARNING = auto()  # Le build est valide mais sous-optimal
    INFO = auto()     # Information sur des choix de build

@dataclass
class ConstraintViolation:
    """Représente une violation de contrainte dans un build."""
    severity: ConstraintViolationSeverity
    message: str
    context: Optional[Dict[str, Any]] = None

class BuildConstraint:
    """Classe de base pour les contraintes de build."""
    
    def __init__(self, weight: float = 1.0):
        self.weight = weight
    
    def check(
        self, 
        profession: Profession,
        specializations: List[Specialization],
        skills: List[Skill],
        weapons: List[Weapon],
        armor: List[Armor],
        trinkets: List[Trinket],
        upgrades: List[UpgradeComponent],
        game_mode: GameMode = GameMode.PVE
    ) -> List[ConstraintViolation]:
        """Vérifie si la contrainte est respectée.
        
        Retourne une liste de violations (vide si la contrainte est respectée).
        """
        raise NotImplementedError

class RoleConstraint(BuildConstraint):
    """Contrainte pour s'assurer que le build correspond au rôle souhaité."""
    
    def __init__(self, required_role: RoleType, **kwargs):
        super().__init__(**kwargs)
        self.required_role = required_role
    
    def check(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE):
        # TODO: Implémenter la logique de vérification du rôle
        # Vérifier les spécialisations, compétences, armes, etc. pour déterminer le rôle
        return []

class BoonCoverageConstraint(BuildConstraint):
    """Contrainte pour s'assurer que les buffs nécessaires sont couverts."""
    
    def __init__(self, required_boons: List[BoonType], **kwargs):
        super().__init__(**kwargs)
        self.required_boons = set(boon for boon in required_boons)
    
    def check(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE):
        # TODO: Analyser les compétences, traits, etc. pour déterminer quels buffs sont fournis
        provided_boons = set()
        
        violations = []
        missing_boons = self.required_boons - provided_boons
        
        if missing_boons:
            violations.append(ConstraintViolation(
                severity=ConstraintViolationSeverity.ERROR,
                message=f"Buffs manquants: {', '.join(boon.value for boon in missing_boons)}",
                context={"missing_boons": missing_boons}
            ))
        
        return violations

class ConditionCoverageConstraint(BuildConstraint):
    """Contrainte pour s'assurer que les conditions nécessaires sont couvertes."""
    
    def __init__(self, required_conditions: List[ConditionType], **kwargs):
        super().__init__(**kwargs)
        self.required_conditions = set(cond for cond in required_conditions)
    
    def check(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE):
        # TODO: Analyser les compétences, armes, etc. pour déterminer quelles conditions sont appliquées
        provided_conditions = set()
        
        violations = []
        missing_conditions = self.required_conditions - provided_conditions
        
        if missing_conditions:
            violations.append(ConstraintViolation(
                severity=ConstraintViolationSeverity.WARNING,
                message=f"Conditions manquantes: {', '.join(cond.value for cond in missing_conditions)}",
                context={"missing_conditions": missing_conditions}
            ))
        
        return violations

class WeaponProficiencyConstraint(BuildConstraint):
    """Contrainte pour s'assurer que les armes sont utilisables par la profession."""
    
    def check(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE):
        violations = []
        
        for weapon in weapons:
            if weapon not in profession.weapons:
                violations.append(ConstraintViolation(
                    severity=ConstraintViolationSeverity.ERROR,
                    message=f"L'arme {weapon.name} n'est pas utilisable par {profession.name}",
                    context={"weapon_id": weapon.id, "profession_id": profession.id}
                ))
        
        return violations

class AttributeThresholdConstraint(BuildConstraint):
    """Contrainte pour s'assurer que les seuils d'attributs sont atteints."""
    
    def __init__(self, attribute: AttributeType, min_value: int, **kwargs):
        super().__init__(**kwargs)
        self.attribute = attribute
        self.min_value = min_value
    
    def check(self, profession, specializations, skills, weapons, armor, trinkets, upgrades, game_mode=GameMode.PVE):
        # TODO: Calculer la valeur de l'attribut à partir de l'équipement, des runes, etc.
        attribute_value = 0
        
        if attribute_value < self.min_value:
            return [ConstraintViolation(
                severity=ConstraintViolationSeverity.WARNING,
                message=f"Valeur d'attribut {self.attribute.value} trop basse: {attribute_value} < {self.min_value}",
                context={
                    "attribute": self.attribute,
                    "current_value": attribute_value,
                    "required_value": self.min_value
                }
            )]
        
        return []

class BuildValidator:
    """Valide un build par rapport à un ensemble de contraintes."""
    
    def __init__(self, constraints: List[BuildConstraint]):
        self.constraints = constraints
    
    def validate(
        self,
        profession: Profession,
        specializations: List[Specialization],
        skills: List[Skill],
        weapons: List[Weapon],
        armor: List[Armor],
        trinkets: List[Trinket],
        upgrades: List[UpgradeComponent],
        game_mode: GameMode = GameMode.PVE
    ) -> List[ConstraintViolation]:
        """Valide un build par rapport aux contraintes définies."""
        violations = []
        
        for constraint in self.constraints:
            try:
                constraint_violations = constraint.check(
                    profession=profession,
                    specializations=specializations,
                    skills=skills,
                    weapons=weapons,
                    armor=armor,
                    trinkets=trinkets,
                    upgrades=upgrades,
                    game_mode=game_mode
                )
                violations.extend(constraint_violations)
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de la contrainte {constraint.__class__.__name__}: {e}")
                violations.append(ConstraintViolation(
                    severity=ConstraintViolationSeverity.ERROR,
                    message=f"Erreur lors de la vérification de la contrainte: {e}",
                    context={"constraint": constraint.__class__.__name__, "error": str(e)}
                ))
        
        return violations
