"""Modèle SQLAlchemy pour la relation entre les professions et les types d'accessoires."""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class ProfessionTrinketType(Base):
    """Représente un type d'accessoire utilisable par une profession spécifique.
    
    Cette table fait le lien entre une profession et un type d'accessoire (Amulette, Anneau, etc.).
    """
    __tablename__ = 'profession_trinket_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profession_id = Column(String(50), ForeignKey('professions.id', ondelete='CASCADE'), nullable=False, index=True)
    trinket_type = Column(String(50), nullable=False)  # Type d'accessoire (par exemple: 'Amulet', 'Ring', 'Accessory')
    is_aquatic = Column(Boolean, default=False, nullable=False)  # Si l'accessoire est aquatique
    
    # Relations
    profession = relationship("Profession", back_populates="trinket_types")
    
    def __repr__(self):
        return f"<ProfessionTrinketType(id={self.id}, profession_id={self.profession_id}, trinket_type='{self.trinket_type}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'profession_id': self.profession_id,
            'trinket_type': self.trinket_type,
            'is_aquatic': self.is_aquatic
        }
