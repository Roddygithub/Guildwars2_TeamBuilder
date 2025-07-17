"""
Package contenant les endpoints de l'API.

Ce module expose les routeurs FastAPI pour les différentes fonctionnalités de l'API.
"""

from fastapi import APIRouter

# Import des routeurs
from . import teams as teams_endpoint
from . import builds as builds_endpoint

# Création du routeur principal
router = APIRouter()

# Inclusion des sous-routeurs
router.include_router(teams_endpoint.router, prefix="/teams", tags=["teams"])
router.include_router(builds_endpoint.router, prefix="/builds", tags=["builds"])

# Export des routeurs pour une utilisation dans main.py
__all__ = ["router"]
