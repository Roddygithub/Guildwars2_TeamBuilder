from fastapi import FastAPI
import uvicorn
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = FastAPI(
        title="GW2 Team Builder Debug",
        description="Version de débogage de l'API",
        version="0.1.0"
    )
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Démarrage de l'application de débogage...")

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "service": "GW2 Team Builder Debug"}
    
    return app

# Création de l'application au niveau du module
app = create_app()

if __name__ == "__main__":
    try:
        logger.info("Démarrage du serveur de débogage...")
        uvicorn.run(
            "main_debug:app",
            host="127.0.0.1",
            port=8000,
            log_level="debug",
            reload=False
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {e}", exc_info=True)
