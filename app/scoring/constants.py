from typing import Dict, List, Set
from enum import Enum

class GameMode(str, Enum):
    ZERG = "zerg"
    HAVOC = "havoc"
    ROAMING = "roaming"

class Role(str, Enum):
    HEALER = "Healer"
    QUICKNESS = "Quickness"
    ALACRITY = "Alacrity"
    DPS = "DPS"
    SUPPORT = "Support"
    BRUISER = "Bruiser"

class Profession(str, Enum):
    GUARDIAN = "Guardian"
    REVENANT = "Revenant"
    ENGINEER = "Engineer"
    RANGER = "Ranger"
    THIEF = "Thief"
    ELEMENTALIST = "Elementalist"
    MESMER = "Mesmer"
    NECROMANCER = "Necromancer"
    WARRIOR = "Warrior"

# Configuration des rôles recommandés par mode de jeu
ROLE_REQUIREMENTS: Dict[GameMode, Dict[Role, int]] = {
    GameMode.ZERG: {
        Role.HEALER: 1,
        Role.QUICKNESS: 1,
        Role.ALACRITY: 1,
        Role.DPS: 7  # Le reste en DPS
    },
    GameMode.HAVOC: {
        Role.HEALER: 1,
        Role.QUICKNESS: 1,
        Role.DPS: 3  # Le reste en DPS
    },
    GameMode.ROAMING: {
        Role.BRUISER: 2,
        Role.SUPPORT: 1,
        Role.DPS: 2
    }
}

# Mapping des rôles possibles par profession
PROFESSION_ROLES: Dict[Profession, List[Role]] = {
    Profession.GUARDIAN: [Role.HEALER, Role.QUICKNESS, Role.SUPPORT, Role.DPS],
    Profession.REVENANT: [Role.ALACRITY, Role.QUICKNESS, Role.DPS],
    Profession.ENGINEER: [Role.ALACRITY, Role.HEALER, Role.DPS],
    Profession.RANGER: [Role.HEALER, Role.DPS],
    Profession.THIEF: [Role.DPS, Role.BRUISER],
    Profession.ELEMENTALIST: [Role.HEALER, Role.DPS],
    Profession.MESMER: [Role.ALACRITY, Role.QUICKNESS, Role.DPS],
    Profession.NECROMANCER: [Role.HEALER, Role.DPS, Role.BRUISER],
    Profession.WARRIOR: [Role.QUICKNESS, Role.DPS, Role.BRUISER]
}

# Bonus de synergie entre rôles
ROLE_SYNERGY: Dict[Role, Dict[Role, float]] = {
    Role.HEALER: {
        Role.QUICKNESS: 1.2,
        Role.ALACRITY: 1.2,
        Role.DPS: 1.1
    },
    Role.QUICKNESS: {
        Role.ALACRITY: 1.3,
        Role.DPS: 1.2
    },
    Role.ALACRITY: {
        Role.DPS: 1.2
    },
    Role.SUPPORT: {
        Role.BRUISER: 1.3,
        Role.DPS: 1.1
    }
}

# Poids des rôles dans le calcul du score
ROLE_WEIGHTS: Dict[Role, float] = {
    Role.HEALER: 1.5,
    Role.QUICKNESS: 1.4,
    Role.ALACRITY: 1.4,
    Role.SUPPORT: 1.3,
    Role.BRUISER: 1.1,
    Role.DPS: 1.0
}
