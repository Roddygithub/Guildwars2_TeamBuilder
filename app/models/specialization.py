"""Modèle SQLAlchemy pour les spécialisations GW2."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Specialization(Base):
    """Modèle représentant une spécialisation GW2."""
    __tablename__ = 'specializations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    profession_id = Column(Integer, ForeignKey('professions.id'), nullable=False)
    icon = Column(String(255))
    
    # Relations
    profession = relationship("Profession", back_populates="specializations")
    
    def __repr__(self):
        return f"<Specialization(id={self.id}, name='{self.name}')>"
