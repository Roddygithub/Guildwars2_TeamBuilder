"""Point d'entrée principal de l'application Guild Wars 2 Team Builder.

Ce module initialise l'application FastAPI, configure le logging,
et monte les routeurs API.
"""
import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import setup_logging

# Configuration du logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
setup_logging(level=log_level)

# Configuration des réponses JSON pour forcer l'encodage UTF-8
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def custom_json_encoder(*args, **kwargs):
    """Encodeur JSON personnalisé pour forcer l'encodage UTF-8."""
    kwargs['ensure_ascii'] = False  # Désactive l'échappement des caractères non-ASCII
    return jsonable_encoder(*args, **kwargs)

# Création de l'application FastAPI avec configuration personnalisée
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
    },
    default_response_class=JSONResponse,
    json_encoder=custom_json_encoder
)

# Middleware pour forcer l'encodage UTF-8 dans les réponses
class ForceUTF8Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # S'assurer que le Content-Type inclut l'encodage UTF-8
        content_type = response.headers.get('content-type')
        if content_type and 'application/json' in content_type and 'charset' not in content_type:
            response.headers['content-type'] = f"{content_type}; charset=utf-8"
        return response

# Appliquer le middleware personnalisé
app.add_middleware(ForceUTF8Middleware)

# Configuration CORS détaillée pour améliorer la communication frontend/backend
from app.config import settings

# Configuration CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Spécifier explicitement les origines du frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Méthodes HTTP autorisées
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # Headers autorisés
    expose_headers=["Content-Type", "Authorization"],  # Headers exposés
    max_age=600,  # Durée de cache des préflight requests
)

# Configuration CORS pour la production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        expose_headers=["Content-Type", "Authorization"],
        max_age=600,
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


@app.get("/ping", response_model=None)
def ping():
    """Health-check endpoint."""
    return {"status": "ok"}


# Routers
from app.api.endpoints import router as api_router

# Inclure le routeur principal avec le préfixe /api
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
