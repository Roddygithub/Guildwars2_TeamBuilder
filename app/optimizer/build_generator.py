"""Générateur de builds personnalisés pour Guild Wars 2.

Ce module fournit des fonctions pour générer des builds optimisés basés sur les rôles,
les professions et les interactions entre les compétences et les équipements.
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import random
import logging
from enum import Enum, auto

from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import or_
from app.database import SessionLocal
from app.models import (
    Profession, Weapon, Skill, Trait, Specialization, Item, Rarity,
    ProfessionWeapon, WeaponType, WeaponFlag, DamageType
)
from app.models.build import BuildData, ProfessionType, RoleType, EquipmentItem, TraitLine

# Configuration du logger
logger = logging.getLogger(__name__)

# Constantes pour la génération de builds
DEFAULT_WEAPON_SETS = 2  # Nombre de jeux d'armes par défaut
MAX_WEAPON_COMBINATIONS = 5  # Nombre maximum de combinaisons d'armes à essayer

class BuildRole(Enum):
    """Rôles spécifiques pour la génération de builds."""
    POWER_DPS = auto()
    CONDITION_DPS = auto()
    HEALER = auto()
    QUICKNESS_SUPPORT = auto()
    ALACRITY_SUPPORT = auto()
    TANK = auto()
    HYBRID = auto()

@dataclass
class BuildTemplate:
    """Modèle pour un template de build personnalisé."""
    profession: str
    elite_spec: Optional[str] = None
    role: RoleType = RoleType.DPS
    build_role: BuildRole = BuildRole.POWER_DPS
    weapons: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    traits: List[Dict[str, Any]] = field(default_factory=list)
    equipment: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    stat_priority: List[str] = field(default_factory=list)
    
    def to_build_data(self) -> BuildData:
        """Convertit le template en objet BuildData pour l'API."""
        return BuildData(
            name=f"{self.elite_spec or self.profession} {self.role.value}",
            profession=ProfessionType(self.profession.lower()),
            role=self.role,
            specializations=[],  # À remplir avec les spécialisations
            skills=[],  # À remplir avec les compétences
            equipment={}  # À remplir avec l'équipement
        )

def map_role_to_build_role(role: RoleType, profession: str) -> BuildRole:
    """Mappe un rôle de base à un rôle de build spécifique."""
    if role == RoleType.HEAL:
        return BuildRole.HEALER
    elif role == RoleType.QUICKNESS:
        return BuildRole.QUICKNESS_SUPPORT
    elif role == RoleType.ALACRITY:
        return BuildRole.ALACRITY_SUPPORT
    elif role == RoleType.TANK:
        return BuildRole.TANK
    elif role == RoleType.SUPPORT:
        # Pour les supports génériques, on choisit en fonction de la profession
        if profession.lower() in ['firebrand', 'herald', 'scrapper']:
            return BuildRole.QUICKNESS_SUPPORT
        elif profession.lower() in ['mechanist', 'specter', 'renegade']:
            return BuildRole.ALACRITY_SUPPORT
        else:
            return BuildRole.HYBRID
    else:  # DPS par défaut
        # On pourrait affiner en fonction de la profession
        return BuildRole.POWER_DPS

def generate_build_for_profession(
    profession: str,
    role: RoleType,
    elite_spec: Optional[str] = None,
    db: Optional[Session] = None
) -> BuildTemplate:
    """Génère un build personnalisé pour une profession et un rôle donnés.
    
    Args:
        profession: Le nom de la profession (en anglais)
        role: Le rôle principal du build
        elite_spec: La spécialisation d'élite (optionnelle)
        db: Session SQLAlchemy (optionnelle)
        
    Returns:
        Un objet BuildTemplate contenant les détails du build généré
    """
    # Utiliser la session fournie ou en créer une nouvelle
    session = db or SessionLocal()
    
    try:
        # Déterminer le rôle de build spécifique
        build_role = map_role_to_build_role(role, profession)
        
        # Créer le template de base
        template = BuildTemplate(
            profession=profession,
            elite_spec=elite_spec,
            role=role,
            build_role=build_role
        )
        
        # 1. Sélectionner les armes appropriées
        template.weapons = select_weapons_for_build(
            profession, 
            elite_spec, 
            build_role,
            session=session
        )
        
        # 2. Sélectionner les compétences (utilitaire, élite, etc.)
        template.skills = select_skills_for_build(
            profession,
            elite_spec,
            build_role,
            template.weapons,
            session=session
        )
        
        # 3. Sélectionner les spécialisations et traits
        template.traits = select_traits_for_build(
            profession,
            elite_spec,
            build_role,
            session=session
        )
        
        # 4. Définir les priorités de statistiques
        template.stat_priority = determine_stat_priority(build_role)
        
        # 5. Sélectionner l'équipement de base
        template.equipment = select_equipment_for_build(
            profession,
            elite_spec,
            build_role,
            template.stat_priority,
            session=session
        )
        
        return template
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du build pour {profession} ({role}): {e}")
        raise
    finally:
        # Ne fermer la session que si on l'a créée nous-mêmes
        if db is None:
            session.close()

def select_weapons_for_build(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    session: Session
) -> List[Dict[str, Any]]:
    """Sélectionne les armes appropriées pour un build donné.
    
    Args:
        profession: Le nom de la profession (en anglais)
        elite_spec: La spécialisation d'élite (optionnelle)
        build_role: Le rôle du build (DPS, heal, etc.)
        session: Session SQLAlchemy pour accéder à la base de données
        
    Returns:
        Une liste de dictionnaires représentant les armes sélectionnées
    """
    try:
        # Récupérer les armes disponibles pour cette profession
        query = session.query(ProfessionWeapon).join(Weapon).join(Profession).filter(
            Profession.name == profession.capitalize()
        )
        
        # Filtrer par spécialisation si spécifiée
        if elite_spec:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    ProfessionWeapon.specialization.has(name=elite_spec),
                    ProfessionWeapon.specialization_id.is_(None)
                )
            )
        
        # Charger les relations nécessaires pour éviter les requêtes N+1
        query = query.options(
            joinedload(ProfessionWeapon.weapon),
            joinedload(ProfessionWeapon.specialization)
        )
        
        # Récupérer toutes les armes correspondantes
        profession_weapons = query.all()
        
        if not profession_weapons:
            logger.warning(f"Aucune arme trouvée pour {profession} ({elite_spec if elite_spec else 'pas de spé'})")
            return []
        
        # Filtrer les armes en fonction du rôle
        weapons = []
        for pw in profession_weapons:
            if not pw.weapon:
                continue
                
            weapon = pw.weapon
            
            # Vérifier la compatibilité avec le rôle
            if not is_weapon_suitable_for_role(weapon, build_role, profession, elite_spec):
                continue
            
            # Convertir les flags de l'arme si nécessaire
            weapon_flags = []
            if hasattr(weapon, 'flags') and weapon.flags:
                if isinstance(weapon.flags, list):
                    weapon_flags = [f.value if hasattr(f, 'value') else str(f) for f in weapon.flags]
                elif isinstance(weapon.flags, str):
                    weapon_flags = [weapon.flags]
                
            weapons.append({
                'id': weapon.id,
                'name': getattr(weapon, 'name', 'Unknown Weapon'),
                'type': getattr(weapon.type, 'value', 'Unknown') if hasattr(weapon, 'type') else 'Unknown',
                'damage_type': getattr(weapon.damage_type, 'value', None) if hasattr(weapon, 'damage_type') and weapon.damage_type else None,
                'slot': getattr(pw.slot, 'value', 'Unknown') if hasattr(pw, 'slot') else 'Unknown',
                'flags': weapon_flags
            })
        
        # Trier les armes par pertinence pour le rôle
        weapons = sorted(
            weapons,
            key=lambda w: get_weapon_priority(w, build_role, profession, elite_spec),
            reverse=True
        )
        
        # Sélectionner les meilleures combinaisons d'armes
        return select_optimal_weapon_combinations(weapons, build_role)
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection des armes pour {profession} ({elite_spec}): {e}")
        return []

def is_weapon_suitable_for_role(
    weapon: Weapon,
    build_role: BuildRole,
    profession: str,
    elite_spec: Optional[str]
) -> bool:
    """Détermine si une arme est adaptée à un rôle donné."""
    # Vérifications de base
    if not weapon or not hasattr(weapon, 'type') or not weapon.type:
        return False
    
    # Vérifier les restrictions de profession
    if hasattr(weapon, 'restrictions') and weapon.restrictions:
        restrictions = []
        if isinstance(weapon.restrictions, list):
            restrictions = [str(r) for r in weapon.restrictions if r]
        elif isinstance(weapon.restrictions, str):
            restrictions = [weapon.restrictions]
            
        if profession.capitalize() not in restrictions:
            return False
    
    # Vérifier les drapeaux de l'arme
    weapon_flags = []
    if hasattr(weapon, 'flags'):
        if isinstance(weapon.flags, list):
            weapon_flags = [f.value if hasattr(f, 'value') else str(f) for f in weapon.flags]
        elif isinstance(weapon.flags, str):
            weapon_flags = [weapon.flags]
    
    # Exclure les armes non adaptées au rôle
    if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        # Les supports préfèrent les armes avec des effets de soutien
        if 'NoUtility' in weapon_flags:
            return False
    
    # Vérifier le type d'arme
    weapon_type = getattr(weapon.type, 'value', '').lower()
    
    # Règles spécifiques par rôle
    if build_role == BuildRole.POWER_DPS:
        # Les DPS puissance préfèrent les armes avec des dégâts directs
        return weapon_type in ['greatsword', 'sword', 'axe', 'dagger', 'staff', 'scepter', 'hammer', 'longbow']
    elif build_role == BuildRole.CONDITION_DPS:
        # Les DPS condition préfèrent les armes avec des conditions
        return weapon_type in ['scepter', 'torch', 'pistol', 'shortbow', 'dagger']
    elif build_role == BuildRole.HEALER:
        # Les soigneurs préfèrent les armes avec des capacités de soutien
        return weapon_type in ['staff', 'warhorn', 'focus', 'shield']
    elif build_role in [BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        # Les supports préfèrent les armes avec des effets de contrôle et de soutien
        return weapon_type in ['staff', 'warhorn', 'focus', 'shield', 'sword', 'mace']
    elif build_role == BuildRole.TANK:
        # Les tanks préfèrent les armes avec des contrôles et de la survie
        return weapon_type in ['shield', 'focus', 'warhorn', 'staff', 'mace']
    
    # Par défaut, inclure toutes les armes non exclues
    return True

def _are_weapons_compatible(weapon1: Dict[str, Any], weapon2: Dict[str, Any]) -> bool:
    """Vérifie si deux armes sont compatibles pour être équipées ensemble.
    
    Args:
        weapon1: Première arme à vérifier
        weapon2: Deuxième arme à vérifier
        
    Returns:
        bool: True si les armes sont compatibles, False sinon
    """
    # Si l'une des armes est à deux mains, elles ne sont pas compatibles
    if 'twohand' in [f.lower() for f in weapon1.get('flags', [])] or \
       'twohand' in [f.lower() for f in weapon2.get('flags', [])]:
        return False
    
    # Vérifier si les deux armes sont des boucliers (incompatibles)
    if weapon1.get('type', '').lower() == 'shield' and weapon2.get('type', '').lower() == 'shield':
        return False
        
    # Vérifier si les deux armes sont des armes à distance (éviter deux armes à distance)
    ranged_weapons = ['shortbow', 'longbow', 'rifle', 'pistol', 'scepter', 'staff']
    if (weapon1.get('type', '').lower() in ranged_weapons and 
        weapon2.get('type', '').lower() in ranged_weapons):
        return False
        
    return True

def select_optimal_weapon_combinations(
    weapons: List[Dict[str, Any]],
    build_role: BuildRole,
    max_combinations: int = 2
) -> List[Dict[str, Any]]:
    """Sélectionne les meilleures combinaisons d'armes pour un build."""
    if not weapons:
        return []
    
    # Extraire les flags des armes pour faciliter les vérifications
    for weapon in weapons:
        if 'flags' not in weapon:
            weapon['flags'] = []
        elif isinstance(weapon['flags'], str):
            weapon['flags'] = [weapon['flags']]
    
    # Grouper les armes par emplacement (main droite/gauche)
    main_hand = [w for w in weapons if w.get('slot', '').lower() in ['weapona1', 'weaponb1', 'mainhand']]
    off_hand = [w for w in weapons if w.get('slot', '').lower() in ['weapona2', 'weaponb2', 'offhand']]
    two_handed = [w for w in weapons if 'twohand' in [f.lower() for f in w.get('flags', [])]]
    
    # Pour les armes à deux mains, on les retourne telles quelles
    if two_handed:
        return two_handed[:max_combinations]
    
    # Pour les armes à une main, on essaie de faire des combinaisons
    combinations = []
    
    # Si on a des armes main droite et gauche, on les combine
    if main_hand and off_hand:
        for mh in main_hand[:max_combinations]:
            for oh in off_hand[:max_combinations]:
                # Vérifier que les armes sont compatibles (éviter bouclier + bouclier par exemple)
                if _are_weapons_compatible(mh, oh):
                    combinations.append([mh, oh])
                    if len(combinations) >= max_combinations:
                        break
            if len(combinations) >= max_combinations:
                break
    
    # Si on n'a pas de combinaisons ou pas assez, on ajoute des armes seules
    if len(combinations) < max_combinations:
        for w in weapons:
            # Vérifier si l'arme n'est pas déjà dans une combinaison
            if not any(w in combo for combo in combinations):
                combinations.append([w])
                if len(combinations) >= max_combinations:
                    break
    
    # Limiter le nombre de combinaisons retournées
    return combinations[:max_combinations]

def select_skills_for_build(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    weapons: List[Dict[str, Any]],
    session: Session
) -> List[Dict[str, Any]]:
    """Sélectionne les compétences appropriées pour un build donné.
    
    Args:
        profession: Le nom de la profession (en anglais)
        elite_spec: La spécialisation d'élite (optionnelle)
        build_role: Le rôle du build (DPS, heal, etc.)
        weapons: Liste des armes sélectionnées pour le build
        session: Session SQLAlchemy pour accéder à la base de données
        
    Returns:
        Une liste de dictionnaires représentant les compétences sélectionnées
    """
    try:
        # Récupérer toutes les compétences disponibles pour cette profession
        all_skills = []
        
        # Récupérer d'abord toutes les compétences (filtrage en mémoire pour les champs JSON)
        skills_query = session.query(Skill)
        
        # Filtrer par spécialisation si spécifiée
        if elite_spec:
            skills_query = skills_query.filter(
                (Skill.specialization.has(name=elite_spec)) | 
                (Skill.specialization == None)
            )
        
        # Récupérer les types d'armes équipées pour le filtrage
        weapon_types = [w.get('type', '').lower() for w in weapons if w and 'type' in w]
        
        # Filtrer les compétences par profession et armes équipées
        for skill in skills_query.all():
            if not hasattr(skill, 'professions') or not skill.professions:
                continue
                
            # Vérifier si la compétence est disponible pour cette profession
            if profession.lower() not in [p.lower() for p in skill.professions]:
                continue
                
            # Vérifier la compatibilité avec les armes équipées si nécessaire
            if hasattr(skill, 'weapon_type') and skill.weapon_type:
                if skill.weapon_type.lower() not in weapon_types:
                    continue
            
            all_skills.append(skill)
        
        if not all_skills:
            logger.warning(f"Aucune compétence trouvée pour {profession} ({elite_spec if elite_spec else 'pas de spé'})")
            return []
        
        # Catégoriser les compétences par type
        healing_skills = []
        utility_skills = []
        elite_skills = []
        
        for skill in all_skills:
            if not hasattr(skill, 'slot') or not skill.slot:
                continue
                
            slot = skill.slot.lower()
            if slot == 'heal':
                healing_skills.append(skill)
            elif slot == 'utility':
                utility_skills.append(skill)
            elif slot == 'elite':
                elite_skills.append(skill)
        
        # Sélectionner les meilleures compétences pour chaque emplacement
        selected_skills = []
        
        # 1. Compétence de soin (heal)
        if healing_skills:
            heal_skill = select_best_skill_for_role(healing_skills, build_role, 'heal', weapons)
            if heal_skill:
                selected_skills.append(heal_skill)
        
        # 2. Compétences utilitaires (jusqu'à 3)
        if utility_skills:
            # Évaluer chaque compétence utilitaire
            utility_scores = []
            for skill in utility_skills:
                score = 0
                
                # Bonus pour les compétences essentielles au rôle
                if is_skill_essential_for_role(skill, build_role, profession, elite_spec):
                    score += 100
                
                # Bonus pour les compétences qui bénéficient des armes équipées
                if hasattr(skill, 'weapon_type') and skill.weapon_type:
                    for weapon in weapons:
                        if weapon.get('type', '').lower() == skill.weapon_type.lower():
                            score += 50
                            break
                
                # Bonus pour les compétences de contrôle (importantes pour les tanks et supports)
                if build_role in [BuildRole.TANK, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
                    if hasattr(skill, 'categories') and any(cat.lower() in ['control', 'stun', 'daze', 'knockback'] 
                                                         for cat in skill.categories or []):
                        score += 30
                
                # Bonus pour les compétences de soutien (importantes pour les soigneurs et supports)
                if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
                    if hasattr(skill, 'categories') and any(cat.lower() in ['boon', 'heal', 'support'] 
                                                         for cat in skill.categories or []):
                        score += 40
                
                utility_scores.append((score, skill))
            
            # Trier par score (décroissant) et prendre les 3 meilleures
            utility_scores.sort(reverse=True, key=lambda x: x[0])
            
            # Ajouter jusqu'à 3 compétences utilitaires
            for _, skill in utility_scores[:3]:
                selected_skills.append(skill)
        
        # 3. Compétence d'élite
        if elite_skills:
            elite_skill = select_best_skill_for_role(elite_skills, build_role, 'elite', weapons)
            if elite_skill:
                selected_skills.append(elite_skill)
        
        # Convertir les objets Skill en dictionnaires
        result = []
        for skill in selected_skills:
            if skill:
                result.append({
                    'id': skill.id,
                    'name': skill.name,
                    'description': skill.description,
                    'icon': skill.icon,
                    'slot': skill.slot,
                    'type': skill.type,
                    'cooldown': skill.cooldown,
                    'initiative': skill.initiative,
                    'facts': skill.facts if hasattr(skill, 'facts') else []
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection des compétences pour {profession} ({elite_spec}): {e}")
        return []

def is_skill_essential_for_role(
    skill: Skill,
    build_role: BuildRole,
    profession: str,
    elite_spec: Optional[str]
) -> bool:
    """Détermine si une compétence est essentielle pour un rôle donné."""
    if not skill or not skill.name:
        return False
    
    skill_name = skill.name.lower()
    
    # Règles pour les soigneurs
    if build_role == BuildRole.HEALER:
        # Compétences de soin de zone ou de soutien
        if any(term in skill_name for term in ['heal', 'regenerate', 'renew', 'mend', 'revive']):
            return True
    
    # Règles pour les DPS
    elif build_role == BuildRole.POWER_DPS:
        # Compétences boostant les dégâts directs
        if any(term in skill_name for term in ['might', 'fury', 'quickness', 'vulnerability']):
            return True
    
    elif build_role == BuildRole.CONDITION_DPS:
        # Compétences infligeant des conditions de dégâts
        if any(term in skill_name for term in ['burn', 'bleed', 'poison', 'torment', 'confusion']):
            return True
    
    # Règles pour les rôles de soutien
    elif build_role in [BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        # Compétences fournissant des buffs d'utilité
        if build_role == BuildRole.QUICKNESS_SUPPORT and 'quickness' in skill_name:
            return True
        if build_role == BuildRole.ALACRITY_SUPPORT and 'alacrity' in skill_name:
            return True
        if any(term in skill_name for term in ['protection', 'stability', 'aegis', 'resistance']):
            return True
    
    # Règles pour les tanks
    elif build_role == BuildRole.TANK:
        # Compétences défensives
        if any(term in skill_name for term in ['block', 'aegis', 'protection', 'barrier', 'invulnerability']):
            return True
    
    # Règles spécifiques aux professions
    if profession.lower() == 'guardian' and 'tome' in skill_name:
        return True
    elif profession.lower() == 'mesmer' and 'portal' in skill_name:
        return True
    
    return False

def select_best_skill_for_role(
    skills: List[Skill],
    build_role: BuildRole,
    slot_type: str,
    weapons: List[Dict[str, Any]]
) -> Optional[Skill]:
    """Sélectionne la meilleure compétence pour un rôle et un emplacement donnés."""
    if not skills:
        return None
    
    # Trier les compétences par pertinence pour le rôle
    scored_skills = []
    for skill in skills:
        if not skill:
            continue
            
        score = 0
        
        # Bonus pour les compétences essentielles
        if hasattr(skill, 'is_elite') and skill.is_elite and slot_type == 'elite':
            score += 50
        
        # Bonus pour les compétences de soin pour les soigneurs
        if build_role == BuildRole.HEALER and slot_type == 'heal':
            score += 100
            if 'heal' in skill.name.lower():
                score += 50
        
        # Bonus pour les compétences de soutien pour les supports
        if build_role in [BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
            if any(term in skill.name.lower() for term in ['quickness', 'alacrity', 'might', 'fury']):
                score += 100
        
        # Bonus pour les compétences défensives pour les tanks
        if build_role == BuildRole.TANK:
            if any(term in skill.name.lower() for term in ['block', 'aegis', 'protection', 'barrier']):
                score += 100
        
        # Bonus pour les compétences offensives pour les DPS
        if build_role in [BuildRole.POWER_DPS, BuildRole.CONDITION_DPS]:
            if any(term in skill.name.lower() for term in ['damage', 'strike', 'smash']):
                score += 50
        
        # Bonus pour les compétences de contrôle pour les DPS et les tanks
        if build_role in [BuildRole.POWER_DPS, BuildRole.TANK]:
            if any(term in skill.name.lower() for term in ['stun', 'daze', 'knockdown', 'launch']):
                score += 30
        
        # Bonus pour les compétences qui interagissent avec les armes équipées
        if skill.weapon_type and weapons:
            weapon_types = [w['type'].lower() for w in weapons if w and 'type' in w]
            if skill.weapon_type.lower() in weapon_types:
                score += 40
        
        scored_skills.append((score, skill))
    
    # Trier par score et retourner la meilleure compétence
    if not scored_skills:
        return None
    
    scored_skills.sort(key=lambda x: x[0], reverse=True)
    return scored_skills[0][1]

def select_traits_for_build(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    session: Session
) -> List[Dict[str, Any]]:
    """Sélectionne les spécialisations et traits pour un build donné.
    
    Args:
        profession: Le nom de la profession (en anglais)
        elite_spec: La spécialisation d'élite (optionnelle)
        build_role: Le rôle du build (DPS, heal, etc.)
        session: Session SQLAlchemy pour accéder à la base de données
        
    Returns:
        Une liste de dictionnaires représentant les spécialisations et traits sélectionnés
    """
    try:
        # Récupérer toutes les spécialisations pour cette profession
        query = session.query(Specialization).filter(
            Specialization.profession == profession.lower()
        )
        
        # Si une spécialisation d'élite est spécifiée, s'assurer qu'elle est incluse
        elite_spec_obj = None
        if elite_spec:
            elite_spec_obj = query.filter(Specialization.name == elite_spec).first()
        
        # Récupérer toutes les spécialisations (de base et d'élite)
        all_specializations = query.all()
        
        if not all_specializations:
            logger.warning(f"Aucune spécialisation trouvée pour {profession}")
            return []
        
        # Sélectionner les spécialisations les plus adaptées au rôle
        selected_specs = select_best_specializations(
            all_specializations,
            elite_spec_obj,
            build_role,
            profession,
            session
        )
        
        # Pour chaque spécialisation sélectionnée, choisir les meilleurs traits
        result = []
        for spec in selected_specs:
            traits = select_traits_for_specialization(
                spec,
                build_role,
                profession,
                elite_spec,
                session
            )
            
            if traits:
                result.append({
                    'id': spec.id,
                    'name': spec.name,
                    'profession': spec.profession,
                    'elite': spec.elite,
                    'icon': spec.icon,
                    'traits': traits
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection des traits pour {profession} ({elite_spec}): {e}")
        return []

def select_best_specializations(
    specializations: List[Specialization],
    elite_spec: Optional[Specialization],
    build_role: BuildRole,
    profession: str,
    session: Session
) -> List[Specialization]:
    """Sélectionne les 3 meilleures spécialisations pour un rôle donné."""
    # Trier les spécialisations par pertinence pour le rôle
    scored_specs = []
    
    for spec in specializations:
        if not spec:
            continue
            
        score = 0
        
        # Bonus pour la spécialisation d'élite (si c'est celle recherchée)
        if elite_spec and spec.id == elite_spec.id:
            score += 1000  # Très fort bonus pour s'assurer qu'elle est sélectionnée
        
        # Bonus pour les spécialisations adaptées au rôle
        if is_specialization_good_for_role(spec, build_role, profession, session):
            score += 500
        
        # Bonus supplémentaire pour les spécialisations de base de la profession
        if not spec.elite:
            score += 100
        
        # Bonus pour les spécialisations populaires ou fortes en méta
        if is_meta_specialization(spec, build_role, profession):
            score += 200
        
        scored_specs.append((score, spec))
    
    # Trier par score et prendre les 3 meilleures
    scored_specs.sort(key=lambda x: x[0], reverse=True)
    
    # S'assurer qu'on a au maximum 3 spécialisations
    result = [spec for (score, spec) in scored_specs[:3]]
    
    # S'assurer que la spécialisation d'élite est incluse si elle existe
    if elite_spec and elite_spec not in result:
        # Remplacer la dernière spécialisation par celle d'élite si nécessaire
        if len(result) >= 3:
            result[-1] = elite_spec
        else:
            result.append(elite_spec)
    
    return result

def is_specialization_good_for_role(
    spec: Specialization,
    build_role: BuildRole,
    profession: str,
    session: Session
) -> bool:
    """Détermine si une spécialisation est adaptée à un rôle donné."""
    if not spec or not spec.name:
        return False
    
    spec_name = spec.name.lower()
    
    # Règles générales basées sur le nom de la spécialisation
    if build_role == BuildRole.HEALER:
        return any(term in spec_name for term in ['water', 'salvation', 'druid', 'tempest'])
    
    elif build_role in [BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        return any(term in spec_name for term in ['tactics', 'inspiration', 'herald', 'firebrand'])
    
    elif build_role == BuildRole.POWER_DPS:
        return any(term in spec_name for term in ['strength', 'arms', 'duel', 'deadly'])
    
    elif build_role == BuildRole.CONDITION_DPS:
        return any(term in spec_name for term in ['curses', 'fire', 'corruption', 'skirmishing'])
    
    elif build_role == BuildRole.TANK:
        return any(term in spec_name for term in ['defense', 'valor', 'retribution'])
    
    # Règles spécifiques aux professions
    if profession.lower() == 'guardian':
        if build_role == BuildRole.HEALER and 'firebrand' in spec_name:
            return True
        elif build_role == BuildRole.QUICKNESS_SUPPORT and 'firebrand' in spec_name:
            return True
    
    elif profession.lower() == 'warrior':
        if build_role in [BuildRole.POWER_DPS, BuildRole.QUICKNESS_SUPPORT] and 'berserker' in spec_name:
            return True
    
    # Par défaut, considérer que la spécialisation est adaptée
    return True

def is_meta_specialization(
    spec: Specialization,
    build_role: BuildRole,
    profession: str
) -> bool:
    """Détermine si une spécialisation est considérée comme forte en méta pour un rôle donné."""
    if not spec or not spec.name:
        return False
    
    spec_name = spec.name.lower()
    
    # Liste des spécialisations fortes en méta par rôle
    meta_specs = {
        BuildRole.HEALER: ['firebrand', 'mechanist', 'druid', 'tempest'],
        BuildRole.QUICKNESS_SUPPORT: ['firebrand', 'herald', 'scrapper', 'chronomancer'],
        BuildRole.ALACRITY_SUPPORT: ['mechanist', 'specter', 'renegade', 'mirage'],
        BuildRole.POWER_DPS: ['berserker', 'dragonhunter', 'soulbeast', 'holosmith'],
        BuildRole.CONDITION_DPS: ['scourge', 'firebrand', 'renegade', 'mirage'],
        BuildRole.TANK: ['firebrand', 'chronomancer', 'scourge', 'herald']
    }
    
    return any(meta_spec in spec_name for meta_spec in meta_specs.get(build_role, []))

def select_traits_for_specialization(
    specialization: Specialization,
    build_role: BuildRole,
    profession: str,
    elite_spec: Optional[str],
    session: Session
) -> List[Dict[str, Any]]:
    """Sélectionne les meilleurs traits pour une spécialisation et un rôle donnés."""
    if not specialization:
        return []
    
    try:
        # Récupérer tous les traits pour cette spécialisation
        traits = session.query(Trait).filter(
            Trait.specialization_id == specialization.id
        ).all()
        
        if not traits:
            return []
        
        # Grouper les traits par niveau (Adept, Master, Grandmaster)
        traits_by_tier = {1: [], 2: [], 3: []}
        for trait in traits:
            if 1 <= trait.tier <= 3:
                traits_by_tier[trait.tier].append(trait)
        
        # Sélectionner le meilleur trait pour chaque niveau
        selected_traits = []
        for tier in [1, 2, 3]:
            tier_traits = traits_by_tier.get(tier, [])
            if tier_traits:
                best_trait = select_best_trait(
                    tier_traits,
                    build_role,
                    profession,
                    elite_spec,
                    tier
                )
                if best_trait:
                    selected_traits.append({
                        'id': best_trait.id,
                        'name': best_trait.name,
                        'description': best_trait.description,
                        'icon': best_trait.icon,
                        'tier': best_trait.tier,
                        'slot': best_trait.slot
                    })
        
        return selected_traits
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection des traits pour {specialization.name}: {e}")
        return []

def select_best_trait(
    traits: List[Trait],
    build_role: BuildRole,
    profession: str,
    elite_spec: Optional[str],
    tier: int
) -> Optional[Trait]:
    """Sélectionne le meilleur trait parmi une liste pour un rôle donné."""
    if not traits:
        return None
    
    # Si un seul trait est disponible, le retourner
    if len(traits) == 1:
        return traits[0]
    
    # Sinon, évaluer chaque trait
    scored_traits = []
    for trait in traits:
        if not trait or not trait.name:
            continue
            
        score = 0
        trait_name = trait.name.lower()
        
        # Bonus pour les traits en fonction du rôle
        if build_role == BuildRole.HEALER:
            if any(term in trait_name for term in ['heal', 'regeneration', 'recovery', 'mending']):
                score += 100
            if 'output' in trait_name and 'damage' not in trait_name:
                score += 50
        
        elif build_role in [BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
            if build_role == BuildRole.QUICKNESS_SUPPORT and 'quickness' in trait_name:
                score += 200
            elif build_role == BuildRole.ALACRITY_SUPPORT and 'alacrity' in trait_name:
                score += 200
            if any(term in trait_name for term in ['boon', 'duration', 'concentration']):
                score += 50
        
        elif build_role == BuildRole.POWER_DPS:
            if any(term in trait_name for term in ['power', 'ferocity', 'precision', 'critical', 'strike']):
                score += 100
        
        elif build_role == BuildRole.CONDITION_DPS:
            if any(term in trait_name for term in ['condition', 'burn', 'bleed', 'poison', 'torment', 'confusion']):
                score += 100
        
        elif build_role == BuildRole.TANK:
            if any(term in trait_name for term in ['toughness', 'vitality', 'protection', 'barrier', 'block']):
                score += 100
        
        # Bonus pour les traits spécifiques à la spécialisation d'élite
        if elite_spec and elite_spec.lower() in trait_name:
            score += 150
        
        # Bonus pour les traits qui améliorent les compétences de l'élite
        if elite_spec and 'elite' in trait_name:
            score += 100
        
        # Pénalité pour les traits qui réduisent les dégâts si on est DPS
        if build_role in [BuildRole.POWER_DPS, BuildRole.CONDITION_DPS]:
            if any(term in trait_name for term in ['reduce', 'decrease', 'less']):
                score -= 50
        
        scored_traits.append((score, trait))
    
    # Trier par score et retourner le meilleur trait
    if not scored_traits:
        return None
    
    scored_traits.sort(key=lambda x: x[0], reverse=True)
    return scored_traits[0][1]

def determine_stat_priority(build_role: BuildRole) -> List[str]:
    """Détermine les priorités de statistiques en fonction du rôle du build."""
    if build_role == BuildRole.POWER_DPS:
        return ["Power", "Precision", "Ferocity", "Vitality"]
    elif build_role == BuildRole.CONDITION_DPS:
        return ["Condition Damage", "Expertise", "Precision", "Vitality"]
    elif build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        return ["Healing Power", "Concentration", "Vitality", "Toughness"]
    elif build_role == BuildRole.TANK:
        return ["Toughness", "Vitality", "Healing Power", "Concentration"]
    else:  # HYBRID
        return ["Power", "Precision", "Ferocity", "Vitality", "Toughness"]

def select_equipment_for_build(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    stat_priority: List[str],
    session: Session
) -> Dict[str, Dict[str, Any]]:
    """Sélectionne l'équipement approprié pour un build donné.
    
    Args:
        profession: Le nom de la profession (en anglais)
        elite_spec: La spécialisation d'élite (optionnelle)
        build_role: Le rôle du build (DPS, heal, etc.)
        stat_priority: Liste des statistiques prioritaires pour ce rôle
        session: Session SQLAlchemy pour accéder à la base de données
        
    Returns:
        Un dictionnaire représentant l'équipement sélectionné
    """
    try:
        # Déterminer les statistiques cibles en fonction du rôle
        stat_combinations = determine_stat_combinations(stat_priority, build_role)
        
        # Sélectionner les pièces d'équipement
        equipment = {}
        
        # 1. Sélectionner les armes (déjà sélectionnées, on les inclut dans l'équipement final)
        # Note: Les armes sont gérées séparément dans la structure du build
        
        # 2. Sélectionner l'armure
        armor_pieces = [
            'Helm', 'Shoulders', 'Coat', 'Gloves', 'Leggings', 'Boots'
        ]
        
        for piece in armor_pieces:
            equipment[piece] = select_armor_piece(
                piece,
                profession,
                elite_spec,
                build_role,
                stat_combinations,
                session
            )
        
        # 3. Sélectionner les accessoires
        accessories = [
            'Amulet', 'Ring1', 'Ring2', 'Accessory1', 'Accessory2', 'Backpack'
        ]
        
        for acc in accessories:
            equipment[acc] = select_accessory(
                acc,
                profession,
                elite_spec,
                build_role,
                stat_combinations,
                session
            )
        
        # 4. Sélectionner les runes et les sigils
        equipment['Rune'] = select_rune(
            profession,
            elite_spec,
            build_role,
            stat_priority,
            session
        )
        
        # 5. Sélectionner les nourritures et améliorations
        equipment['Food'] = select_food(
            profession,
            elite_spec,
            build_role,
            stat_priority,
            session
        )
        
        equipment['Utility'] = select_utility(
            profession,
            elite_spec,
            build_role,
            stat_priority,
            session
        )
        
        return equipment
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de l'équipement pour {profession} ({elite_spec}): {e}")
        return {}

def determine_stat_combinations(stat_priority: List[str], build_role: BuildRole) -> List[Dict[str, float]]:
    """Détermine les combinaisons de statistiques à privilégier pour un rôle donné."""
    # Définir les combinaisons de stats courantes pour chaque rôle
    stat_combinations = []
    
    if build_role in [BuildRole.POWER_DPS, BuildRole.TANK]:
        stat_combinations.append({
            'Power': 1.0,
            'Precision': 0.8,
            'Ferocity': 0.7,
            'Toughness': 0.5 if build_role == BuildRole.TANK else 0.1,
            'Vitality': 0.4 if build_role == BuildRole.TANK else 0.2,
            'Healing': 0.0
        })
    
    if build_role in [BuildRole.CONDITION_DPS]:
        stat_combinations.append({
            'ConditionDamage': 1.0,
            'Expertise': 0.9,
            'Precision': 0.6,
            'Power': 0.3,
            'Vitality': 0.2,
            'Toughness': 0.1,
            'Healing': 0.0
        })
    
    if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
        stat_combinations.append({
            'Healing': 1.0,
            'Concentration': 0.9,
            'Vitality': 0.6,
            'Toughness': 0.5,
            'Power': 0.3,
            'ConditionDamage': 0.2
        })
    
    # Ajuster les combinaisons en fonction des priorités spécifiées
    if stat_priority:
        for combo in stat_combinations:
            # Réinitialiser les poids
            for stat in combo:
                combo[stat] = 0.0
            
            # Définir les poids en fonction de la priorité
            for i, stat in enumerate(stat_priority):
                if stat in combo:
                    # Plus la statistique est prioritaire, plus le poids est élevé
                    combo[stat] = 1.0 - (i * 0.2)
    
    return stat_combinations

def select_armor_piece(
    piece: str,
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    stat_combinations: List[Dict[str, float]],
    session: Session
) -> Dict[str, Any]:
    """Sélectionne une pièce d'armure adaptée au build."""
    try:
        # Récupérer les pièces d'armure disponibles pour cet emplacement
        # Utiliser cast pour le champ JSON et opérateur ->> pour l'accès au texte
        from sqlalchemy import cast, String
        from sqlalchemy.sql.expression import or_
        
        # Récupérer d'abord tous les éléments d'armure de niveau approprié
        armor_query = session.query(Item).filter(
            Item.type == 'Armor',
            Item.level >= 80
        )
        
        # Filtrer en mémoire pour les champs JSON (plus simple et plus fiable)
        armor_pieces = []
        for item in armor_query.all():
            if not item.details:
                continue
                
            weight_class = item.details.get('weight_class')
            item_type = item.details.get('type')
            
            if (weight_class in ['Light', 'Medium', 'Heavy'] and 
                item_type == piece):
                armor_pieces.append(item)
        
        if not armor_pieces:
            return {}
        
        # Évaluer chaque pièce d'armure
        best_piece = None
        best_score = -1
        
        for piece in armor_pieces:
            if not piece.details or 'stats' not in piece.details:
                continue
                
            # Calculer le score de cette pièce pour chaque combinaison de stats
            for combo in stat_combinations:
                score = 0
                
                # Ajouter les bonus de statistiques
                for stat, weight in combo.items():
                    stat_value = piece.details['stats'].get(stat, 0)
                    score += stat_value * weight
                
                # Bonus pour les pièces avec des attributs rares/ascendus
                if piece.rarity == 'Ascended':
                    score *= 1.2
                elif piece.rarity == 'Exotic':
                    score *= 1.0
                else:
                    score *= 0.8
                
                # Mettre à jour la meilleure pièce si nécessaire
                if score > best_score:
                    best_score = score
                    best_piece = piece
        
        if best_piece:
            return {
                'id': best_piece.id,
                'name': best_piece.name,
                'type': best_piece.type,
                'rarity': best_piece.rarity,
                'level': best_piece.level,
                'stats': best_piece.details.get('stats', {}) if best_piece.details else {}
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de la pièce d'armure {piece}: {e}")
        return {}

def select_accessory(
    accessory_type: str,
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    stat_combinations: List[Dict[str, float]],
    session: Session
) -> Dict[str, Any]:
    """Sélectionne un accessoire adapté au build."""
    try:
        # Récupérer d'abord tous les accessoires de niveau approprié
        accessories_query = session.query(Item).filter(
            Item.type == 'Trinket',
            Item.level >= 80
        )
        
        # Filtrer en mémoire pour le type d'accessoire
        accessories = []
        for item in accessories_query.all():
            if not item.details:
                continue
                
            item_type = item.details.get('type')
            if item_type == accessory_type:
                accessories.append(item)
        
        if not accessories:
            return {}
        
        # Évaluer chaque accessoire
        best_accessory = None
        best_score = -1
        
        for accessory in accessories:
            if not accessory.details or 'stats' not in accessory.details:
                continue
                
            # Calculer le score de cet accessoire pour chaque combinaison de stats
            for combo in stat_combinations:
                score = 0
                
                # Ajouter les bonus de statistiques
                for stat, weight in combo.items():
                    stat_value = accessory.details['stats'].get(stat, 0)
                    score += stat_value * weight
                
                # Bonus pour les accessoires avec des attributs rares/ascendus
                if accessory.rarity == 'Ascended':
                    score *= 1.2
                elif accessory.rarity == 'Exotic':
                    score *= 1.0
                else:
                    score *= 0.8
                
                # Mettre à jour le meilleur accessoire si nécessaire
                if score > best_score:
                    best_score = score
                    best_accessory = accessory
        
        if best_accessory:
            return {
                'id': best_accessory.id,
                'name': best_accessory.name,
                'type': best_accessory.type,
                'rarity': best_accessory.rarity,
                'level': best_accessory.level,
                'stats': best_accessory.details.get('stats', {}) if best_accessory.details else {}
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de l'accessoire {accessory_type}: {e}")
        return {}

def select_rune(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    stat_priority: List[str],
    session: Session
) -> Dict[str, Any]:
    """Sélectionne une rune adaptée au build."""
    try:
        # Récupérer d'abord tous les composants d'amélioration de niveau approprié
        runes_query = session.query(Item).filter(
            Item.type == 'UpgradeComponent',
            Item.level >= 80
        )
        
        # Filtrer en mémoire pour les runes
        runes = []
        for item in runes_query.all():
            if not item.details:
                continue
                
            item_type = item.details.get('type')
            if item_type == 'Rune':
                runes.append(item)
        
        if not runes:
            return {}
        
        # Déterminer les bonus de rune les plus utiles pour ce rôle
        desired_bonuses = []
        
        if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
            desired_bonuses.extend(['Healing', 'Boon Duration', 'Concentration', 'Vitality'])
        
        if build_role == BuildRole.POWER_DPS:
            desired_bonuses.extend(['Power', 'Precision', 'Ferocity', 'Might Duration'])
        
        if build_role == BuildRole.CONDITION_DPS:
            desired_bonuses.extend(['Condition Damage', 'Condition Duration', 'Expertise', 'Bleeding', 'Burning'])
        
        if build_role == BuildRole.TANK:
            desired_bonuses.extend(['Toughness', 'Vitality', 'Healing', 'Barrier'])
        
        # Trouver la rune avec les bonus les plus pertinents
        best_rune = None
        best_score = -1
        
        for rune in runes:
            if not rune.details or 'bonuses' not in rune.details:
                continue
                
            score = 0
            
            # Vérifier chaque bonus de la rune
            for bonus in rune.details['bonuses']:
                for desired in desired_bonuses:
                    if desired.lower() in bonus.lower():
                        score += 1
            
            # Bonus pour les runes de haut niveau
            if rune.rarity == 'Rare':
                score += 1
            elif rune.rarity == 'Exotic':
                score += 2
            elif rune.rarity == 'Ascended':
                score += 3
            
            # Mettre à jour la meilleure rune si nécessaire
            if score > best_score:
                best_score = score
                best_rune = rune
        
        if best_rune:
            return {
                'id': best_rune.id,
                'name': best_rune.name,
                'type': best_rune.type,
                'rarity': best_rune.rarity,
                'level': best_rune.level,
                'bonuses': best_rune.details.get('bonuses', []) if best_rune.details else []
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de la rune: {e}")
        return {}

def select_food(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    stat_priority: List[str],
    session: Session
) -> Dict[str, Any]:
    """Sélectionne une nourriture adaptée au build."""
    try:
        # Récupérer d'abord tous les consommables de niveau approprié
        foods_query = session.query(Item).filter(
            Item.type == 'Consumable',
            Item.level >= 60
        )
        
        # Filtrer en mémoire pour la nourriture
        foods = []
        for item in foods_query.all():
            if not item.details:
                continue
                
            item_type = item.details.get('type')
            if item_type == 'Food':
                foods.append(item)
        
        if not foods:
            return {}
        
        # Déterminer les bonus de nourriture les plus utiles pour ce rôle
        desired_effects = []
        
        if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
            desired_effects.extend(['Healing', 'Concentration', 'Vitality', 'Health Regeneration'])
        
        if build_role == BuildRole.POWER_DPS:
            desired_effects.extend(['Power', 'Precision', 'Ferocity', 'Experience from Kills'])
        
        if build_role == BuildRole.CONDITION_DPS:
            desired_effects.extend(['Condition Damage', 'Condition Duration', 'Expertise', 'Experience from Kills'])
        
        if build_role == BuildRole.TANK:
            desired_effects.extend(['Toughness', 'Vitality', 'Health Regeneration', 'Reduced Incoming Damage'])
        
        # Trouver la nourriture avec les effets les plus pertinents
        best_food = None
        best_score = -1
        
        for food in foods:
            if not food.details or 'effects' not in food.details:
                continue
                
            score = 0
            
            # Vérifier chaque effet de la nourriture
            for effect in food.details['effects']:
                for desired in desired_effects:
                    if desired.lower() in effect.lower():
                        score += 1
            
            # Mettre à jour la meilleure nourriture si nécessaire
            if score > best_score:
                best_score = score
                best_food = food
        
        if best_food:
            return {
                'id': best_food.id,
                'name': best_food.name,
                'type': best_food.type,
                'rarity': best_food.rarity,
                'level': best_food.level,
                'effects': best_food.details.get('effects', []) if best_food.details else [],
                'duration': best_food.details.get('duration_minutes', 30) if best_food.details else 30
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de la nourriture: {e}")
        return {}

def select_utility(
    profession: str,
    elite_spec: Optional[str],
    build_role: BuildRole,
    stat_priority: List[str],
    session: Session
) -> Dict[str, Any]:
    """Sélectionne une amélioration utilitaire adaptée au build."""
    try:
        # Récupérer d'abord tous les consommables de niveau approprié
        utilities_query = session.query(Item).filter(
            Item.type == 'Consumable',
            Item.level >= 80
        )
        
        # Filtrer en mémoire pour les améliorations utilitaires
        utilities = []
        for item in utilities_query.all():
            if not item.details:
                continue
                
            item_type = item.details.get('type')
            if item_type == 'Utility':
                utilities.append(item)
        
        if not utilities:
            return {}
        
        # Déterminer les effets utilitaires les plus utiles pour ce rôle
        desired_effects = []
        
        if build_role in [BuildRole.HEALER, BuildRole.QUICKNESS_SUPPORT, BuildRole.ALACRITY_SUPPORT]:
            desired_effects.extend(['Boon Duration', 'Healing', 'Concentration', 'Vitality'])
        
        if build_role == BuildRole.POWER_DPS:
            desired_effects.extend(['Power', 'Precision', 'Ferocity', 'Might Duration'])
        
        if build_role == BuildRole.CONDITION_DPS:
            desired_effects.extend(['Condition Damage', 'Condition Duration', 'Expertise', 'Bleeding', 'Burning'])
        
        if build_role == BuildRole.TANK:
            desired_effects.extend(['Toughness', 'Vitality', 'Healing', 'Barrier', 'Reduced Incoming Damage'])
        
        # Trouver l'utilitaire avec les effets les plus pertinents
        best_utility = None
        best_score = -1
        
        for utility in utilities:
            if not utility.details or 'effects' not in utility.details:
                continue
                
            score = 0
            
            # Vérifier chaque effet de l'utilitaire
            for effect in utility.details['effects']:
                for desired in desired_effects:
                    if desired.lower() in effect.lower():
                        score += 1
            
            # Mettre à jour le meilleur utilitaire si nécessaire
            if score > best_score:
                best_score = score
                best_utility = utility
        
        if best_utility:
            return {
                'id': best_utility.id,
                'name': best_utility.name,
                'type': best_utility.type,
                'rarity': best_utility.rarity,
                'level': best_utility.level,
                'effects': best_utility.details.get('effects', []) if best_utility.details else [],
                'duration': best_utility.details.get('duration_minutes', 30) if best_utility.details else 30
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Erreur lors de la sélection de l'utilitaire: {e}")
        return {}

# Fonction d'aide pour la génération de builds
def generate_build_details(member) -> dict:
    """Génère les détails d'un build pour un membre d'équipe.
    
    Args:
        member: Un objet PlayerBuild contenant les informations de base
        
    Returns:
        Un dictionnaire contenant les détails du build généré
    """
    try:
        # Générer un build personnalisé
        build = generate_build_for_profession(
            profession=member.profession_id,
            role=member.roles[0] if member.roles else RoleType.DPS,
            elite_spec=member.elite_spec
        )
        
        # Convertir en format de sortie
        return {
            "profession": build.profession,
            "elite_spec": build.elite_spec,
            "roles": [r.value for r in member.roles],
            "weapons": build.weapons,
            "skills": build.skills,
            "traits": build.traits,
            "equipment": build.equipment,
            "stats_priority": build.stat_priority,
            "rotation": []  # À implémenter
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du build pour {member.profession_id}: {e}")
        # Retourner une structure vide en cas d'erreur
        return {
            "profession": member.profession_id,
            "elite_spec": member.elite_spec,
            "roles": [r.value for r in member.roles],
            "weapons": [],
            "skills": [],
            "traits": [],
            "equipment": {},
            "stats_priority": [],
            "rotation": []
        }
