"""Tests unitaires pour le modèle Trait."""

import pytest
from datetime import datetime

from app.models.trait import Trait, TraitTier, TraitType, TraitSlot, TraitCategory
from app.models.profession import Profession
from app.models.specialization import Specialization
from app.models.skill import Skill
from app.core.exceptions import ValidationError

# ===== FIXTURES =====

@pytest.fixture
def sample_profession(db):
    """Crée une profession de test."""
    profession = Profession(
        id='test_profession',
        name='Test Profession',
        icon='test_icon.png',
        icon_big='test_icon_big.png',
        icon_hero='test_icon_hero.png',
        profession='Test',
        weapons={},
        skills=[],
        training=[]
    )
    db.add(profession)
    db.commit()
    return profession

@pytest.fixture
def sample_specialization(db, sample_profession):
    """Crée une spécialisation de test."""
    spec = Specialization(
        id=1,
        name='Test Specialization',
        profession_id=sample_profession.id,
        elite=False,
        minor_traits=[],
        major_traits=[],
        icon='test_spec_icon.png',
        background='test_bg.png',
        profession_icon='test_prof_icon.png',
        profession_icon_big='test_prof_icon_big.png',
        description='Test description'
    )
    db.add(spec)
    db.commit()
    return spec

@pytest.fixture
def sample_skill(db):
    """Crée une compétence de test."""
    skill = Skill(
        id=1000,
        name='Test Skill',
        description='Test skill description',
        icon='test_skill.png',
        chat_link='[&1234]',
        type='Utility',
        slot='Utility',
        categories=['Test']
    )
    db.add(skill)
    db.commit()
    return skill

# ===== TESTS =====

def test_create_trait_minor(db, sample_specialization):
    """Teste la création d'un trait mineur valide."""
    trait = Trait(
        id=100,
        name='Test Minor Trait',
        description='Test description',
        icon='test_icon.png',
        type=TraitType.CORE,
        tier=TraitTier.MINOR,
        specialization_id=sample_specialization.id,
        categories=[TraitCategory.OFFENSE.value, TraitCategory.DEFENSE.value],
        facts=[{"type": "AttributeAdjust", "target": "Power", "value": 100}],
        traited_facts=None
    )
    
    db.add(trait)
    db.commit()
    
    # Vérification des attributs de base
    assert trait.id == 100
    assert trait.name == 'Test Minor Trait'
    assert trait.tier == TraitTier.MINOR
    assert trait.type == TraitType.CORE
    assert trait.specialization_id == sample_specialization.id
    assert trait.profession_id is None
    assert trait.categories == [TraitCategory.OFFENSE.value, TraitCategory.DEFENSE.value]
    assert len(trait.facts) == 1
    assert trait.facts[0]["type"] == "AttributeAdjust"
    
    # Vérification des relations
    assert trait.specialization.id == sample_specialization.id
    assert trait in sample_specialization.traits

def test_create_trait_major(db, sample_specialization):
    """Teste la création d'un trait majeur avec emplacement."""
    trait = Trait(
        id=101,
        name='Test Major Trait',
        type=TraitType.CORE,
        tier=TraitTier.MAJOR,
        slot=TraitSlot.ADEPT,
        specialization_id=sample_specialization.id
    )
    
    db.add(trait)
    db.commit()
    
    assert trait.id == 101
    assert trait.tier == TraitTier.MAJOR
    assert trait.slot == TraitSlot.ADEPT

def test_create_trait_profession(db, sample_profession):
    """Teste la création d'un trait de profession."""
    trait = Trait(
        id=200,
        name='Test Profession Trait',
        type=TraitType.PROFESSION,
        tier=TraitTier.MINOR,
        profession_id=sample_profession.id
    )
    
    db.add(trait)
    db.commit()
    
    assert trait.type == TraitType.PROFESSION
    assert trait.profession_id == sample_profession.id
    assert trait.profession.id == sample_profession.id

def test_trait_validation_errors(db, sample_specialization):
    """Teste les validations du modèle Trait."""
    # Test: Un trait doit avoir soit une spécialisation, soit une profession
    with pytest.raises(ValidationError):
        trait = Trait(
            id=300,
            name='Invalid Trait',
            type=TraitType.CORE,
            tier=TraitTier.MINOR
        )
        db.add(trait)
        db.commit()
    
    # Test: Un trait de profession doit être de niveau MINOR
    with pytest.raises(ValidationError):
        trait = Trait(
            id=301,
            name='Invalid Profession Trait',
            type=TraitType.PROFESSION,
            tier=TraitTier.MAJOR,  # Doit être MINOR
            profession_id='test_profession'
        )
        db.add(trait)
        db.commit()
    
    # Test: Un trait majeur doit avoir un emplacement défini
    with pytest.raises(ValidationError):
        trait = Trait(
            id=302,
            name='Invalid Major Trait',
            type=TraitType.CORE,
            tier=TraitTier.MAJOR,  # Nécessite un slot
            specialization_id=sample_specialization.id
        )
        db.add(trait)
        db.commit()

def test_trait_skills_relationship(db, sample_specialization, sample_skill):
    """Teste la relation many-to-many entre les traits et les compétences."""
    trait = Trait(
        id=400,
        name='Trait with Skills',
        type=TraitType.CORE,
        tier=TraitTier.MAJOR,
        slot=TraitSlot.ADEPT,
        specialization_id=sample_specialization.id
    )
    
    # Ajout de la compétence au trait
    trait.skills.append(sample_skill)
    db.add(trait)
    db.commit()
    
    # Vérification de la relation
    assert len(trait.skills) == 1
    assert trait.skills[0].id == sample_skill.id
    assert sample_skill in trait.skills
    
    # Vérification de la relation inverse
    assert len(sample_skill.traits) == 1
    assert sample_skill.traits[0].id == trait.id

def test_trait_utility_methods(db, sample_specialization):
    """Teste les méthodes utilitaires du modèle Trait."""
    # Création d'un trait avec des faits
    trait = Trait(
        id=500,
        name='Utility Test Trait',
        type=TraitType.ELITE,
        tier=TraitTier.MAJOR,
        slot=TraitSlot.GRANDMASTER,
        specialization_id=sample_specialization.id,
        facts=[
            {"type": "AttributeAdjust", "target": "Power", "value": 120},
            {"type": "Buff", "description": "Gain might on critical hit"},
            {"type": "Damage", "hit_count": 3}
        ]
    )
    
    # Test de get_attribute_modifiers
    modifiers = trait.get_attribute_modifiers()
    assert modifiers == {"Power": 120}
    
    # Test de has_effect
    assert trait.has_effect("Buff") is True
    assert trait.has_effect("Damage") is True
    assert trait.has_effect("Healing") is False
    
    # Test des méthodes de vérification
    assert trait.is_elite() is True
    assert trait.is_major() is True
    assert trait.is_minor() is False

def test_trait_serialization(db, sample_specialization, sample_skill):
    """Teste la sérialisation du modèle Trait."""
    # Création d'un trait avec une compétence
    trait = Trait(
        id=600,
        name='Serialization Test',
        type=TraitType.CORE,
        tier=TraitTier.MAJOR,
        slot=TraitSlot.MASTER,
        specialization_id=sample_specialization.id,
        facts=[{"type": "Test", "value": 1}]
    )
    trait.skills.append(sample_skill)
    db.add(trait)
    db.commit()
    
    # Test de la sérialisation de base
    data = trait.to_dict()
    assert data["id"] == 600
    assert data["name"] == "Serialization Test"
    assert data["type"] == "Core"
    assert data["tier"] == "Major"
    assert data["slot"] == "Master"
    assert data["specialization_id"] == sample_specialization.id
    assert data["skills"] == [sample_skill.id]
    assert "specialization" not in data  # Non inclus par défaut
    
    # Test de la sérialisation avec les relations
    data_with_relations = trait.to_dict(include_related=True)
    assert "specialization" in data_with_relations
    assert data_with_relations["specialization"]["id"] == sample_specialization.id
    assert len(data_with_relations["skills"]) == 1
    assert data_with_relations["skills"][0]["id"] == sample_skill.id
