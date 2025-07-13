"""Modèle SQLAlchemy pour les armures GW2."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum, Float, Table
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base

class ArmorType(PyEnum):
    """Types d'armures dans GW2."""
    BOOTS = "Boots"
    COAT = "Coat"
    GLOVES = "Gloves"
    HELM = "Helm"
    HELM_AQUATIC = "HelmAquatic"
    LEGGINGS = "Leggings"
    SHOULDERS = "Shoulders"
    
class WeightClass(PyEnum):
    """Classes de poids des armures."""
    CLOTHING = "Clothing"
    LIGHT = "Light"
    MEDIUM = "Medium"
    HEAVY = "Heavy"
    
class InfusionSlotFlag(PyEnum):
    """Types d'emplacements d'infusion."""
    DEFENSE = "Defense"
    OFFENSE = "Offense"
    UTILITY = "Utility"
    AGONY = "Agony"
    UNIVERSAL = "Universal"

class Armor(Base):
    """Modèle représentant une pièce d'armure GW2.
    
    Attributes:
        id (int): Identifiant unique de l'armure
        name (str): Nom de l'armure (en anglais)
        name_fr (str): Nom de l'armure en français
        description (str): Description de l'armure
        description_fr (str): Description de l'armure en français
        icon (str): URL de l'icône de l'armure
        chat_link (str): Lien de chat pour l'armure
        type (ArmorType): Type d'armure (bottes, gants, etc.)
        weight_class (WeightClass): Classe de poids (Léger/Moyen/Lourd)
        defense (int): Valeur de défense de l'armure
        infusion_slots (List[dict]): Emplacements d'infusion
        infusion_upgrade_flags (List[str]): Types d'infusions compatibles
        suffix_item_id (int): ID de l'objet suffixe
        secondary_suffix_item_id (str): ID secondaire de l'objet suffixe
        stat_choices (List[int]): IDs des choix de statistiques
        game_types (List[str]): Types de jeu où l'armure est utilisable
        flags (List[str]): Drapeaux de propriétés spéciales
        restrictions (List[str]): Restrictions d'utilisation
        rarity (str): Rareté de l'armure
        level (int): Niveau requis pour utiliser l'armure
        default_skin (int): ID du skin par défaut
        details (dict): Détails spécifiques à l'armure
        
        # Relations
        profession_armors: relation avec les armures de profession
        runes: runes équipées sur cette armure
    """
    __tablename__ = 'armors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    icon = Column(String(255))
    chat_link = Column(String(100), nullable=True)
    type = Column(Enum(ArmorType), nullable=False, index=True)
    weight_class = Column(Enum(WeightClass), nullable=False, index=True)
    defense = Column(Integer, nullable=False, default=0)
    infusion_slots = Column(JSON, nullable=True)  # Liste d'emplacements d'infusion
    infusion_upgrade_flags = Column(JSON, nullable=True)  # Types d'infusions
    suffix_item_id = Column(Integer, nullable=True)
    secondary_suffix_item_id = Column(String(50), nullable=True)
    stat_choices = Column(JSON, nullable=True)  # Liste d'IDs de statistiques
    game_types = Column(JSON, nullable=True)  # Liste de types de jeu
    flags = Column(JSON, nullable=True)  # Drapeaux de propriétés
    restrictions = Column(JSON, nullable=True)  # Liste de restrictions
    rarity = Column(String(20), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=0, index=True)
    default_skin = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)  # Détails spécifiques
    
    # Clé étrangère vers la table items
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Relation avec Item
    item = relationship("Item", back_populates="armor", uselist=False)
    
    # Relations avec d'autres tables
    profession_armors = relationship(
        "ProfessionArmor",
        back_populates="armor",
        cascade="all, delete-orphan"
    )
    
    upgrades = relationship(
        "UpgradeComponent",
        secondary="armor_upgrade_components",
        back_populates="armors"
    )
    
    def __repr__(self):
        return f"<Armor(id={self.id}, name='{self.name}', type='{self.type}', weight='{self.weight_class}')>"
    
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
            'weight_class': self.weight_class.value if self.weight_class else None,
            'defense': self.defense,
            'infusion_slots': self.infusion_slots or [],
            'infusion_upgrade_flags': self.infusion_upgrade_flags or [],
            'suffix_item_id': self.suffix_item_id,
            'secondary_suffix_item_id': self.secondary_suffix_item_id,
            'stat_choices': self.stat_choices or [],
            'game_types': self.game_types or [],
            'flags': self.flags or [],
            'restrictions': self.restrictions or [],
            'rarity': self.rarity,
            'level': self.level,
            'default_skin': self.default_skin,
            'details': self.details or {}
        }


# Table d'association pour la relation many-to-many entre armures et runes
armor_runes = Base.metadata.tables.get('armor_runes')
if armor_runes is None:
    armor_runes = Table(
        'armor_runes',
        Base.metadata,
        Column('armor_id', Integer, ForeignKey('armors.id', ondelete='CASCADE'), primary_key=True),
        Column('rune_id', Integer, ForeignKey('runes.id', ondelete='CASCADE'), primary_key=True),
        Column('count', Integer, nullable=False, default=1)  # Nombre de runes (pour les ensembles)
    )


class ProfessionArmor(Base):
    """Table d'association entre les professions et les armures avec des métadonnées."""
    __tablename__ = 'profession_armors'
    
    profession_id = Column(
        String(50), 
        ForeignKey('professions.id', ondelete='CASCADE'), 
        primary_key=True
    )
    
    armor_id = Column(
        Integer, 
        ForeignKey('armors.id', ondelete='CASCADE'), 
        primary_key=True
    )
    
    # Type d'emplacement d'équipement (utilisé pour les restrictions)
    slot = Column(String(50), nullable=False, index=True)
    
    # Relations
    profession = relationship("Profession", back_populates="available_armors")
    armor = relationship("Armor", back_populates="profession_armors")
    
    def __repr__(self):
        return f"<ProfessionArmor(profession_id={self.profession_id}, armor_id={self.armor_id}, slot='{self.slot}')>"
