"""Modèles SQLAlchemy pour les objets (items) GW2."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class ItemType(PyEnum):
    """Types d'objets dans GW2."""
    ARMOR = "Armor"
    BACK = "Back"
    BAG = "Bag"
    CONSUMABLE = "Consumable"
    CONTAINER = "Container"
    CRAFTING_MATERIAL = "CraftingMaterial"
    GATHERING = "Gathering"
    GIZMO = "Gizmo"
    KEY = "Key"
    MINI_PET = "MiniPet"
    TOOL = "Tool"
    TRAIT = "Trait"
    TRINKET = "Trinket"
    TROPHY = "Trophy"
    UPGRADE_COMPONENT = "UpgradeComponent"
    WEAPON = "Weapon"

class Rarity(PyEnum):
    """Rareté des objets dans GW2."""
    JUNK = "Junk"
    BASIC = "Basic"
    FINE = "Fine"
    MASTERWORK = "Masterwork"
    RARE = "Rare"
    EXOTIC = "Exotic"
    ASCENDED = "Ascended"
    LEGENDARY = "Legendary"

class Item(Base):
    """Modèle de base pour tous les objets dans GW2."""
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    icon = Column(String(255))
    type = Column(Enum(ItemType), nullable=False, index=True)
    level = Column(Integer, default=0, index=True)
    rarity = Column(Enum(Rarity), nullable=False, index=True)
    vendor_value = Column(Integer, default=0)
    flags = Column(JSON, nullable=True)
    restrictions = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Clés étrangères uniquement ici
    stats_id = Column(Integer, ForeignKey('item_stats.id'), nullable=True)
    
    # Relations avec les sous-types d'objets (configurées dans relationships.py)
    weapon = None  # Sera configuré dans relationships.py
    armor = None  # Sera configuré dans relationships.py
    trinket = None  # Sera configuré dans relationships.py
    upgrade_component = None  # Sera configuré dans relationships.py
    
    # Relation avec ItemStats (configurée dans relationships.py)
    stats = None  # Sera configuré dans relationships.py
    stat_mappings = None  # Sera configuré dans relationships.py
    
    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "name_fr": self.name_fr,
            "description": self.description,
            "description_fr": self.description_fr,
            "icon": self.icon,
            "type": self.type.value if self.type else None,
            "level": self.level,
            "rarity": self.rarity.value if self.rarity else None,
            "vendor_value": self.vendor_value,
            "flags": self.flags,
            "restrictions": self.restrictions,
            "details": self.details,
            "stats": self.stats.to_dict() if self.stats else None
        }
