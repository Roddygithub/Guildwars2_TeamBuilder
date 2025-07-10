"""Modèle SQLAlchemy pour les compétences GW2."""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Skill(Base):
    """Modèle représentant une compétence GW2."""
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(255))
    profession_id = Column(Integer, ForeignKey('professions.id'))
    specialization_id = Column(Integer, ForeignKey('specializations.id'))
    is_elite = Column(Boolean, default=False)
    slot = Column(String(50))  # heal/utility/elite/weapon
    
    # Relations
    profession = relationship("Profession", back_populates="skills")
    specialization = relationship("Specialization", back_populates="skills")
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"
