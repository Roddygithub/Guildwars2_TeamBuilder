from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from pathlib import Path
import logging
import logging.handlers
import traceback
import os
import sys

# Configuration du logging
def setup_logging():
    """Configure la journalisation avec affichage dans la console et écriture dans un fichier."""
    # Créer le dossier de logs s'il n'existe pas
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Chemin du fichier de log
    log_file = os.path.join(log_dir, 'server.log')
    
    # Configuration du format des logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Niveau de log
    log_level = logging.DEBUG
    
    # Configuration du logger racine
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Supprimer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler pour le fichier
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info("Journalisation configurée avec succès")
    return logger

# Configuration initiale du logging
logger = setup_logging()
logger.info("Démarrage de l'application")

app = FastAPI(title="GW2 Team Builder",
              description="API pour la génération optimisée d'équipes GW2",
              version="0.1.0")

# Configuration CORS - à mettre avant les imports des routeurs pour éviter les problèmes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En développement uniquement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import des routeurs après la configuration CORS
try:
    logger.info("Début de l'importation du routeur API...")
    from app.api.endpoints import router as api_router
    logger.info("Routeur API importé avec succès")
    
    # Afficher les routes avant l'ajout
    logger.info("Routes avant ajout du routeur API:")
    for i, route in enumerate(app.routes):
        logger.info(f"  {i}. {route.path} ({', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'})")
    
    # Inclure le routeur API
    logger.info("Inclusion du routeur API avec le préfixe /api")
    app.include_router(api_router, prefix="/api")
    
    # Afficher les routes après l'ajout
    logger.info("Routes après ajout du routeur API:")
    for i, route in enumerate(app.routes):
        logger.info(f"  {i}. {route.path} ({', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'})")
    
    # Vérifier spécifiquement la présence de la route /api/teams/generate
    team_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/teams/generate' in r.path]
    logger.info(f"Routes de génération d'équipe trouvées: {len(team_routes)}")
    for i, route in enumerate(team_routes):
        logger.info(f"  Route de génération {i+1}: {route.path} ({', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'})")
    
    logger.info("Routeurs API chargés avec succès")
except Exception as e:
    logger.error(f"Erreur lors du chargement des routeurs API: {e}")
    logger.error(traceback.format_exc())
    raise

# Configuration CORS déjà définie plus haut

# Middleware pour logger les requêtes entrantes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Requête reçue: {request.method} {request.url}")
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne du serveur"}
        )

# Servir les fichiers statiques (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "GW2 Team Builder API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
