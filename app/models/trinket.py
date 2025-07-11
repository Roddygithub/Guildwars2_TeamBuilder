"""Modèle SQLAlchemy pour les bijoux GW2."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum, Float
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class TrinketType(PyEnum):
    """Types de bijoux dans GW2."""
    ACCESSORY = "Accessory"
    AMULET = "Amulet"
    RING = "Ring"
    BACK = "Back"

class InfusionSlotFlag(PyEnum):
    """Types d'emplacements d'infusion."""
    DEFENSE = "Defense"
    OFFENSE = "Offense"
    UTILITY = "Utility"
    AGONY = "Agony"
    UNIVERSAL = "Universal"

class Trinket(Base):
    """Modèle représentant un bijou GW2 (accessoire, anneau, amulette, etc.).
    
    Attributes:
        id (int): Identifiant unique du bijou
        name (str): Nom du bijou (en anglais)
        name_fr (str): Nom du bijou en français
        description (str): Description du bijou
        description_fr (str): Description du bijou en français
        icon (str): URL de l'icône du bijou
        chat_link (str): Lien de chat pour le bijou
        type (TrinketType): Type de bijou (accessoire, anneau, etc.)
        level (int): Niveau requis pour utiliser le bijou
        rarity (str): Rareté du bijou
        vendor_value (int): Valeur en pièces de cuivre chez les marchands
        default_skin (int): ID du skin par défaut
        details (dict): Détails spécifiques au bijou
        infusion_slots (List[dict]): Emplacements d'infusion
        infusion_upgrade_flags (List[str]): Types d'infusions compatibles
        suffix_item_id (int): ID de l'objet suffixe
        secondary_suffix_item_id (str): ID secondaire de l'objet suffixe
        stat_choices (List[int]): IDs des choix de statistiques
        game_types (List[str]): Types de jeu où le bijou est utilisable
        flags (List[str]): Drapeaux de propriétés spéciales
        restrictions (List[str]): Restrictions d'utilisation
        
        # Relations
        profession_trinkets: relation avec les bijoux de profession
    """
    __tablename__ = 'trinkets'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    icon = Column(String(255))
    chat_link = Column(String(100), nullable=True)
    type = Column(Enum(TrinketType), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=0, index=True)
    rarity = Column(String(20), nullable=False, index=True)
    vendor_value = Column(Integer, default=0)
    default_skin = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)  # Détails spécifiques
    infusion_slots = Column(JSON, nullable=True)  # Liste d'emplacements d'infusion
    infusion_upgrade_flags = Column(JSON, nullable=True)  # Types d'infusions
    suffix_item_id = Column(Integer, nullable=True)
    secondary_suffix_item_id = Column(String(50), nullable=True)
    stat_choices = Column(JSON, nullable=True)  # Liste d'IDs de statistiques
    game_types = Column(JSON, nullable=True)  # Liste de types de jeu
    flags = Column(JSON, nullable=True)  # Drapeaux de propriétés
    restrictions = Column(JSON, nullable=True)  # Liste de restrictions
    
    # Clé étrangère vers la table items
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Relation avec Item
    item = relationship("Item", back_populates="trinket", uselist=False)
    
    # Relations avec d'autres tables
    profession_trinkets = relationship(
        "ProfessionTrinket",
        back_populates="trinket",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Trinket(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'name_fr': self.name_fr,
            'description': self.description,
            'description_fr': self.description_fr,
            'icon': self.icon,
            'chat_link': self.chat_link,
            'type': self.type.value if self.type else None,
            'level': self.level,
            'rarity': self.rarity,
            'vendor_value': self.vendor_value,
            'default_skin': self.default_skin,
            'details': self.details or {},
            'infusion_slots': self.infusion_slots or [],
            'infusion_upgrade_flags': self.infusion_upgrade_flags or [],
            'suffix_item_id': self.suffix_item_id,
            'secondary_suffix_item_id': self.secondary_suffix_item_id,
            'stat_choices': self.stat_choices or [],
            'game_types': self.game_types or [],
            'flags': self.flags or [],
            'restrictions': self.restrictions or []
        }


class ProfessionTrinket(Base):
    """Table d'association entre les professions et les bijoux avec des métadonnées."""
    __tablename__ = 'profession_trinkets'
    
    profession_id = Column(
        String(50), 
        ForeignKey('professions.id', ondelete='CASCADE'), 
        primary_key=True
    )
    
    trinket_id = Column(
        Integer, 
        ForeignKey('trinkets.id', ondelete='CASCADE'), 
        primary_key=True
    )
    
    # Type d'emplacement (utilisé pour les restrictions)
    slot = Column(String(50), nullable=False, index=True)
    
    # Relations
    profession = relationship("Profession", back_populates="available_trinkets")
    trinket = relationship("Trinket", back_populates="profession_trinkets")
    
    def __repr__(self):
        return f"<ProfessionTrinket(profession_id={self.profession_id}, trinket_id={self.trinket_id}, slot='{self.slot}')>"
