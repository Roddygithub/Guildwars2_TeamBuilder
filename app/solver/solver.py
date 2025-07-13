"""Solveur de builds GW2 basé sur des contraintes."""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging
import random
from collections import defaultdict

from sqlalchemy.orm import Session
from constraint import Problem, AllDifferentConstraint, InSetConstraint

from app.game_mechanics import (
    RoleType, GameMode, BuffType, ConditionType, BoonType, 
    AttributeType, DamageType, SkillCategory
)
from app.models import (
    Profession, Specialization, Skill, Trait, 
    Weapon, Armor, Trinket, UpgradeComponent
)
from .constraints import BuildConstraint, ConstraintViolation, ConstraintViolationSeverity, BuildValidator

logger = logging.getLogger(__name__)

@dataclass
class BuildSolution:
    """Représente une solution de build générée par le solveur."""
    profession: Profession
    specializations: List[Specialization]
    skills: List[Skill]
    weapons: List[Weapon]
    armor: List[Armor]
    trinkets: List[Trinket]
    upgrades: List[UpgradeComponent]
    score: float = 0.0
    violations: List[ConstraintViolation] = None
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la solution en dictionnaire pour la sérialisation."""
        return {
            'profession': self.profession.to_dict() if self.profession else None,
            'specializations': [s.to_dict() for s in self.specializations],
            'skills': [s.to_dict() for s in self.skills],
            'weapons': [w.to_dict() for w in self.weapons],
            'armor': [a.to_dict() for a in self.armor],
            'trinkets': [t.to_dict() for t in self.trinkets],
            'upgrades': [u.to_dict() for u in self.upgrades],
            'score': self.score,
            'violations': [{
                'severity': v.severity.name,
                'message': v.message,
                'context': v.context
            } for v in self.violations]
        }

class BuildGenerator:
    """Générateur de builds GW2 basé sur un solveur de contraintes."""
    
    def __init__(
        self, 
        db: Session,
        profession: Profession,
        game_mode: GameMode = GameMode.PVE,
        role: RoleType = None,
        required_boons: List[BoonType] = None,
        required_conditions: List[ConditionType] = None,
        preferred_weapons: List[Weapon] = None,
        preferred_skills: List[Skill] = None,
        preferred_specializations: List[Specialization] = None,
        max_solutions: int = 10,
        max_iterations: int = 1000
    ):
        self.db = db
        self.profession = profession
        self.game_mode = game_mode
        self.role = role or self._determine_default_role()
        self.required_boons = required_boons or []
        self.required_conditions = required_conditions or []
        self.preferred_weapons = preferred_weapons or []
        self.preferred_skills = preferred_skills or []
        self.preferred_specializations = preferred_specializations or []
        self.max_solutions = max_solutions
        self.max_iterations = max_iterations
        
        # Initialiser le validateur avec les contraintes de base
        self.validator = self._create_validator()
        
        # Cache pour les données fréquemment utilisées
        self._available_weapons = None
        self._available_skills = None
        self._available_specializations = None
        self._available_armor = None
        self._available_trinkets = None
        self._available_upgrades = None
    
    def _determine_default_role(self) -> RoleType:
        """Détermine le rôle par défaut en fonction de la profession."""
        # TODO: Implémenter une logique plus sophistiquée basée sur la profession
        return RoleType.DPS
    
    def _create_validator(self) -> BuildValidator:
        """Crée un validateur avec les contraintes appropriées."""
        constraints = []
        
        # Contrainte de rôle si spécifié
        if self.role:
            constraints.append(RoleConstraint(required_role=self.role))
        
        # Contraintes de buffs et conditions si spécifiés
        if self.required_boons:
            constraints.append(BoonCoverageConstraint(required_boons=self.required_boons))
        
        if self.required_conditions:
            constraints.append(ConditionCoverageConstraint(required_conditions=self.required_conditions))
        
        # Contrainte de compétence avec les armes
        constraints.append(WeaponProficiencyConstraint())
        
        # Contraintes de statistiques minimales selon le rôle
        if self.role in [RoleType.HEALER, RoleType.SUPPORT, RoleType.BOON_SUPPORT]:
            constraints.append(AttributeThresholdConstraint(
                attribute=AttributeType.HEALING_POWER,
                min_value=1000
            ))
            constraints.append(AttributeThresholdConstraint(
                attribute=AttributeType.CONCENTRATION,
                min_value=800
            ))
        
        if self.role in [RoleType.DPS, RoleType.POWER, RoleType.CONDITION, RoleType.BOON_DPS]:
            if self.role in [RoleType.POWER, RoleType.DPS]:
                constraints.append(AttributeThresholdConstraint(
                    attribute=AttributeType.POWER,
                    min_value=2500
                ))
                constraints.append(AttributeThresholdConstraint(
                    attribute=AttributeType.FEROCITY,
                    min_value=800
                ))
            
            if self.role in [RoleType.CONDITION, RoleType.DPS]:
                constraints.append(AttributeThresholdConstraint(
                    attribute=AttributeType.CONDITION_DAMAGE,
                    min_value=1500
                ))
                constraints.append(AttributeThresholdConstraint(
                    attribute=AttributeType.EXPERTISE,
                    min_value=800
                ))
        
        return BuildValidator(constraints=constraints)
    
    async def generate_builds(self) -> List[BuildSolution]:
        """Génère des builds optimaux en fonction des contraintes."""
        # Charger les données nécessaires
        await self._load_required_data()
        
        solutions = []
        
        # Stratégie: Essayer d'abord les builds avec les préférences, puis élargir
        for iteration in range(self.max_iterations):
            if len(solutions) >= self.max_solutions:
                break
            
            # Générer un build aléatoire (pour l'instant, à améliorer avec un vrai solveur de contraintes)
            build = self._generate_random_build()
            
            # Valider le build
            violations = self.validator.validate(
                profession=build.profession,
                specializations=build.specializations,
                skills=build.skills,
                weapons=build.weapons,
                armor=build.armor,
                trinkets=build.trinkets,
                upgrades=build.upgrades,
                game_mode=self.game_mode
            )
            
            # Calculer un score basé sur les violations
            score = self._calculate_build_score(build, violations)
            build.score = score
            build.violations = violations
            
            # Ne garder que les builds avec un score acceptable
            if self._is_acceptable_build(build, violations):
                solutions.append(build)
        
        # Trier les solutions par score décroissant
        solutions.sort(key=lambda x: x.score, reverse=True)
        
        return solutions[:self.max_solutions]
    
    async def _load_required_data(self):
        """Charge les données nécessaires depuis la base de données."""
        # TODO: Implémenter le chargement des données depuis la base de données
        # avec mise en cache pour éviter les requêtes redondantes
        pass
    
    def _generate_random_build(self) -> BuildSolution:
        """Génère un build aléatoire (version simplifiée)."""
        # Sélectionner des spécialisations (2-3)
        num_specializations = random.randint(2, 3)
        specializations = random.sample(
            self._available_specializations or [],
            min(num_specializations, len(self._available_specializations or []))
        )
        
        # Sélectionner des armes (1-2 jeux)
        num_weapon_sets = random.randint(1, 2)
        weapons = random.sample(
            self._available_weapons or [],
            min(num_weapon_sets * 2, len(self._available_weapons or []))
        )
        
        # Sélectionner des compétences (1 soin, 3 utilitaires, 1 élite)
        heal_skills = [s for s in (self._available_skills or []) if s.category == SkillCategory.HEAL]
        utility_skills = [s for s in (self._available_skills or []) if s.category == SkillCategory.UTILITY]
        elite_skills = [s for s in (self._available_skills or []) if s.category == SkillCategory.ELITE]
        
        skills = []
        if heal_skills:
            skills.append(random.choice(heal_skills))
        
        skills.extend(random.sample(
            utility_skills,
            min(3, len(utility_skills))
        ))
        
        if elite_skills:
            skills.append(random.choice(elite_skills))
        
        # Sélectionner de l'équipement (simplifié)
        armor = random.sample(
            self._available_armor or [],
            min(6, len(self._available_armor or []))
        )
        
        trinkets = random.sample(
            self._available_trinkets or [],
            min(6, len(self._available_trinkets or []))
        )
        
        upgrades = random.sample(
            self._available_upgrades or [],
            min(6 + 2, len(self._available_upgrades or []))  # 6 runes + 2 cachets
        )
        
        return BuildSolution(
            profession=self.profession,
            specializations=specializations,
            skills=skills,
            weapons=weapons,
            armor=armor,
            trinkets=trinkets,
            upgrades=upgrades
        )
    
    def _calculate_build_score(self, build: BuildSolution, violations: List[ConstraintViolation]) -> float:
        """Calcule un score pour le build basé sur les violations de contraintes."""
        score = 100.0  # Score de base
        
        # Pénalités pour les violations
        for violation in violations:
            if violation.severity == ConstraintViolationSeverity.ERROR:
                score -= 50.0
            elif violation.severity == ConstraintViolationSeverity.WARNING:
                score -= 10.0
            else:  # INFO
                score -= 1.0
        
        # Bonus pour les préférences
        for weapon in build.weapons:
            if weapon in self.preferred_weapons:
                score += 5.0
        
        for skill in build.skills:
            if skill in self.preferred_skills:
                score += 3.0
        
        for spec in build.specializations:
            if spec in self.preferred_specializations:
                score += 7.0
        
        return max(0.0, score)  # Le score ne peut pas être négatif
    
    def _is_acceptable_build(self, build: BuildSolution, violations: List[ConstraintViolation]) -> bool:
        """Détermine si un build est acceptable en fonction de ses violations."""
        # Ne pas accepter de builds avec des erreurs critiques
        if any(v.severity == ConstraintViolationSeverity.ERROR for v in violations):
            return False
        
        # Pour l'instant, accepter tous les autres builds
        # (pourrait être étendu avec des critères plus stricts)
        return True
