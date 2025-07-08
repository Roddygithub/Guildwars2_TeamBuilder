"""Guild Wars 2 WvW Team Builder - Outil d'optimisation de compositions d'équipe.

Ce package fournit des fonctionnalités pour optimiser les compositions d'équipe pour le mode
Monde contre Monde (WvW) de Guild Wars 2. Il inclut des algorithmes de scoring avancés,
des optimiseurs génétiques et une API pour interagir avec les données du jeu.

Exemple d'utilisation:
    >>> from app import get_logger, optimize_team
    >>> from app.scoring.schema import ScoringConfig
    >>> 
    >>> # Configuration du logging
    >>> logger = get_logger(__name__)
    >>> 
    >>> # Configuration du scoring
    >>> config = ScoringConfig(
    ...     buff_weights={"quickness": 2.0, "alacrity": 2.0},
    ...     role_weights={"heal": 2.0, "dps": 1.0}
    ... )
    >>> 
    >>> # Optimisation d'une équipe
    >>> result = optimize_team(team_size=5, config=config)
    >>> print(f"Meilleure composition trouvée avec un score de {result['score']:.2f}")
"""

# Import des éléments principaux pour une utilisation simplifiée
from .logging_config import get_logger, setup_logging
from .optimizer import optimize_team, BaseTeamOptimizer
from .scoring import score_team, PlayerBuild, ScoringConfig

# Configuration initiale du logging
setup_logging()

# Version de l'application
__version__ = "0.1.0"
__author__ = "Votre Nom <votre.email@example.com>"
__license__ = "MIT"

# Définition de l'API publique
__all__ = [
    # Fonctions principales
    'optimize_team',
    'score_team',
    'get_logger',
    'setup_logging',
    
    # Classes principales
    'BaseTeamOptimizer',
    'PlayerBuild',
    'ScoringConfig',
    
    # Constantes
    '__version__',
    '__author__',
    '__license__',
]

# Configuration initiale
if __name__ == "__main__":
    # Configuration avancée du logging pour l'exécution directe
    setup_logging(
        level='DEBUG',
        log_dir='logs',
        log_file='app.log',
        log_to_console=True,
        log_to_file=True,
        enable_colors=True,
        log_level_overrides={
            'app.database': 'INFO',
            'app.api': 'INFO',
            'uvicorn': 'WARNING',
            'uvicorn.error': 'WARNING',
            'uvicorn.access': 'WARNING',
            'fastapi': 'WARNING',
            'sqlalchemy.engine': 'WARNING'
        }
    )
    
    logger = get_logger(__name__)
    logger.info("Guild Wars 2 WvW Team Builder initialisé")
