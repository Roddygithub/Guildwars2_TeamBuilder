"""Modèle SQLAlchemy pour les compétences GW2."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base
from .weapon import WeaponType  # Import de WeaponType depuis weapon.py

class SkillType(PyEnum):
    """Types de compétences dans GW2."""
    HEAL = "Heal"
    UTILITY = "Utility"
    ELITE = "Elite"
    WEAPON = "Weapon"
    PROFESSION = "Profession"
    DOWNED = "Downed"
    DODGE = "Dodge"
    PET = "Pet"
    BUNDLE = "Bundle"
    TOOLBELT = "Toolbelt"
    TRAIT = "Trait"
    TRANSFORMATION = "Transformation"

# Suppression de la définition en double de WeaponType
# L'énumération est maintenant importée depuis weapon.py

class Skill(Base):
    """Modèle représentant une compétence GW2.
    
    Une compétence peut être associée à une ou plusieurs professions, et peut être liée à des armes,
    des spécialisations ou des traits. Le modèle gère également les chaînes de compétences et les
    compétences alternatives.
    
    Exemple d'utilisation:
        ```python
        # Récupérer toutes les compétences d'une profession
        guardian_skills = session.query(Skill).filter(
            Skill.professions.contains(['Guardian'])
        ).all()
        
        # Trouver les compétences d'une arme spécifique
        sword_skills = session.query(Skill).join(
            weapon_skills, Skill.id == weapon_skills.c.skill_id
        ).filter(
            weapon_skills.c.weapon_id == 'Sword'
        ).all()
        ```
    """
    """Modèle représentant une compétence GW2.
    
    Attributes:
        id (int): Identifiant unique de la compétence
        name (str): Nom de la compétence (en anglais)
        name_fr (str): Nom de la compétence en français
        description (str): Description de la compétence
        description_fr (str): Description de la compétence en français
        icon (str): URL de l'icône de la compétence
        chat_link (str): Lien de chat pour la compétence
        type (SkillType): Type de compétence (heal/utility/elite/weapon/etc.)
        weapon_type (WeaponType): Type d'arme pour les compétences d'arme
        slot (str): Emplacement de la compétence (1-5 pour les armes, heal/utility/elite)
        initiative (int): Coût en initiative (pour les voleurs)
        energy (int): Coût en énergie (pour les revenants)
        professions (List[str]): Liste des noms des professions pouvant utiliser cette compétence
        categories (List[str]): Catégories de la compétence (par exemple, "Signet", "Shout", etc.)
        attunement (str): Attunement pour les éléments (pour les élémentaristes)
        dual_wield (str): Type d'arme en main secondaire pour les compétences à deux mains
        flip_skill (int): ID de la compémentaire (pour les compétences qui en ont)
        next_chain (int): ID de la prochaine compétence dans la chaîne
        prev_chain (int): ID de la compétence précédente dans la chaîne
        toolbelt_skill (int): ID de la compétence de la ceinture à outils (pour les ingénieurs)
        transform_skills (List[int]): IDs des compétences de transformation
        bundle_skills (List[int]): IDs des compétences du bundle
        
        # Relations
        profession: relation avec la profession parente (si spécifique à une profession)
        specialization: relation avec la spécialisation parente (si spécifique à une spécialisation)
    """
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_fr = Column(String(100), nullable=True, index=True)
    name_de = Column(String(100), nullable=True, index=True)
    name_es = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)
    description_es = Column(Text, nullable=True)
    icon = Column(String(255))
    chat_link = Column(String(100), nullable=True, index=True)
    type = Column(Enum(SkillType), nullable=False, index=True)
    weapon_type = Column(Enum(WeaponType), nullable=True, index=True)
    slot = Column(String(50), index=True)  # 1-5 pour les armes, heal/utility/elite
    initiative = Column(Integer, nullable=True)  # Pour les voleurs
    energy = Column(Integer, nullable=True)  # Pour les revenants
    professions = Column(JSON, nullable=True, index=True)  # Liste des noms de professions (doit correspondre aux IDs de la table professions)
    categories = Column(JSON, nullable=True)  # Catégories comme "Signet", "Shout", etc.
    attunement = Column(String(20), nullable=True)  # Pour les élémentaristes
    dual_wield = Column(String(20), nullable=True)  # Type d'arme en main secondaire
    flip_skill = Column(Integer, ForeignKey('skills.id'), nullable=True)  # Compétence complémentaire
    next_chain = Column(Integer, ForeignKey('skills.id'), nullable=True)  # Prochaine compétence dans la chaîne
    prev_chain = Column(Integer, ForeignKey('skills.id'), nullable=True)  # Compétence précédente dans la chaîne
    toolbelt_skill = Column(Integer, ForeignKey('skills.id'), nullable=True)  # Pour les ingénieurs
    transform_skills = Column(JSON, nullable=True)  # IDs des compétences de transformation
    bundle_skills = Column(JSON, nullable=True)  # IDs des compétences du bundle
    cost = Column(Integer, nullable=True)  # Coût en initiative/énergie
    recharge = Column(Integer, nullable=True)  # Temps de recharge en secondes
    combo_finisher = Column(String(50), nullable=True)  # Type de finisseur de combo
    combo_field = Column(String(50), nullable=True)  # Type de champ de combo
    flags = Column(JSON, nullable=True)  # Flags supplémentaires
    facts = Column(JSON, nullable=True)  # Faits de compétence bruts de l'API
    traited_facts = Column(JSON, nullable=True)  # Faits modifiés par des traits
    created = Column(String(50), nullable=True)  # Date de création dans l'API
    updated = Column(String(50), nullable=True)  # Date de dernière mise à jour
    
    # Clés étrangères optionnelles pour les relations
    profession_id = Column(String(50), ForeignKey('professions.id', ondelete='CASCADE'), nullable=True, index=True)
    specialization_id = Column(Integer, ForeignKey('specializations.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Relations
    profession = relationship(
        "Profession",
        back_populates="skills",
        foreign_keys=[profession_id],
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Profession à laquelle cette compétence est associée (si spécifique à une profession)',
            'example': 'skill.profession pour accéder aux détails de la profession'
        }
    )
    
    profession_weapon_types = relationship(
        "ProfessionWeaponSkill",
        back_populates="skill",
        foreign_keys="[ProfessionWeaponSkill.skill_id]",
        cascade="all, delete-orphan",
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Types d\'arme de profession associés à cette compétence',
            'example': 'skill.profession_weapon_types pour accéder aux types d\'arme compatibles'
        }
    )
    
    weapons = relationship(
        "Weapon",
        secondary="weapon_skills",
        back_populates="skills",
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Armes avec lesquelles cette compétence peut être utilisée',
            'example': 'skill.weapons pour obtenir la liste des armes compatibles'
        }
    )
    
    # La relation traits sera configurée après la définition de la classe Trait
    # pour éviter les imports circulaires
    
    specialization = relationship(
        "Specialization", 
        back_populates="skills",
        foreign_keys=[specialization_id],
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Spécialisation à laquelle cette compétence est associée (si spécifique à une spécialisation)',
            'example': 'skill.specialization pour accéder aux détails de la spécialisation'
        }
    )
    
    # Relations pour les chaînes de compétences
    # Note: Les relations sont marquées avec post_update=True pour éviter les problèmes de dépendance circulaire
    flip_skill_rel = relationship(
        "Skill",
        foreign_keys=[flip_skill],
        remote_side=[id],
        post_update=True,
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Compétence alternative (ex: compétence flip pour les kits d\'ingénieur)',
            'example': 'skill.flip_skill_rel pour accéder à la compétence flip associée'
        }
    )
    
    next_chain_rel = relationship(
        "Skill",
        foreign_keys=[next_chain],
        remote_side=[id],
        post_update=True,
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Prochaine compétence dans la chaîne d\'attaques',
            'example': 'skill.next_chain_rel pour accéder à la prochaine attaque de la chaîne'
        }
    )
    
    prev_chain_rel = relationship(
        "Skill",
        foreign_keys=[prev_chain],
        remote_side=[id],
        post_update=True,
        lazy="selectin",  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'Compétence précédente dans la chaîne d\'attaques',
            'example': 'skill.prev_chain_rel pour accéder à l\'attaque précédente de la chaîne'
        }
    )
    
    toolbelt_skill_rel = relationship(
        "Skill",
        foreign_keys=[toolbelt_skill],
        remote_side=[id],
        post_update=True,
        lazy="selectin"  # Chargement plus efficace pour les requêtes fréquentes
    )
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self, include_related: bool = True, minimal: bool = False) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation JSON.
        
        Args:
            include_related: Inclure les objets liés (weapons, traits, etc.)
            minimal: Retourner uniquement les champs essentiels
            
        Returns:
            dict: Représentation sérialisable de l'objet
            
        Exemple:
            ```python
            # Sérialisation complète (par défaut)
            skill_dict = skill.to_dict()
            
            # Sérialisation minimale (champs essentiels uniquement)
            skill_minimal = skill.to_dict(minimal=True)
            
            # Sans les objets liés
            skill_no_related = skill.to_dict(include_related=False)
            ```
        """
        base_dict = {
            'id': self.id,
            'name': self.name,
            'type': self.type.value if self.type else None,
            'icon': self.icon,
            'professions': self.professions or [],
            'slot': self.slot,
            'cost': self.cost,
            'recharge': self.recharge,
        }
        
        if minimal:
            return base_dict
            
        full_dict = {
            **base_dict,
            'name_fr': self.name_fr,
            'name_de': self.name_de,
            'name_es': self.name_es,
            'description': self.description,
            'description_fr': self.description_fr,
            'description_de': self.description_de,
            'description_es': self.description_es,
            'chat_link': self.chat_link,
            'weapon_type': self.weapon_type.value if self.weapon_type else None,
            'initiative': self.initiative,
            'energy': self.energy,
            'categories': self.categories or [],
            'attunement': self.attunement,
            'dual_wield': self.dual_wield,
            'flip_skill': self.flip_skill,
            'next_chain': self.next_chain,
            'prev_chain': self.prev_chain,
            'toolbelt_skill': self.toolbelt_skill,
            'transform_skills': self.transform_skills or [],
            'bundle_skills': self.bundle_skills or [],
            'combo_finisher': self.combo_finisher,
            'combo_field': self.combo_field,
            'flags': self.flags or [],
            'facts': self.facts or [],
            'traited_facts': self.traited_facts or [],
            'profession_id': self.profession_id,
            'specialization_id': self.specialization_id,
            'created': self.created,
            'updated': self.updated,
        }
        
        if include_related:
            full_dict.update({
                'weapons': [w.to_dict(minimal=True) for w in self.weapons],
                'traits': [t.to_dict(minimal=True) for t in self.traits],
                'profession': self.profession.to_dict(minimal=True) if self.profession else None,
                'specialization': self.specialization.to_dict(minimal=True) if self.specialization else None,
                'flip_skill_rel': self.flip_skill_rel.to_dict(minimal=True) if self.flip_skill_rel else None,
                'next_chain_rel': self.next_chain_rel.to_dict(minimal=True) if self.next_chain_rel else None,
                'prev_chain_rel': self.prev_chain_rel.to_dict(minimal=True) if self.prev_chain_rel else None,
                'toolbelt_skill_rel': self.toolbelt_skill_rel.to_dict(minimal=True) if self.toolbelt_skill_rel else None,
            })
            
        return full_dict
        
    def get_skill_chain(self) -> list['Skill']:
        """Retourne la chaîne complète de compétences à laquelle cette compétence appartient.
        
        Returns:
            list[Skill]: Liste ordonnée des compétences dans la chaîne
            
        Exemple:
            ```python
            # Obtenir la chaîne complète d'une compéquence d'attaques
            chain = skill.get_skill_chain()
            for i, chain_skill in enumerate(chain, 1):
                print(f"{i}. {chain_skill.name}")
            ```
        """
        chain = []
        current = self
        
        # Remonter au début de la chaîne
        while current.prev_chain_rel:
            current = current.prev_chain_rel
            
        # Parcourir la chaîne jusqu'à la fin
        while current:
            chain.append(current)
            current = current.next_chain_rel
            
        return chain
        
    def get_related_skills(self) -> dict[str, list['Skill']]:
        """Récupère toutes les compétences liées à cette compétence.
        
        Returns:
            dict: Dictionnaire contenant les compétences liées par type
            
        Exemple:
            ```python
            related = skill.get_related_skills()
            print(f"Compétence flip: {related['flip_skill'][0].name if related['flip_skill'] else 'Aucune'}")
            print(f"Compétences dans la chaîne: {[s.name for s in related['chain_skills']]}")
            ```
        """
        from sqlalchemy.orm import Session
        from ..database import SessionLocal
        
        db = SessionLocal()
        try:
            related = {
                'flip_skill': [self.flip_skill_rel] if self.flip_skill_rel else [],
                'toolbelt_skill': [self.toolbelt_skill_rel] if self.toolbelt_skill_rel else [],
                'chain_skills': self.get_skill_chain(),
                'transform_skills': db.query(Skill).filter(
                    Skill.id.in_(self.transform_skills or [])
                ).all(),
                'bundle_skills': db.query(Skill).filter(
                    Skill.id.in_(self.bundle_skills or [])
                ).all(),
            }
            return related
        finally:
            db.close()
            
    def is_available_for_profession(self, profession_id: str) -> bool:
        """Vérifie si cette compétence est disponible pour une profession donnée.
        
        Args:
            profession_id: ID de la profession à vérifier (ex: 'Guardian', 'Elementalist')
            
        Returns:
            bool: True si la compétence est disponible pour cette profession
            
        Exemple:
            ```python
            # Vérifier si une compétence est disponible pour le Gardien
            is_guardian_skill = skill.is_available_for_profession('Guardian')
            ```
        """
        if not self.professions:
            return False
        return profession_id in self.professions
        
    def get_weapon_skills(self, weapon_type: WeaponType = None) -> list['Skill']:
        """Récupère les compétences d'arme associées à cette compétence.
        
        Args:
            weapon_type: Filtrer par type d'arme (optionnel)
            
        Returns:
            list[Skill]: Liste des compétences d'arme correspondantes
            
        Exemple:
            ```python
            # Toutes les compétences d'arme de cette compétence
            weapon_skills = skill.get_weapon_skills()
            
            # Uniquement les compétences d'épée
            sword_skills = skill.get_weapon_skills(WeaponType.SWORD)
            ```
        """
        if not hasattr(self, 'weapons') or not self.weapons:
            return []
            
        if weapon_type:
            return [w for w in self.weapons if w.type == weapon_type]
            
        return self.weapons
        
    def get_transform_skills(self) -> list['Skill']:
        """Récupère les compétences de transformation associées à cette compétence.
        
        Returns:
            list[Skill]: Liste des compétences de transformation
            
        Exemple:
            ```python
            # Obtenir toutes les compétences de transformation
            transform_skills = skill.get_transform_skills()
            ```
        """
        if not self.transform_skills:
            return []
            
        from sqlalchemy.orm import Session
        from ..database import SessionLocal
        
        db = SessionLocal()
        try:
            return db.query(Skill).filter(
                Skill.id.in_(self.transform_skills)
            ).all()
        finally:
            db.close()
            
    def get_bundle_skills(self) -> list['Skill']:
        """Récupère les compétences de bundle associées à cette compétence.
        
        Returns:
            list[Skill]: Liste des compétences de bundle
            
        Exemple:
            ```python
            # Obtenir toutes les compétences de bundle
            bundle_skills = skill.get_bundle_skills()
            ```
        """
        if not self.bundle_skills:
            return []
            
        from sqlalchemy.orm import Session
        from ..database import SessionLocal
        
        db = SessionLocal()
        try:
            return db.query(Skill).filter(
                Skill.id.in_(self.bundle_skills)
            ).all()
        finally:
            db.close()
            
    def get_skill_facts(self, include_traited: bool = True) -> list[dict]:
        """Récupère les faits de compétence, avec option pour inclure les faits modifiés par les traits.
        
        Args:
            include_traited: Inclure les faits modifiés par les traits
            
        Returns:
            list[dict]: Liste des faits de compétence
            
        Exemple:
            ```python
            # Obtenir tous les faits (y compris modifiés par les traits)
            all_facts = skill.get_skill_facts()
            
            # Obtenir uniquement les faits de base
            base_facts = skill.get_skill_facts(include_traited=False)
            ```
        """
        facts = self.facts or []
        if include_traited and self.traited_facts:
            facts.extend(self.traited_facts)
        return facts
        
    def get_skill_facts_by_type(self, fact_type: str, include_traited: bool = True) -> list[dict]:
        """Récupère les faits de compétence d'un type spécifique.
        
        Args:
            fact_type: Type de fait à rechercher (ex: 'Damage', 'Buff', 'Heal')
            include_traited: Inclure les faits modifiés par les traits
            
        Returns:
            list[dict]: Liste des faits correspondants
            
        Exemple:
            ```python
            # Obtenir tous les faits de dégâts
            damage_facts = skill.get_skill_facts_by_type('Damage')
            
            # Obtenir les buffs (y compris modifiés par les traits)
            buffs = skill.get_skill_facts_by_type('Buff')
            ```
        """
        facts = self.get_skill_facts(include_traited=include_traited)
        return [f for f in facts if f.get('type') == fact_type]
        
    def get_skill_fact_value(self, fact_type: str, attribute: str = None, default=None):
        """Récupère la valeur d'un attribut spécifique d'un fait de compétence.
        
        Args:
            fact_type: Type de fait à rechercher
            attribute: Attribut à récupérer (si None, retourne le premier fait correspondant)
            default: Valeur par défaut si le fait ou l'attribut n'existe pas
            
        Returns:
            La valeur de l'attribut ou le fait complet si attribute est None
            
        Exemple:
            ```python
            # Obtenir les dégâts de base d'une compétence
            damage = skill.get_skill_fact_value('Damage', 'dmg_multiplier')
            
            # Obtenir le premier fait de type Buff
            buff_fact = skill.get_skill_fact_value('Buff')
            ```
        """
        facts = self.get_skill_facts_by_type(fact_type)
        if not facts:
            return default
            
        fact = facts[0]  # Prend le premier fait correspondant
        if attribute is None:
            return fact
            
        return fact.get(attribute, default)
        
    def get_coefficients(self) -> dict:
        """Calcule les coefficients de dégâts et de soins de la compétence.
        
        Returns:
            dict: Dictionnaire contenant les coefficients calculés
            
        Exemple:
            ```python
            # Obtenir les coefficients de la compétence
            coeffs = skill.get_coefficients()
            print(f"Dégâts: {coeffs.get('damage')}, Soins: {coeffs.get('healing')")
            ```
        """
        damage_fact = self.get_skill_fact_value('Damage')
        heal_fact = self.get_skill_fact_value('Heal')
        
        return {
            'damage': damage_fact.get('dmg_multiplier', 0) if damage_fact else 0,
            'healing': heal_fact.get('hit_count', 1) * heal_fact.get('dmg_multiplier', 0) if heal_fact else 0,
            'hits': damage_fact.get('hit_count', 1) if damage_fact else 0,
            'duration': self.get_skill_fact_value('Duration', 'duration', 0) or 0,
            'radius': self.get_skill_fact_value('Radius', 'distance', 0) or 0,
            'range': self.get_skill_fact_value('Range', 'value', 0) or 0,
        }


# Configuration des relations après la définition des classes pour éviter les imports circulaires
from sqlalchemy.orm import configure_mappers

def setup_skill_relationships():
    """Configure les relations après que tous les modèles ont été chargés."""
    from .trait import Trait  # Import local pour éviter les imports circulaires
    
    # Configuration de la relation traits
    Skill.traits = relationship(
        "Trait",
        secondary="trait_skills",
        back_populates="skills",
        lazy="selectin",
        info={
            'description': 'Traits qui interagissent avec cette compétence',
            'example': 'skill.traits pour obtenir la liste des traits affectant cette compétence'
        }
    )
    
    # Configurer les mappers pour prendre en compte la relation
    configure_mappers()

# Appel de la fonction de configuration des relations
setup_skill_relationships()
