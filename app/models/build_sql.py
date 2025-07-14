"""Modèle SQLAlchemy pour les builds de personnages."""
from datetime import datetime
from typing import Dict, List
import json
from sqlalchemy import Column, Integer, String, Enum, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from app.database import Base
from .build import ProfessionType, RoleType, TraitLine, EquipmentItem

class Build(Base):
    """Modèle SQLAlchemy pour un build de personnage."""
    __tablename__ = 'builds'
    
    # Suppression du __init__ personnalisé pour utiliser la méthode standard SQLAlchemy
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    profession = Column(Enum(ProfessionType), nullable=False)
    role = Column(Enum(RoleType), nullable=False)
    
    # Stockage des spécialisations et compétences en JSON
    specializations = Column(JSON, nullable=False, default=list)
    skills = Column(JSON, nullable=False, default=list)
    equipment = Column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    
    # Métadonnées
    description = Column(Text, nullable=True)
    source = Column(String(512), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relation avec User (désactivée pour le moment)
    # TODO: Réactiver cette relation une fois le modèle User implémenté
    # user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    # user = relationship("User", back_populates="builds")
    
    # Méthodes pour la sérialisation/désérialisation
    def to_dict(self):
        """Convertit l'objet en dictionnaire."""
        return {
            'id': self.id,
            'name': self.name,
            'profession': self.profession.value,
            'role': self.role.value,
            'specializations': [
                {
                    'id': spec['id'],
                    'name': spec['name'],
                    'traits': spec['traits']
                } for spec in self.specializations
            ],
            'skills': self.skills,
            'equipment': {
                slot: {
                    'id': item['id'],
                    'name': item['name'],
                    'infusions': item.get('infusions', []),
                    'upgrades': item.get('upgrades', [])
                } for slot, item in self.equipment.items()
            },
            'description': self.description,
            'source': self.source,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_pydantic(cls, build_data: 'BuildData'):
        """Crée une instance de Build à partir d'un objet BuildData Pydantic."""
        return cls(
            name=build_data.name,
            profession=build_data.profession,
            role=build_data.role,
            specializations=[
                {
                    'id': spec.id,
                    'name': spec.name,
                    'traits': spec.traits
                } for spec in build_data.specializations
            ],
            skills=build_data.skills,
            equipment={
                slot: {
                    'id': item.id,
                    'name': item.name,
                    'infusions': item.infusions,
                    'upgrades': item.upgrades
                } for slot, item in build_data.equipment.items()
            },
            description=build_data.description,
            source=str(build_data.source) if build_data.source else None
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Build':
        """Crée une instance de Build à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données du build
            
        Returns:
            Une instance de Build
        """
        # Convertir les chaînes en énumérations si nécessaire
        if isinstance(data.get('profession'), str):
            data['profession'] = ProfessionType[data['profession']]
        if isinstance(data.get('role'), str):
            data['role'] = RoleType[data['role']]
            
        # Créer une instance de Build avec les données fournies
        build = cls(
            name=data['name'],
            profession=data['profession'],
            role=data['role'],
            specializations=data.get('specializations', []),
            skills=data.get('skills', []),
            equipment=data.get('equipment', {}),
            description=data.get('description'),
            source=data.get('source'),
            is_public=data.get('is_public', False)
        )
        
        return build
