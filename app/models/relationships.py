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

def validate_relationship(relationship_name: str, model_class: Type, related_class: Type) -> bool:
    """Valide qu'une relation existe entre deux classes de modèles.
    
    Args:
        relationship_name: Nom de la relation à valider
        model_class: Classe du modèle source
        related_class: Classe du modèle cible
        
    Returns:
        bool: True si la relation est valide, False sinon
    """
    try:
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
    logger.info("Configuration des relations SQLAlchemy...")
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
    
    # Relations pour Weapon
    Weapon.item = relationship("Item", back_populates="weapon", uselist=False)
    Weapon.profession_weapons = relationship(
        "ProfessionWeapon",
        back_populates="weapon",
        cascade="all, delete-orphan"
    )
    
    # Relations pour Armor
    Armor.item = relationship("Item", back_populates="armor", uselist=False)
    
    # Relations pour Trinket
    Trinket.item = relationship("Item", back_populates="trinket", uselist=False)
    
    # Relations pour UpgradeComponent
    UpgradeComponent.item = relationship("Item", back_populates="upgrade_component", uselist=False)
    
    try:
        # Configuration des mappers SQLAlchemy
        logger.info("Configuration des mappers SQLAlchemy...")
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
