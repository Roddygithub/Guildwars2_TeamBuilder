"""Script de test minimal pour le serveur FastAPI."""
import socket
import logging
from fastapi import FastAPI, Request
import uvicorn

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/test")
async def test(request: Request):
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Requête reçue de {client_host} sur /test")
    return {
        "message": "Hello, World!",
        "client": client_host,
        "server": socket.gethostname()
    }

if __name__ == "__main__":
    logger.info("Démarrage du serveur Uvicorn...")
    logger.info(f"Adresse: 127.0.0.1, Port: 8001")
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,
            log_level="debug",
            log_config=None,
            access_log=True
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur: {e}", exc_info=True)
        raise
