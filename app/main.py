"""Point d'entrée principal de l'application Guild Wars 2 Team Builder.

Ce module initialise l'application FastAPI, configure le logging,
et monte les routeurs API.
"""
import os
from fastapi import FastAPI

from app.logging_config import setup_logging

# Configuration du logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
setup_logging(level=log_level)

# Création de l'application FastAPI
app = FastAPI(
    title="GW2 Team Builder",
    version="0.1.0",
    description="Outil d'optimisation de compositions d'équipe pour Guild Wars 2 WvW",
    contact={
        "name": "Équipe GW2 Team Builder",
        "url": "https://github.com/votre-utilisateur/gw2-team-builder"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Import des modèles et initialisation de la base de données
from app.database import init_db


@app.on_event("startup")
async def on_startup() -> None:
    """Initialise les ressources de l'application au démarrage.
    
    Cette fonction est appelée automatiquement par FastAPI au démarrage de l'application.
    Elle initialise la base de données et effectue d'autres tâches d'initialisation.
    """
    # Initialisation de la base de données
    init_db()
    
    # Log de démarrage
    import logging
    logger = logging.getLogger(__name__)
    logger.info("L'application GW2 Team Builder démarre...")
    logger.debug("Niveau de log: %s", log_level)


@app.get("/ping")
def ping() -> dict[str, str]:
    """Health-check endpoint."""
    return {"status": "ok"}


# Routers
from app.api.teams import router as teams_router
from app.api.endpoints.builds import router as builds_router

# Inclure les routeurs
app.include_router(teams_router)
app.include_router(builds_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
