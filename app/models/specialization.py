"""Modèle SQLAlchemy pour les spécialisations GW2."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Specialization(Base):
    """Modèle représentant une spécialisation GW2.
    
    Une spécialisation est un ensemble de traits et de compétences qui modifient la façon dont une profession est jouée.
    Chaque profession a plusieurs spécialisations, dont certaines sont des spécialisations d'élite.
    
    Exemple d'utilisation:
        ```python
        # Récupérer toutes les spécialisations d'élite d'une profession
        elite_specs = session.query(Specialization).filter(
            Specialization.profession_id == 'Guardian',
            Specialization.elite == True
        ).all()
        
        # Récupérer les traits majeurs d'une spécialisation
        dragonhunter = session.query(Specialization).filter_by(name='Dragonhunter').first()
        major_traits = session.query(Trait).filter(
            Trait.id.in_(dragonhunter.major_traits)
        ).all()
        ```
        
    Attributes:
        id (int): Identifiant unique de la spécialisation
        name (str): Nom de la spécialisation (en anglais)
        name_fr (str): Nom de la spécialisation en français
        profession_id (str): ID de la profession parente (format: 'Guardian', 'Warrior', etc.)
        elite (bool): Si c'est une spécialisation d'élite
        minor_traits (List[int]): Liste des IDs des traits mineurs
        major_traits (List[int]): Liste des IDs des traits majeurs
        weapon_trait (int): ID du trait d'arme associé (si applicable)
        icon (str): URL de l'icône de la spécialisation
        background (str): URL de l'image de fond de la spécialisation
        profession_icon (str): URL de l'icône de la profession associée
        profession_icon_big (str): URL de la grande icône de la profession
        description (str): Description de la spécialisation
        playable (bool): Si la spécialisation est jouable
        
        # Relations
        profession (Profession): relation avec la profession parente
        skills (List[Skill]): compétences spécifiques à cette spécialisation
        traits (List[Trait]): traits spécifiques à cette spécialisation
        weapon_types (List[ProfessionWeaponType]): types d'armes accessibles avec cette spécialisation
    """
    __tablename__ = 'specializations'
    
    # Configuration de la table
    __table_args__ = (
        # Index sur les champs fréquemment utilisés dans les WHERE
        {'sqlite_autoincrement': True},
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True, index=True)
    name_de = Column(String(100), nullable=True, index=True)
    name_es = Column(String(100), nullable=True, index=True)
    profession_id = Column(
        String(50), 
        ForeignKey('professions.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    elite = Column(Boolean, default=False, index=True)
    minor_traits = Column(JSON, nullable=True)  # Liste des IDs des traits mineurs
    major_traits = Column(JSON, nullable=True)  # Liste des IDs des traits majeurs
    weapon_trait = Column(Integer, nullable=True)  # ID du trait d'arme
    icon = Column(String(255))
    background = Column(String(255))
    profession_icon = Column(String(255))
    profession_icon_big = Column(String(255))
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)
    description_es = Column(Text, nullable=True)
    playable = Column(Boolean, default=True, index=True)
    background_legendary = Column(String(255), nullable=True)  # Version légendaire du fond
    training_track_ids = Column(JSON, nullable=True)  # IDs des voies d'entraînement
    flags = Column(JSON, nullable=True)  # Flags supplémentaires
    created = Column(String(50), nullable=True)  # Date de création dans l'API
    updated = Column(String(50), nullable=True)  # Date de dernière mise à jour
    
    # Relations
    profession = relationship(
        "Profession",
        back_populates="specializations",
        lazy="selectin"  # Chargement plus efficace pour les requêtes fréquentes
    )
    
    # Relation avec les types d'armes de la spécialisation
    weapon_types = relationship(
        "ProfessionWeaponType",
        back_populates="specialization",
        cascade="all, delete-orphan",
        lazy="selectin"  # Chargement plus efficace pour les requêtes fréquentes
    )
    
    skills = relationship(
        "Skill",
        back_populates="specialization",
        foreign_keys="[Skill.specialization_id]",
        lazy="selectin"  # Chargement plus efficace pour les requêtes fréquentes
    )
    
    traits = relationship(
        "Trait",
        back_populates="specialization",
        foreign_keys="[Trait.specialization_id]",
        cascade="all, delete-orphan",
        lazy="selectin"  # Chargement plus efficace pour les requêtes fréquentes
    )
    
    def __repr__(self):
        return f"<Specialization(id={self.id}, name='{self.name}')>"
    
    def to_dict(self, include_related=True):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON.
        
        Args:
            include_related (bool): Si True, inclut les objets liés (skills, traits, etc.)
            
        Returns:
            dict: Dictionnaire représentant la spécialisation
        """
        result = {
            'id': self.id,
            'name': self.name,
            'name_fr': self.name_fr,
            'name_de': self.name_de,
            'name_es': self.name_es,
            'profession_id': self.profession_id,
            'elite': self.elite,
            'minor_traits': self.minor_traits or [],
            'major_traits': self.major_traits or [],
            'weapon_trait': self.weapon_trait,
            'icon': self.icon,
            'background': self.background,
            'background_legendary': self.background_legendary,
            'profession_icon': self.profession_icon,
            'profession_icon_big': self.profession_icon_big,
            'description': self.description,
            'description_fr': self.description_fr,
            'description_de': self.description_de,
            'description_es': self.description_es,
            'playable': self.playable,
            'training_track_ids': self.training_track_ids or [],
            'flags': self.flags or [],
            'created': self.created,
            'updated': self.updated,
        }
        
        if include_related:
            result.update({
                'weapon_types': [wt.to_dict(include_related=False) for wt in self.weapon_types],
                'skills': [s.to_dict(include_related=False) for s in self.skills],
                'traits': [t.to_dict(include_related=False) for t in self.traits]
            })
        
        return result
    
    def get_minor_traits_list(self, session=None):
        """Retourne la liste des objets Trait mineurs.
        
        Args:
            session: Session SQLAlchemy (optionnel, si fournie, évite une nouvelle requête)
            
        Returns:
            List[Trait]: Liste des traits mineurs de la spécialisation
        """
        if not self.minor_traits:
            return []
            
        if session is not None:
            from .trait import Trait
            return session.query(Trait).filter(Trait.id.in_(self.minor_traits)).all()
            
        return [t for t in (self.traits or []) if t.id in (self.minor_traits or [])]
    
    def get_major_traits_list(self, session=None):
        """Retourne la liste des objets Trait majeurs.
        
        Args:
            session: Session SQLAlchemy (optionnel, si fournie, évite une nouvelle requête)
            
        Returns:
            List[Trait]: Liste des traits majeurs de la spécialisation
        """
        if not self.major_traits:
            return []
            
        if session is not None:
            from .trait import Trait
            return session.query(Trait).filter(Trait.id.in_(self.major_traits)).all()
            
        return [t for t in (self.traits or []) if t.id in (self.major_traits or [])]
    
    def get_weapon_skills(self, weapon_type, hand=None, session=None):
        """Récupère les compétences d'arme pour un type d'arme donné.
        
        Args:
            weapon_type (WeaponType): Type d'arme à rechercher
            hand (str, optional): 'MainHand', 'OffHand' ou 'TwoHand'
            session: Session SQLAlchemy (optionnel)
            
        Returns:
            List[Skill]: Liste des compétences correspondantes
        """
        from .skill import Skill
        from .weapon import WeaponType
        
        weapon_type_str = weapon_type.value if hasattr(weapon_type, 'value') else str(weapon_type)
        
        query = {
            'specialization_id': self.id,
            'weapon_type': weapon_type_str
        }
        
        if hand:
            query['hand'] = hand
            
        if session is not None:
            return session.query(Skill).filter_by(**query).all()
            
        return [s for s in (self.skills or []) 
                if s.weapon_type == weapon_type_str and 
                (hand is None or getattr(s, 'hand', None) == hand)]
