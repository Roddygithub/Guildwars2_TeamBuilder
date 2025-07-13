"""
Tests pour les endpoints d'import/export de builds.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from app.main import app
from app.models.build import BuildData, ProfessionType, RoleType, TraitLine

# Configuration des tests
TEST_EXPORT_DIR = "test_exports"
os.makedirs(TEST_EXPORT_DIR, exist_ok=True)

# Client de test
client = TestClient(app)

def test_import_build():
    """Teste l'import d'un build depuis un fichier JSON."""
    # Créer un fichier de test temporaire
    test_build = {
        "name": "Test Build",
        "profession": "guardian",
        "role": "heal",
        "specializations": [
            {"id": 46, "name": "Zeal", "traits": [909, 914, 909]},
            {"id": 27, "name": "Honor", "traits": [915, 908, 894]},
            {"id": 62, "name": "Firebrand", "traits": [904, 0, 0]}
        ],
        "skills": [62561, 9153, 0, 0, 0],
        "equipment": {
            "Helm": {"id": 48033, "name": "Test Helm", "infusions": [], "upgrades": []}
        },
        "description": "Build de test"
    }
    
    # Créer un fichier temporaire
    test_file = Path("test_build.json")
    test_file.write_text(json.dumps(test_build), encoding="utf-8")
    
    try:
        # Tester l'import
        with open(test_file, "rb") as f:
            files = {"file": ("test_build.json", f, "application/json")}
            response = client.post("/api/builds/import", files=files)
            
        # Vérifier la réponse
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "Test Build"
        assert data["profession_id"] == "guardian"
        assert "heal" in data["roles"]
        
    finally:
        # Nettoyer
        if test_file.exists():
            test_file.unlink()

def test_export_build():
    """Teste l'export d'un build."""
    # Ce test utilise l'endpoint d'export direct
    test_build = {
        "name": "Test Export",
        "profession": "guardian",
        "role": "dps",
        "specializations": [
            {"id": 1, "name": "Test", "traits": [1, 2, 3]}
        ] * 3,
        "skills": [1, 2, 3, 4, 5],
        "equipment": {},
        "description": "Build de test pour export"
    }
    
    # Tester l'export
    response = client.post(
        "/api/builds/export",
        json=test_build,
        headers={"Content-Type": "application/json"}
    )
    
    # Vérifier la réponse
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    # Vérifier que le contenu est un JSON valide
    content = response.content.decode()
    exported_data = json.loads(content)
    assert exported_data["name"] == "Test Export"
    assert exported_data["profession"] == "guardian"

def test_get_build_template():
    """Teste la récupération d'un modèle de build vide."""
    response = client.get("/api/builds/template")
    
    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier la structure de base
    assert "name" in data
    assert "profession" in data
    assert "role" in data
    assert len(data["specializations"]) == 3
    assert len(data["skills"]) == 5
    assert isinstance(data["equipment"], dict)

def test_export_nonexistent_build():
    """Teste l'export d'un build qui n'existe pas."""
    # Ce test suppose que l'ID 9999 n'existe pas
    response = client.get("/api/builds/export/9999")
    
    # Vérifier que l'API renvoie une erreur 404
    assert response.status_code == 404

def test_invalid_import_file():
    """Teste l'import avec un fichier invalide."""
    # Créer un fichier invalide
    test_file = Path("invalid_build.txt")
    test_file.write_text("ceci n'est pas du JSON valide", encoding="utf-8")
    
    try:
        # Tester l'import
        with open(test_file, "rb") as f:
            files = {"file": ("invalid_build.txt", f, "text/plain")}
            response = client.post("/api/builds/import", files=files)
            
        # Vérifier que l'API renvoie une erreur 400
        assert response.status_code == 400
        
    finally:
        # Nettoyer
        if test_file.exists():
            test_file.unlink()

# Nettoyage après les tests
def test_cleanup():
    """Nettoie les fichiers de test."""
    if os.path.exists(TEST_EXPORT_DIR):
        for file in Path(TEST_EXPORT_DIR).glob("*"):
            if file.is_file():
                file.unlink()
        os.rmdir(TEST_EXPORT_DIR)
