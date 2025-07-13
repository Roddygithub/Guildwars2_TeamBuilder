"""Modèle SQLAlchemy pour la relation entre les professions et les types d'armures."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class ProfessionArmorType(Base):
    """Représente un type d'armure utilisable par une profession spécifique.
    
    Cette table fait le lien entre une profession et un type d'armure (Léger/Moyen/Lourd).
    """
    __tablename__ = 'profession_armor_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profession_id = Column(String(50), ForeignKey('professions.id', ondelete='CASCADE'), nullable=False, index=True)
    armor_type = Column(String(50), nullable=False)  # Type d'armure (par exemple: 'Light', 'Medium', 'Heavy')
    weight_class = Column(String(20), nullable=False)  # Classe de poids ('Cloth', 'Leather', 'Mail', 'Plate')
    
    # Relations
    profession = relationship("Profession", back_populates="armor_types")
    
    def __repr__(self):
        return f"<ProfessionArmorType(id={self.id}, profession_id={self.profession_id}, armor_type='{self.armor_type}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'profession_id': self.profession_id,
            'armor_type': self.armor_type,
            'weight_class': self.weight_class
        }
