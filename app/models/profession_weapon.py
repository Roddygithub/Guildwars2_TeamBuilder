"""Modèle SQLAlchemy pour la relation entre les compétences et les armes de profession."""

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class ProfessionWeaponType(Base):
    """Représente un type d'arme utilisable par une profession spécifique.
    
    Cette table fait le lien entre une profession, un type d'arme et les compétences associées.
    Diffère de ProfessionWeapon qui fait le lien entre une profession et une arme spécifique.
    """
    __tablename__ = 'profession_weapon_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profession_id = Column(String(50), ForeignKey('professions.id', ondelete='CASCADE'), nullable=False, index=True)
    weapon_type = Column(String(50), nullable=False)  # Type d'arme (par exemple: 'Axe', 'Sword', 'Greatsword')
    hand = Column(String(10), nullable=False)  # 'MainHand', 'OffHand', 'TwoHand', 'Aquatic'
    specialization_id = Column(Integer, ForeignKey('specializations.id', ondelete='SET NULL'), nullable=True)
    is_elite = Column(Boolean, default=False, nullable=False)  # Si l'arme nécessite une spécialisation élite
    
    # Relations
    profession = relationship("Profession", back_populates="weapon_types")
    specialization = relationship("Specialization", back_populates="weapon_types")
    weapon_skills = relationship(
        "ProfessionWeaponSkill", 
        back_populates="weapon_type", 
        cascade="all, delete-orphan",
        foreign_keys="[ProfessionWeaponSkill.weapon_type_id]"
    )
    profession_weapons = relationship(
        "ProfessionWeapon",
        back_populates="weapon_type",
        cascade="all, delete-orphan"
    )
    
    # Alias for backward compatibility
    skills = relationship("ProfessionWeaponSkill", viewonly=True, overlaps="weapon_skills")
    
    def __repr__(self):
        return f"<ProfessionWeaponType(id={self.id}, profession_id={self.profession_id}, weapon_type='{self.weapon_type}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'profession_id': self.profession_id,
            'weapon_type': self.weapon_type,
            'hand': self.hand,
            'specialization_id': self.specialization_id,
            'is_elite': self.is_elite,
            'skills': [skill.to_dict() for skill in self.skills] if self.skills else []
        }

class ProfessionWeaponSkill(Base):
    """Table d'association entre les compétences et les types d'armes de profession.
    
    Cette table établit une relation many-to-many entre les compétences et les types d'armes de profession,
    avec des métadonnées supplémentaires comme le slot et la spécialisation.
    """
    __tablename__ = 'profession_weapon_skills'
    
    # Clés primaires composées
    weapon_type_id = Column(
        Integer, 
        ForeignKey('profession_weapon_types.id', ondelete='CASCADE'), 
        primary_key=True,
        name='profession_weapon_id'  # Keep the old column name for backward compatibility
    )
    skill_id = Column(
        Integer, 
        ForeignKey('skills.id', ondelete='CASCADE'), 
        primary_key=True
    )
    
    # Métadonnées supplémentaires
    slot = Column(String(20), nullable=True)  # Par exemple: '1', '2', '3', '4', '5', 'heal', 'utility', 'elite'
    skill_type = Column(String(20), nullable=True)  # Par exemple: 'weapon', 'heal', 'utility', 'elite'
    
    # Relations
    weapon_type = relationship(
        "ProfessionWeaponType", 
        back_populates="weapon_skills",
        foreign_keys=[weapon_type_id]
    )
    skill = relationship("Skill", back_populates="profession_weapon_types")
    
    def __repr__(self):
        return f"<ProfessionWeaponSkill(weapon_type_id={self.weapon_type_id}, skill_id={self.skill_id})>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'profession_weapon_id': self.weapon_type_id,  # Keep old key for backward compatibility
            'weapon_type_id': self.weapon_type_id,
            'skill_id': self.skill_id,
            'slot': self.slot,
            'skill_type': self.skill_type
        }
