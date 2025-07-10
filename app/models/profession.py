"""Modèle SQLAlchemy pour les professions GW2."""

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from .base import Base

class Profession(Base):
    """Modèle représentant une profession GW2."""
    __tablename__ = 'professions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    icon = Column(String(255))
    
    # Relations
    specializations = relationship("Specialization", back_populates="profession")
    
    def __repr__(self):
        return f"<Profession(id={self.id}, name='{self.name}')>"
