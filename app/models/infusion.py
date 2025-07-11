"""Modèle SQLAlchemy pour les infusions GW2."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class InfusionType(PyEnum):
    """Types d'infusions dans GW2."""
    AGONY = "Agony"
    DEFENSE = "Defense"
    OFFENSE = "Offense"
    UTILITY = "Utility"
    UNIVERSAL = "Universal"
    ENRICHMENT = "Enrichment"

class Infusion(Base):
    """Modèle représentant une infusion GW2.
    
    Les infusions sont des améliorations spéciales qui peuvent être ajoutées aux emplacements d'infusion
    sur les équipements de niveau 80.
    
    Attributes:
        id (int): Identifiant unique de l'infusion
        name (str): Nom de l'infusion (en anglais)
        name_fr (str): Nom de l'infusion en français
        description (str): Description de l'infusion
        description_fr (str): Description de l'infusion en français
        icon (str): URL de l'icône de l'infusion
        type (InfusionType): Type d'infusion (Agony, Defense, etc.)
        level (int): Niveau de l'infusion
        rarity (str): Rareté de l'infusion
        vendor_value (int): Valeur en pièces de cuivre chez les marchands
        flags (List[str]): Drapeaux de propriétés spéciales
        restrictions (List[str]): Restrictions d'utilisation
        details (dict): Détails spécifiques à l'infusion (bonus, attributs, etc.)
        
        # Relations
        upgrade_components: relation avec les composants d'amélioration
    """
    __tablename__ = 'infusions'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    icon = Column(String(255))
    type = Column(Enum(InfusionType), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=0, index=True)
    rarity = Column(String(20), nullable=False, index=True)
    vendor_value = Column(Integer, default=0)
    flags = Column(JSON, nullable=True)
    restrictions = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Relation avec les composants d'amélioration
    upgrade_components = relationship(
        "UpgradeComponent",
        secondary="upgrade_component_infusions",
        back_populates="infusions"
    )
    
    def __repr__(self):
        return f"<Infusion(id={self.id}, name='{self.name}', type='{self.type}')>"
    
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
            "rarity": self.rarity,
            "vendor_value": self.vendor_value,
            "flags": self.flags,
            "restrictions": self.restrictions,
            "details": self.details
        }
