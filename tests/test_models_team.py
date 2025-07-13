"""Tests pour les modèles liés aux équipes."""
import pytest
from pydantic import ValidationError

from app.models.team import (
    Playstyle,
    TeamMember,
    TeamComposition,
    TeamRequest,
    TeamResponse
)


def test_playstyle_enum():
    """Teste les valeurs de l'énumération Playstyle."""
    assert Playstyle.ZERG == "zerg"
    assert Playstyle.HAVOC == "havoc"
    assert Playstyle.ROAMING == "roaming"
    assert Playstyle.GVG == "gvg"
    
    # Test de la conversion depuis une chaîne
    assert Playstyle("zerg") == Playstyle.ZERG
    
    # Test avec une valeur invalide
    with pytest.raises(ValueError):
        Playstyle("invalid")


def test_team_member_creation():
    """Teste la création d'un membre d'équipe."""
    # Test avec les champs obligatoires
    member = TeamMember(role="heal", profession="guardian")
    assert member.role == "heal"
    assert member.profession == "guardian"
    assert member.build_url is None
    
    # Test avec un URL de build
    member_with_url = TeamMember(
        role="dps",
        profession="warrior",
        build_url="https://example.com/build/123"
    )
    assert member_with_url.build_url == "https://example.com/build/123"
    
    # Test avec des données manquantes
    with pytest.raises(ValidationError):
        TeamMember()  # manque role et profession


def test_team_composition_creation():
    """Teste la création d'une composition d'équipe."""
    # Test avec des membres et un score
    members = [
        TeamMember(role="heal", profession="guardian"),
        TeamMember(role="dps", profession="warrior")
    ]
    composition = TeamComposition(
        members=members,
        score=0.85,
        score_breakdown={"heal": 0.9, "dps": 0.8}
    )
    
    assert len(composition.members) == 2
    assert composition.score == 0.85
    assert composition.score_breakdown["heal"] == 0.9
    assert composition.score_breakdown["dps"] == 0.8
    
    # Test avec des valeurs par défaut
    default_composition = TeamComposition(
        members=members,
        score=1.0
    )
    assert default_composition.score_breakdown == {}


def test_team_request_validation():
    """Teste la validation des requêtes d'équipe."""
    # Test avec des valeurs minimales
    request = TeamRequest(playstyle=Playstyle.HAVOC)
    assert request.team_size == 5
    assert request.playstyle == Playstyle.HAVOC
    assert request.allowed_professions is None
    assert request.required_roles is None
    
    # Test avec des valeurs personnalisées
    custom_request = TeamRequest(
        team_size=10,
        playstyle=Playstyle.ZERG,
        allowed_professions=["guardian", "warrior", "ranger"],
        required_roles={"heal": 2, "dps": 8}
    )
    assert custom_request.team_size == 10
    assert custom_request.playstyle == Playstyle.ZERG
    assert len(custom_request.allowed_professions) == 3
    assert custom_request.required_roles["heal"] == 2
    
    # Test avec une taille d'équipe invalide
    with pytest.raises(ValidationError):
        TeamRequest(playstyle=Playstyle.HAVOC, team_size=0)
    
    with pytest.raises(ValidationError):
        TeamRequest(playstyle=Playstyle.HAVOC, team_size=51)


def test_team_response_creation():
    """Teste la création d'une réponse d'équipe."""
    # Créer une requête de test
    team_request = TeamRequest(playstyle=Playstyle.HAVOC)
    
    # Créer une composition de test
    members = [TeamMember(role="dps", profession="warrior") for _ in range(5)]
    composition = TeamComposition(members=members, score=0.9)
    
    # Créer une réponse
    response = TeamResponse(
        teams=[composition, composition],
        request=team_request,
        metadata={"version": "1.0"}
    )
    
    assert len(response.teams) == 2
    assert response.request.playstyle == Playstyle.HAVOC
    assert response.metadata["version"] == "1.0"
    
    # Test avec des valeurs par défaut
    default_response = TeamResponse(
        teams=[composition],
        request=team_request
    )
    assert default_response.metadata == {}


def test_team_composition_with_optional_fields():
    """Teste la création d'une composition avec des champs optionnels manquants."""
    # Test avec un score_breakdown vide
    members = [TeamMember(role="dps", profession="warrior")]
    composition = TeamComposition(members=members, score=1.0, score_breakdown={})
    assert composition.score_breakdown == {}
    
    # Test sans score_breakdown
    composition = TeamComposition(members=members, score=1.0)
    assert composition.score_breakdown == {}


def test_team_member_with_optional_fields():
    """Teste la création d'un membre avec des champs optionnels manquants."""
    # Test sans build_url
    member = TeamMember(role="dps", profession="warrior")
    assert member.build_url is None
    
    # Test avec build_url vide (devrait être None)
    member = TeamMember(role="dps", profession="warrior", build_url=None)
    assert member.build_url is None


def test_team_request_with_optional_fields():
    """Teste la création d'une requête avec des champs optionnels."""
    # Test avec allowed_professions vide
    request = TeamRequest(
        playstyle=Playstyle.HAVOC,
        allowed_professions=[],
        required_roles={}
    )
    assert request.allowed_professions == []
    assert request.required_roles == {}
    
    # Test avec required_roles None
    request = TeamRequest(
        playstyle=Playstyle.HAVOC,
        required_roles=None
    )
    assert request.required_roles is None
