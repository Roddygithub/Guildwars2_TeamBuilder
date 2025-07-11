"""Modèle SQLAlchemy pour les professions GW2."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Profession(Base):
    """Modèle représentant une profession GW2.
    
    Attributes:
        id (int): Identifiant unique de la profession
        name (str): Nom de la profession (en anglais)
        name_fr (str): Nom de la profession en français
        icon (str): URL de l'icône de la profession
        icon_big (str): URL de la grande icône de la profession
        icon_armor (str): URL de l'icône de l'armure de la profession
        weapon_sword (int): ID de l'arme d'épée de la profession (pour l'icône)
        description (str): Description de la profession
        playable (bool): Si la profession est jouable
        specialization_ids (List[int]): Liste des IDs des spécialisations de base
        
        # Relations
        specializations: relation avec les spécialisations de cette profession
        skills: relation avec les compétences de base de cette profession
        weapon_skills: relation avec les compétences d'arme de cette profession
    """
    __tablename__ = 'professions'
    
    # L'ID est une chaîne (ex: 'Guardian', 'Warrior', etc.)
    id = Column(String(50), primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    name_fr = Column(String(50), nullable=True, index=True)
    name_de = Column(String(50), nullable=True, index=True)
    name_es = Column(String(50), nullable=True, index=True)
    icon = Column(String(255))
    icon_big = Column(String(255))
    icon_armor = Column(String(255))
    weapon_sword = Column(Integer, nullable=True)  # ID de l'arme d'épée pour l'icône
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)
    description_es = Column(Text, nullable=True)
    playable = Column(Boolean, default=True, index=True)
    
    # Champs JSON - stockés sous forme de chaînes JSON
    specialization_ids = Column(JSON, nullable=True, default=list)  # Liste des IDs des spécialisations
    training_track_ids = Column(JSON, nullable=True, default=list)  # Voies d'entraînement
    flags = Column(JSON, nullable=True, default=list)  # Flags supplémentaires
    
    # Métadonnées
    created = Column(String(50), nullable=True)  # Date de création dans l'API
    updated = Column(String(50), nullable=True)  # Date de dernière mise à jour
    
    # Relations
    specializations = relationship(
        "Specialization", 
        back_populates="profession",
        foreign_keys="[Specialization.profession_id]",
        cascade="all, delete-orphan"
    )
    
    # Relation avec les types d'armes de la profession
    weapon_types = relationship(
        "ProfessionWeaponType",
        back_populates="profession",
        cascade="all, delete-orphan"
    )
    
    # Relation avec les types d'armure de la profession (Léger/Moyen/Lourd)
    armor_types = relationship(
        "ProfessionArmorType",
        back_populates="profession",
        cascade="all, delete-orphan"
    )
    
    # Relation avec les types d'accessoires de la profession (Amulette, Anneau, etc.)
    trinket_types = relationship(
        "ProfessionTrinketType",
        back_populates="profession",
        cascade="all, delete-orphan"
    )
    traits = relationship(
        "Trait",
        back_populates="profession",
        foreign_keys="[Trait.profession_id]",
        cascade="all, delete-orphan"
    )
    skills = relationship(
        "Skill", 
        back_populates="profession",
        foreign_keys="[Skill.profession_id]"
    )
    # Relation avec les compétences d'arme de la profession
    weapon_skills = relationship(
        "ProfessionWeaponSkill",
        secondary="profession_weapon_types",
        primaryjoin="and_(Profession.id == ProfessionWeaponType.profession_id)",
        secondaryjoin="and_(ProfessionWeaponType.id == ProfessionWeaponSkill.weapon_type_id)",
        viewonly=True,
        overlaps="weapon_types,skills"
    )
    available_weapons = relationship(
        "ProfessionWeapon",
        back_populates="profession",
        foreign_keys="[ProfessionWeapon.profession_id]",
        cascade="all, delete-orphan"
    )
    
    available_armors = relationship(
        "ProfessionArmor",
        back_populates="profession",
        foreign_keys="[ProfessionArmor.profession_id]",
        cascade="all, delete-orphan"
    )
    
    available_trinkets = relationship(
        "ProfessionTrinket",
        back_populates="profession",
        foreign_keys="[ProfessionTrinket.profession_id]",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Profession(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'name_fr': self.name_fr,
            'name_de': self.name_de,
            'name_es': self.name_es,
            'icon': self.icon,
            'icon_big': self.icon_big,
            'icon_armor': self.icon_armor,
            'weapon_sword': self.weapon_sword,
            'description': self.description,
            'description_fr': self.description_fr,
            'description_de': self.description_de,
            'description_es': self.description_es,
            'playable': self.playable,
            'specialization_ids': self.specialization_ids or [],
            'training_track_ids': self.training_track_ids or [],
            'flags': self.flags or [],
            'created': self.created,
            'updated': self.updated,
            'available_weapons': [w.to_dict() for w in self.available_weapons],
            'available_armors': [a.to_dict() for a in self.available_armors],
            'available_trinkets': [t.to_dict() for t in self.available_trinkets]
        }
