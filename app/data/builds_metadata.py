"""Métadonnées des builds pour Guild Wars 2 WvW.

Ce fichier contient les configurations de builds pour chaque profession,
spécialement optimisées pour le Monde contre Monde (WvW).

Structure d'un build :
  - name: Nom du build (affiché dans l'UI)
  - playstyles: Styles de jeu supportés (zerg, havoc, roaming, etc.)
  - buffs: Ensemble des buffs fournis par le build
  - roles: Rôles remplis par le build
  - elite_spec: Spécialisation d'élite (optionnel)
  - description: Description du rôle et du gameplay (optionnel)
  - weapons: Armes recommandées (optionnel)
  - utilities: Compétences utilitaires recommandées (optionnel)
"""
from __future__ import annotations

from typing import Dict, List, Set

Build = Dict[str, object]
_PROFESSION_BUILDS: Dict[str, List[Build]] = {
    "Guardian": [
        # Firebrand Support (Zerg)
        {
            "name": "Firebrand Heal Quickness (Zerg)",
            "playstyles": ["zerg", "havoc"],
            "buffs": {"might", "quickness", "stability", "aegis", "protection", "resolution", "regeneration", "resistance"},
            "roles": {"heal", "quickness", "support", "frontline", "team_fight_support", "team_fight_boons", "team_fight_cleanser"},
            "elite_spec": "Firebrand",
            "description": "Support de soins et buffs pour zerg, fournit stabilité et soins constants",
            "weapons": ["Mace/Shield", "Staff"],
            "utilities": ["Mantra of Potence", "Mantra of Solace", "Mantra of Liberation", "\"Feel My Wrath!\""],
        },
        # Firebrand DPS (Zerg/Havoc)
        {
            "name": "Firebrand DPS (Zerg/Havoc)",
            "playstyles": ["zerg", "havoc"],
            "buffs": {"quickness", "fury", "might", "aegis"},
            "roles": {"dps", "quickness", "frontline", "team_fight_dps", "team_fight_boons"},
            "elite_spec": "Firebrand",
            "description": "DPS rapproché avec support de quicness, idéal pour la pression en mêlée",
            "weapons": ["Axe/Shield", "Greatsword"],
        },
        # Dragonhunter Roamer
        {
            "name": "Dragonhunter Roamer",
            "playstyles": ["roaming"],
            "buffs": {"aegis", "protection"},
            "roles": {"dps", "roamer", "solo_dueler", "team_fighter"},
            "elite_spec": "Dragonhunter",
            "description": "DPS mobile avec un bon potentiel de burst, idéal pour le roaming",
            "weapons": ["Greatsword", "Sword/Shield"],
        },
    ],
    "Mesmer": [
        # Chronomancer Support (Zerg)
        {
            "name": "Chronomancer Support (Zerg)",
            "playstyles": ["zerg"],
            "buffs": {"alacrity", "quickness", "stability", "aegis"},
            "roles": {"support", "backline", "team_fight_support", "team_fight_cc", "team_fight_boons"},
            "elite_spec": "Chronomancer",
            "description": "Support de contrôle et buffs pour zerg, excellente manipulation du temps",
            "weapons": ["Sword/Shield", "Staff"],
        },
        # Mirage Roamer
        {
            "name": "Mirage Roamer",
            "playstyles": ["roaming"],
            "buffs": {"vigor", "swiftness"},
            "roles": {"dps", "roamer", "solo_dueler", "disruptor"},
            "elite_spec": "Mirage",
            "description": "DPS mobile avec une excellente survie et mobilité",
            "weapons": ["Axe/Torch", "Staff"],
        },
    ],
    "Warrior": [
        # Spellbreaker (Zerg/Havoc)
        {
            "name": "Spellbreaker (Zerg/Havoc)",
            "playstyles": ["zerg", "havoc"],
            "buffs": {"might", "fury"},
            "roles": {"dps", "frontline", "team_fight_cc", "team_fight_boonrip"},
            "elite_spec": "Spellbreaker",
            "description": "DPS rapproché spécialisé dans le vol de buffs et le contrôle",
            "weapons": ["Greatsword", "Dagger/Shield"],
        },
        # Berserker Roamer
        {
            "name": "Berserker Roamer",
            "playstyles": ["roaming"],
            "buffs": {"might"},
            "roles": {"dps", "roamer", "solo_dueler"},
            "elite_spec": "Berserker",
            "description": "DPS explosif avec un fort potentiel de burst",
            "weapons": ["Greatsword", "Axe/Axe"],
        },
    ],
    "Revenant": [
        # Herald Support (Zerg)
        {
            "name": "Herald Support (Zerg)",
            "playstyles": ["zerg"],
            "buffs": {"fury", "might", "protection", "swiftness", "regeneration"},
            "roles": {"support", "frontline", "team_fight_support", "team_fight_boons"},
            "elite_spec": "Herald",
            "description": "Support offensif avec d'excellents buffs de groupe",
            "weapons": ["Staff", "Sword/Shield"],
        },
        # Vindicator Roamer
        {
            "name": "Vindicator Roamer",
            "playstyles": ["roaming"],
            "buffs": {"swiftness", "vigor"},
            "roles": {"dps", "roamer", "solo_dueler"},
            "elite_spec": "Vindicator",
            "description": "DPS mobile avec une excellente mobilité et survie",
            "weapons": ["Greatsword", "Sword/Sword"],
        },
    ],
    "Engineer": [
        # Scrapper Support (Zerg)
        {
            "name": "Scrapper Support (Zerg)",
            "playstyles": ["zerg"],
            "buffs": {"quickness", "superspeed", "barrier"},
            "roles": {"support", "frontline", "team_fight_support", "team_fight_cleanser"},
            "elite_spec": "Scrapper",
            "description": "Support de zone avec soins et nettoyage de conditions",
            "weapons": ["Hammer", "Pistol/Shield"],
        },
        # Holosmith Roamer
        {
            "name": "Holosmith Roamer",
            "playstyles": ["roaming"],
            "buffs": {"swiftness"},
            "roles": {"dps", "roamer", "solo_dueler"},
            "elite_spec": "Holosmith",
            "description": "DPS à distance/rapproché avec un bon potentiel de burst",
            "weapons": ["Rifle", "Pistol/Shield"],
        },
    ],
    "Ranger": [
        # Druid Support (Zerg)
        {
            "name": "Druid Support (Zerg)",
            "playstyles": ["zerg"],
            "buffs": {"regeneration", "protection", "vigor"},
            "roles": {"heal", "support", "backline", "team_fight_heal"},
            "elite_spec": "Druid",
            "description": "Soigneur à distance avec un bon potentiel de soins de zone",
            "weapons": ["Staff", "Longbow"],
        },
        # Soulbeast Roamer
        {
            "name": "Soulbeast Roamer",
            "playstyles": ["roaming"],
            "buffs": {"fury", "might"},
            "roles": {"dps", "roamer", "solo_dueler"},
            "elite_spec": "Soulbeast",
            "description": "DPS à distance/rapproché avec un bon potentiel de burst",
            "weapons": ["Greatsword", "Longbow"],
        },
    ],
    "Thief": [
        # Deadeye Roamer
        {
            "name": "Deadeye Roamer",
            "playstyles": ["roaming"],
            "buffs": {"stealth"},
            "roles": {"dps", "roamer", "solo_dueler", "disruptor"},
            "elite_spec": "Deadeye",
            "description": "DPS furtif avec un fort potentiel de burst",
            "weapons": ["Rifle", "Dagger/Pistol"],
        },
    ],
    "Elementalist": [
        # Tempest Support (Zerg)
        {
            "name": "Tempest Support (Zerg)",
            "playstyles": ["zerg"],
            "buffs": {"might", "fury", "swiftness", "protection"},
            "roles": {"heal", "support", "backline", "team_fight_heal"},
            "elite_spec": "Tempest",
            "description": "Soigneur de zone avec d'excellents soins et buffs",
            "weapons": ["Staff", "Warhorn"],
        },
        # Weaver Roamer
        {
            "name": "Weaver Roamer",
            "playstyles": ["roaming"],
            "buffs": {"might"},
            "roles": {"dps", "roamer", "solo_dueler"},
            "elite_spec": "Weaver",
            "description": "DPS polyvalent avec une grande variété de compétences",
            "weapons": ["Sword/Dagger", "Staff"],
        },
    ],
    "Necromancer": [
        # Scourge (Zerg)
        {
            "name": "Scourge (Zerg)",
            "playstyles": ["zerg"],
            "buffs": {"barrier"},
            "roles": {"dps", "backline", "team_fight_dps", "team_fight_cc", "team_fight_boon_corrupt"},
            "elite_spec": "Scourge",
            "description": "DPS de zone avec barrière et corruption de buffs",
            "weapons": ["Staff", "Scepter/Torch"],
        },
        # Reaper Roamer
        {
            "name": "Reaper Roamer",
            "playstyles": ["roaming"],
            "buffs": set(),
            "roles": {"dps", "roamer", "solo_dueler"},
            "elite_spec": "Reaper",
            "description": "DPS rapproché avec une excellente survie",
            "weapons": ["Greatsword", "Axe/Warhorn"],
        },
    ],
}


def get_builds(profession: str) -> List[Build]:
    return _PROFESSION_BUILDS.get(profession, [])
