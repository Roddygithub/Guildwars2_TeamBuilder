"""Tests pour le modèle BuildData."""
import pytest
from pydantic import ValidationError

from app.models.build import BuildData, ProfessionType, RoleType, TraitLine, EquipmentItem


def test_build_data_creation():
    """Teste la création d'un build valide."""
    build = BuildData(
        name="Heal Firebrand",
        profession=ProfessionType.GUARDIAN,
        role=RoleType.HEAL,
        specializations=[
            TraitLine(id=46, name="Zeal", traits=[909, 914, 909]),
            TraitLine(id=27, name="Honor", traits=[915, 908, 894]),
            TraitLine(id=62, name="Firebrand", traits=[904, 0, 0])
        ],
        skills=[62561, 9153, 0, 0, 0],
        equipment={
            "Helm": {"id": 48033, "name": "Harrier's Wreath of the Diviner", "infusions": []}
        }
    )
    
    assert build.name == "Heal Firebrand"
    assert build.profession == ProfessionType.GUARDIAN
    assert build.role == RoleType.HEAL
    assert len(build.specializations) == 3
    assert len(build.skills) == 5
    assert "Helm" in build.equipment


def test_build_data_validation():
    """Teste la validation des données du build."""
    # Test avec des données manquantes
    with pytest.raises(ValidationError):
        BuildData()
    
    # Test avec un nombre incorrect de spécialisations
    with pytest.raises(ValidationError):
        BuildData(
            name="Invalid Build",
            profession="guardian",
            role="heal",
            specializations=[],
            skills=[0, 0, 0, 0, 0],
            equipment={}
        )
    
    # Test avec un nombre incorrect de compétences
    with pytest.raises(ValidationError):
        BuildData(
            name="Invalid Build",
            profession="guardian",
            role="heal",
            specializations=[
                {"id": 1, "name": "Test", "traits": [0, 0, 0]}
            ] * 3,
            skills=[0, 0, 0],  # Doit avoir 5 compétences
            equipment={}
        )


def test_equipment_item_validation():
    """Teste la validation des objets d'équipement."""
    # Test avec des données valides
    item = EquipmentItem(id=123, name="Test Item")
    assert item.id == 123
    assert item.name == "Test Item"
    assert item.infusions == []
    assert item.upgrades == []
    
    # Test avec des infusions
    item = EquipmentItem(
        id=123,
        name="Test Item",
        infusions=[1, 2, 3],
        upgrades=[4, 5]
    )
    assert item.infusions == [1, 2, 3]
    assert item.upgrades == [4, 5]


def test_trait_line_validation():
    """Teste la validation des lignes de traits."""
    # Test avec des données valides
    trait_line = TraitLine(id=1, name="Test", traits=[1, 2, 3])
    assert trait_line.id == 1
    assert trait_line.name == "Test"
    assert trait_line.traits == [1, 2, 3]
    
    # Le modèle n'impose pas de contrainte sur le nombre de traits
    # Test avec moins de 3 traits
    trait_line = TraitLine(id=1, name="Test", traits=[1, 2])
    assert len(trait_line.traits) == 2
    
    # Test avec plus de 3 traits
    trait_line = TraitLine(id=1, name="Test", traits=[1, 2, 3, 4])
    assert len(trait_line.traits) == 4


def test_profession_type_validation():
    """Teste la validation des types de profession."""
    # Test avec une profession valide
    assert ProfessionType("guardian") == ProfessionType.GUARDIAN
    
    # Test avec une profession invalide
    with pytest.raises(ValueError):
        ProfessionType("invalid_profession")


def test_role_type_validation():
    """Teste la validation des types de rôle."""
    # Test avec un rôle valide
    assert RoleType("heal") == RoleType.HEAL
    
    # Test avec un rôle invalide
    with pytest.raises(ValueError):
        RoleType("invalid_role")
