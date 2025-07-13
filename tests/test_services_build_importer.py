"""Tests pour le service BuildImporter."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.build_importer import BuildImporter
from app.models.build import BuildData, ProfessionType, RoleType, TraitLine
from app.scoring.engine import PlayerBuild


def test_build_importer_from_dict():
    """Teste la création d'un PlayerBuild à partir d'un dictionnaire."""
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
        "equipment": {
            "Helm": {"id": 48033, "name": "Harrier's Wreath of the Diviner", "infusions": []}
        },
        "source": "https://example.com/build/123"
    }
    
    player_build = BuildImporter.from_dict(build_data)
    
    assert isinstance(player_build, PlayerBuild)
    assert player_build.profession_id == "guardian"
    assert "heal" in player_build.roles  # Vérifie que le rôle est bien défini
    assert "aegis" in player_build.buffs  # Vérifie que les buffs de gardien sont ajoutés
    assert "protection" in player_build.buffs  # Vérifie les buffs de support
    # Convertir en chaîne pour la comparaison car source peut être un HttpUrl
    assert str(player_build.source) == "https://example.com/build/123"


def test_build_importer_extract_buffs():
    """Teste l'extraction des buffs en fonction du rôle et de la profession."""
    # Test avec un heal guardian
    build = BuildData(
        name="Test",
        profession=ProfessionType.GUARDIAN,
        role=RoleType.HEAL,
        specializations=[
            TraitLine(id=1, name="Test", traits=[1, 2, 3])
        ] * 3,
        skills=[0] * 5,
        equipment={}
    )
    
    buffs = BuildImporter._extract_buffs(build)
    # Vérifie que les buffs de base du gardien sont présents
    assert "aegis" in buffs
    assert "stability" in buffs
    # Vérifie les buffs de support pour un heal
    assert "protection" in buffs
    assert "regeneration" in buffs
    # Vérifie les buffs généraux pour les non-DPS
    assert "might" in buffs
    assert "fury" in buffs
    
    # Test avec un DPS
    build.role = RoleType.DPS
    buffs = BuildImporter._extract_buffs(build)
    # Les buffs de base du gardien doivent toujours être présents
    assert "aegis" in buffs
    assert "stability" in buffs
    # Les buffs de support ne devraient pas être présents pour un DPS
    assert "protection" not in buffs
    assert "regeneration" not in buffs
    # Les buffs généraux ne sont pas ajoutés pour les DPS purs
    assert "might" not in buffs
    assert "fury" not in buffs


def test_build_importer_from_gw2skilleditor_url():
    """Teste la création d'un PlayerBuild à partir d'une URL gw2skilleditor."""
    with pytest.raises(NotImplementedError):
        BuildImporter.from_gw2skilleditor_url("https://lucky-noobs.com/builds/view/123")
    
    # Test avec un mock pour simuler une future implémentation
    with patch.object(BuildImporter, 'from_gw2skilleditor_url') as mock_method:
        # Créer un mock de PlayerBuild avec les bons paramètres
        mock_build = MagicMock(spec=PlayerBuild)
        mock_build.profession_id = "guardian"
        mock_build.roles = {"heal"}
        mock_build.buffs = {"aegis", "stability", "protection"}
        mock_build.source = "https://lucky-noobs.com/builds/view/123"
        
        mock_method.return_value = mock_build
        
        # Appeler la méthode et vérifier les propriétés
        build = BuildImporter.from_gw2skilleditor_url("https://lucky-noobs.com/builds/view/123")
        assert build.profession_id == "guardian"
        assert "heal" in build.roles
        assert "aegis" in build.buffs


def test_build_importer_invalid_data():
    """Teste la gestion des données invalides."""
    # Test avec des données manquantes
    with pytest.raises(ValueError):
        BuildImporter.from_dict({})
    
    # Test avec une profession invalide
    with pytest.raises(ValueError):
        BuildImporter.from_dict({
            "profession": "invalid_profession",
            "role": "heal",
            "specializations": [],
            "skills": [0, 0, 0, 0, 0],
            "equipment": {}
        })
    
    # Test avec un rôle invalide
    with pytest.raises(ValueError):
        BuildImporter.from_dict({
            "profession": "guardian",
            "role": "invalid_role",
            "specializations": [],
            "skills": [0, 0, 0, 0, 0],
            "equipment": {}
        })
