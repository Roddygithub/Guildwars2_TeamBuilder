"""Integration tests for /teams/suggest endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_sampling_endpoint_ok():
    payload = {
        "team_size": 5,
        "algorithm": "sampling",
        "samples": 100,
        "top_n": 3,
        "playstyle": "raid_guild",
        "allowed_professions": ["Guardian", "Mesmer", "Warrior", "Revenant"],
    }
    resp = client.post("/teams/suggest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "teams" in data
    assert len(data["teams"]) <= 3


def test_genetic_endpoint_ok():
    payload = {
        "team_size": 5,
        "algorithm": "genetic",
        "generations": 10,
        "population": 50,
        "top_n": 2,
        "playstyle": "raid_guild",
        "allowed_professions": ["Guardian", "Mesmer", "Warrior", "Revenant"],
    }
    resp = client.post("/teams/suggest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "teams" in data
    assert len(data["teams"]) <= 2
