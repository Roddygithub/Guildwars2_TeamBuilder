"""Modèle SQLAlchemy pour la relation entre les compétences et les armes de profession.

Ce module définit les modèles pour gérer les relations entre les compétences, les armes
de profession et les types d'armes, avec des optimisations de performance.
"""

import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional, Type, TypeVar, TYPE_CHECKING
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, and_
from sqlalchemy.orm import relationship, Session, joinedload

from ..utils.db_utils import with_session
from .base import Base

if TYPE_CHECKING:
    from .skill import Skill
    from .profession import Profession
    from .specialization import Specialization

# Type variable pour les méthodes de classe
T = TypeVar('T', bound='ProfessionWeaponType')

# Configuration du logging
logger = logging.getLogger(__name__)

class ProfessionWeaponType(Base):
    """Représente un type d'arme utilisable par une profession spécifique.
    
    Cette table fait le lien entre une profession, un type d'arme et les compétences associées.
    Diffère de ProfessionWeapon qui fait le lien entre une profession et une arme spécifique.
    
    Ce modèle utilise plusieurs techniques d'optimisation :
    - Gestion automatique des sessions via @with_session
    - Mise en cache des requêtes fréquentes avec @lru_cache
    - Chargement par lots des relations pour éviter le problème N+1
    
    Attributes:
        id (int): Identifiant unique
        profession_id (str): ID de la profession
        weapon_type (str): Type d'arme (ex: 'Axe', 'Sword')
        hand (str): Type de prise en main ('MainHand', 'OffHand', 'TwoHand', 'Aquatic')
        specialization_id (int, optional): ID de la spécialisation requise
        is_elite (bool): Si l'arme nécessite une spécialisation élite
    """
    __tablename__ = 'profession_weapon_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profession_id = Column(String(50), ForeignKey('professions.id', ondelete='CASCADE'), nullable=False, index=True)
    weapon_type = Column(String(50), nullable=False)  # Type d'arme (par exemple: 'Axe', 'Sword', 'Greatsword')
    hand = Column(String(10), nullable=False)  # 'MainHand', 'OffHand', 'TwoHand', 'Aquatic'
    specialization_id = Column(Integer, ForeignKey('specializations.id', ondelete='SET NULL'), nullable=True)
    is_elite = Column(Boolean, default=False, nullable=False)  # Si l'arme nécessite une spécialisation élite
    
    # Relations
    profession = relationship("Profession", back_populates="weapon_types")
    specialization = relationship("Specialization", back_populates="weapon_types")
    weapon_skills = relationship(
        "ProfessionWeaponSkill", 
        back_populates="weapon_type", 
        cascade="all, delete-orphan",
        foreign_keys="[ProfessionWeaponSkill.weapon_type_id]"
    )
    profession_weapons = relationship(
        "ProfessionWeapon",
        back_populates="weapon_type",
        cascade="all, delete-orphan"
    )
    
    # Alias for backward compatibility
    skills = relationship("ProfessionWeaponSkill", viewonly=True, overlaps="weapon_skills")
    
    def __repr__(self):
        return f"<ProfessionWeaponType(id={self.id}, profession_id={self.profession_id}, weapon_type='{self.weapon_type}')>"
    
    def clear_cache(self):
        """Vide le cache pour cette instance."""
        if hasattr(self, '_weapons_cache'):
            del self._weapons_cache
        if hasattr(self, '_skills_cache'):
            del self._skills_cache
    
    @classmethod
    def get_by_id(
        cls: Type[T], 
        weapon_type_id: int, 
        session: Optional[Session] = None
    ) -> Optional[T]:
        """Récupère un type d'arme par son ID avec chargement optimisé des relations.
        
        Args:
            weapon_type_id: ID du type d'arme à récupérer
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            ProfessionWeaponType: Le type d'arme trouvé ou None
        """
        @with_session
        def _get_weapon_type(session: Session) -> Optional[T]:
            return session.query(cls).options(
                joinedload(cls.profession_weapons)
                    .joinedload(ProfessionWeapon.weapon),
                joinedload(cls.weapon_skills)
                    .joinedload(ProfessionWeaponSkill.skill),
                joinedload(cls.profession),
                joinedload(cls.specialization)
            ).get(weapon_type_id)
            
        return _get_weapon_type(session=session)
    
    @with_session
    def get_weapons(self, session: Session = None) -> List[Dict[str, Any]]:
        """Récupère les armes de ce type avec mise en cache.
        
        Returns:
            List[Dict]: Liste des armes de ce type avec leurs métadonnées
        """
        # Vérifie le cache
        if hasattr(self, '_weapons_cache'):
            return self._weapons_cache
            
        # Récupère les armes de ce type avec chargement optimisé
        weapons = session.query(Weapon).join(
            ProfessionWeapon,
            and_(
                ProfessionWeapon.weapon_type_id == self.id,
                ProfessionWeapon.weapon_id == Weapon.id
            )
        ).options(
            joinedload(Weapon.skills)
        ).all()
        
        # Formate les résultats
        result = [{
            'id': w.id,
            'name': w.name,
            'type': w.type.value if w.type else None,
            'rarity': w.rarity,
            'level': w.level,
            'skills': [s.to_dict(include_related=False) for s in w.skills] if w.skills else []
        } for w in weapons]
        
        # Met en cache le résultat
        self._weapons_cache = result
        return result
    
    @with_session
    def get_skills_by_slot(self, slot: str = None, session: Session = None) -> List[Dict[str, Any]]:
        """Récupère les compétences de ce type d'arme, éventuellement filtrées par slot.
        
        Args:
            slot: Slot de compétence à filtrer (ex: '1', '2', 'heal', 'utility', 'elite')
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            List[Dict]: Liste des compétences avec leurs métadonnées
        """
        cache_key = f"skills_{slot if slot else 'all'}"
        
        # Vérifie le cache
        if hasattr(self, '_skills_cache') and cache_key in self._skills_cache:
            return self._skills_cache[cache_key]
            
        # Construit la requête de base
        query = session.query(ProfessionWeaponSkill, Skill).join(
            Skill,
            ProfessionWeaponSkill.skill_id == Skill.id
        ).filter(
            ProfessionWeaponSkill.weapon_type_id == self.id
        )
        
        # Filtre par slot si spécifié
        if slot is not None:
            query = query.filter(ProfessionWeaponSkill.slot == slot)
            
        # Exécute la requête
        results = query.options(
            joinedload(Skill.facts),
            joinedload(Skill.traits)
        ).all()
        
        # Formate les résultats
        skills = []
        for pws, skill in results:
            skill_data = skill.to_dict(include_related=False)
            skill_data.update({
                'slot': pws.slot,
                'skill_type': pws.skill_type
            })
            skills.append(skill_data)
        
        # Initialise le cache si nécessaire
        if not hasattr(self, '_skills_cache'):
            self._skills_cache = {}
            
        # Met en cache le résultat
        self._skills_cache[cache_key] = skills
        return skills
    
    @classmethod
    def batch_load_by_profession(
        cls: Type[T],
        profession_id: str,
        session: Optional[Session] = None
    ) -> List[T]:
        """Charge tous les types d'armes pour une profession donnée.
        
        Args:
            profession_id: ID de la profession
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            List[ProfessionWeaponType]: Liste des types d'armes pour la profession
        """
        @with_session
        def _batch_load(session: Session) -> List[T]:
            return session.query(cls).options(
                joinedload(cls.weapon_skills)
                    .joinedload(ProfessionWeaponSkill.skill),
                joinedload(cls.specialization)
            ).filter(
                cls.profession_id == profession_id
            ).order_by(
                cls.weapon_type,
                cls.hand
            ).all()
            
        return _batch_load(session=session)
    
    def to_dict(self, include_related: bool = True) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire pour la sérialisation JSON.
        
        Args:
            include_related: Si True, inclut les objets liés (compétences, spécialisation, etc.)
            
        Returns:
            Dict: Représentation du type d'arme sous forme de dictionnaire
        """
        result = {
            'id': self.id,
            'profession_id': self.profession_id,
            'weapon_type': self.weapon_type,
            'hand': self.hand,
            'specialization_id': self.specialization_id,
            'is_elite': self.is_elite
        }
        
        if include_related:
            # Charge les relations si nécessaire (avec lazy loading)
            try:
                # Charge les compétences de base
                if hasattr(self, 'weapon_skills') and self.weapon_skills:
                    result['skills'] = [
                        {
                            'id': pws.skill_id,
                            'slot': pws.slot,
                            'skill_type': pws.skill_type,
                            'skill': pws.skill.to_dict(include_related=False) if pws.skill else None
                        }
                        for pws in self.weapon_skills
                    ]
                
                # Charge la spécialisation si disponible
                if hasattr(self, 'specialization') and self.specialization:
                    result['specialization'] = self.specialization.to_dict(include_related=False)
                    
                # Charge la profession si disponible
                if hasattr(self, 'profession') and self.profession:
                    result['profession'] = self.profession.to_dict(include_related=False)
                    
            except Exception as e:
                logger.warning(
                    f"Erreur lors du chargement des relations pour le type d'arme {self.id}: {e}"
                )
        
        return result

class ProfessionWeaponSkill(Base):
    """Table d'association entre les compétences et les types d'armes de profession.
    
    Cette table établit une relation many-to-many entre les compétences et les types d'armes de profession,
    avec des métadonnées supplémentaires comme le slot et la spécialisation.
    
    Attributes:
        weapon_type_id (int): ID du type d'arme
        skill_id (int): ID de la compétence
        slot (str, optional): Emplacement de la compétence (ex: '1', '2', 'heal')
        skill_type (str, optional): Type de compétence (ex: 'weapon', 'heal', 'utility')
    """
    __tablename__ = 'profession_weapon_skills'
    
    # Clés primaires composées
    weapon_type_id = Column(
        Integer, 
        ForeignKey('profession_weapon_types.id', ondelete='CASCADE'), 
        primary_key=True,
        name='profession_weapon_id'  # Keep the old column name for backward compatibility
    )
    skill_id = Column(
        Integer, 
        ForeignKey('skills.id', ondelete='CASCADE'), 
        primary_key=True
    )
    
    # Métadonnées supplémentaires
    slot = Column(String(20), nullable=True)  # Par exemple: '1', '2', '3', '4', '5', 'heal', 'utility', 'elite'
    skill_type = Column(String(20), nullable=True)  # Par exemple: 'weapon', 'heal', 'utility', 'elite'
    
    # Relations
    weapon_type = relationship(
        "ProfessionWeaponType", 
        back_populates="weapon_skills",
        foreign_keys=[weapon_type_id]
    )
    skill = relationship("Skill", back_populates="profession_weapon_types")
    
    def __repr__(self):
        return f"<ProfessionWeaponSkill(weapon_type_id={self.weapon_type_id}, skill_id={self.skill_id})>"
    
    @classmethod
    def batch_load_by_weapon_types(
        cls,
        weapon_type_ids: List[int],
        session: Optional[Session] = None
    ) -> Dict[int, List['ProfessionWeaponSkill']]:
        """Charge les compétences d'arme pour plusieurs types d'armes en une seule requête.
        
        Args:
            weapon_type_ids: Liste des IDs de types d'armes
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            Dict[int, List[ProfessionWeaponSkill]]: Dictionnaire {weapon_type_id: [skills]}
        """
        @with_session
        def _batch_load(session: Session) -> Dict[int, List['ProfessionWeaponSkill']]:
            if not weapon_type_ids:
                return {}
                
            # Récupère toutes les compétences pour les types d'armes demandés
            skills = session.query(cls).filter(
                cls.weapon_type_id.in_(weapon_type_ids)
            ).options(
                joinedload(cls.skill)
            ).all()
            
            # Groupe les compétences par weapon_type_id
            result = {}
            for skill in skills:
                if skill.weapon_type_id not in result:
                    result[skill.weapon_type_id] = []
                result[skill.weapon_type_id].append(skill)
                
            return result
            
        return _batch_load(session=session)
    
    def to_dict(self, include_related: bool = False) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire pour la sérialisation JSON.
        
        Args:
            include_related: Si True, inclut les objets liés (compétence)
            
        Returns:
            Dict: Représentation de la compétence d'arme sous forme de dictionnaire
        """
        result = {
            'profession_weapon_id': self.weapon_type_id,  # Rétrocompatibilité
            'weapon_type_id': self.weapon_type_id,
            'skill_id': self.skill_id,
            'slot': self.slot,
            'skill_type': self.skill_type
        }
        
        if include_related and hasattr(self, 'skill') and self.skill:
            result['skill'] = self.skill.to_dict(include_related=False)
            
        return result
