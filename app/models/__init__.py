"""Package contenant les modèles de données de l'application.

Ce package exporte à la fois les modèles Pydantic pour l'API et les modèles SQLAlchemy.
Les imports sont organisés pour éviter les dépendances circulaires.
"""

# 1. Import de la base en premier
from .base import Base

# 2. Import des énumérations et types de base
from .item import ItemType, Rarity
from .weapon import WeaponType, DamageType, WeaponSlot, WeaponFlag
from .armor import ArmorType, WeightClass, InfusionSlotFlag
from .trinket import TrinketType
from .upgrade_component import UpgradeComponentType, InfusionUpgradeFlag

# 3. Import des modèles principaux (sans relations)
from .profession import Profession
from .specialization import Specialization
from .trait import Trait
from .weapon import Weapon
from .skill import Skill
from .armor import Armor
from .trinket import Trinket
from .upgrade_component import UpgradeComponent, Rune, Sigil, Relic
from .infusion import Infusion, InfusionType
from .item_stats import ItemStats
from .item_stat_mapping import ItemStat
from .item import Item

# 4. Import des modèles de jointure (après que tous les modèles principaux soient définis)
from .profession_weapon import ProfessionWeaponType, ProfessionWeaponSkill
from .profession_armor import ProfessionArmorType
from .profession_trinket import ProfessionTrinketType

# 5. Import des modèles Pydantic pour l'API (s'ils n'ont pas de dépendances circulaires)
from .team import TeamRequest, TeamResponse, TeamComposition, TeamMember, Playstyle

# 6. Configuration des relations entre les modèles
# Note: Ce module doit être importé après tous les autres modèles
from . import relationships  # noqa: F401

__all__ = [
    # Base de données
    'Base',
    
    # Modèles principaux
    'Profession',
    'Specialization',
    'Skill',
    'Trait',
    'Weapon',
    'Armor',
    'Trinket',
    'UpgradeComponent',
    'Rune',
    'Sigil',
    'Relic',
    'Infusion',
    'Item',
    'ItemStats',
    'ItemStat',
    
    # Enums
    'WeaponType',
    'DamageType',
    'WeaponSlot',
    'WeaponFlag',
    'ArmorType',
    'WeightClass',
    'InfusionSlotFlag',
    'TrinketType',
    'UpgradeComponentType',
    'InfusionUpgradeFlag',
    'InfusionType',
    'ItemType',
    'Rarity',
    
    # Tables d'association
    'ProfessionWeapon',
    'ProfessionArmorType',
    'ProfessionTrinketType',
    
    # Modèles Pydantic pour l'API
    'TeamRequest',
    'TeamResponse',
    'TeamComposition',
    'TeamMember',
    'Playstyle'
]
