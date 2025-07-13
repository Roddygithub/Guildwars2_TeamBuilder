"""Modèles SQLAlchemy pour les composants d'amélioration GW2 (runes, cachets, reliques)."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum, Table
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class UpgradeComponentType(PyEnum):
    """Types de composants d'amélioration."""
    RUNE = "Rune"
    SIGIL = "Sigil"
    RELIC = "Relic"
    GEM = "Gem"
    JEWEL = "Jewel"

class InfusionUpgradeFlag(PyEnum):
    """Types d'améliorations d'infusion."""
    AGONY = "Agony"
    DEFENSE = "Defense"
    INFUSION = "Infusion"
    OFFENSE = "Offense"
    UTILITY = "Utility"
    UNIVERSAL = "Universal"

class UpgradeComponent(Base):
    """Modèle de base pour les composants d'amélioration (runes, cachets, reliques).
    
    Attributes:
        id (int): Identifiant unique du composant
        name (str): Nom du composant (en anglais)
        name_fr (str): Nom du composant en français
        description (str): Description du composant
        description_fr (str): Description du composant en français
        icon (str): URL de l'icône du composant
        chat_link (str): Lien de chat pour le composant
        type (UpgradeComponentType): Type de composant (rune, cachet, etc.)
        level (int): Niveau du composant
        rarity (str): Rareté du composant
        vendor_value (int): Valeur en pièces de cuivre chez les marchands
        flags (List[str]): Drapeaux de propriétés spéciales
        restrictions (List[str]): Restrictions d'utilisation
        details (dict): Détails spécifiques au type de composant
        
        # Relations
        infusions: relation avec les infusions
        armors: relation avec les armures équipées
        weapons: relation avec les armes équipées
    """
    __tablename__ = 'upgrade_components'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    icon = Column(String(255))
    chat_link = Column(String(100), nullable=True)
    type = Column(Enum(UpgradeComponentType), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=0, index=True)
    rarity = Column(String(20), nullable=False, index=True)
    vendor_value = Column(Integer, default=0)
    flags = Column(JSON, nullable=True)  # Drapeaux de propriétés
    restrictions = Column(JSON, nullable=True)  # Liste de restrictions
    details = Column(JSON, nullable=True)  # Détails spécifiques au type
    
    # Clé étrangère vers la table items
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Relation avec Item
    item = relationship("Item", back_populates="upgrade_component", uselist=False)
    
    # Relations avec d'autres tables
    infusions = relationship(
        "Infusion",
        secondary="upgrade_component_infusions",
        back_populates="upgrade_components"
    )
    
    armors = relationship(
        "Armor",
        secondary="armor_upgrade_components",
        back_populates="upgrades"
    )
    
    weapons = relationship(
        "Weapon",
        secondary="weapon_upgrade_components",
        back_populates="upgrades"
    )
    
    def __repr__(self):
        return f"<UpgradeComponent(id={self.id}, name='{self.name}', type='{self.type}')>"
    
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
            'flags': self.flags or [],
            'restrictions': self.restrictions or [],
            'details': self.details or {}
        }


class Rune(UpgradeComponent):
    """Modèle représentant une rune GW2.
    
    Hérite de UpgradeComponent avec des propriétés spécifiques aux runes.
    """
    __tablename__ = 'runes'
    
    id = Column(Integer, ForeignKey('upgrade_components.id'), primary_key=True)
    bonuses = Column(JSON, nullable=True)  # Bonus par nombre de runes équipées
    
    __mapper_args__ = {
        'polymorphic_identity': 'rune',
        'inherit_condition': (id == UpgradeComponent.id) & (UpgradeComponent.type == 'Rune')
    }
    
    def __repr__(self):
        return f"<Rune(id={self.id}, name='{self.name}')>"


class Sigil(UpgradeComponent):
    """Modèle représentant un cachet GW2.
    
    Hérite de UpgradeComponent avec des propriétés spécifiques aux cachets.
    """
    __tablename__ = 'sigils'
    
    id = Column(Integer, ForeignKey('upgrade_components.id'), primary_key=True)
    suffix = Column(String(100), nullable=True)  # Suffixe du cachet
    
    __mapper_args__ = {
        'polymorphic_identity': 'sigil',
        'inherit_condition': (id == UpgradeComponent.id) & (UpgradeComponent.type == 'Sigil')
    }
    
    def __repr__(self):
        return f"<Sigil(id={self.id}, name='{self.name}')>"


class Relic(UpgradeComponent):
    """Modèle représentant une relique GW2 (introduite avec l'extension End of Dragons).
    
    Hérite de UpgradeComponent avec des propriétés spécifiques aux reliques.
    """
    __tablename__ = 'relics'
    
    id = Column(Integer, ForeignKey('upgrade_components.id'), primary_key=True)
    active_skill_id = Column(Integer, nullable=True)  # ID de la compétence active
    
    __mapper_args__ = {
        'polymorphic_identity': 'relic',
        'inherit_condition': (id == UpgradeComponent.id) & (UpgradeComponent.type == 'Relic')
    }
    
    def __repr__(self):
        return f"<Relic(id={self.id}, name='{self.name}')>"


# Tables d'association pour les relations many-to-many
upgrade_component_infusions = Base.metadata.tables.get('upgrade_component_infusions')
if upgrade_component_infusions is None:
    upgrade_component_infusions = Table(
        'upgrade_component_infusions',
        Base.metadata,
        Column('upgrade_component_id', Integer, ForeignKey('upgrade_components.id', ondelete='CASCADE'), primary_key=True),
        Column('infusion_id', Integer, ForeignKey('infusions.id', ondelete='CASCADE'), primary_key=True)
    )

armor_upgrade_components = Base.metadata.tables.get('armor_upgrade_components')
if armor_upgrade_components is None:
    armor_upgrade_components = Table(
        'armor_upgrade_components',
        Base.metadata,
        Column('armor_id', Integer, ForeignKey('armors.id', ondelete='CASCADE'), primary_key=True),
        Column('upgrade_component_id', Integer, ForeignKey('upgrade_components.id', ondelete='CASCADE'), primary_key=True),
        Column('slot', String(50), nullable=False)  # Emplacement (ex: "rune" pour les runes d'armure)
    )

weapon_upgrade_components = Base.metadata.tables.get('weapon_upgrade_components')
if weapon_upgrade_components is None:
    weapon_upgrade_components = Table(
        'weapon_upgrade_components',
        Base.metadata,
        Column('weapon_id', Integer, ForeignKey('weapons.id', ondelete='CASCADE'), primary_key=True),
        Column('upgrade_component_id', Integer, ForeignKey('upgrade_components.id', ondelete='CASCADE'), primary_key=True),
        Column('slot', String(50), nullable=False)  # Emplacement (ex: "sigil1", "sigil2" pour les cachets d'arme)
    )
