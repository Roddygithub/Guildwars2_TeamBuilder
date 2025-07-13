"""Tests pour le point de terminaison d'analyse d'équipe."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.build import BuildData, ProfessionType, RoleType, TraitLine
from app.scoring.engine import TeamScoreResult

client = TestClient(app)


def test_analyze_team_with_manual_builds():
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
    mock_result = TeamScoreResult(
        total_score=0.9,
        buff_score=0.95,
        role_score=0.85,
        buff_breakdown={"might": {"score": 1.0}, "quickness": {"score": 1.0}},
        role_breakdown={"heal": {"score": 1.0}, "dps": {"score": 0.8}},
        group_coverage={"group1": {"buffs": ["might", "quickness"]}}
    )
    
    with patch('app.api.analyze.analyze_team', return_value=mock_result):
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


def test_analyze_team_with_gw2skilleditor_urls():
    """Teste l'analyse d'une équipe avec des URLs gw2skilleditor."""
    # Mock du résultat du scoring
    mock_result = TeamScoreResult(
        total_score=0.85,
        buff_score=0.9,
        role_score=0.8,
        buff_breakdown={"might": {"score": 1.0}, "alacrity": {"score": 0.8}},
        role_breakdown={"dps": {"score": 0.9}, "support": {"score": 0.7}},
        group_coverage={"group1": {"buffs": ["might", "alacrity"]}}
    )
    
    with patch('app.api.analyze.analyze_team', return_value=mock_result):
        response = client.post(
            "/analyze/team",
            json={
                "builds": [
                    {"type": "url", "data": "https://lucky-noobs.com/builds/view/123"}
                ] * 5,
                "playstyle": "havoc"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["team_score"] == 0.85
    assert data["buff_coverage"] == 0.9
    assert data["role_coverage"] == 0.8


def test_analyze_team_invalid_playstyle():
    """Teste la validation du playstyle."""
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "manual", "data": {"profession": "guardian", "role": "heal"}}] * 5,
            "playstyle": "invalid_playstyle"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_analyze_team_invalid_build_type():
    """Teste la validation du type de build."""
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "invalid_type", "data": {}}] * 5,
            "playstyle": "zerg"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_analyze_team_incorrect_build_count():
    """Teste la validation du nombre de builds."""
    # Moins de 5 builds
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "manual", "data": {"profession": "guardian", "role": "heal"}}] * 3,
            "playstyle": "zerg"
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Plus de 5 builds
    response = client.post(
        "/analyze/team",
        json={
            "builds": [{"type": "manual", "data": {"profession": "guardian", "role": "heal"}}] * 6,
            "playstyle": "zerg"
        }
    )
    assert response.status_code == 422  # Validation error
