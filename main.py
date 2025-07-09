from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from pathlib import Path

# Import des routeurs
from app.api.endpoints import teams

app = FastAPI(title="GW2 Team Builder",
              description="API pour la génération optimisée d'équipes GW2",
              version="0.1.0")

# Inclure les routeurs
app.include_router(teams.router)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
