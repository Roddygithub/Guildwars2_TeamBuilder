"""Modèles Pydantic pour la configuration de l'évaluation des équipes.

Ces modèles définissent comment une équipe GW2 est notée. Ils se concentrent sur la
configuration (poids / pénalités) sans intégrer de logique algorithmique.
Le moteur de score importe ces modèles pour effectuer les calculs.
"""
from __future__ import annotations

from datetime import datetime, UTC
from enum import Enum, auto
from typing import Dict, List, Optional, FrozenSet, ClassVar, Any, Tuple

from pydantic import (
    BaseModel, 
    Field, 
    ConfigDict,
    field_validator,
    model_validator,
    model_serializer,
    confloat,
    ValidationInfo,
    field_serializer
)

# Constantes pour la configuration
DEFAULT_BUFF_WEIGHT = 1.0
DEFAULT_ROLE_WEIGHT = 1.0
DEFAULT_REQUIRED_COUNT = 1
DEFAULT_DUPLICATE_THRESHOLD = 2
DEFAULT_PENALTY_PER_EXTRA = 1.0

# -----------------------------
# Énumérations fondamentales
# -----------------------------

class BuffType(str, Enum):
    """Types de buffs disponibles dans le jeu.
    
    Cette énumération définit tous les types de buffs qui peuvent être pris en compte
    dans l'évaluation d'une équipe. Les buffs sont des effets positifs qui améliorent
    les capacités des joueurs.
    """
    # Note: Ajout de la méthode model_dump pour la compatibilité avec Pydantic v2
    def model_dump(self, **kwargs):
        return self.value
    """Types de buffs disponibles dans le jeu.
    
    Cette énumération définit tous les types de buffs qui peuvent être pris en compte
    dans l'évaluation d'une équipe. Les buffs sont des effets positifs qui améliorent
    les capacités des joueurs.
    """
    # Buffs de base
    MIGHT = "might"
    FURY = "fury"
    QUICKNESS = "quickness"
    ALACRITY = "alacrity"
    SWIFTNESS = "swiftness"
    VIGOR = "vigor"
    PROTECTION = "protection"
    REGENERATION = "regeneration"
    RESOLUTION = "resolution"
    STABILITY = "stability"
    AEGIS = "aegis"
    RESISTANCE = "resistance"
    SUPERSPEED = "superspeed"
    STEALTH = "stealth"
    REVEALED = "revealed"
    RESURRECTION = "resurrection"
    
    # Buffs spécifiques au WvW
    BARRIER = "barrier"
    INVULNERABILITY = "invulnerability"
    UNBLOCKABLE = "unblockable"
    REFLECTION = "reflection"
    STUN_BREAK = "stun_break"
    CONDITION_CLEANSE = "condition_cleanse"
    BOON_RIP = "boon_rip"
    BOON_CORRUPT = "boon_corrupt"
    
    # Contrôle de foule (CC)
    CC = "cc"
    STUN = "stun"
    DAZE = "daze"
    KNOCKBACK = "knockback"
    PULL = "pull"
    LAUNCH = "launch"
    FLOAT = "float"
    SINK = "sink"
    TAUNT = "taunt"
    FEAR = "fear"
    
    # Altérations de statut
    CHILL = "chill"
    CRIPPLE = "cripple"
    IMMOBILIZE = "immobilize"
    WEAKNESS = "weakness"
    VULNERABILITY = "vulnerability"
    BLIND = "blind"
    
    # Dégâts de condition
    POISON = "poison"
    BURNING = "burning"
    BLEEDING = "bleeding"
    TORMENT = "torment"
    CONFUSION = "confusion"
    
    @classmethod
    def values(cls) -> List[str]:
        """Retourne la liste des valeurs d'énumération."""
        return [e.value for e in cls]


class RoleType(str, Enum):
    """Types de rôles disponibles dans le jeu.
    
    Cette énumération définit tous les rôles qui peuvent être attribués à un build
    et qui sont pris en compte dans l'évaluation d'une équipe.
    """
    # Note: Ajout de la méthode model_dump pour la compatibilité avec Pydantic v2
    def model_dump(self, **kwargs):
        return self.value
    """Types de rôles disponibles dans le jeu.
    
    Cette énumération définit tous les rôles qui peuvent être attribués à un build
    et qui sont pris en compte dans l'évaluation d'une équipe.
    """
    # Rôles de base
    DPS = "dps"
    HEAL = "heal"
    QUICKNESS = "quickness"
    ALACRITY = "alacrity"
    TANK = "tank"
    
    # Rôles spécifiques au WvW
    ZERG = "zerg"                # Spécialisation pour les combats en grand groupe
    HAVOC = "havoc"              # Spécialisation pour les petits groupes mobiles
    ROAMER = "roamer"            # Spécialisation pour le jeu en solo/duo
    BOMBER = "bomber"            # Spécialisé dans les dégâts de zone
    SUPPORT = "support"          # Support polyvalent
    BUNKER = "bunker"            # Défense de point
    PUSHER = "pusher"            # Pression offensive
    DISRUPTOR = "disruptor"      # Désorganisation ennemie
    SCOUT = "scout"              # Renseignement et détection
    CAPTAIN = "captain"          # Leader de groupe
    BACKLINE = "backline"        # Dégâts à distance
    FRONTLINE = "frontline"      # Combat rapproché
    MIDLINE = "midline"          # Soutien et contrôle
    PLUS_ONE = "plus_one"        # Renfort rapide
    SOLO_DUELER = "solo_dueler"  # Combat en 1v1
    TEAM_FIGHTER = "team_fighter" # Combat en groupe
    SIDE_NODER = "side_noder"    # Contrôle de points
    ROAMER_PLUS_ONE = "roamer_plus_one"     # Flanc + renfort
    TEAM_FIGHT_SUPPORT = "team_fight_support"  # Soutien en combat d'équipe
    
    @classmethod
    def values(cls) -> List[str]:
        """Retourne la liste des valeurs d'énumération."""
        return [e.value for e in cls]

# Rôles spécifiques aux combats d'équipe (ajoutés comme constantes pour rétrocompatibilité)
TEAM_FIGHT_DPS = "team_fight_dps"                # Dégâts en combat d'équipe
TEAM_FIGHT_CC = "team_fight_cc"                  # Contrôle en combat d'équipe
TEAM_FIGHT_HEAL = "team_fight_heal"              # Soins en combat d'équipe
TEAM_FIGHT_BOONS = "team_fight_boons"            # Buffs en combat d'équipe
TEAM_FIGHT_CLEANSER = "team_fight_cleanser"      # Nettoyage en combat d'équipe
TEAM_FIGHT_RES = "team_fight_res"                # Résurrection en combat d'équipe
TEAM_FIGHT_STEALTH = "team_fight_stealth"        # Furtivité en combat d'équipe
TEAM_FIGHT_BOONRIP = "team_fight_boonrip"        # Vol de buffs en combat d'équipe
TEAM_FIGHT_CORRUPT = "team_fight_corrupt"        # Corruption en combat d'équipe
TEAM_FIGHT_CC_BREAK = "team_fight_cc_break"      # Rupture de contrôle en combat d'équipe
TEAM_FIGHT_STABILITY = "team_fight_stability"    # Stabilité en combat d'équipe

# -----------------------------
# Modèles de configuration principaux
# -----------------------------

class BuffWeight(BaseModel):
    """Poids attribué à un buff spécifique dans le calcul du score.
    
    Attributes:
        weight: Importance de la couverture de ce buff (>= 0).
        description: Description du rôle du buff dans l'équipe.
    """
    weight: float = Field(
        default=DEFAULT_BUFF_WEIGHT,
        ge=0.0,
        description="Importance de la couverture de ce buff (>= 0)."
    )
    description: str = Field(
        default="",
        description="Description du rôle du buff dans l'équipe."
    )
    
    class Config:
        schema_extra = {
            "example": {
                "weight": 1.5,
                "description": "Augmente la vitesse d'attaque de l'équipe"
            }
        }


class RoleWeight(BaseModel):
    """Configuration du poids et des exigences pour un rôle spécifique.
    
    Attributes:
        weight: Importance de ce rôle dans le calcul du score (>= 0).
        required_count: Nombre de joueurs devant remplir ce rôle.
        description: Description du rôle et de ses responsabilités.
    """
    weight: float = Field(
        default=DEFAULT_ROLE_WEIGHT,
        ge=0.0,
        description="Importance de ce rôle dans le calcul du score (>= 0)."
    )
    required_count: int = Field(
        default=DEFAULT_REQUIRED_COUNT,
        ge=1,
        description="Nombre de joueurs devant remplir ce rôle."
    )
    description: str = Field(
        default="",
        description="Description du rôle et de ses responsabilités."
    )
    
    class Config:
        schema_extra = {
            "example": {
                "weight": 2.0,
                "required_count": 1,
                "description": "Soigneur principal de l'équipe"
            }
        }


class DuplicatePenalty(BaseModel):
    """Configuration des pénalités pour les doublons de profession.
    
    Attributes:
        threshold: Nombre maximum autorisé de chaque profession avant pénalité.
        penalty_per_extra: Pénalité appliquée pour chaque occurrence supplémentaire.
        enabled: Active ou désactive la pénalité.
    """
    threshold: int = Field(
        default=DEFAULT_DUPLICATE_THRESHOLD,
        ge=1,
        description="Nombre maximum autorisé de chaque profession avant pénalité."
    )
    penalty_per_extra: float = Field(
        default=DEFAULT_PENALTY_PER_EXTRA,
        ge=0.0,
        description="Pénalité appliquée pour chaque occurrence supplémentaire."
    )
    enabled: bool = Field(
        default=True,
        description="Active ou désactive la pénalité."
    )
    
    class Config:
        schema_extra = {
            "example": {
                "threshold": 2,
                "penalty_per_extra": 1.0,
                "enabled": True
            }
        }


class ScoringConfig(BaseModel):
    """Configuration complète pour le calcul des scores d'équipe.
    
    Cette classe rassemble tous les paramètres nécessaires pour évaluer une équipe
    en fonction de sa composition, de ses buffs et de ses rôles.
    
    Attributes:
        buff_weights: Poids pour chaque buff à prendre en compte.
        role_weights: Configuration des rôles et de leur importance.
        duplicate_penalty: Configuration des pénalités pour les doublons.
        version: Version du schéma de configuration.
    """
    buff_weights: Dict[BuffType, BuffWeight] = Field(
        default_factory=dict,
        description="Poids pour chaque buff à prendre en compte."
    )
    role_weights: Dict[RoleType, RoleWeight] = Field(
        default_factory=dict,
        description="Configuration des rôles et de leur importance."
    )
    duplicate_penalty: Optional[DuplicatePenalty] = Field(
        default_factory=lambda: DuplicatePenalty(),
        description="Configuration des pénalités pour les doublons."
    )
    version: str = Field(
        default="1.0.0",
        description="Version du schéma de configuration."
    )
    
    # Validation avancée
    @field_validator('buff_weights')
    @classmethod
    def validate_buff_weights(cls, v: Dict[BuffType, BuffWeight], info: ValidationInfo) -> Dict[BuffType, BuffWeight]:
        """Valide que les poids des buffs sont valides."""
        if not isinstance(v, dict):
            raise ValueError("buff_weights doit être un dictionnaire")
        
        result = {}
        for buff_type, weight in v.items():
            if not isinstance(buff_type, BuffType):
                try:
                    buff_type = BuffType(buff_type)
                except ValueError:
                    raise ValueError(f"Type de buff invalide: {buff_type}")
            if not isinstance(weight, BuffWeight):
                raise ValueError(f"Le poids pour {buff_type} doit être une instance de BuffWeight")
            if weight.weight < 0:
                raise ValueError(f"Le poids du buff {buff_type} ne peut pas être négatif")
            result[buff_type] = weight
            
        return result
    
    @field_validator('role_weights')
    @classmethod
    def validate_role_weights(cls, v: Dict[RoleType, RoleWeight], info: ValidationInfo) -> Dict[RoleType, RoleWeight]:
        """Valide que les poids des rôles sont valides."""
        if not isinstance(v, dict):
            raise ValueError("role_weights doit être un dictionnaire")
            
        result = {}
        for role_type, weight in v.items():
            if not isinstance(role_type, RoleType):
                try:
                    role_type = RoleType(role_type)
                except ValueError:
                    raise ValueError(f"Type de rôle invalide: {role_type}")
            if not isinstance(weight, RoleWeight):
                raise ValueError(f"Le poids pour {role_type} doit être une instance de RoleWeight")
            if weight.weight < 0:
                raise ValueError(f"Le poids du rôle {role_type} ne peut pas être négatif")
            if weight.required_count < 1:
                raise ValueError(f"Le nombre requis pour le rôle {role_type} doit être >= 1")
            result[role_type] = weight
                
        return result
    
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "buff_weights": {
                    "quickness": {"weight": 2.0, "description": "Augmente la vitesse d'attaque"},
                    "alacrity": {"weight": 2.0, "description": "Réduit les temps de recharge"}
                },
                "role_weights": {
                    "heal": {"weight": 2.0, "required_count": 1, "description": "Soigneur principal"},
                    "dps": {"weight": 1.0, "required_count": 3, "description": "Dégâts"}
                },
                "duplicate_penalty": {
                    "threshold": 2,
                    "penalty_per_extra": 1.0,
                    "enabled": True
                },
                "version": "1.0.0"
            }
        }
    )
    
    @model_serializer
    def serialize_model(self):
        """Sérialise le modèle en utilisant les valeurs des énumérations."""
        result = self.model_dump()
        # Convertir les clés d'énumération en chaînes
        if 'buff_weights' in result and result['buff_weights'] is not None:
            result['buff_weights'] = {k.value: v for k, v in result['buff_weights'].items()}
        if 'role_weights' in result and result['role_weights'] is not None:
            result['role_weights'] = {k.value: v for k, v in result['role_weights'].items()}
        return result


# -----------------------------
# Résultats d'évaluation d'équipe
# -----------------------------

class BuffCoverage(BaseModel):
    """Couverture d'un buff spécifique dans l'équipe.
    
    Attributes:
        buff: Type de buff (issu de l'énumération BuffType).
        covered: Indique si le buff est couvert par l'équipe.
        provided_by: Liste des builds fournissant ce buff.
        weight: Poids du buff dans le calcul du score.
    """
    buff: BuffType = Field(..., description="Type de buff")
    covered: bool = Field(..., description="Indique si le buff est couvert")
    provided_by: List[str] = Field(
        default_factory=list,
        description="Liste des builds fournissant ce buff"
    )
    weight: float = Field(..., description="Poids du buff dans le calcul du score")
    
    class Config:
        json_encoders = {
            BuffType: lambda x: x.value
        }


class RoleCoverage(BaseModel):
    """Couverture d'un rôle spécifique dans l'équipe.
    
    Attributes:
        role: Type de rôle (issu de l'énumération RoleType).
        fulfilled_count: Nombre de joueurs remplissant ce rôle.
        required_count: Nombre de joueurs requis pour ce rôle.
        fulfilled: Indique si le rôle est suffisamment couvert.
        weight: Poids du rôle dans le calcul du score.
    """
    role: RoleType = Field(..., description="Type de rôle")
    fulfilled_count: int = Field(..., description="Nombre de joueurs remplissant ce rôle")
    required_count: int = Field(..., description="Nombre de joueurs requis pour ce rôle")
    fulfilled: bool = Field(..., description="Indique si le rôle est suffisamment couvert")
    weight: float = Field(..., description="Poids du rôle dans le calcul du score")
    
    class Config:
        json_encoders = {
            RoleType: lambda x: x.value
        }


class TeamScoreResult(BaseModel):
    """Résultat complet de l'évaluation d'une équipe.
    
    Cette classe contient le score global de l'équipe ainsi qu'une ventilation
    détaillée des scores par catégorie (buffs, rôles, pénalités).
    
    Attributes:
        total_score: Score global de l'équipe (0.0 à 1.0).
        buff_score: Score de couverture des buffs (0.0 à 1.0).
        role_score: Score de couverture des rôles (0.0 à 1.0).
        duplicate_penalty: Pénalité pour les doublons (0.0 à 1.0).
        buff_breakdown: Détail des scores par buff.
        role_breakdown: Détail des scores par rôle.
        buff_coverage: État de couverture de chaque buff.
        role_coverage: État de couverture de chaque rôle.
        timestamp: Horodatage de l'évaluation.
    """
    total_score: float = Field(..., ge=0.0, le=1.0, description="Score global de l'équipe (0.0 à 1.0)")
    buff_score: float = Field(..., ge=0.0, le=1.0, description="Score de couverture des buffs (0.0 à 1.0)")
    role_score: float = Field(..., ge=0.0, le=1.0, description="Score de couverture des rôles (0.0 à 1.0)")
    duplicate_penalty: float = Field(..., ge=0.0, description="Pénalité pour les doublons (0.0 à 1.0)")
    
    buff_breakdown: Dict[BuffType, float] = Field(
        default_factory=dict,
        description="Détail des scores par buff"
    )
    
    role_breakdown: Dict[RoleType, float] = Field(
        default_factory=dict,
        description="Détail des scores par rôle"
    )
    
    buff_coverage: List[BuffCoverage] = Field(
        default_factory=list,
        description="État de couverture de chaque buff"
    )
    
    role_coverage: List[RoleCoverage] = Field(
        default_factory=list,
        description="État de couverture de chaque rôle"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Horodatage de l'évaluation au format ISO 8601"
    )
    
    class Config:
        json_encoders = {
            BuffType: lambda x: x.value,
            RoleType: lambda x: x.value
        }
        schema_extra = {
            "example": {
                "total_score": 0.85,
                "buff_score": 0.9,
                "role_score": 0.95,
                "duplicate_penalty": 0.1,
                "buff_breakdown": {"quickness": 1.0, "alacrity": 0.8},
                "role_breakdown": {"heal": 1.0, "dps": 0.9},
                "buff_coverage": [
                    {"buff": "quickness", "covered": True, "weight": 2.0, "provided_by": ["Firebrand"]}
                ],
                "role_coverage": [
                    {"role": "heal", "fulfilled_count": 1, "required_count": 1, "fulfilled": True, "weight": 2.0}
                ],
                "timestamp": "2023-10-26T14:30:00Z"
            }
        }
