"""Modèle pour les statistiques d'objets dans Guild Wars 2.

Ce module définit le modèle SQLAlchemy pour les statistiques d'objets (ItemStats) qui sont utilisées
pour définir les propriétés des objets dans le jeu.
"""
from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from app.database import Base

class ItemStats(Base):
    """Modèle représentant les statistiques d'un objet dans Guild Wars 2.
    
    Les statistiques d'objets définissent les bonus d'attributs (comme la puissance, la précision, etc.)
    qui sont appliqués aux personnages équipant des objets avec ces statistiques.
    """
    __tablename__ = 'item_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=False)  # Utilise l'ID de l'API GW2
    name = Column(String(255), nullable=False, index=True)  # Nom de la statistique (ex: "Berserker")
    name_fr = Column(String(255), nullable=True)  # Traduction française du nom
    
    # Description de la statistique
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)  # Traduction française de la description
    
    # Attributs de base
    power = Column(Integer, default=0)  # Puissance
    precision = Column(Integer, default=0)  # Précision
    toughness = Column(Integer, default=0)  # Résistance
    vitality = Column(Integer, default=0)  # Vitalité
    concentration = Column(Float, default=0.0)  # Concentration (augmente la durée des améliorations)
    condition_damage = Column(Integer, default=0)  # Dégâts d'altération
    expertise = Column(Float, default=0.0)  # Expertise (augmente la durée des altérations)
    ferocity = Column(Integer, default=0)  # Férocité (augmente les dégâts critiques)
    healing_power = Column(Integer, default=0)  # Pouvoir de soin
    
    # Attributs dérivés (peuvent être calculés à partir des attributs de base)
    armor = Column(Integer, default=0)  # Armure (défense)
    boon_duration = Column(Float, default=0.0)  # Durée des améliorations (%)
    critical_chance = Column(Float, default=0.0)  # Chance de coup critique (%)
    critical_damage = Column(Float, default=150.0)  # Dégâts critiques (%)
    condition_duration = Column(Float, default=0.0)  # Durée des altérations (%)
    
    # Les relations seront configurées après la définition des classes
    
    def __repr__(self):
        return f"<ItemStats(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'name_fr': self.name_fr,
            'description': self.description,
            'description_fr': self.description_fr,
            'power': self.power,
            'precision': self.precision,
            'toughness': self.toughness,
            'vitality': self.vitality,
            'concentration': self.concentration,
            'condition_damage': self.condition_damage,
            'expertise': self.expertise,
            'ferocity': self.ferocity,
            'healing_power': self.healing_power,
            'armor': self.armor,
            'boon_duration': self.boon_duration,
            'critical_chance': self.critical_chance,
            'critical_damage': self.critical_damage,
            'condition_duration': self.condition_duration
        }
