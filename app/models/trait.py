"""Modèle SQLAlchemy pour les traits GW2."""

from typing import List, Dict, Any, Optional, Union
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum, Table, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.exc import DataError
from enum import Enum as PyEnum
from .base import Base
from ..core.exceptions import ValidationError

class TraitTier(PyEnum):
    """Niveaux de sélection des traits."""
    MINOR = "Minor"  # Traits mineurs (obligatoires)
    MAJOR = "Major"  # Traits majeurs (au choix)
    
class TraitSlot(PyEnum):
    """Emplacements des traits dans l'interface."""
    ADEPT = "Adept"        # Premier trait majeur (niveau 30)
    MASTER = "Master"      # Deuxième trait majeur (niveau 60)
    GRANDMASTER = "Grandmaster"  # Troisième trait majeur (niveau 80)
    MINOR = "Minor"        # Trait mineur (passif)
    
class TraitType(PyEnum):
    """Types de traits."""
    PROFESSION = "Profession"  # Trait de profession
    CORE = "Core"             # Trait de spécialisation de base
    ELITE = "Elite"           # Trait de spécialisation d'élite
    
class TraitCategory(PyEnum):
    """Catégories de traits."""
    OFFENSE = "Offense"
    DEFENSE = "Defense"
    SUPPORT = "Support"
    CONTROL = "Control"
    CONDITION = "Condition"
    POWER = "Power"
    UTILITY = "Utility"
    
class Trait(Base):
    """Modèle représentant un trait GW2.
    
    Un trait est une amélioration passive ou active qui modifie les compétences et les capacités
    d'un personnage. Les traits sont organisés en spécialisations et peuvent être de différents
    types (Profession, Core, Elite) et niveaux (Minor, Major).
    
    Exemples d'utilisation:
    
    ### Récupération de base
    ```python
    # Récupérer un trait par son ID
    trait = session.query(Trait).get(trait_id)
    
    # Récupérer tous les traits majeurs d'une spécialisation
    from sqlalchemy.orm import joinedload
    
    traits = session.query(Trait).filter_by(
        specialization_id=specialization_id,
        tier=TraitTier.MAJOR
    ).options(joinedload(Trait.skills)).all()
    ```
    
    ### Recherche avancée
    ```python
    # Trouver tous les traits offensifs d'élite
    from sqlalchemy import or_
    
    offensive_elite_traits = session.query(Trait).filter(
        Trait.type == TraitType.ELITE,
        Trait.categories.op('&&')(['Offense', 'Power'])  # Utilisation de l'opérateur PostgreSQL &&
    ).all()
    
    # Trouver des traits par leurs effets
    traits_with_bleed = session.query(Trait).filter(
        Trait.facts.any({"type": "Bleeding"}) |
        Trait.traited_facts.any({"type": "Bleeding"})
    ).all()
    ```
    
    ### Utilisation des méthodes utilitaires
    ```python
    # Obtenir les modificateurs d'attributs d'un trait
    modifiers = trait.get_attribute_modifiers()
    # Ex: {'Power': 120, 'Precision': 85}
    
    # Vérifier si un trait a un effet spécifique
    if trait.has_effect('Buff'):
        print("Ce trait fournit un buff!")
    
    # Vérifier le type de trait
    if trait.is_elite():
        print("Trait d'élite")
    elif trait.is_minor():
        print("Trait mineur")
    ```
    
    ### Création d'un nouveau trait
    ```python
    # Création d'un trait mineur de base
    minor_trait = Trait(
        id=1001,
        name="Nouveau Trait Mineur",
        description="Description du trait",
        type=TraitType.CORE,
        tier=TraitTier.MINOR,
        specialization_id=1,
        categories=["Offense", "Power"],
        facts=[{"type": "AttributeAdjust", "target": "Power", "value": 100}]
    )
    
    # Création d'un trait majeur avec emplacement
    major_trait = Trait(
        id=1002,
        name="Nouveau Trait Majeur",
        type=TraitType.ELITE,
        tier=TraitTier.MAJOR,
        slot=TraitSlot.GRANDMASTER,
        specialization_id=2,
        facts=[
            {"type": "Buff", "description": "Gain de puissance supplémentaire"},
            {"type": "AttributeAdjust", "target": "ConditionDamage", "value": 150}
        ]
    )
    
    # Ajout d'une compétence au trait
    from app.models.skill import Skill
    skill = session.query(Skill).get(1234)
    major_trait.skills.append(skill)
    
    # Validation et sauvegarde
    session.add(major_trait)
    session.commit()
    ```
    
    ### Sérialisation
    ```python
    # Sérialisation de base
    trait_data = trait.to_dict()
    
    # Sérialisation avec les relations
    trait_full_data = trait.to_dict(include_related=True)
    
    # Exemple de sortie:
    # {
    #   'id': 1,
    #   'name': 'Trait Puissant',
    #   'type': 'Elite',
    #   'tier': 'Major',
    #   'skills': [1, 2, 3],  # IDs des compétences
    #   'specialization': {...},  # Données de la spécialisation
    #   ...
    # }
    ```
    
    Attributes:
        id (int): Identifiant unique du trait (correspond à l'ID de l'API GW2)
        name (str): Nom du trait en anglais
        name_fr (str, optional): Nom du trait en français
        description (str, optional): Description des effets principaux du trait
        description_fr (str, optional): Description en français
        icon (str, optional): URL de l'icône du trait
        chat_link (str, optional): Lien de chat pour le trait
        type (TraitType): Type de trait (Profession/Core/Elite)
        tier (TraitTier): Niveau du trait (Minor/Major)
        slot (TraitSlot, optional): Emplacement du trait (Adept/Master/Grandmaster)
        categories (List[str], optional): Catégories du trait (Offense/Defense/Support/etc.)
        facts (List[dict], optional): Effets et conditions du trait
        traited_facts (List[dict], optional): Effets conditionnels du trait
        specialization_id (int, optional): ID de la spécialisation parente
        profession_id (int, optional): ID de la profession parente
        
        # Relations
        specialization (Specialization): Spécialisation à laquelle le trait appartient
        profession (Profession): Profession à laquelle le trait est associé (si c'est un trait de profession)
        skills (List[Skill]): Liste des compétences associées à ce trait
    """
    __tablename__ = 'traits'
    
    # Configuration de la table
    __table_args__ = {
        'comment': 'Stocke les traits de spécialisation et de profession',
        'sqlite_autoincrement': False,  # On utilise les IDs de l'API GW2
        'extend_existing': True  # Permet de mettre à jour la définition si elle existe déjà
    }
    
    # Colonnes de base
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment='Identifiant unique du trait (ID GW2)'
    )
    
    # Métadonnées
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment='Nom du trait en anglais'
    )
    name_fr = Column(
        String(100), 
        nullable=True,
        comment='Nom du trait en français'
    )
    description = Column(
        Text, 
        nullable=True,
        comment='Description des effets du trait en anglais'
    )
    description_fr = Column(
        Text, 
        nullable=True,
        comment='Description des effets du trait en français'
    )
    
    # Données de présentation
    icon = Column(
        String(255),
        nullable=True,
        comment='URL de l\'icône du trait sur le CDN GW2'
    )
    chat_link = Column(
        String(100), 
        nullable=True,
        comment='Code de lien de chat pour ce trait'
    )
    
    # Classification
    type = Column(
        Enum(TraitType), 
        nullable=False, 
        index=True,
        comment='Type de trait (Profession/Core/Elite)'
    )
    tier = Column(
        Enum(TraitTier), 
        nullable=False, 
        index=True,
        comment='Niveau du trait (Minor/Major)'
    )
    slot = Column(
        Enum(TraitSlot), 
        nullable=True, 
        index=True,
        comment='Emplacement du trait (Adept/Master/Grandmaster)'
    )
    
    # Données structurées
    categories = Column(
        JSON, 
        nullable=True,
        comment='Liste des catégories du trait (Offense/Defense/Support/etc.)'
    )
    facts = Column(
        JSON, 
        nullable=True,
        comment='Liste des effets et conditions du trait'
    )
    traited_facts = Column(
        JSON, 
        nullable=True,
        comment='Liste des effets conditionnels du trait'
    )
    
    # Clés étrangères avec commentaires et contraintes
    specialization_id = Column(
        Integer, 
        ForeignKey(
            'specializations.id', 
            ondelete='CASCADE',
            name='fk_trait_specialization_id'
        ), 
        nullable=True,
        index=True,
        comment='Référence à la spécialisation parente (null si c\'est un trait de profession)'
    )
    
    profession_id = Column(
        String(50), 
        ForeignKey(
            'professions.id', 
            ondelete='CASCADE',
            name='fk_trait_profession_id'
        ), 
        nullable=True,
        index=True,
        comment='Référence à la profession parente (pour les traits de profession)'
    )
    
    # Relations avec chargement optimisé
    specialization = relationship(
        "Specialization",
        back_populates="traits",
        foreign_keys=[specialization_id],
        lazy='selectin',  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'La spécialisation à laquelle ce trait appartient',
            'example': 'trait.specialization pour accéder à la spécialisation parente',
            'performance': 'Utilise selectin pour optimiser le chargement des relations'
        }
    )
    
    profession = relationship(
        "Profession",
        back_populates="traits",
        foreign_keys=[profession_id],
        lazy='selectin',  # Chargement plus efficace pour les requêtes fréquentes
        info={
            'description': 'La profession à laquelle ce trait est associé',
            'example': 'trait.profession pour accéder à la profession parente (si c\'est un trait de profession)',
            'performance': 'Utilise selectin pour optimiser le chargement des relations'
        }
    )
    
    # La relation skills sera configurée après la définition de la classe Skill
    # pour éviter les imports circulaires
    
    def __repr__(self):
        return f"<Trait(id={self.id}, name='{self.name}', type='{self.type}')>"
        
    # ===== VALIDATEURS =====
    
    @validates('categories')
    def validate_categories(self, key, categories):
        """Valide le format des catégories du trait."""
        if categories is None:
            return None
            
        if not isinstance(categories, list):
            raise ValidationError("Les catégories doivent être une liste")
            
        valid_categories = [cat.value for cat in TraitCategory]
        for cat in categories:
            if cat not in valid_categories:
                raise ValidationError(f"Catégorie invalide: {cat}. Doit être parmi: {', '.join(valid_categories)}")
                
        return categories
    
    @validates('facts', 'traited_facts')
    def validate_facts(self, key, facts):
        """Valide le format des faits et effets conditionnels."""
        if facts is None:
            return None
            
        if not isinstance(facts, list):
            raise ValidationError(f"{key} doit être une liste de dictionnaires")
            
        # Vérifie que chaque fait est un dictionnaire avec les champs requis
        for fact in facts:
            if not isinstance(fact, dict):
                raise ValidationError(f"Chaque fait dans {key} doit être un dictionnaire")
                
            if 'type' not in fact:
                raise ValidationError(f"Chaque fait dans {key} doit avoir un champ 'type'")
                
        return facts
    
    # ===== MÉTHODES UTILITAIRES =====
    
    def get_attribute_modifiers(self) -> Dict[str, float]:
        """
        Extrait tous les modificateurs d'attributs des faits du trait.
        
        Cette méthode analyse les faits du trait pour trouver tous les ajustements
        d'attributs (faits de type 'AttributeAdjust') et les retourne sous forme
        de dictionnaire.
        
        Returns:
            Dict[str, float]: Dictionnaire où les clés sont les noms des attributs
                et les valeurs sont les valeurs d'ajustement.
                
        Exemples:
            ```python
            # Pour un trait avec ces faits:
            # [
            #   {"type": "AttributeAdjust", "target": "Power", "value": 120},
            #   {"type": "AttributeAdjust", "target": "Precision", "value": 85},
            #   {"type": "Buff", "description": "Augmente les dégâts"}
            # ]
            
            modifiers = trait.get_attribute_modifiers()
            # Retourne: {'Power': 120, 'Precision': 85}
            ```
            
            # Utilisation dans un calcul de statistiques
            base_power = 1000
            effective_power = base_power + trait.get_attribute_modifiers().get('Power', 0)
            """
        if not self.facts:
            return {}
            
        modifiers = {}
        for fact in self.facts:
            if fact.get('type') == 'AttributeAdjust' and 'value' in fact and 'target' in fact:
                attr_name = fact['target']
                modifiers[attr_name] = fact['value']
                
        return modifiers
    
    def has_effect(self, effect_type: str) -> bool:
        """
        Vérifie si le trait a un effet du type spécifié.
        
        Cette méthode recherche dans les faits et les faits conditionnés du trait
        pour trouver un effet correspondant au type spécifié. La recherche est
        insensible à la casse.
        
        Args:
            effect_type (str): Type d'effet à vérifier (ex: 'Buff', 'Damage', 'Heal')
            
        Returns:
            bool: True si l'effet est présent dans les faits ou faits conditionnés,
                  False sinon.
                  
        Exemples:
            # Vérifier si un trait applique un buff
            if trait.has_effect('Buff'):
                print("Ce trait fournit un buff!")
            
            # Vérifier les types d'effets courants
            effect_types = ['Bleeding', 'Burning', 'Poison']
            for effect in effect_types:
                if trait.has_effect(effect):
                    print(f"Ce trait applique l'effet {effect}")
            
            # Utilisation avec une liste d'effets à vérifier
            offensive_effects = ['Damage', 'Bleeding', 'Burning', 'Confusion']
            has_offensive_effect = any(trait.has_effect(effect) for effect in offensive_effects)
        """
        if not self.facts:
            return False
            
        # Vérifier dans les faits standards
        if any(fact.get('type') == effect_type for fact in self.facts):
            return True
            
        # Vérifier dans les faits conditionnés s'ils existent
        if self.traited_facts:
            return any(fact.get('type') == effect_type for fact in self.traited_facts)
            
        return False
    
    def get_skill_ids(self) -> List[int]:
        """
        Retourne la liste des IDs des compétences associées à ce trait.
        
        Cette méthode est utile pour obtenir rapidement les identifiants des compétences
        liées à ce trait sans avoir à charger les objets complets.
        
        Returns:
            List[int]: Liste des IDs des compétences associées au trait.
            
        Exemple:
            # Obtenir les IDs des compétences d'un trait
            skill_ids = trait.get_skill_ids()
            # Exemple de sortie: [123, 456, 789]
            
            # Charger les compétences associées (si nécessaire)
            from sqlalchemy.orm import joinedload
            trait_with_skills = (
                session.query(Trait)
                .options(joinedload(Trait.skills))
                .get(trait_id)
            )
        """
        return [skill.id for skill in self.skills] if self.skills else []
    
    def is_elite(self) -> bool:
        """
        Vérifie si le trait est un trait d'élite.
        
        Un trait est considéré comme d'élite si son type est 'Elite'.
        
        Returns:
            bool: True si c'est un trait d'élite, False sinon
            
        Exemple:
            ```python
            # Filtrer les traits d'élite
            elite_traits = [t for t in traits if t.is_elite()]
            
            # Utilisation dans une condition
            if trait.is_elite():
                print("Ce trait est une amélioration d'élite!")
            ```
        """
        return self.type == TraitType.ELITE
        
    def is_major(self) -> bool:
        """
        Vérifie si le trait est un trait majeur.
        
        Les traits majeurs sont des améliorations optionnelles que les joueurs
        peuvent choisir dans leur arbre de spécialisation. Ils sont plus puissants
        que les traits mineurs et sont généralement associés à un emplacement spécifique
        (Adept, Master, Grandmaster).
        
        Returns:
            bool: True si c'est un trait majeur, False sinon
            
        Exemple:
            ```python
            # Compter les traits majeurs offensifs
            offensive_major_traits = [
                t for t in traits 
                if t.is_major() and 'Offense' in t.categories
            ]
            ```
        """
        return self.tier == TraitTier.MAJOR
        
    def is_minor(self) -> bool:
        """
        Vérifie si le trait est un trait mineur.
        
        Les traits mineurs sont des améliorations passives qui sont automatiquement
        activées lorsqu'une spécialisation est sélectionnée. Ils sont généralement
        plus faibles que les traits majeurs mais fournissent des bonus de base.
        
        Returns:
            bool: True si c'est un trait mineur, False sinon
            
        Exemple:
            ```python
            # Récupérer uniquement les traits mineurs
            minor_traits = [t for t in traits if t.is_minor()]
            
            # Vérifier si un trait est mineur avant de l'appliquer
            if not trait.is_minor():
                # Logique pour les traits non-mineurs
                pass
            ```
        """
        return self.tier == TraitTier.MINOR
    
    def to_dict(self, include_related: bool = False, include_details: bool = True) -> dict:
        """Convertit l'objet en dictionnaire pour la sérialisation JSON.
        
        Cette méthode permet de sérialiser un trait avec différents niveaux de détail,
        ce qui est utile pour optimiser les performances des API et réduire la taille
        des réponses.
        
        Args:
            include_related (bool): Si True, inclut les objets liés (compétences, etc.)
                dans un format détaillé. Si False, seuls les IDs sont inclus.
            include_details (bool): Si False, seules les informations essentielles sont incluses.
                Utile pour les listes ou les aperçus.
                
        Returns:
            dict: Dictionnaire contenant les données du trait
            
        Exemple:
            # Sérialisation minimale (pour les listes)
            trait_dict = trait.to_dict(include_details=False)
            
            # Sérialisation complète sans les relations
            trait_dict_full = trait.to_dict()
            
            # Sérialisation complète avec les relations
            trait_dict_with_relations = trait.to_dict(include_related=True)
        """
        base_dict = {
            'id': self.id,
            'name': self.name,
            'name_fr': self.name_fr or self.name,  # Fallback sur le nom anglais
            'type': self.type.value if self.type else None,
            'tier': self.tier.value if self.tier else None,
            'slot': self.slot.value if self.slot else None,
            'categories': self.categories or [],
            'specialization_id': self.specialization_id,
            'profession_id': self.profession_id,
        }
        
        # Ajout des détails si demandé
        if include_details:
            base_dict.update({
                'description': self.description,
                'description_fr': self.description_fr or self.description,  # Fallback
                'icon': self.icon,
                'chat_link': self.chat_link,
                'facts': self.facts or [],
                'traited_facts': self.traited_facts or [],
            })
        
        # Gestion des relations
        if include_related:
            from app.models.skill import Skill  # Import local pour éviter les imports circulaires
            
            related_data = {}
            
            # Sérialisation des compétences liées
            if self.skills:
                related_data['skills'] = [
                    skill.to_dict(include_related=False, include_details=include_details) 
                    for skill in sorted(self.skills, key=lambda s: s.name)
                ]
            else:
                related_data['skills'] = []
                
            # Sérialisation de la spécialisation liée
            if self.specialization:
                related_data['specialization'] = self.specialization.to_dict(
                    include_related=False, 
                    include_details=include_details
                )
                
            # Sérialisation de la profession liée
            if self.profession:
                related_data['profession'] = self.profession.to_dict(
                    include_related=False,
                    include_details=include_details
                )
                
            base_dict.update(related_data)
        else:
            # Seulement les IDs des compétences si les relations ne sont pas chargées
            base_dict['skills'] = [skill.id for skill in self.skills] if self.skills else []
            
        return base_dict
        
    def get_effect_types(self) -> set:
        """
        Retourne l'ensemble des types d'effets uniques pour ce trait.
        
        Cette méthode analyse les faits et les faits conditionnés du trait
        pour extraire tous les types d'effets uniques.
        
        Returns:
            set: Ensemble des types d'effets uniques
            
        Exemple:
            # Obtenir tous les types d'effets d'un trait
            effect_types = trait.get_effect_types()
            # Exemple de sortie: {'Buff', 'Damage', 'Heal'}
        """
        effect_types = set()
        
        # Analyser les faits standards
        if self.facts:
            effect_types.update(fact.get('type') for fact in self.facts if fact.get('type'))
            
        # Analyser les faits conditionnés
        if self.traited_facts:
            effect_types.update(fact.get('type') for fact in self.traited_facts if fact.get('type'))
            
        return effect_types
        
    def get_related_skill_ids(self, session=None) -> List[int]:
        """
        Récupère les IDs des compétences liées à ce trait.
        
        Cette méthode est optimisée pour éviter le chargement complet des objets Skill
        en utilisant directement une requête SQL pour récupérer uniquement les IDs.
        
        Args:
            session: Session SQLAlchemy optionnelle. Si non fournie, utilise self.skills.
            
        Returns:
            List[int]: Liste des IDs des compétences liées
            
        Exemple:
            # Utilisation avec une session existante (recommandé pour les performances)
            from sqlalchemy.orm import Session
            session = Session()
            skill_ids = trait.get_related_skill_ids(session=session)
            
            # Utilisation sans session (moins efficace)
            skill_ids = trait.get_related_skill_ids()
        """
        if session is not None:
            from sqlalchemy import select
            from app.models.skill import Skill, trait_skills
            
            stmt = select(trait_skills.c.skill_id).where(
                trait_skills.c.trait_id == self.id
            )
            result = session.execute(stmt)
            return [row[0] for row in result]
            
        # Fallback si aucune session n'est fournie
        return self.get_skill_ids()
        
    def get_attribute_modifiers_summary(self) -> Dict[str, float]:
        """
        Retourne un résumé des modificateurs d'attributs avec leur description.
        
        Contrairement à get_attribute_modifiers() qui retourne uniquement les valeurs,
        cette méthode inclut également les descriptions pour une meilleure lisibilité.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionnaire des modificateurs avec leur description
            
        Exemple:
            # Obtenir un résumé des modificateurs
            modifiers = trait.get_attribute_modifiers_summary()
            # Exemple de sortie:
            # {
            #     'Power': {'value': 120, 'description': 'Augmente la puissance'},
            #     'Precision': {'value': 85, 'description': 'Augmente la précision'}
            # }
        """
        modifiers = {}
        
        # Analyser les faits standards
        if self.facts:
            for fact in self.facts:
                if fact.get('type') == 'AttributeAdjust' and 'target' in fact and 'value' in fact:
                    attr_name = fact['target']
                    modifiers[attr_name] = {
                        'value': fact['value'],
                        'description': fact.get('description', ''),
                        'is_conditional': False
                    }
        
        # Analyser les faits conditionnés
        if self.traited_facts:
            for fact in self.traited_facts:
                if fact.get('type') == 'AttributeAdjust' and 'target' in fact and 'value' in fact:
                    attr_name = fact['target']
                    # Ne pas écraser les valeurs existantes à moins qu'elles ne soient conditionnelles
                    if attr_name not in modifiers or modifiers[attr_name].get('is_conditional', True):
                        modifiers[attr_name] = {
                            'value': fact['value'],
                            'description': fact.get('description', ''),
                            'is_conditional': True,
                            'condition': fact.get('requires_trait')
                        }
        
        return modifiers


# Table d'association pour la relation many-to-many entre traits et compétences
if 'trait_skills' not in Base.metadata.tables:
    trait_skills = Table(
        'trait_skills',
        Base.metadata,
        Column(
            'trait_id', 
            Integer, 
            ForeignKey('traits.id', ondelete='CASCADE', name='fk_trait_skills_trait_id'),
            primary_key=True,
            comment='ID du trait associé à la compétence'
        ),
        Column(
            'skill_id', 
            Integer, 
            ForeignKey('skills.id', ondelete='CASCADE', name='fk_trait_skills_skill_id'),
            primary_key=True,
            comment='ID de la compétence associée au trait'
        ),
        comment='Table de liaison entre les traits et les compétences associées',
        info={
            'description': 'Relation many-to-many entre les traits et les compétences',
            'version': '1.0.0'
        }
    )
else:
    trait_skills = Base.metadata.tables['trait_skills']

# Configuration de la relation skills après la définition de toutes les classes
# pour éviter les imports circulaires
from sqlalchemy.orm import configure_mappers

def setup_trait_relationships():
    """Configure les relations pour le modèle Trait.
    
    Cette fonction est appelée depuis relationships.py après l'import de tous les modèles.
    """
    # Configuration de la relation skills
    Trait.skills = relationship(
        "Skill",
        secondary="trait_skills",
        back_populates="traits",
        lazy='selectin',
        order_by="Skill.name",
        info={
            'description': 'Liste des compétences associées à ce trait',
            'example': 'trait.skills pour obtenir toutes les compétences liées à ce trait',
            'performance': 'Utilise selectin pour optimiser le chargement des relations'
        }
    )
    
    # Configuration de la relation inverse dans Skill (si nécessaire)
    if 'Skill' in globals() and hasattr(Skill, 'traits'):
        Skill.traits = relationship(
            "Trait",
            secondary="trait_skills",
            back_populates="skills",
            viewonly=True
        )

# Ajout d'un gestionnaire d'événements pour valider les données avant l'insertion/mise à jour
@event.listens_for(Trait, 'before_insert')
@event.listens_for(Trait, 'before_update')
def validate_trait_data(mapper, connection, target):
    """Valide les données du trait avant insertion ou mise à jour."""
    # Vérifie qu'un trait a soit une spécialisation, soit une profession, mais pas les deux
    if target.specialization_id is not None and target.profession_id is not None:
        raise ValidationError("Un trait ne peut pas appartenir à la fois à une spécialisation et à une profession")
        
    if target.specialization_id is None and target.profession_id is None:
        raise ValidationError("Un trait doit appartenir soit à une spécialisation, soit à une profession")
    
    # Validation du type de trait par rapport à la présence de spécialisation/profession
    if target.specialization_id and target.type == TraitType.PROFESSION:
        raise ValidationError("Un trait de spécialisation ne peut pas être de type 'Profession'")
        
    if target.profession_id and target.type != TraitType.PROFESSION:
        raise ValidationError("Un trait de profession doit être de type 'Profession'")
    
    # Validation du niveau du trait
    if target.type == TraitType.PROFESSION and target.tier != TraitTier.MINOR:
        raise ValidationError("Les traits de profession doivent être de niveau 'Minor'")
    
    # Validation de l'emplacement pour les traits majeurs
    if target.tier == TraitTier.MAJOR and not target.slot:
        raise ValidationError("Les traits majeurs doivent avoir un emplacement (slot) défini")
