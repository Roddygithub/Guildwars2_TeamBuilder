"""Configuration des relations entre les modèles SQLAlchemy.

Ce module centralise la configuration des relations pour éviter les problèmes
d'imports circulaires entre les modèles. Il fournit également des fonctions de validation
pour vérifier que toutes les relations sont correctement configurées.
"""
import logging
from typing import Dict, List, Type, Any, Optional
from sqlalchemy.orm import relationship, configure_mappers, Mapper
from sqlalchemy.exc import SQLAlchemyError

# Configuration du logging
logger = logging.getLogger(__name__)

# Import des modèles après leur définition pour éviter les imports circulaires
from .item import Item
from .item_stats import ItemStats
from .item_stat_mapping import ItemStat
from .weapon import Weapon
from .armor import Armor
from .trinket import Trinket
from .upgrade_component import UpgradeComponent
from .skill import Skill
from .trait import Trait
from .profession import Profession
from .specialization import Specialization
from .profession_weapon import ProfessionWeaponType, ProfessionWeaponSkill

def validate_relationship(relationship_name: str, model_class, related_class) -> bool:
    """Valide qu'une relation existe entre deux classes de modèles.
    
    Args:
        relationship_name: Nom de la relation à valider
        model_class: Classe du modèle source ou nom du modèle sous forme de chaîne
        related_class: Classe du modèle cible ou nom du modèle sous forme de chaîne
        
    Returns:
        bool: True si la relation est valide, False sinon
    """
    try:
        # Si model_class est une chaîne, on essaie de le résoudre depuis les globals
        if isinstance(model_class, str):
            model_class = globals().get(model_class)
            if model_class is None:
                logger.error(f"Impossible de résoudre la classe de modèle '{model_class}' depuis les globals")
                return False
        
        # Si related_class est une chaîne, on essaie de le résoudre depuis les globals
        if isinstance(related_class, str):
            related_class = globals().get(related_class)
            if related_class is None:
                logger.error(f"Impossible de résoudre la classe de modèle liée '{related_class}' depuis les globals")
                return False
        
        # Vérifie que la relation existe dans la classe source
        if not hasattr(model_class, relationship_name):
            logger.error(f"La relation '{relationship_name}' n'existe pas dans la classe {model_class.__name__}")
            return False
            
        # Obtient le mapper SQLAlchemy pour la classe source
        mapper = model_class.__mapper__
        
        # Vérifie que la relation est configurée dans le mapper
        if relationship_name not in mapper.relationships:
            logger.error(f"La relation '{relationship_name}' n'est pas configurée dans le mapper de {model_class.__name__}")
            return False
            
        # Vérifie que la classe cible est correcte
        rel = getattr(model_class, relationship_name)
        if rel.mapper.class_ != related_class:
            logger.error(
                f"La relation '{relationship_name}' dans {model_class.__name__} "
                f"pointe vers {rel.mapper.class_.__name__} au lieu de {related_class.__name__}"
            )
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation de la relation {relationship_name}: {e}")
        return False

def setup_relationships() -> None:
    """Configure toutes les relations entre les modèles.
    
    Cette fonction doit être appelée après que tous les modèles aient été importés
    pour s'assurer que toutes les relations sont correctement configurées.
    
    Raises:
        RuntimeError: Si une erreur survient lors de la configuration des relations
    """
    logger.info("Début de la configuration des relations SQLAlchemy...")
    
    # Log des modèles importés
    logger.debug("Modèles importés:")
    for name, obj in globals().items():
        if hasattr(obj, '__module__') and obj.__module__.startswith('app.models'):
            logger.debug(f"- {name} ({obj.__module__})")
            
    # Vérification des attributs des modèles
    logger.debug("Vérification des attributs des modèles...")
    model_names = ["Item", "Weapon", "Skill", "Trait", "ProfessionWeaponType", "ProfessionWeaponSkill"]
    for name in model_names:
        if name in globals():
            model = globals()[name]
            logger.debug(f"Attributs de {name}: {dir(model)}")
        else:
            logger.warning(f"Modèle non trouvé: {name}")
    
    logger.info("Configuration des relations...")
    # Relations pour Item
    Item.stats = relationship(
        "ItemStats", 
        foreign_keys=[Item.stats_id], 
        back_populates="items"
    )
    Item.stat_mappings = relationship(
        "ItemStat", 
        back_populates="item", 
        cascade="all, delete-orphan"
    )
    Item.weapon = relationship(
        "Weapon", 
        back_populates="item", 
        uselist=False
    )
    Item.armor = relationship(
        "Armor", 
        back_populates="item", 
        uselist=False
    )
    Item.trinket = relationship(
        "Trinket", 
        back_populates="item", 
        uselist=False
    )
    Item.upgrade_component = relationship(
        "UpgradeComponent", 
        back_populates="item", 
        uselist=False
    )
    
    # Relations pour ItemStats
    ItemStats.stat_mappings = relationship(
        "ItemStat", 
        back_populates="statistics", 
        cascade="all, delete-orphan"
    )
    ItemStats.items = relationship(
        "Item", 
        back_populates="stats", 
        foreign_keys="[Item.stats_id]"
    )
    
    # Relations pour ItemStat
    ItemStat.item = relationship("Item", back_populates="stat_mappings")
    ItemStat.statistics = relationship("ItemStats", back_populates="stat_mappings")
    
    # Relations pour Weapon (utiliser des chaînes pour éviter les problèmes d'importation circulaire)
    if 'Weapon' in globals():
        Weapon = globals()['Weapon']
        Weapon.item = relationship("Item", back_populates="weapon", uselist=False)
        
        # Relation avec les compétences de l'arme
        Weapon.skills = relationship(
            "Skill",
            secondary="weapon_skills",
            back_populates="weapons",
            lazy="selectin",
            overlaps="weapons,skills"
        )
        
        # Relation avec les types d'armes de profession
        # Relation simplifiée - ne référence que le type d'arme, pas la spécialisation
        Weapon.profession_weapon_types = relationship(
            "ProfessionWeaponType",
            primaryjoin="Weapon.type == foreign(remote(ProfessionWeaponType.weapon_type))",
            viewonly=True,
            overlaps="weapon_skills"
        )
    else:
        logger.warning("La classe Weapon n'est pas disponible pour la configuration des relations")
    
    # Relations pour Armor
    Armor.item = relationship(
        "Item", 
        back_populates="armor", 
        uselist=False,
        overlaps="armor,armor"
    )
    
    # Relations pour Trinket
    Trinket.item = relationship(
        "Item", 
        back_populates="trinket", 
        uselist=False,
        overlaps="trinket,trinket"
    )
    
    # Relations pour UpgradeComponent
    UpgradeComponent.item = relationship(
        "Item", 
        back_populates="upgrade_component", 
        uselist=False,
        overlaps="upgrade_component,upgrade_component"
    )
    
    # Relations pour Skill
    if 'Skill' in globals():
        Skill = globals()['Skill']
        
        # Relation avec Profession
        if hasattr(Skill, 'profession_id'):
            Skill.profession = relationship(
                "Profession",
                back_populates="skills",
                foreign_keys="[Skill.profession_id]",
                lazy="selectin"
            )
        
        # Relation avec Specialization
        if hasattr(Skill, 'specialization_id'):
            Skill.specialization = relationship(
                "Specialization",
                back_populates="skills",
                foreign_keys="[Skill.specialization_id]",
                lazy="selectin"
            )
        
        # Relation avec Weapon (many-to-many via weapon_skills)
        Skill.weapons = relationship(
            "Weapon",
            secondary="weapon_skills",
            back_populates="skills",
            lazy="selectin",
            overlaps="skills,weapons"
        )
    
    # Relations pour Trait (configuration différée)
    if 'Trait' in globals():
        Trait = globals()['Trait']
        
        # Relation avec Specialization
        if hasattr(Trait, 'specialization_id'):
            Trait.specialization = relationship(
                "Specialization",
                back_populates="traits",
                foreign_keys="[Trait.specialization_id]",
                lazy="selectin"
            )
        else:
            logger.warning("Impossible de configurer la relation Trait.specialization: colonne specialization_id manquante dans le modèle Trait")
    
    # Relations pour ProfessionWeaponType (configuration différée)
    if 'ProfessionWeaponType' in globals():
        ProfessionWeaponType = globals()['ProfessionWeaponType']
        
        # Relation avec Weapon
        if hasattr(ProfessionWeaponType, 'weapon_id'):
            ProfessionWeaponType.weapon = relationship(
                "Weapon",
                back_populates="profession_weapon_types",
                foreign_keys="[ProfessionWeaponType.weapon_id]"
            )
        
        # Relation avec ProfessionWeaponSkill (déjà définie dans le modèle avec viewonly=True et overlaps)
    
    # Relations pour ProfessionWeaponSkill
    if 'ProfessionWeaponSkill' in globals():
        ProfessionWeaponSkill = globals()['ProfessionWeaponSkill']
        
        # Relation avec ProfessionWeapon
        if hasattr(ProfessionWeaponSkill, 'profession_weapon_id'):
            ProfessionWeaponSkill.profession_weapon = relationship(
                "ProfessionWeapon",
                back_populates="skills"
            )
        
        # Relation avec Skill
        if hasattr(ProfessionWeaponSkill, 'skill_id'):
            ProfessionWeaponSkill.skill = relationship(
                "Skill",
                back_populates="profession_weapon_skills",
                overlaps="profession_weapon_skills,profession_weapon_types"
            )
    
    # Ajout de la relation manquante dans Skill
    if 'Skill' in globals() and 'ProfessionWeaponSkill' in globals():
        Skill = globals()['Skill']
        Skill.profession_weapon_skills = relationship(
            "ProfessionWeaponSkill",
            back_populates="skill",
            foreign_keys="[ProfessionWeaponSkill.skill_id]",
            overlaps="skill,profession_weapon_types,profession_weapon_skills"
        )
    
    # Configuration des relations pour le modèle Trait
    if 'Skill' in globals() and 'Trait' in globals():
        Skill = globals()['Skill']
        Trait = globals()['Trait']
        
        # Configuration de la relation many-to-many entre Skill et Trait
        # via la table d'association trait_skills
        Skill.traits = relationship(
            "Trait",
            secondary="trait_skills",
            back_populates="skills",
            viewonly=True
        )
        
        # Configuration de la relation inverse dans Trait
        Trait.skills = relationship(
            "Skill",
            secondary="trait_skills",
            back_populates="traits",
            viewonly=True
        )
    else:
        logger.warning("Impossible de configurer la relation entre Skill et Trait: modèles non chargés")
    
    # Configuration des relations pour le modèle ProfessionWeaponType
    if 'ProfessionWeaponType' in globals():
        ProfessionWeaponType = globals()['ProfessionWeaponType']
        
        # Relation inverse pour les compétences de type arme de profession
        ProfessionWeaponType.weapon_skills = relationship(
            "ProfessionWeaponSkill",
            back_populates="weapon_type",
            cascade="all, delete-orphan",
            foreign_keys="[ProfessionWeaponSkill.weapon_type_id]"
        )
        
        # Relation avec la profession
        ProfessionWeaponType.profession = relationship(
            "Profession",
            back_populates="weapon_types"
        )
        
        # Relation avec la spécialisation
        ProfessionWeaponType.specialization = relationship(
            "Specialization",
            back_populates="weapon_types"
        )
    else:
        logger.warning("Impossible de configurer les relations pour ProfessionWeaponType")
    
    try:
        # Configuration des mappers SQLAlchemy
        logger.info("Début de la configuration des mappers SQLAlchemy...")
        
        # Log des relations configurées
        logger.debug("Relations configurées:")
        for name, obj in globals().items():
            if hasattr(obj, 'property') and hasattr(obj.property, 'mapper'):
                logger.debug(f"- {name}: {obj.property}")
        
        logger.info("Appel à configure_mappers()...")
        configure_mappers()
        logger.info("Configuration des mappers terminée avec succès")
        
        # Validation des relations critiques
        logger.info("Validation des relations critiques...")
        validate_critical_relationships()
        logger.info("Validation des relations critiques terminée")
        
    except SQLAlchemyError as e:
        error_msg = f"Erreur lors de la configuration des mappers SQLAlchemy: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Erreur inattendue lors de la configuration des relations: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def validate_critical_relationships() -> None:
    """Valide les relations critiques entre les modèles.
    
    Cette fonction vérifie que les relations critiques sont correctement configurées
    et génère des avertissements pour les problèmes détectés.
    """
    # Liste des relations critiques à valider
    critical_relationships = [
        (Item, 'weapon', Weapon, 'Item.weapon'),
        (Weapon, 'item', Item, 'Weapon.item'),
        (Item, 'armor', Armor, 'Item.armor'),
        (Armor, 'item', Item, 'Armor.item'),
        (Item, 'trinket', Trinket, 'Item.trinket'),
        (Trinket, 'item', Item, 'Trinket.item'),
        (Item, 'upgrade_component', UpgradeComponent, 'Item.upgrade_component'),
        (UpgradeComponent, 'item', Item, 'UpgradeComponent.item'),
        (Item, 'stats', ItemStats, 'Item.stats'),
        (ItemStats, 'items', Item, 'ItemStats.items'),
        (Skill, 'profession', 'Profession', 'Skill.profession'),
        (Skill, 'specialization', 'Specialization', 'Skill.specialization'),
        (Skill, 'weapons', Weapon, 'Skill.weapons'),
        (Trait, 'specialization', 'Specialization', 'Trait.specialization'),
        ('ProfessionWeaponType', 'skills', 'ProfessionWeaponSkill', 'ProfessionWeaponType.skills'),
        ('Skill', 'profession_weapon_types', 'ProfessionWeaponSkill', 'Skill.profession_weapon_types'),
    ]
    
    # Validation de chaque relation critique
    for model, rel_name, related_model, desc in critical_relationships:
        if not validate_relationship(rel_name, model, related_model):
            logger.warning(f"Relation critique non valide: {desc}")
        else:
            logger.debug(f"Relation validée: {desc}")

# Appel immédiat pour configurer les relations
try:
    setup_relationships()
except Exception as e:
    logger.critical(f"Échec critique lors de la configuration des relations: {e}")
    raise
