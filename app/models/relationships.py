"""Configuration des relations entre les modèles SQLAlchemy.

Ce module centralise la configuration des relations pour éviter les problèmes
d'imports circulaires entre les modèles.
"""
from sqlalchemy.orm import relationship, configure_mappers

# Import des modèles après leur définition pour éviter les imports circulaires
from .item import Item
from .item_stats import ItemStats
from .item_stat_mapping import ItemStat
from .weapon import Weapon
from .armor import Armor
from .trinket import Trinket
from .upgrade_component import UpgradeComponent

def setup_relationships():
    """Configure toutes les relations entre les modèles."""
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
    
    # Configuration des mappers SQLAlchemy
    configure_mappers()

# Appel immédiat pour configurer les relations
setup_relationships()
