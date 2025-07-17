"""
Package contenant les schémas Pydantic pour les réponses de l'API.

Ce package définit les modèles de réponse utilisés par les endpoints de l'API
pour assurer une validation et une documentation cohérente des données renvoyées.
"""

from .build import PlayerBuildResponse, player_build_to_response

__all__ = [
    'PlayerBuildResponse',
    'player_build_to_response',
]
