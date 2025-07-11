"""Modèle pour la relation entre les objets et leurs statistiques dans Guild Wars 2."""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class ItemStat(Base):
    """Table d'association entre les objets (Item) et leurs statistiques (ItemStats)."""
    __tablename__ = 'item_stat_mapping'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False, index=True)
    stat_id = Column(Integer, ForeignKey('item_stats.id'), nullable=False, index=True)
    value = Column(Integer, default=0)  # Valeur de la statistique pour cet objet
    
    # Relations avec des chaînes pour éviter les imports circulaires
    item = relationship("Item", back_populates="stat_mappings")
    statistics = relationship("ItemStats", back_populates="stat_mappings")
    
    def __repr__(self):
        return f"<ItemStat(item_id={self.item_id}, stat_id={self.stat_id}, value={self.value})>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'item_id': self.item_id,
            'stat_id': self.stat_id,
            'value': self.value
        }
