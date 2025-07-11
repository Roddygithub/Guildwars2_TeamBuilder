"""Gestion des interactions entre les compétences, traits et mécaniques de jeu GW2."""

from typing import Dict, List, Optional, Set, Tuple, Union
from enum import Enum
import math

from .constants import (
    BuffType, ConditionType, BoonType, RoleType, GameMode, 
    AttributeType, DamageType, ComboFieldType, ComboFinisherType, SkillCategory
)
from app.models import Skill, Trait, Weapon, Armor, Trinket, UpgradeComponent

class InteractionEffect:
    """Représente un effet d'interaction entre des compétences, traits ou équipements."""
    
    def __init__(
        self,
        source_type: str,  # 'skill', 'trait', 'weapon', 'armor', 'trinket', 'upgrade'
        source_id: int,
        effect_type: str,
        effect_value: Union[float, int, str, dict],
        conditions: Optional[List[dict]] = None,
        target: str = 'self',  # 'self', 'ally', 'enemy', 'area', 'combo'
        duration: Optional[float] = None,
        stacks: Optional[int] = None,
        radius: Optional[float] = None,
        combo_field: Optional[ComboFieldType] = None,
        combo_finisher: Optional[ComboFinisherType] = None,
        description: Optional[str] = None
    ):
        self.source_type = source_type
        self.source_id = source_id
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.conditions = conditions or []
        self.target = target
        self.duration = duration
        self.stacks = stacks
        self.radius = radius
        self.combo_field = combo_field
        self.combo_finisher = combo_finisher
        self.description = description
    
    def to_dict(self) -> dict:
        """Convertit l'effet en dictionnaire pour la sérialisation."""
        return {
            'source_type': self.source_type,
            'source_id': self.source_id,
            'effect_type': self.effect_type,
            'effect_value': self.effect_value,
            'conditions': self.conditions,
            'target': self.target,
            'duration': self.duration,
            'stacks': self.stacks,
            'radius': self.radius,
            'combo_field': self.combo_field.value if self.combo_field else None,
            'combo_finisher': self.combo_finisher.value if self.combo_finisher else None,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'InteractionEffect':
        """Crée un effet à partir d'un dictionnaire."""
        return cls(
            source_type=data['source_type'],
            source_id=data['source_id'],
            effect_type=data['effect_type'],
            effect_value=data['effect_value'],
            conditions=data.get('conditions', []),
            target=data.get('target', 'self'),
            duration=data.get('duration'),
            stacks=data.get('stacks'),
            radius=data.get('radius'),
            combo_field=ComboFieldType(data['combo_field']) if data.get('combo_field') else None,
            combo_finisher=ComboFinisherType(data['combo_finisher']) if data.get('combo_finisher') else None,
            description=data.get('description')
        )

class InteractionAnalyzer:
    """Analyse les interactions entre les compétences, traits et équipements."""
    
    def __init__(self, game_mode: GameMode = GameMode.PVE):
        self.game_mode = game_mode
        self.effects_cache: Dict[Tuple[str, int], List[InteractionEffect]] = {}
    
    def add_effect(self, effect: InteractionEffect) -> None:
        """Ajoute un effet d'interaction au cache."""
        key = (effect.source_type, effect.source_id)
        if key not in self.effects_cache:
            self.effects_cache[key] = []
        self.effects_cache[key].append(effect)
    
    def get_effects_for_skill(self, skill_id: int) -> List[InteractionEffect]:
        """Récupère tous les effets liés à une compétence."""
        return self.effects_cache.get(('skill', skill_id), [])
    
    def get_effects_for_trait(self, trait_id: int) -> List[InteractionEffect]:
        """Récupère tous les effets liés à un trait."""
        return self.effects_cache.get(('trait', trait_id), [])
    
    def get_effects_for_item(self, item_type: str, item_id: int) -> List[InteractionEffect]:
        """Récupère tous les effets liés à un objet (arme, armure, etc.)."""
        return self.effects_cache.get((item_type, item_id), [])
    
    def analyze_skill_interactions(
        self, 
        skill: Skill, 
        traits: List[Trait],
        equipped_weapons: List[Weapon],
        equipped_armor: List[Armor],
        equipped_trinkets: List[Trinket],
        equipped_upgrades: List[UpgradeComponent]
    ) -> List[InteractionEffect]:
        """Analyse les interactions pour une compétence donnée avec les traits et l'équipement."""
        effects: List[InteractionEffect] = []
        
        # Effets de base de la compétence
        effects.extend(self._extract_skill_effects(skill))
        
        # Effets des traits qui modifient cette compétence
        for trait in traits:
            trait_effects = self._get_trait_effects_on_skill(trait, skill)
            effects.extend(trait_effects)
        
        # Effets des armes équipées
        for weapon in equipped_weapons:
            weapon_effects = self._get_weapon_effects_on_skill(weapon, skill)
            effects.extend(weapon_effects)
        
        # Effets de l'armure équipée
        for armor in equipped_armor:
            armor_effects = self._get_armor_effects_on_skill(armor, skill)
            effects.extend(armor_effects)
        
        # Effets des bijoux équipés
        for trinket in equipped_trinkets:
            trinket_effects = self._get_trinket_effects_on_skill(trinket, skill)
            effects.extend(trinket_effects)
        
        # Effets des améliorations équipées (runes, cachets, etc.)
        for upgrade in equipped_upgrades:
            upgrade_effects = self._get_upgrade_effects_on_skill(upgrade, skill)
            effects.extend(upgrade_effects)
        
        # Appliquer les modificateurs de mode de jeu
        effects = self._apply_game_mode_modifiers(effects)
        
        return effects
    
    def _extract_skill_effects(self, skill: Skill) -> List[InteractionEffect]:
        """Extrait les effets d'une compétence."""
        # TODO: Implémenter l'extraction des effets à partir des données de la compétence
        # Cela nécessitera d'analyser les champs 'facts' et 'traited_facts' de l'API GW2
        return []
    
    def _get_trait_effects_on_skill(self, trait: Trait, skill: Skill) -> List[InteractionEffect]:
        """Récupère les effets d'un trait sur une compétence spécifique."""
        # TODO: Implémenter la logique pour déterminer comment un trait affecte une compétence
        # Cela nécessitera d'analyser les effets du trait et de les appliquer à la compétence
        return []
    
    def _get_weapon_effects_on_skill(self, weapon: Weapon, skill: Skill) -> List[InteractionEffect]:
        """Récupère les effets d'une arme sur une compétence spécifique."""
        # TODO: Implémenter la logique pour déterminer comment une arme affecte une compétence
        return []
    
    def _get_armor_effects_on_skill(self, armor: Armor, skill: Skill) -> List[InteractionEffect]:
        """Récupère les effets d'une armure sur une compétence spécifique."""
        # TODO: Implémenter la logique pour déterminer comment une armure affecte une compétence
        return []
    
    def _get_trinket_effects_on_skill(self, trinket: Trinket, skill: Skill) -> List[InteractionEffect]:
        """Récupère les effets d'un bijou sur une compétence spécifique."""
        # TODO: Implémenter la logique pour déterminer comment un bijou affecte une compétence
        return []
    
    def _get_upgrade_effects_on_skill(self, upgrade: UpgradeComponent, skill: Skill) -> List[InteractionEffect]:
        """Récupère les effets d'une amélioration sur une compétence spécifique."""
        # TODO: Implémenter la logique pour déterminer comment une amélioration affecte une compétence
        return []
    
    def _apply_game_mode_modifiers(self, effects: List[InteractionEffect]) -> List[InteractionEffect]:
        """Applique les modificateurs spécifiques au mode de jeu."""
        # Dans PvP et WvW, certains effets peuvent être modifiés
        if self.game_mode in (GameMode.PVP, GameMode.WVS, GameMode.WVW):
            modified_effects = []
            for effect in effects:
                # Exemple: Réduire la durée des contrôles en PvP/WvW
                if effect.effect_type in ('apply_condition', 'apply_boon') and effect.duration:
                    if effect.effect_value in [
                        ConditionType.STUN, 
                        ConditionType.DAZE, 
                        ConditionType.KNOCKDOWN,
                        ConditionType.FEAR,
                        ConditionType.TAUNT
                    ]:
                        # Réduire la durée de 50% en PvP/WvW
                        modified_effect = effect
                        modified_effect.duration = effect.duration * 0.5
                        modified_effects.append(modified_effect)
                        continue
                
                modified_effects.append(effect)
            
            return modified_effects
        
        return effects

class ComboAnalyzer:
    """Analyse les interactions de combo dans GW2."""
    
    def __init__(self):
        self.combo_fields: Dict[ComboFieldType, List[dict]] = {
            ComboFieldType.FIRE: [
                {'finisher': ComboFinisherType.BLAST, 'effect': 'Might (3x)'},
                {'finisher': ComboFinisherType.LEAP, 'effect': 'Fire Aura'},
                {'finisher': ComboFinisherType.PROJECTILE, 'effect': 'Burning'},
            ],
            # TODO: Ajouter d'autres types de champs de combo
        }
    
    def get_combo_effect(
        self, 
        field_type: ComboFieldType, 
        finisher_type: ComboFinisherType
    ) -> Optional[dict]:
        """Récupère l'effet d'un combo champ-finisseur."""
        field_effects = self.combo_fields.get(field_type, [])
        for effect in field_effects:
            if effect['finisher'] == finisher_type:
                return effect
        return None
