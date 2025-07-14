"""
Tests supplémentaires pour les cas limites des endpoints de builds.
"""
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app

# Client de test
client = TestClient(app)

def test_export_invalid_build():
    """Teste l'export d'un build avec des données invalides."""
    # Données de build invalides (manque des champs requis)
    invalid_build = {
        "name": "Build Invalide",
        # Il manque 'profession', 'role', etc.
    }
    
    response = client.post(
        "/api/builds/export",
        json=invalid_build,
        headers={"Content-Type": "application/json"}
    )
    
    # Vérifier que l'API renvoie une erreur 422 (Unprocessable Entity)
    assert response.status_code == 422
    assert "detail" in response.json()

def test_import_missing_file():
    """Teste l'import sans fournir de fichier."""
    response = client.post("/api/builds/import")
    
    # Vérifier que l'API renvoie une erreur 422 (Unprocessable Entity)
    assert response.status_code == 422

def test_import_empty_file():
    """Teste l'import d'un fichier vide."""
    # Créer un fichier vide
    empty_file = Path("empty_file.json")
    empty_file.touch()
    
    try:
        with open(empty_file, "rb") as f:
            files = {"file": ("empty_file.json", f, "application/json")}
            response = client.post("/api/builds/import", files=files)
            
        # Vérifier que l'API renvoie une erreur 400
        assert response.status_code == 400
        assert "Fichier vide" in response.json().get("detail", "")
        
    finally:
        # Nettoyer
        if empty_file.exists():
            empty_file.unlink()

def test_export_build_with_special_chars():
    """Teste l'export d'un build avec des caractères spéciaux."""
    test_build = {
        "name": "Bûild spécial éàçù@#$",
        "profession": "guardian",
        "role": "dps",
        "specializations": [
            {"id": 1, "name": "Test", "traits": [1, 2, 3]}
        ] * 3,
        "skills": [1, 2, 3, 4, 5],
        "equipment": {},
        "description": "Ceci est un test avec des caractères spéciaux: éàçù@#$"
    }
    
    response = client.post(
        "/api/builds/export",
        json=test_build,
        headers={"Content-Type": "application/json"}
    )
    
    # Vérifier que l'export fonctionne avec des caractères spéciaux
    assert response.status_code == 200
    exported_data = response.json()
    assert exported_data["name"] == "Bûild spécial éàçù@#$"

def test_concurrent_imports():
    """Teste l'import simultané de plusieurs builds."""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    def import_build(i):
        test_build = {
            "name": f"Test Build {i}",
            "profession": "guardian",
            "role": "dps",
            "specializations": [
                {"id": i % 10, "name": f"Spec {i}", "traits": [1, 2, 3]}
            ] * 3,
            "skills": [1, 2, 3, 4, 5],
            "equipment": {},
            "description": f"Build de test {i}"
        }
        
        # Créer un fichier temporaire
        test_file = Path(f"test_build_{i}.json")
        test_file.write_text(json.dumps(test_build), encoding="utf-8")
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (f"test_build_{i}.json", f, "application/json")}
                response = client.post("/api/builds/import", files=files)
                return response.status_code == 200
        finally:
            if test_file.exists():
                test_file.unlink()
    
    # Exécuter 5 imports en parallèle
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(import_build, range(5)))
    
    # Vérifier que tous les imports ont réussi
    assert all(results), "Tous les imports n'ont pas réussi"

def test_export_large_build():
    """Teste l'export d'un build avec beaucoup de données."""
    # Créer un build avec beaucoup d'équipement et de compétences
    large_equipment = {
        f"slot_{i}": {
            "id": 1000 + i,
            "name": f"Item {i}",
            "infusions": [2000 + i] * 3,
            "upgrades": [3000 + i] * 4
        } for i in range(20)  # 20 emplacements d'équipement
    }
    
    large_skills = [i for i in range(50)]  # 50 compétences
    
    large_build = {
        "name": "Large Build",
        "profession": "guardian",
        "role": "support",
        "specializations": [
            {"id": i, "name": f"Spec {i}", "traits": [i*10, i*10+1, i*10+2]}
            for i in range(3)  # 3 spécialisations
        ],
        "skills": large_skills,
        "equipment": large_equipment,
        "description": "Build avec beaucoup de données " + "test " * 1000
    }
    
    response = client.post(
        "/api/builds/export",
        json=large_build,
        headers={"Content-Type": "application/json"}
    )
    
    # Vérifier que l'export fonctionne avec beaucoup de données
    assert response.status_code == 200
    exported_data = response.json()
    assert exported_data["name"] == "Large Build"
    assert len(exported_data["skills"]) == 50
    assert len(exported_data["equipment"]) == 20

# Ajouter d'autres tests selon les besoins...
