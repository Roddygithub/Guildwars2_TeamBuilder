"""Module pour exporter des builds GW2 au format gw2skills.net.

Ce module fournit des fonctions pour convertir les builds internes du projet
au format utilisé par gw2skills.net, permettant un partage facile des builds
générés.
"""
from __future__ import annotations

import base64
import json
import logging
import zlib
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Union

from app.scoring.engine import PlayerBuild

logger = logging.getLogger(__name__)

# Constantes pour l'encodage/décodage des builds
gw2skills_version = 1
build_template = {
    "version": gw2skills_version,
    "profession": "",
    "specialization": "",
    "weapons": {"mainhand": None, "offhand": None, "aquatic": None},
    "slot_skills": {"heal": None, "utility1": None, "utility2": None, "utility3": None, "elite": None},
    "specializations": {"line1": None, "line2": None, "line3": None},
    "traits": {"line1": None, "line2": None, "line3": None},
    "selected_weapons": ["Weapon1"],
    "selected_skills": ["Heal", "Utility", "Utility", "Utility", "Elite"],
    "infusions": {},
    "attributes": {},
    "rune_id": None,
    "rune_count": 0,
    "suffix_item_id": None,
    "infix_upgrade_id": None,
    "infix_upgrade": None,
    "stat_selections": ["Berserker"],
    "rune_selection_index": 0,
    "weapon_type": 0,
    "is_weapon_swap_locked": False,
}


def _compress_build_data(build_data: Dict[str, Any]) -> str:
    """Compresse les données du build en une chaîne encodée en base64.
    
    Args:
        build_data: Dictionnaire contenant les données du build
        
    Returns:
        Chaîne encodée représentant le build compressé
    """
    # Conversion du dictionnaire en JSON
    json_str = json.dumps(build_data, separators=(",", ":"), ensure_ascii=False)
    
    # Compression des données
    compressed = zlib.compress(json_str.encode("utf-8"), level=9)
    
    # Encodage en base64 avec remplacement des caractères spéciaux
    encoded = base64.b64encode(compressed).decode("ascii")
    encoded = encoded.replace("+", "-").replace("/", "_").replace("=", ".")
    
    return encoded


def _decompress_build_data(encoded_data: str) -> Dict[str, Any]:
    """Décompresse une chaîne encodée en base64 en données de build.
    
    Args:
        encoded_data: Chaîne encodée représentant le build compressé
        
    Returns:
        Dictionnaire contenant les données du build
    """
    # Décodage base64 avec remplacement des caractères spéciaux
    encoded_data = encoded_data.replace("-", "+").replace("_", "/").replace(".", "=")
    
    # Décodage base64
    compressed = base64.b64decode(encoded_data)
    
    # Décompression
    json_str = zlib.decompress(compressed).decode("utf-8")
    
    # Conversion en dictionnaire
    return json.loads(json_str)


def export_to_gw2skills(build: PlayerBuild) -> str:
    """Exporte un build au format gw2skills.net.
    
    Args:
        build: Le build à exporter
        
    Returns:
        URL complète pour visualiser le build sur gw2skills.net
    """
    # Création d'une copie du template
    build_data = build_template.copy()
    
    # Mise à jour des champs de base
    build_data["profession"] = build.profession.lower()
    build_data["specialization"] = build.elite_spec or build.profession
    
    # Configuration des armes
    if build.weapons:
        weapons = [w.lower() for w in build.weapons if w]
        if weapons:
            build_data["weapons"]["mainhand"] = weapons[0] if len(weapons) > 0 else None
            build_data["weapons"]["offhand"] = weapons[1] if len(weapons) > 1 else None
    
    # Configuration des compétences
    if build.utilities:
        utilities = [s.lower() for s in build.utilities if s]
        if utilities:
            build_data["slot_skills"]["heal"] = utilities[0] if len(utilities) > 0 else None
            build_data["slot_skills"]["utility1"] = utilities[1] if len(utilities) > 1 else None
            build_data["slot_skills"]["utility2"] = utilities[2] if len(utilities) > 2 else None
            build_data["slot_skills"]["utility3"] = utilities[3] if len(utilities) > 3 else None
            build_data["slot_skills"]["elite"] = utilities[4] if len(utilities) > 4 else None
    
    # Configuration des spécialisations (simplifiée)
    # Note: Cette partie nécessite une logique plus sophistiquée dans une vraie implémentation
    if build.elite_spec:
        build_data["specializations"]["line3"] = build.elite_spec.lower()
    
    # Compression des données
    encoded_build = _compress_build_data(build_data)
    
    # Construction de l'URL
    return f"https://gw2skills.net/editor/?{encoded_build}"


def export_to_json(build: PlayerBuild) -> Dict[str, Any]:
    """Exporte un build au format JSON structuré.
    
    Args:
        build: Le build à exporter
        
    Returns:
        Dictionnaire contenant les données du build au format structuré
    """
    # Conversion du build en dictionnaire
    build_dict = asdict(build)
    
    # Ajout d'informations supplémentaires
    result = {
        "version": "1.0",
        "build": build_dict,
        "metadata": {
            "exported_from": "GW2 Team Builder",
            "export_timestamp": "2025-07-08T12:00:00Z",  # Devrait être dynamique
            "compatible_with": ["gw2skills.net"]
        }
    }
    
    return result


# Exemple d'utilisation
if __name__ == "__main__":
    # Création d'un exemple de build
    example_build = PlayerBuild(
        profession="Guardian",
        elite_spec="Firebrand",
        role="heal",
        buffs=["quickness", "aegis", "might"],
        playstyles=["zerg"],
        weapons=["Axe", "Shield", "Staff"],
        utilities=["Mantra of Solace", "Mantra of Potence", "Mantra of Liberation", "Mantra of Lore", "Tome of Resolve"],
        description="Heal Firebrand with Quickness"
    )
    
    # Export au format gw2skills.net
    gw2skills_url = export_to_gw2skills(example_build)
    print(f"GW2Skills URL: {gw2skills_url}")
    
    # Export au format JSON
    json_export = export_to_json(example_build)
    import json
    print("\nJSON Export:")
    print(json.dumps(json_export, indent=2, ensure_ascii=False))
