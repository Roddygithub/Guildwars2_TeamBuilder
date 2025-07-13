"""Package pour le mappage des données entre l'API GW2 et les modèles internes.

Ce package fournit des utilitaires pour convertir les données brutes de l'API GW2
en objets de notre modèle de données interne, et vice versa.
"""

from .gw2_api_mapper import GW2APIMapper

__all__ = [
    'GW2APIMapper',
]
