"""Modèles SQLAlchemy pour les entités Guild Wars 2 nécessaires à la construction d'équipe.

Ce module définit les modèles de données pour les entités GW2 (professions, spécialisations, compétences)
et fournit des méthodes utilitaires pour interagir avec ces données.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Any
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, JSON, Index, ForeignKey, event, Table, DateTime, Boolean
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.database import Base
from app.logging_config import get_logger

logger = get_logger(__name__)


class Profession(Base):
    """Représente une profession de Guild Wars 2.
    
    Une profession est une classe de personnage jouable dans GW2, comme le Gardien,
    le Voleur, ou le Mécano.
    """
    __tablename__ = "professions"
    __table_args__ = (
        Index('idx_profession_name', 'name'),  # Index pour les recherches par nom
        {'sqlite_autoincrement': True},
    )

    # Colonnes
    id = Column(
        String(32), 
        primary_key=True, 
        index=True,
        comment="Identifiant unique de la profession (ex: 'Guardian', 'Thief')"
    )
    
    name = Column(
        String(100), 
        nullable=False,
        index=True,
        comment="Nom affiché de la profession (ex: 'Gardien', 'Voleur')"
    )
    
    data = Column(
        JSON, 
        nullable=False,
        comment="Données brutes de l'API GW2 pour cette profession"
    )
    
    # Relations
    specializations = relationship(
        "Specialization", 
        back_populates="profession",
        cascade="all, delete-orphan"
    )
    
    # Méthodes utilitaires
    def get_elite_specs(self) -> List[Dict[str, Any]]:
        """Retourne la liste des spécialisations d'élite pour cette profession."""
        return [spec for spec in self.data.get('specializations', []) if spec.get('elite', False)]
    
    def get_core_attributes(self) -> Set[str]:
        """Retourne l'ensemble des attributs de base de la profession."""
        return set(self.data.get('attributes', []))
    
    def get_weapons(self) -> Dict[str, List[str]]:
        """Retourne les armes disponibles pour cette profession."""
        return self.data.get('weapons', {})
    
    def __repr__(self) -> str:
        return f"<Profession(id='{self.id}', name='{self.name}')>"


class Specialization(Base):
    """Représente une spécialisation de profession dans Guild Wars 2.
    
    Une spécialisation est une branche de compétences qui modifie la façon dont
    une profession est jouée. Certaines spécialisations sont des spécialisations d'élite.
    """
    __tablename__ = "specializations"
    __table_args__ = (
        Index('idx_spec_profession', 'profession_id'),
        Index('idx_spec_name', 'name'),
        {'sqlite_autoincrement': True},
    )

    # Colonnes
    id = Column(
        Integer, 
        primary_key=True,
        comment="Identifiant unique de la spécialisation"
    )
    
    name = Column(
        String(100), 
        nullable=False,
        index=True,
        comment="Nom affiché de la spécialisation"
    )
    
    profession_id = Column(
        String(32), 
        ForeignKey('professions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Identifiant de la profession parente"
    )
    
    elite = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Niveau d'élite (0=non, 1=élite, 2=spécialisation d'élite)"
    )
    
    data = Column(
        JSON, 
        nullable=False,
        comment="Données brutes de l'API GW2 pour cette spécialisation"
    )
    
    # Relations
    profession = relationship("Profession", back_populates="specializations")
    
    # Méthodes utilitaires
    def is_elite(self) -> bool:
        """Détermine si c'est une spécialisation d'élite."""
        return self.elite > 0
    
    def get_traits(self) -> List[Dict[str, Any]]:
        """Retourne la liste des traits de cette spécialisation."""
        return self.data.get('major_traits', []) + self.data.get('minor_traits', [])
    
    def __repr__(self) -> str:
        return f"<Specialization(id={self.id}, name='{self.name}', elite={self.is_elite()})>"


class Skill(Base):
    """Représente une compétence dans Guild Wars 2.
    
    Une compétence est une capacité qu'un personnage peut utiliser, comme une attaque,
    une compétence de soin ou un buff.
    """
    __tablename__ = "skills"
    __table_args__ = (
        Index('idx_skill_name', 'name'),
        Index('idx_skill_profession', 'profession_id'),
        Index('idx_skill_type', 'skill_type'),
        {'sqlite_autoincrement': True},
    )

    # Colonnes
    id = Column(
        Integer, 
        primary_key=True,
        comment="Identifiant unique de la compétence"
    )
    
    name = Column(
        String(100), 
        nullable=False,
        index=True,
        comment="Nom affiché de la compétence"
    )
    
    profession_id = Column(
        String(32), 
        ForeignKey('professions.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Identifiant de la profession associée (null si commune)"
    )
    
    skill_type = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Type de compétence (ex: 'Heal', 'Utility', 'Elite', 'Weapon')"
    )
    
    data = Column(
        JSON, 
        nullable=False,
        comment="Données brutes de l'API GW2 pour cette compétence"
    )
    
    # Relations
    profession = relationship("Profession")
    
    # Méthodes utilitaires
    def get_categories(self) -> List[str]:
        """Retourne les catégories de la compétence (ex: ['Stance', 'Physical'])."""
        return self.data.get('categories', [])
    
    def get_facts(self) -> List[Dict[str, Any]]:
        """Retourne les faits (effets) de la compétence."""
        return self.data.get('facts', []) + self.data.get('traited_facts', [])
    
    def is_healing_skill(self) -> bool:
        """Détermine si c'est une compétence de soin."""
        return "Heal" in self.get_categories()
    
    def is_utility_skill(self) -> bool:
        """Détermine si c'est une compétence utilitaire."""
        return self.skill_type == "Utility"
    
    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', type='{self.skill_type}')>"


# Table d'association pour les builds et les compétences
build_skills = Table(
    'build_skills',
    Base.metadata,
    Column('build_id', Integer, ForeignKey('builds.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True),
    Column('slot', Integer, nullable=False, comment='Emplacement de la compétence (0-4)')
)

# Table d'association pour les builds et les spécialisations
build_specializations = Table(
    'build_specializations',
    Base.metadata,
    Column('build_id', Integer, ForeignKey('builds.id'), primary_key=True),
    Column('specialization_id', Integer, ForeignKey('specializations.id'), primary_key=True),
    Column('trait_choices', JSON, nullable=True, comment='Choix de traits pour cette spécialisation')
)

class Build(Base):
    """Représente un build de joueur sauvegardé.
    
    Ce modèle stocke les informations sur un build de personnage, y compris les compétences,
    les spécialisations et l'équipement.
    """
    __tablename__ = "builds"
    __table_args__ = (
        Index('idx_build_name', 'name'),
        Index('idx_build_profession', 'profession_id'),
        Index('idx_build_created_at', 'created_at'),
        {'sqlite_autoincrement': True},
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Identifiant unique du build"
    )
    
    name = Column(
        String(100),
        nullable=False,
        comment="Nom du build"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Description du build et notes"
    )
    
    profession_id = Column(
        String(32),
        ForeignKey('professions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Identifiant de la profession du build"
    )
    
    elite_spec_id = Column(
        Integer,
        ForeignKey('specializations.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Identifiant de la spécialisation d'élite (si applicable)"
    )
    
    role = Column(
        String(50),
        nullable=False,
        comment="Rôle principal du build (ex: 'dps', 'heal', 'support', 'tank')"
    )
    
    playstyle = Column(
        String(50),
        nullable=True,
        comment="Style de jeu (ex: 'zerg', 'havoc', 'roaming', 'fractal', 'raid')"
    )
    
    equipment = Column(
        JSON,
        nullable=False,
        default=dict,
        comment="Équipement du personnage (armes, armures, bijoux, etc.)"
    )
    
    buffs = Column(
        JSON,
        nullable=False,
        default=list,
        comment="Liste des buffs fournis par le build"
    )
    
    is_public = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Si le build est public ou privé"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date de création du build"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Dernière mise à jour du build"
    )
    
    created_by = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="ID de l'utilisateur qui a créé le build"
    )
    
    # Relations
    profession = relationship("Profession", back_populates="builds", cascade="all, delete-orphan")
    elite_spec = relationship("Specialization")
    skills = relationship(
        "Skill",
        secondary=build_skills,
        back_populates="builds",
        viewonly=True
    )
    specializations = relationship(
        "Specialization",
        secondary=build_specializations,
        back_populates="builds",
        viewonly=True
    )
    
    def __repr__(self):
        return f"<Build {self.id}: {self.name} ({self.profession_id} - {self.role})>"
    
    def to_dict(self):
        """Convertit le build en dictionnaire pour la sérialisation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "profession_id": self.profession_id,
            "elite_spec_id": self.elite_spec_id,
            "role": self.role,
            "playstyle": self.playstyle,
            "equipment": self.equipment,
            "buffs": self.buffs,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }

# Événements et hooks
@event.listens_for(Profession, 'after_insert')
def log_profession_insert(mapper, connection, target):
    """Log l'insertion d'une nouvelle profession."""
    logger.info("Nouvelle profession ajoutée: %s (ID: %s)", target.name, target.id)


@event.listens_for(Specialization, 'after_insert')
def log_specialization_insert(mapper, connection, target):
    """Log l'insertion d'une nouvelle spécialisation."""
    logger.info(
        "Nouvelle spécialisation ajoutée: %s (ID: %d, Élite: %s)",
        target.name, target.id, "Oui" if target.is_elite() else "Non"
    )
