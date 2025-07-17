from fastapi import FastAPI
import uvicorn
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GW2 Team Builder Test",
              description="Version de test de l'API",
              version="0.1.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Démarrage de l'application...")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "GW2 Team Builder Test"}

if __name__ == "__main__":
    logger.info("Démarrage du serveur...")
    uvicorn.run(
        "main_test:app",
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        reload=False
    )
