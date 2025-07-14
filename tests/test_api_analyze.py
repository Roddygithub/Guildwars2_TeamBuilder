"""Tests pour le point de terminaison d'analyse d'équipe."""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.models.build import BuildData, ProfessionType, RoleType, TraitLine
from app.scoring.engine import TeamScoreResult
from app.services.gw2skilleditor_importer import TeamAnalysisResult

client = TestClient(app)


@pytest.mark.asyncio
async def test_analyze_team_with_manual_builds():
    """Teste l'analyse d'une équipe avec des builds manuels."""
    # Données de test
    build_data = {
        "name": "Heal Firebrand",
        "profession": "guardian",
        "role": "heal",
        "specializations": [
            {"id": 46, "name": "Zeal", "traits": [909, 914, 909]},
            {"id": 27, "name": "Honor", "traits": [915, 908, 894]},
            {"id": 62, "name": "Firebrand", "traits": [904, 0, 0]}
        ],
        "skills": [62561, 9153, 0, 0, 0],
        "equipment": {"Helm": {"id": 48033, "name": "Harrier's Wreath"}}
    }
    
    # Mock du résultat du scoring
    mock_result = TeamAnalysisResult(
        team_score=0.9,
        buff_coverage=0.95,
        role_coverage=0.85,
        strengths=["Excellente couverture des buffs"],
        improvement_areas=[],
        detailed_breakdown={
            "buff_breakdown": {"might": {"score": 1.0}, "quickness": {"score": 1.0}},
            "role_breakdown": {"heal": {"score": 1.0}, "dps": {"score": 0.8}},
            "group_coverage": {"group1": {"buffs": ["might", "quickness"]}}
        },
        suggested_improvements=[]
    )
    
    # Créer un mock pour la fonction asynchrone
    with patch('app.api.analyze.analyze_team', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_result
        
        # Appeler l'endpoint
        response = client.post(
            "/analyze/team",
            json={
                "builds": [{"type": "manual", "data": build_data}] * 5,
                "playstyle": "zerg"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["team_score"] == 0.9
    assert data["buff_coverage"] == 0.95
    assert data["role_coverage"] == 0.85
    assert "strengths" in data
    assert "improvement_areas" in data
    assert "detailed_breakdown" in data


@pytest.mark.asyncio
async def test_analyze_team_with_gw2skilleditor_urls():
    """Teste l'analyse d'une équipe avec des URLs gw2skilleditor."""
    # Mock du résultat du scoring
    mock_result = TeamAnalysisResult(
        team_score=0.85,
        buff_coverage=0.9,
        role_coverage=0.8,
        strengths=["Bonne couverture des buffs"],
        improvement_areas=[],
        detailed_breakdown={
            "buff_breakdown": {"might": {"score": 0.9}, "alacrity": {"score": 0.9}},
            "role_breakdown": {"dps": {"score": 0.8}, "support": {"score": 0.9}},
            "group_coverage": {"group1": {"buffs": ["might", "alacrity"]}}
        },
        suggested_improvements=[]
    )
    
    # Créer un mock pour la fonction asynchrone
    with patch('app.api.analyze.analyze_team', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_result
        
        # Appeler l'endpoint
        response = client.post(
            "/analyze/team",
            json={
                "builds": [{"type": "url", "data": "https://gw2skilleditor.com/build/12345"} for _ in range(5)],
                "playstyle": "havoc"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["team_score"] == 0.85
    assert data["buff_coverage"] == 0.9
    assert data["role_coverage"] == 0.8


@pytest.mark.asyncio
async def test_analyze_team_invalid_playstyle():
    """Teste la validation du playstyle."""
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "manual", "data": {"profession": "guardian", "role": "dps"}}] * 5,
            "playstyle": "invalid"
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_team_invalid_build_type():
    """Teste la validation du type de build."""
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "invalid", "data": {}}] * 5,
            "playstyle": "zerg"
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_team_incorrect_build_count():
    """Teste la validation du nombre de builds."""
    # Moins de 5 builds
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "manual", "data": {"profession": "guardian"}}] * 4,
            "playstyle": "zerg"
        }
    )
    assert response.status_code == 422
    
    # Plus de 5 builds
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "manual", "data": {"profession": "guardian"}}] * 6,
            "playstyle": "zerg"
        }
    )
    assert response.status_code == 422  # Validation error
