"""
Module d'optimisation d'équipe pour Guild Wars 2 TeamBuilder.

Ce module contient les fonctions pour évaluer et optimiser la synergie d'une équipe
en fonction des rôles, des buffs et des capacités des membres.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
from enum import Enum

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuildRole(str, Enum):
    """Énumération des rôles possibles pour un build."""
    POWER_DPS = "power_dps"
    CONDITION_DPS = "condition_dps"
    HEALER = "healer"
    TANK = "tank"
    QUICKNESS_SUPPORT = "quickness_support"
    ALACRITY_SUPPORT = "alacrity_support"
    HYBRID = "hybrid"

def evaluate_team_synergy(team: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Évalue la synergie globale d'une équipe.
    
    Args:
        team: Liste des membres de l'équipe avec leurs builds
        
    Returns:
        Un dictionnaire contenant l'évaluation de la synergie et des suggestions d'amélioration
    """
    try:
        if not team:
            return {'score': 0, 'coverage': {}, 'suggestions': []}
            
        # 1. Analyser la couverture des rôles
        role_coverage = analyze_role_coverage(team)
        
        # 2. Analyser la couverture des buffs
        buff_coverage = analyze_buff_coverage(team)
        
        # 3. Analyser les synergies de profession
        profession_synergy = analyze_profession_synergy(team)
        
        # 4. Calculer le score global de synergie (0-100)
        synergy_score = calculate_synergy_score(role_coverage, buff_coverage, profession_synergy)
        
        # 5. Générer des suggestions d'amélioration
        suggestions = generate_synergy_suggestions(role_coverage, buff_coverage, profession_synergy, team)
        
        return {
            'score': synergy_score,
            'role_coverage': role_coverage,
            'buff_coverage': buff_coverage,
            'profession_synergy': profession_synergy,
            'suggestions': suggestions
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation de la synergie d'équipe: {e}")
        return {'score': 0, 'coverage': {}, 'suggestions': []}

def analyze_role_coverage(team: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyse la couverture des rôles dans l'équipe."""
    role_counts = {
        'dps': 0,
        'heal': 0,
        'support': 0,
        'tank': 0,
        'quickness': 0,
        'alacrity': 0,
        'might': 0,
        'fury': 0,
        'protection': 0,
        'aegis': 0,
        'stability': 0
    }
    
    for member in team:
        build = member.get('build', {})
        role = build.get('role', '').lower()
        
        # Compter les rôles principaux
        if 'dps' in role:
            role_counts['dps'] += 1
        if 'heal' in role or 'support' in role:
            role_counts['heal'] += 1
        if 'tank' in role:
            role_counts['tank'] += 1
            
        # Compter les rôles de support spécifiques
        if 'quickness' in role:
            role_counts['quickness'] += 1
        if 'alacrity' in role:
            role_counts['alacrity'] += 1
            
        # Compter les buffs fournis
        buffs = build.get('buffs', [])
        if 'might' in buffs:
            role_counts['might'] += 1
        if 'fury' in buffs:
            role_counts['fury'] += 1
        if 'protection' in buffs:
            role_counts['protection'] += 1
        if 'aegis' in buffs:
            role_counts['aegis'] += 1
        if 'stability' in buffs:
            role_counts['stability'] += 1
    
    # Évaluer la couverture des rôles
    role_evaluation = {
        'dps_covered': role_counts['dps'] >= 3,  # Au moins 3 DPS recommandés
        'heal_covered': role_counts['heal'] >= 1,  # Au moins 1 heal
        'tank_covered': role_counts['tank'] >= 1,  # Au moins 1 tank
        'quick_covered': role_counts['quickness'] >= 1,  # Au moins 1 source de quickness
        'alac_covered': role_counts['alacrity'] >= 1,  # Au moins 1 source d'alacrity
        'might_covered': role_counts['might'] >= 1,  # Au moins 1 source de might
        'fury_covered': role_counts['fury'] >= 1,  # Au moins 1 source de fury
        'prot_covered': role_counts['protection'] >= 1,  # Au moins 1 source de protection
        'aegis_covered': role_counts['aegis'] >= 1,  # Au moins 1 source d'aegis
        'stab_covered': role_counts['stability'] >= 1,  # Au moins 1 source de stabilité
    }
    
    return {
        'counts': role_counts,
        'evaluation': role_evaluation
    }

def analyze_buff_coverage(team: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyse la couverture des buffs dans l'équipe."""
    buffs = {
        'offensive': {
            'might': False,
            'fury': False,
            'quickness': False,
            'alacrity': False,
            'banner': False,
            'spotter': False,
            'sun_spirit': False,
            'frost_spirit': False,
            'empower_ally': False
        },
        'defensive': {
            'protection': False,
            'aegis': False,
            'stability': False,
            'resistance': False,
            'vigor': False,
            'regeneration': False,
            'barrier': False
        },
        'utility': {
            'stealth': False,
            'superspeed': False,
            'portal': False,
            'pulls': False,
            'cc': False,
            'reflect': False
        }
    }
    
    for member in team:
        build = member.get('build', {})
        profession = build.get('profession', '').lower()
        elite_spec = build.get('elite_spec', '').lower()
        
        # Vérifier les buffs offensifs
        if 'warrior' in profession or 'berserker' in elite_spec or 'spellbreaker' in elite_spec or 'bladesworn' in elite_spec:
            buffs['offensive']['banner'] = True
            
        if 'ranger' in profession or 'druid' in elite_spec or 'soulbeast' in elite_spec or 'untamed' in elite_spec:
            buffs['offensive']['spotter'] = True
            buffs['offensive']['frost_spirit'] = True
            buffs['offensive']['sun_spirit'] = True
            
        if 'guardian' in profession or 'firebrand' in elite_spec or 'dragonhunter' in elite_spec or 'willbender' in elite_spec:
            buffs['offensive']['empower_ally'] = True
            
        # Vérifier les buffs défensifs
        if 'guardian' in profession or 'firebrand' in elite_spec:
            buffs['defensive']['aegis'] = True
            buffs['defensive']['stability'] = True
            buffs['defensive']['protection'] = True
            
        if 'elementalist' in profession and 'tempest' in elite_spec:
            buffs['defensive']['protection'] = True
            buffs['defensive']['regeneration'] = True
            
        # Vérifier les utilités
        if 'thief' in profession or 'daredevil' in elite_spec or 'deadeye' in elite_spec or 'specter' in elite_spec:
            buffs['utility']['stealth'] = True
            
        if 'engineer' in profession or 'scrapper' in elite_spec or 'holosmith' in elite_spec or 'mechanist' in elite_spec:
            buffs['utility']['superspeed'] = True
            
        if 'mesmer' in profession or 'chronomancer' in elite_spec or 'mirage' in elite_spec or 'virtuoso' in elite_spec:
            buffs['utility']['portal'] = True
            buffs['utility']['reflect'] = True
    
    # Évaluer la couverture des buffs
    buff_evaluation = {
        'offensive_score': sum(1 for v in buffs['offensive'].values() if v) / len(buffs['offensive']) * 100,
        'defensive_score': sum(1 for v in buffs['defensive'].values() if v) / len(buffs['defensive']) * 100,
        'utility_score': sum(1 for v in buffs['utility'].values() if v) / len(buffs['utility']) * 100,
        'total_score': (
            sum(1 for v in buffs['offensive'].values() if v) + 
            sum(1 for v in buffs['defensive'].values() if v) + 
            sum(1 for v in buffs['utility'].values() if v)
        ) / (len(buffs['offensive']) + len(buffs['defensive']) + len(buffs['utility'])) * 100
    }
    
    return {
        'buffs': buffs,
        'evaluation': buff_evaluation
    }

def analyze_profession_synergy(team: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyse les synergies entre les professions de l'équipe."""
    profession_counts = {}
    profession_combos = []
    
    # Compter les occurrences de chaque profession
    for member in team:
        build = member.get('build', {})
        profession = build.get('profession', '').lower()
        elite_spec = build.get('elite_spec', '').lower()
        
        # Utiliser la spécialisation d'élite si disponible, sinon la profession de base
        prof_key = elite_spec if elite_spec else profession
        
        if prof_key in profession_counts:
            profession_counts[prof_key] += 1
        else:
            profession_counts[prof_key] = 1
    
    # Identifier les combinaisons de professions
    profession_list = list(profession_counts.keys())
    
    # Évaluer les synergies connues
    synergy_scores = []
    
    # Vérifier les synergies connues
    if 'firebrand' in profession_list and 'scourge' in profession_list:
        synergy_scores.append(('Firebrand + Scourge', 90, 'Excellente synergie condition avec support et dégâts'))
    
    if 'druid' in profession_list and 'chronomancer' in profession_list:
        synergy_scores.append(('Druid + Chronomancer', 85, 'Bonne synergie de support et contrôle de foule'))
    
    if 'herald' in profession_list and 'renegade' in profession_list:
        synergy_scores.append(('Herald + Renegade', 88, 'Bonne synergie de buffs offensifs et défensifs'))
    
    if 'mechanist' in profession_list and 'specter' in profession_list:
        synergy_scores.append(('Mechanist + Specter', 82, 'Bonne synergie pour le support et les dégâts à distance'))
    
    # Calculer un score de diversité des professions
    unique_professions = len(profession_counts)
    total_members = len(team)
    diversity_score = (unique_professions / total_members) * 100 if total_members > 0 else 0
    
    # Vérifier les doublons de spécialisation
    duplicate_specs = [spec for spec, count in profession_counts.items() if count > 1]
    
    return {
        'profession_distribution': profession_counts,
        'diversity_score': diversity_score,
        'duplicate_specializations': duplicate_specs,
        'synergies': synergy_scores
    }

def calculate_synergy_score(role_coverage: Dict[str, Any], buff_coverage: Dict[str, Any], 
                          profession_synergy: Dict[str, Any]) -> float:
    """Calcule un score de synergie global pour l'équipe."""
    # Poids pour chaque composante du score
    WEIGHTS = {
        'role_coverage': 0.5,
        'buff_coverage': 0.3,
        'profession_synergy': 0.2
    }
    
    # Calculer le score de couverture des rôles (0-100)
    role_eval = role_coverage.get('evaluation', {})
    role_score = (
        int(role_eval.get('dps_covered', False)) * 20 +
        int(role_eval.get('heal_covered', False)) * 15 +
        int(role_eval.get('tank_covered', False)) * 15 +
        int(role_eval.get('quick_covered', False)) * 10 +
        int(role_eval.get('alac_covered', False)) * 10 +
        int(role_eval.get('might_covered', False)) * 5 +
        int(role_eval.get('fury_covered', False)) * 5 +
        int(role_eval.get('prot_covered', False)) * 5 +
        int(role_eval.get('aegis_covered', False)) * 5 +
        int(role_eval.get('stab_covered', False)) * 5
    )
    
    # Récupérer le score de couverture des buffs
    buff_eval = buff_coverage.get('evaluation', {})
    buff_score = buff_eval.get('total_score', 0)
    
    # Calculer le score de synergie des professions
    prof_synergy = profession_synergy.get('synergies', [])
    prof_score = profession_synergy.get('diversity_score', 0)
    
    # Ajouter des points pour les synergies spécifiques
    for _, score, _ in prof_synergy:
        prof_score += score / 5  # Ajouter un pourcentage du score de synergie
    
    # Limiter à 100
    prof_score = min(prof_score, 100)
    
    # Calculer le score final pondéré
    final_score = (
        role_score * WEIGHTS['role_coverage'] +
        buff_score * WEIGHTS['buff_coverage'] +
        prof_score * WEIGHTS['profession_synergy']
    )
    
    return round(final_score, 1)

def generate_synergy_suggestions(role_coverage: Dict[str, Any], buff_coverage: Dict[str, Any], 
                               profession_synergy: Dict[str, Any], team: List[Dict[str, Any]]) -> List[str]:
    """Génère des suggestions pour améliorer la synergie de l'équipe."""
    suggestions = []
    
    # Vérifier la couverture des rôles
    role_eval = role_coverage.get('evaluation', {})
    
    if not role_eval.get('heal_covered', False):
        suggestions.append("L'équipe n'a pas de soigneur. Envisagez d'ajouter un support de soins comme un Druide, un Firebrand ou un Mechanist.")
    
    if not role_eval.get('tank_covered', False) and len(team) >= 5:
        suggestions.append("Pour un groupe de 5 joueurs ou plus, il est recommandé d'avoir un tank pour gérer la mécanique d'aggro.")
    
    if not role_eval.get('quick_covered', False):
        suggestions.append("Aucune source de Quickness détectée. Envisagez d'ajouter un Firebrand, Chronomancer ou Scrapper.")
    
    if not role_eval.get('alac_covered', False):
        suggestions.append("Aucune source d'Alacrité détectée. Envisagez d'ajouter un Renegade, Mechanist ou Specter.")
    
    # Vérifier la couverture des buffs
    buff_eval = buff_coverage.get('evaluation', {})
    
    if buff_eval.get('offensive_score', 0) < 50:
        suggestions.append("La couverture des buffs offensifs est faible. Envisagez d'ajouter des buffs comme Might, Fury ou des buffs spécifiques de classe.")
    
    if buff_eval.get('defensive_score', 0) < 50:
        suggestions.append("La couverture des buffs défensifs est faible. Envisagez d'ajouter des buffs comme Protection, Aegis ou Stabilité.")
    
    # Vérifier les synergies de profession
    if profession_synergy.get('diversity_score', 0) < 50 and len(team) >= 3:
        suggestions.append("L'équipe manque de diversité de professions. Envisagez d'ajouter des rôles complémentaires.")
    
    duplicate_specs = profession_synergy.get('duplicate_specializations', [])
    if duplicate_specs and len(team) <= 5:
        for spec in duplicate_specs:
            suggestions.append(f"Plusieurs {spec} dans l'équipe. Envisagez de diversifier les spécialisations pour une meilleure couverture des rôles.")
    
    # Si pas de suggestions spécifiques, ajouter des suggestions générales
    if not suggestions:
        suggestions.append("L'équipe a une bonne couverture des rôles et des buffs. Pensez à optimiser les rotations et la coordination pour maximiser les performances.")
    
    return suggestions
