"""Modèle SQLAlchemy pour les armes GW2.

Ce module définit le modèle Weapon pour les armes dans Guild Wars 2, avec des optimisations
pour les performances, y compris la mise en cache et le chargement par lots.
"""

import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional, TypeVar, Type, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum, Float, Table
from sqlalchemy.orm import relationship, Session, joinedload
from enum import Enum as PyEnum

from ..utils.db_utils import with_session
from .base import Base
from .item import Rarity

if TYPE_CHECKING:
    from .skill import Skill
    from .profession import Profession
    from .specialization import Specialization
    from .item import Item, Rarity
    from .upgrade_component import UpgradeComponent

# Type variable pour les méthodes de classe
T = TypeVar('T', bound='Weapon')

# Configuration du logging
logger = logging.getLogger(__name__)

class WeaponType(PyEnum):
    """Types d'armes dans GW2.
    
    Note: Les armes sont organisées par catégories logiques pour une meilleure lisibilité.
    """
    # Armes à une main
    AXE = "Axe"
    DAGGER = "Dagger"
    MACE = "Mace"
    PISTOL = "Pistol"
    SWORD = "Sword"
    SCEPTER = "Scepter"
    
    # Armes à deux mains
    GREATSWORD = "Greatsword"
    HAMMER = "Hammer"
    LONGBOW = "Longbow"
    RIFLE = "Rifle"
    SHORTBOW = "Shortbow"
    SPEARGUN = "Speargun"
    STAFF = "Staff"
    
    # Armes aquatiques
    HARPOON = "Harpoon"
    SPEAR = "Spear"
    TRIDENT = "Trident"
    
    # Armes spéciales et accessoires
    FOCUS = "Focus"
    SHIELD = "Shield"
    TORCH = "Torch"
    WARHORN = "Warhorn"
    
    # Objets spéciaux
    SCYTHE = "Scythe"
    LARGE_BUNDLE = "LargeBundle"
    SMALL_BUNDLE = "SmallBundle"
    TOY = "Toy"

class DamageType(PyEnum):
    """Types de dégâts des armes."""
    PHYSICAL = "Physical"
    FIRE = "Fire"
    ICE = "Ice"
    LIGHTNING = "Lightning"
    CHAOS = "Chaos"
    
class WeaponSlot(PyEnum):
    """Emplacements d'armes."""
    WEAPON_A1 = "WeaponA1"  # Arme principale main droite
    WEAPON_A2 = "WeaponA2"  # Arme principale main gauche
    WEAPON_B1 = "WeaponB1"  # Arme secondaire main droite
    WEAPON_B2 = "WeaponB2"  # Arme secondaire main gauche
    AQUATIC = "Aquatic"     # Arme aquatique
    PROFESSION_1 = "Profession1"  # Compétence de profession 1
    PROFESSION_2 = "Profession2"  # Compétence de profession 2
    PROFESSION_3 = "Profession3"  # Compétence de profession 3
    PROFESSION_4 = "Profession4"  # Compétence de profession 4
    PROFESSION_5 = "Profession5"  # Compétence de profession 5

class WeaponFlag(PyEnum):
    """Drapeaux pour les propriétés spéciales des armes."""
    MAINHAND = "Mainhand"
    OFFHAND = "Offhand"
    TWO_HAND = "TwoHand"
    AQUATIC = "Aquatic"
    NO_OFFHAND = "NoOffhand"
    NO_MAINHAND = "NoMainhand"

class Weapon(Base):
    """Modèle représentant une arme GW2 avec des optimisations de performances.
    
    Ce modèle utilise plusieurs techniques d'optimisation :
    - Gestion automatique des sessions via @with_session
    - Mise en cache des requêtes fréquentes avec @lru_cache
    - Chargement par lots des relations pour éviter le problème N+1
    
    Attributes:
        id (int): Identifiant unique de l'arme
        name (str): Nom de l'arme (en anglais)
        name_fr (str): Nom de l'arme en français
        description (str): Description de l'arme
        description_fr (str): Description de l'arme en français
        icon (str): URL de l'icône de l'arme
        chat_link (str): Lien de chat pour l'arme
        type (WeaponType): Type d'arme
        damage_type (DamageType): Type de dégâts
        min_power (int): Dégâts minimaux
        max_power (int): Dégâts maximaux
        defense (int): Défense (pour les boucliers)
        attributes (dict): Attributs de l'arme (Précision, Puissance, etc.)
        infusion_slots (List[dict]): Emplacements d'infusions
        infusion_upgrade_flags (List[str]): Types d'infusions compatibles
        suffix_item_id (int): ID de l'objet suffixe (pour les armes exotiques)
        secondary_suffix_item_id (str): ID secondaire de l'objet suffixe
        stat_choices (List[int]): IDs des choix de statistiques
        game_types (List[str]): Types de jeu où l'arme est utilisable (PvE, PvP, WvW)
        flags (List[WeaponFlag]): Drapeaux de propriétés spéciales
        restrictions (List[str]): Restrictions d'utilisation (professions, etc.)
        rarity (Rarity): Rareté de l'arme (Junk, Basic, Fine, Masterwork, Rare, Exotic, Ascended, Legendary)
        level (int): Niveau requis pour utiliser l'arme
        default_skin (int): ID du skin par défaut
        details (dict): Détails spécifiques à l'arme (dégâts par seconde, etc.)
        
    Relations:
        profession_weapons: Relation avec les armes de profession
        skills: Compétences associées à cette arme (many-to-many)
        upgrades: Composants d'amélioration compatibles (many-to-many)
        item: Objet Item associé à cette arme (one-to-one)
    """
    __tablename__ = 'weapons'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    icon = Column(String(255))
    chat_link = Column(String(100), nullable=True)
    type = Column(Enum(WeaponType), nullable=False, index=True)
    damage_type = Column(Enum(DamageType, values_callable=lambda x: [e.value for e in DamageType]), nullable=True)
    min_power = Column(Integer, nullable=True)
    max_power = Column(Integer, nullable=True)
    defense = Column(Integer, nullable=True)
    attributes = Column(JSON, nullable=True)  # Dictionnaire d'attributs
    infusion_slots = Column(JSON, nullable=True)  # Liste d'emplacements d'infusion
    infusion_upgrade_flags = Column(JSON, nullable=True)  # Types d'infusions
    suffix_item_id = Column(Integer, nullable=True)
    secondary_suffix_item_id = Column(String(50), nullable=True)
    stat_choices = Column(JSON, nullable=True)  # Liste d'IDs de statistiques
    game_types = Column(JSON, nullable=True)  # Liste de types de jeu
    flags = Column(JSON, nullable=True)  # Liste de WeaponFlag
    restrictions = Column(JSON, nullable=True)  # Liste de restrictions
    rarity = Column(Enum(Rarity), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=0, index=True)
    default_skin = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)  # Détails spécifiques
    
    # Clé étrangère vers la table items
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Relation avec Item
    item = relationship("Item", back_populates="weapon", uselist=False)
    
    # Relations avec d'autres tables
    profession_weapons = relationship(
        "ProfessionWeapon",
        back_populates="weapon",
        cascade="all, delete-orphan"
    )
    
    skills = relationship(
        "Skill",
        secondary="weapon_skills",
        back_populates="weapons"
    )
    
    upgrades = relationship(
        "UpgradeComponent",
        secondary="weapon_upgrade_components",
        back_populates="weapons"
    )
    
    def __repr__(self):
        return f"<Weapon(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def clear_cache(self):
        """Vide le cache pour cette instance."""
        # Invalide les caches pour cette instance
        self.get_skills_by_type.cache_clear()
        self.get_profession_weapons.cache_clear()
    
    @classmethod
    def get_by_id(cls: Type[T], weapon_id: int, session: Optional[Session] = None) -> Optional[T]:
        """Récupère une arme par son ID avec chargement optimisé des relations.
        
        Args:
            weapon_id: ID de l'arme à récupérer
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            Weapon: L'arme trouvée ou None
        """
        @with_session
        def _get_weapon(session: Session) -> Optional[T]:
            return session.query(cls).options(
                joinedload(cls.profession_weapons)
                    .joinedload(ProfessionWeapon.weapon_type)
                    .joinedload(ProfessionWeaponType.weapon_skills)
                    .joinedload(ProfessionWeapon.skill),
                joinedload(cls.skills),
                joinedload(cls.upgrades),
                joinedload(cls.item)
            ).get(weapon_id)
            
        return _get_weapon(session=session)
    
    @with_session
    def get_skills_by_type(self, skill_type: str, session: Session = None) -> List['Skill']:
        """Récupère les compétences de l'arme par type avec mise en cache.
        
        Args:
            skill_type: Type de compétence à filtrer (ex: 'weapon', 'heal')
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            List[Skill]: Liste des compétences correspondant au type
        """
        # Utilisation de l'ID de l'arme comme clé de cache
        cache_key = f"{self.id}_{skill_type}"
        
        @lru_cache(maxsize=128)
        def _get_skills(weapon_id: int, skill_type: str) -> List['Skill']:
            from .skill import Skill
            
            # Récupère les IDs des compétences liées à cette arme
            skill_ids = [skill.id for skill in self.skills]
            
            if not skill_ids:
                return []
                
            # Filtre par type de compétence
            return session.query(Skill).filter(
                Skill.id.in_(skill_ids),
                Skill.type == skill_type
            ).all()
            
        # Invalide le cache si nécessaire
        if not hasattr(self, '_skills_cache'):
            self._skills_cache = {}
            
        if cache_key not in self._skills_cache:
            self._skills_cache[cache_key] = _get_skills(self.id, skill_type)
            
        return self._skills_cache[cache_key]
    
    @with_session
    def get_profession_weapons(self, session: Session = None) -> List[Dict[str, Any]]:
        """Récupère les informations sur les professions qui peuvent utiliser cette arme.
        
        Returns:
            List[Dict]: Liste des informations sur les professions et spécialisations
        """
        from .profession import Profession
        from .specialization import Specialization
        
        # Vérifie si le cache existe et est valide
        if hasattr(self, '_profession_weapons_cache'):
            return self._profession_weapons_cache
            
        # Récupère les relations profession_weapons avec chargement optimisé
        result = session.query(ProfessionWeapon, Profession, Specialization).\
            join(Profession, Profession.id == ProfessionWeapon.profession_id).\
            outerjoin(Specialization, Specialization.id == ProfessionWeapon.specialization_id).\
            filter(ProfessionWeapon.weapon_id == self.id).\
            all()
        
        # Formate les résultats
        profession_weapons = []
        for pw, prof, spec in result:
            pw_data = {
                'profession': prof.to_dict(),
                'slot': pw.slot,
                'specialization': spec.to_dict() if spec else None,
                'weapon_type': pw.weapon_type.weapon_type if pw.weapon_type else None,
                'hand': pw.weapon_type.hand if pw.weapon_type else None,
                'is_elite': pw.weapon_type.is_elite if pw.weapon_type else False
            }
            profession_weapons.append(pw_data)
        
        # Met en cache le résultat
        self._profession_weapons_cache = profession_weapons
        return profession_weapons
    
    @classmethod
    def batch_load_by_ids(
        cls: Type[T], 
        weapon_ids: List[int], 
        session: Optional[Session] = None
    ) -> Dict[int, T]:
        """Charge plusieurs armes par leurs IDs en une seule requête.
        
        Args:
            weapon_ids: Liste des IDs d'armes à charger
            session: Session SQLAlchemy (optionnelle)
            
        Returns:
            Dict[int, Weapon]: Dictionnaire {id: weapon} des armes trouvées
        """
        @with_session
        def _batch_load(session: Session) -> Dict[int, T]:
            if not weapon_ids:
                return {}
                
            weapons = session.query(cls).filter(cls.id.in_(weapon_ids)).all()
            return {weapon.id: weapon for weapon in weapons}
            
        return _batch_load(session=session)
    
    def to_dict(self, include_related: bool = True) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire pour la sérialisation JSON.
        
        Args:
            include_related: Si True, inclut les objets liés (professions, compétences, etc.)
            
        Returns:
            Dict: Représentation de l'arme sous forme de dictionnaire
        """
        result = {
            'id': self.id,
            'name': self.name,
            'name_fr': self.name_fr,
            'description': self.description,
            'description_fr': self.description_fr,
            'icon': self.icon,
            'chat_link': self.chat_link,
            'type': self.type.value if self.type else None,
            'damage_type': self.damage_type.value if self.damage_type else None,
            'min_power': self.min_power,
            'max_power': self.max_power,
            'defense': self.defense,
            'attributes': self.attributes or {},
            'infusion_slots': self.infusion_slots or [],
            'infusion_upgrade_flags': self.infusion_upgrade_flags or [],
            'suffix_item_id': self.suffix_item_id,
            'secondary_suffix_item_id': self.secondary_suffix_item_id,
            'stat_choices': self.stat_choices or [],
            'game_types': self.game_types or [],
            'flags': [f.value if hasattr(f, 'value') else f for f in (self.flags or [])],
            'restrictions': self.restrictions or [],
            'rarity': self.rarity,
            'level': self.level,
            'default_skin': self.default_skin,
            'details': self.details or {}
        }
        
        if include_related:
            # Charge les relations si nécessaire (avec lazy loading)
            try:
                if self.skills:
                    result['skills'] = [s.to_dict(include_related=False) for s in self.skills]
                
                if hasattr(self, 'profession_weapons'):
                    result['profession_weapons'] = self.get_profession_weapons()
                
                if hasattr(self, 'upgrades') and self.upgrades:
                    result['upgrades'] = [u.to_dict(include_related=False) for u in self.upgrades]
                    
                if hasattr(self, 'item') and self.item:
                    result['item'] = self.item.to_dict(include_related=False)
                    
            except Exception as e:
                logger.warning(f"Erreur lors du chargement des relations pour l'arme {self.id}: {e}")
        
        return result


# Table d'association pour la relation many-to-many entre armes et compétences
weapon_skills = Base.metadata.tables.get('weapon_skills')
if weapon_skills is None:
    weapon_skills = Table(
        'weapon_skills',
        Base.metadata,
        Column('weapon_id', Integer, ForeignKey('weapons.id', ondelete='CASCADE'), primary_key=True),
        Column('skill_id', Integer, ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)
    )


class ProfessionWeapon(Base):
    """Table d'association entre les professions et les armes avec des métadonnées supplémentaires."""
    __tablename__ = 'profession_weapons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profession_id = Column(
        String(50), 
        ForeignKey('professions.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    weapon_id = Column(
        Integer, 
        ForeignKey('weapons.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    weapon_type_id = Column(
        Integer,
        ForeignKey('profession_weapon_types.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    slot = Column(Enum(WeaponSlot), nullable=False, index=True)
    specialization_id = Column(
        Integer, 
        ForeignKey('specializations.id', ondelete='CASCADE'), 
        nullable=True,
        index=True
    )
    
    # Relations
    profession = relationship("Profession", back_populates="available_weapons")
    weapon = relationship("Weapon", back_populates="profession_weapons")
    specialization = relationship("Specialization")
    
    # Relationship with ProfessionWeaponType
    weapon_type = relationship(
        "ProfessionWeaponType",
        foreign_keys=[weapon_type_id],
        back_populates="profession_weapons",
        uselist=False
    )
    
    # Alias for backward compatibility - will be removed in the future
    @property
    def skills(self):
        if self.weapon_type:
            return self.weapon_type.weapon_skills
        return []
    
    def __repr__(self):
        return f"<ProfessionWeapon(id={self.id}, profession_id={self.profession_id}, weapon_id={self.weapon_id}, slot='{self.slot}')>"
