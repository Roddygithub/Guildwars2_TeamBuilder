"""Package pour l'intégration avec l'API officielle de Guild Wars 2.

Ce package fournit des outils pour interagir avec l'API GW2, y compris :
- Un client HTTP asynchrone avec mise en cache et gestion des limites de débit
- Des modèles de données pour les réponses de l'API
- Des utilitaires pour la gestion du cache et la configuration
"""

from .client import GW2APIClient, GW2APIError, RateLimitExceeded, APIUnavailable, NotFoundError
from .config import settings, configure_api, GW2APIVersion

__all__ = [
    'GW2APIClient',
    'GW2APIError',
    'RateLimitExceeded',
    'APIUnavailable',
    'NotFoundError',
    'settings',
    'configure_api',
    'GW2APIVersion'
]