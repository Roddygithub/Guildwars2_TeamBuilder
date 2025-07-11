"""Mappage des données de l'API GW2 vers les modèles internes.

Ce module fournit des fonctions pour convertir les données brutes de l'API GW2
en objets de notre modèle de données interne.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    Profession, Specialization, Skill, Trait, 
    Weapon, Armor, Trinket, UpgradeComponent,
    ItemStats, ItemStat, Item, ItemType
)
from app.game_mechanics import (
    GameMode, RoleType, AttributeType, DamageType, 
    BuffType, BoonType, ConditionType, SkillCategory
)

logger = logging.getLogger(__name__)

class GW2APIMapper:
    """Classe utilitaire pour mapper les données de l'API GW2 vers les modèles internes."""
    
    def __init__(self, db_session: Session):
        """Initialise le mappeur avec une session de base de données."""
        self.db = db_session
        
        # Cache pour les entités fréquemment utilisées
        self._profession_cache: Dict[str, Profession] = {}
        self._specialization_cache: Dict[int, Specialization] = {}
        self._skill_cache: Dict[int, Skill] = {}
        self._trait_cache: Dict[int, Trait] = {}
        self._item_cache: Dict[int, Item] = {}
    
    # Méthodes pour les professions
    
    def map_profession(self, api_data: Dict[str, Any]) -> Profession:
        """Mappe les données d'une profession de l'API vers notre modèle."""
        prof_id = api_data.get('id')
        if not prof_id:
            raise ValueError("Données de profession invalides: ID manquant")
        
        # Vérifier si la profession existe déjà en cache
        if prof_id in self._profession_cache:
            return self._profession_cache[prof_id]
        
        # Vérifier si la profession existe en base de données
        profession = self.db.query(Profession).filter_by(id=prof_id).first()
        
        if not profession:
            profession = Profession(id=prof_id)
            self.db.add(profession)
        
        # Mettre à jour les propriétés de base
        profession.name = api_data.get('name', '')
        profession.icon = api_data.get('icon')
        profession.icon_big = api_data.get('icon_big')
        
        # Ne pas assigner directement weapon_skills, c'est une relation
        # Les armes seront gérées via la relation weapon_types
        weapons_data = api_data.get('weapons', {})
        
        # Mettre à jour les autres propriétés
        profession.flags = api_data.get('flags', [])
        profession.specialization_ids = api_data.get('specializations', [])
        profession.training_track_ids = api_data.get('training', [])
        
        # Ne pas assigner directement skills, c'est une relation
        # Les compétences seront gérées via la relation skills
        
        # Mettre en cache la profession
        self._profession_cache[prof_id] = profession
        
        return profession
    
    # Méthodes pour les statistiques d'objets
    
    def map_itemstat(self, api_data: Dict[str, Any]) -> 'ItemStats':
        """Mappe les données d'une statistique d'objet de l'API vers notre modèle.
        
        Args:
            api_data: Données brutes de la statistique d'objet depuis l'API
            
        Returns:
            L'objet ItemStats créé ou mis à jour
            
        Raises:
            ValueError: Si les données de la statistique sont invalides ou incomplètes
        """
        if not api_data.get('id'):
            raise ValueError("Données de statistique d'objet invalides: ID manquant")
            
        # Vérifier si la statistique existe déjà en base de données
        itemstat = self.db.query(ItemStats).get(api_data['id'])
        
        if not itemstat:
            itemstat = ItemStats(id=api_data['id'])
            self.db.add(itemstat)
        
        # Mettre à jour les propriétés de base
        itemstat.name = api_data.get('name', '')
        itemstat.name_fr = api_data.get('name_fr', '')
        itemstat.description = api_data.get('description', '')
        itemstat.description_fr = api_data.get('description_fr', '')
        
        # Réinitialiser tous les attributs à 0
        for attr in ['power', 'precision', 'toughness', 'vitality', 'concentration',
                    'condition_damage', 'expertise', 'ferocity', 'healing_power',
                    'armor', 'boon_duration', 'critical_chance', 'critical_damage',
                    'condition_duration']:
            setattr(itemstat, attr, 0)
        
        # Mettre à jour les attributs spécifiés dans les données
        if 'attributes' in api_data and isinstance(api_data['attributes'], list):
            for attr_obj in api_data['attributes']:
                if not isinstance(attr_obj, dict):
                    logger.warning(f"Format d'attribut inattendu: {attr_obj}")
                    continue
                    
                attr_name = attr_obj.get('attribute')
                value = attr_obj.get('value', 0)
                
                # Convertir les noms d'attributs de l'API vers nos noms de colonnes
                attr_map = {
                    'Power': 'power',
                    'Precision': 'precision',
                    'Toughness': 'toughness',
                    'Vitality': 'vitality',
                    'Concentration': 'concentration',
                    'ConditionDamage': 'condition_damage',
                    'Expertise': 'expertise',
                    'Ferocity': 'ferocity',
                    'Healing': 'healing_power',
                    'Armor': 'armor',
                    'BoonDuration': 'boon_duration',
                    'CriticalChance': 'critical_chance',
                    'CriticalDamage': 'critical_damage',
                    'ConditionDuration': 'condition_duration'
                }
                
                if attr_name in attr_map:
                    setattr(itemstat, attr_map[attr_name], value)
                    logger.debug(f"Attribut mappé: {attr_name} = {value} -> {attr_map[attr_name]}")
        
        # Journaliser la création/mise à jour
        logger.debug(f"Statistique d'objet {'mise à jour' if itemstat.id else 'créée'}: {itemstat.name} (ID: {itemstat.id})")
        
        return itemstat
    
    # Méthodes pour les spécialisations
    
    def map_specialization(self, api_data: Dict[str, Any]) -> Specialization:
        """Mappe les données d'une spécialisation de l'API vers notre modèle."""
        spec_id = api_data.get('id')
        if not spec_id:
            raise ValueError("Données de spécialisation invalides: ID manquant")
        
        # Vérifier si la spécialisation existe déjà en cache
        if spec_id in self._specialization_cache:
            return self._specialization_cache[spec_id]
        
        # Vérifier si la spécialisation existe en base de données
        specialization = self.db.query(Specialization).filter_by(id=spec_id).first()
        
        if not specialization:
            specialization = Specialization(id=spec_id)
            self.db.add(specialization)
        
        # Mettre à jour les propriétés de base
        specialization.name = api_data.get('name', '')
        specialization.profession = api_data.get('profession')
        specialization.elite = api_data.get('elite', False)
        specialization.icon = api_data.get('icon')
        specialization.background = api_data.get('background')
        
        # Traiter les traits mineurs et majeurs
        specialization.minor_traits = api_data.get('minor_traits', [])
        specialization.major_traits = api_data.get('major_traits', [])
        specialization.weapon_trait = api_data.get('weapon_trait')
        
        # Mettre en cache la spécialisation
        self._specialization_cache[spec_id] = specialization
        
        return specialization
    
    # Méthodes pour les compétences
    
    def map_skill(self, api_data: Dict[str, Any]) -> Skill:
        """Mappe les données d'une compétence de l'API vers notre modèle."""
        skill_id = api_data.get('id')
        if not skill_id:
            raise ValueError("Données de compétence invalides: ID manquant")
        
        # Vérifier si la compétence existe déjà en cache
        if skill_id in self._skill_cache:
            return self._skill_cache[skill_id]
        
        # Vérifier si la compétence existe en base de données
        skill = self.db.query(Skill).filter_by(id=skill_id).first()
        
        if not skill:
            skill = Skill(id=skill_id)
            self.db.add(skill)
        
        # Mettre à jour les propriétés de base
        skill.name = api_data.get('name', '')
        skill.description = api_data.get('description')
        skill.icon = api_data.get('icon')
        skill.chat_link = api_data.get('chat_link')
        skill.type = api_data.get('type')
        skill.weapon_type = api_data.get('weapon_type')
        skill.professions = api_data.get('professions', [])
        skill.slot = api_data.get('slot')
        skill.facts = api_data.get('facts', [])
        skill.traited_facts = api_data.get('traited_facts', [])
        skill.categories = api_data.get('categories', [])
        skill.attunement = api_data.get('attunement')
        skill.cost = api_data.get('cost')
        skill.dual_wield = api_data.get('dual_wield')
        skill.flip_skill = api_data.get('flip_skill')
        skill.initiative = api_data.get('initiative')
        skill.next_chain = api_data.get('next_chain')
        skill.prev_chain = api_data.get('prev_chain')
        skill.transform_skills = api_data.get('transform_skills', [])
        skill.bundle_skills = api_data.get('bundle_skills', [])
        skill.toolbelt_skill = api_data.get('toolbelt_skill')
        
        # Mettre en cache la compétence
        self._skill_cache[skill_id] = skill
        
        return skill
    
    # Méthodes pour les traits
    
    def map_trait(self, api_data: Dict[str, Any]) -> Trait:
        """Mappe les données d'un trait de l'API vers notre modèle."""
        trait_id = api_data.get('id')
        if not trait_id:
            raise ValueError("Données de trait invalides: ID manquant")
        
        # Vérifier si le trait existe déjà en cache
        if trait_id in self._trait_cache:
            return self._trait_cache[trait_id]
        
        # Vérifier si le trait existe en base de données
        trait = self.db.query(Trait).filter_by(id=trait_id).first()
        
        if not trait:
            trait = Trait(id=trait_id)
            self.db.add(trait)
        
        # Mettre à jour les propriétés de base
        trait.name = api_data.get('name', '')
        trait.icon = api_data.get('icon')
        trait.description = api_data.get('description')
        trait.specialization = api_data.get('specialization')
        trait.tier = api_data.get('tier')
        trait.slot = api_data.get('slot')
        trait.facts = api_data.get('facts', [])
        trait.traited_facts = api_data.get('traited_facts', [])
        trait.skills = api_data.get('skills', [])
        
        # Mettre en cache le trait
        self._trait_cache[trait_id] = trait
        
        return trait
    
    # Méthodes pour les statistiques d'objets (item stats)
    
    def map_itemstat(self, api_data: Dict[str, Any]) -> ItemStats:
        """Mappe les données d'une statistique d'objet de l'API vers notre modèle.
        
        Args:
            api_data: Données brutes de la statistique d'objet depuis l'API
            
        Returns:
            L'objet ItemStats créé ou mis à jour
            
        Raises:
            ValueError: Si les données sont invalides ou incomplètes
        """
        if not api_data or 'id' not in api_data:
            raise ValueError("Données de statistique d'objet invalides: ID manquant")
            
        stat_id = api_data['id']
        
        # Vérifier si la statistique existe déjà en base de données
        item_stats = self.db.query(ItemStats).filter_by(id=stat_id).first()
        
        if not item_stats:
            item_stats = ItemStats(id=stat_id)
            self.db.add(item_stats)
        
        # Mettre à jour les propriétés de base
        item_stats.name = api_data.get('name', '')
        item_stats.description = api_data.get('description', '')
        
        # Mettre à jour les attributs de statistiques
        attributes = api_data.get('attributes', [])
        for attr_data in attributes:
            # Les attributs sont sous forme de liste de dictionnaires avec 'attribute' et 'value'
            attr_name = attr_data.get('attribute', '').lower()
            value = attr_data.get('value', 0)
            
            # Mapper les noms d'attributs de l'API vers les noms de colonnes du modèle
            attr_mapping = {
                'power': 'power',
                'precision': 'precision',
                'toughness': 'toughness',
                'vitality': 'vitality',
                'concentration': 'concentration',
                'conditiondamage': 'condition_damage',
                'expertise': 'expertise',
                'ferocity': 'ferocity',
                'healing': 'healing_power',
                'armor': 'armor',
                'boonduration': 'boon_duration',
                'criticalchance': 'critical_chance',
                'criticaldamage': 'critical_damage',
                'conditionduration': 'condition_duration'
            }
            
            # Appliquer le mappage si nécessaire
            attr_name = attr_mapping.get(attr_name.lower(), attr_name)
            
            # Mettre à jour l'attribut s'il existe dans le modèle
            if hasattr(item_stats, attr_name):
                setattr(item_stats, attr_name, value)
        
        # Traiter les statistiques de défense si présentes
        if 'defense' in api_data:
            item_stats.armor = api_data['defense']
        
        # Pour les statistiques de dégâts, on peut les ignorer car elles sont déjà incluses dans les attributs
        # via l'API (power, condition_damage, etc.)
        
        return item_stats
    
    def _map_with_mapper(self, mapper: 'GW2APIMapper', data: Dict[str, Any]) -> Any:
        """Utilise le mapper pour convertir les données en modèle ItemStats."""
        if hasattr(mapper, 'map_itemstat'):
            return mapper.map_itemstat(data)
        else:
            # Implémentation de secours si la méthode n'est pas disponible dans le mapper
            from app.models.item_stats import ItemStats
            
            # Extraire les attributs de base
            item_stat = ItemStats(
                id=data.get('id'),
                name=data.get('name', ''),
                name_fr=data.get('name', ''),  # La traduction sera mise à jour plus tard
                description=data.get('description', ''),
                description_fr=data.get('description', ''),  # La traduction sera mise à jour plus tard
            )
            
            # Mettre à jour les attributs à partir des données de l'API
            attributes = data.get('attributes', [])
            for attr in attributes:
                attr_type = attr.get('attribute')
                value = attr.get('modifier', 0)
                
                if attr_type == 'Power':
                    item_stat.power = value
                elif attr_type == 'Precision':
                    item_stat.precision = value
                elif attr_type == 'Toughness':
                    item_stat.toughness = value
                elif attr_type == 'Vitality':
                    item_stat.vitality = value
                elif attr_type == 'ConditionDamage':
                    item_stat.condition_damage = value
                elif attr_type == 'ConditionDuration':
                    item_stat.expertise = value
                elif attr_type == 'BoonDuration':
                    item_stat.concentration = value
                elif attr_type == 'Healing':
                    item_stat.healing_power = value
                elif attr_type == 'CritDamage':
                    item_stat.ferocity = value
            
            return item_stat.get('id')
    
    # Méthodes pour les objets (items)
    
    def map_item(self, api_data: Dict[str, Any]) -> Item:
        """Mappe les données d'un objet de l'API vers notre modèle."""
        item_id = api_data.get('id')
        if not item_id:
            raise ValueError("Données d'objet invalides: ID manquant")
        
        # Vérifier si l'objet existe déjà en cache
        if item_id in self._item_cache:
            return self._item_cache[item_id]
        
        # Vérifier si l'objet existe en base de données
        item = self.db.query(Item).filter_by(id=item_id).first()
        
        if not item:
            item = Item(id=item_id)
            self.db.add(item)
        
        # Mettre à jour les propriétés de base
        item.name = api_data.get('name', '')
        item.description = api_data.get('description')
        item.type = api_data.get('type')
        item.level = api_data.get('level', 0)
        item.rarity = api_data.get('rarity')
        item.vendor_value = api_data.get('vendor_value', 0)
        item.default_skin = api_data.get('default_skin')
        item.game_types = api_data.get('game_types', [])
        item.flags = api_data.get('flags', [])
        item.restrictions = api_data.get('restrictions', [])
        item.chat_link = api_data.get('chat_link')
        item.icon = api_data.get('icon')
        
        # Gérer les détails spécifiques au type d'objet
        details = api_data.get('details')
        
        # Valider que details est un dictionnaire
        if not isinstance(details, dict):
            logger.warning(f"Détails d'objet invalides (type: {type(details).__name__}) pour l'objet {item_id} (type: {item.type})")
            details = {}
        
        try:
            if item.type == "Armor":
                item.armor = self._map_armor_details(details)
            elif item.type == "Weapon":
                item.weapon = self._map_weapon_details(details)
            elif item.type in ["Accessory", "Amulet", "Ring", "Trinket"]:
                item.trinket = self._map_trinket_details(details)
            elif item.type == "UpgradeComponent":
                item.upgrade_component = self._map_upgrade_component_details(details)
        except Exception as e:
            logger.error(f"Erreur lors du mappage des détails pour l'objet {item_id} (type: {item.type}): {e}")
            # Initialiser des détails vides pour éviter les erreurs ultérieures
            if item.type == "Armor":
                item.armor = self._map_armor_details({})
            elif item.type == "Weapon":
                item.weapon = self._map_weapon_details({})
            elif item.type in ["Accessory", "Amulet", "Ring", "Trinket"]:
                item.trinket = self._map_trinket_details({})
            elif item.type == "UpgradeComponent":
                item.upgrade_component = self._map_upgrade_component_details({})
        
        # Mettre en cache l'objet
        self._item_cache[item_id] = item
        
        return item
    
    # Méthodes auxiliaires pour le mappage des détails spécifiques
    
    def _map_armor_details(self, details: Dict[str, Any]) -> Armor:
        """Mappe les détails spécifiques à une armure."""
        armor = Armor()
        
        armor.type = details.get('type')
        armor.weight_class = details.get('weight_class')
        armor.defense = details.get('defense', 0)
        armor.infusion_slots = details.get('infusion_slots', [])
        armor.infix_upgrade = details.get('infix_upgrade')
        armor.suffix_item_id = details.get('suffix_item_id')
        armor.secondary_suffix_item_id = details.get('secondary_suffix_item_id')
        armor.stat_choices = details.get('stat_choices', [])
        
        return armor
    
    def _map_weapon_details(self, details: Dict[str, Any]) -> Weapon:
        """Mappe les détails spécifiques à une arme."""
        weapon = Weapon()
        
        weapon.type = details.get('type')
        weapon.damage_type = details.get('damage_type')
        weapon.min_power = details.get('min_power', 0)
        weapon.max_power = details.get('max_power', 0)
        weapon.defense = details.get('defense', 0)
        weapon.infusion_slots = details.get('infusion_slots', [])
        weapon.infix_upgrade = details.get('infix_upgrade')
        weapon.suffix_item_id = details.get('suffix_item_id')
        weapon.secondary_suffix_item_id = details.get('secondary_suffix_item_id')
        weapon.stat_choices = details.get('stat_choices', [])
        
        return weapon
    
    def _map_trinket_details(self, details: Dict[str, Any]) -> Trinket:
        """Mappe les détails spécifiques à un bijou."""
        trinket = Trinket()
        
        trinket.type = details.get('type')
        trinket.infusion_slots = details.get('infusion_slots', [])
        trinket.infix_upgrade = details.get('infix_upgrade')
        trinket.suffix_item_id = details.get('suffix_item_id')
        trinket.secondary_suffix_item_id = details.get('secondary_suffix_item_id')
        trinket.stat_choices = details.get('stat_choices', [])
        
        return trinket
    
    def _map_upgrade_component_details(self, details: Dict[str, Any]) -> UpgradeComponent:
        """Mappe les détails spécifiques à un composant d'amélioration."""
        upgrade = UpgradeComponent()
        
        upgrade.type = details.get('type')
        upgrade.flags = details.get('flags', [])
        upgrade.infusion_upgrade_flags = details.get('infusion_upgrade_flags', [])
        upgrade.suffix = details.get('suffix')
        upgrade.infix_upgrade = details.get('infix_upgrade')
        upgrade.bonuses = details.get('bonuses', [])
        
        return upgrade
    
    # Méthodes pour les statistiques d'objets
    
    def map_item_stats(self, api_data: Dict[str, Any]) -> ItemStats:
        """Mappe les données de statistiques d'objet de l'API vers notre modèle."""
        stats_id = api_data.get('id')
        if not stats_id:
            raise ValueError("Données de statistiques d'objet invalides: ID manquant")
        
        # Vérifier si les statistiques existent en base de données
        item_stats = self.db.query(ItemStats).filter_by(id=stats_id).first()
        
        if not item_stats:
            item_stats = ItemStats(id=stats_id)
            self.db.add(item_stats)
        
        # Mettre à jour les propriétés de base
        item_stats.name = api_data.get('name', '')
        
        # Mapper les attributs
        attributes = api_data.get('attributes', {})
        for attr_name, attr_value in attributes.items():
            # Vérifier si l'attribut existe déjà
            attr = (
                self.db.query(ItemStat)
                .filter_by(stats_id=stats_id, attribute=attr_name)
                .first()
            )
            
            if not attr:
                attr = ItemStat(stats_id=stats_id, attribute=attr_name, value=attr_value)
                self.db.add(attr)
            else:
                attr.value = attr_value
        
        return item_stats
    
    # Méthodes utilitaires
    
    def clear_cache(self) -> None:
        """Vide le cache interne du mappeur."""
        self._profession_cache.clear()
        self._specialization_cache.clear()
        self._skill_cache.clear()
        self._trait_cache.clear()
        self._item_cache.clear()
