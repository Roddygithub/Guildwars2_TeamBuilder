"""Tests unitaires pour le modèle Skill."""

import pytest
from datetime import datetime

from app.models.skill import Skill, SkillType
from app.models.weapon import Weapon, WeaponType
from app.models.profession import Profession
from app.models.specialization import Specialization
from app.models.trait import Trait
from app.core.exceptions import ValidationError

# ===== FIXTURES =====

@pytest.fixture
def sample_profession(db):
    """Crée une profession de test."""
    profession = Profession(
        id='test_profession',
        name='Test Profession',
        icon='test_icon.png',
        profession='Test',
        weapons={},
        skills=[],
        training=[]
    )
    db.add(profession)
    db.commit()
    return profession

@pytest.fixture
def sample_weapon(db):
    """Crée une arme de test."""
    weapon = Weapon(
        id=1,
        name='Test Sword',
        type=WeaponType.SWORD,
        damage_type='Physical',
        min_power=100,
        max_power=200,
        defense=0,
        attributes={}
    )
    db.add(weapon)
    db.commit()
    return weapon

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
        icon='test_spec_icon.png'
    )
    db.add(spec)
    db.commit()
    return spec

@pytest.fixture
def sample_trait(db, sample_specialization):
    """Crée un trait de test."""
    trait = Trait(
        id=1,
        name='Test Trait',
        description='Test description',
        icon='test_icon.png',
        specialization_id=sample_specialization.id,
        tier=1,
        slot=1,
        categories=['Test']
    )
    db.add(trait)
    db.commit()
    return trait

@pytest.fixture
def sample_skill(db, sample_profession, sample_weapon, sample_trait):
    """Crée une compétence de test avec des relations."""
    # Créer d'abord une compétence de base
    skill = Skill(
        id=1,
        name='Test Skill',
        description='A test skill',
        icon='test_skill.png',
        type=SkillType.WEAPON,
        weapon_type=WeaponType.SWORD,
        slot='1',
        professions=[sample_profession.id],
        categories=['Test'],
        cost=5,
        recharge=10,
        facts=[{
            'type': 'Damage',
            'hit_count': 1,
            'dmg_multiplier': 1.0
        }],
        traited_facts=[{
            'type': 'Damage',
            'hit_count': 1,
            'dmg_multiplier': 1.2,
            'requires_trait': sample_trait.id
        }]
    )
    
    # Ajouter les relations many-to-many
    skill.weapons = [sample_weapon]
    skill.traits = [sample_trait]
    
    db.add(skill)
    db.commit()
    return skill

# ===== TESTS =====

def test_create_skill_basic(db, sample_skill):
    """Teste la création d'une compétence de base."""
    # Vérifier que la compétence a été correctement enregistrée
    assert sample_skill.id == 1
    assert sample_skill.name == 'Test Skill'
    assert sample_skill.type == SkillType.WEAPON
    assert sample_skill.weapon_type == WeaponType.SWORD
    assert sample_skill.slot == '1'
    assert sample_skill.cost == 5
    assert sample_skill.recharge == 10
    assert len(sample_skill.facts) == 1
    assert sample_skill.facts[0]['type'] == 'Damage'

def test_skill_relationships(db, sample_skill, sample_weapon, sample_trait, sample_profession):
    """Teste les relations de la compétence."""
    # Vérifier la relation avec les armes
    assert len(sample_skill.weapons) == 1
    assert sample_skill.weapons[0].id == sample_weapon.id
    
    # Vérifier la relation avec les traits
    assert len(sample_skill.traits) == 1
    assert sample_skill.traits[0].id == sample_trait.id
    
    # Vérifier la relation avec la profession
    assert sample_profession.id in sample_skill.professions

def test_skill_utility_methods(db, sample_skill):
    """Teste les méthodes utilitaires du modèle Skill."""
    # Tester get_skill_facts
    facts = sample_skill.get_skill_facts()
    assert len(facts) == 2  # facts + traited_facts
    
    # Tester get_skill_facts_by_type
    damage_facts = sample_skill.get_skill_facts_by_type('Damage')
    assert len(damage_facts) == 2
    
    # Tester get_skill_fact_value
    damage_mult = sample_skill.get_skill_fact_value('Damage', 'dmg_multiplier')
    assert damage_mult == 1.0  # Prend le premier fait de dégâts (base)
    
    # Tester get_coefficients
    coeffs = sample_skill.get_coefficients()
    assert 'damage' in coeffs
    assert 'healing' in coeffs
    assert coeffs['damage'] == 1.0

def test_skill_serialization(db, sample_skill):
    """Teste la sérialisation du modèle Skill."""
    # Test de la sérialisation minimale
    min_data = sample_skill.to_dict(minimal=True)
    assert 'id' in min_data
    assert 'name' in min_data
    assert 'type' in min_data
    assert 'weapons' not in min_data  # Les relations ne sont pas incluses en mode minimal
    
    # Test de la sérialisation complète
    full_data = sample_skill.to_dict()
    assert 'weapons' in full_data
    assert 'traits' in full_data
    assert 'profession' in full_data
    
    # Tester la sérialisation sans les relations
    no_relations = sample_skill.to_dict(include_related=False)
    assert 'weapons' not in no_relations
    assert 'traits' not in no_relations

def test_skill_chain_relationships(db, sample_skill):
    """Teste les relations de chaîne de compétences."""
    # Créer une deuxième compétence dans la chaîne
    next_skill = Skill(
        id=2,
        name='Next Skill',
        type=SkillType.WEAPON,
        slot='2',
        prev_chain=sample_skill.id,
        professions=sample_skill.professions
    )
    db.add(next_skill)
    db.flush()
    
    # Mettre à jour la première compétence pour pointer vers la suivante
    sample_skill.next_chain = next_skill.id
    db.commit()
    
    # Vérifier la relation next_chain
    assert sample_skill.next_chain_rel.id == next_skill.id
    assert next_skill.prev_chain_rel.id == sample_skill.id
    
    # Tester get_skill_chain
    chain = sample_skill.get_skill_chain()
    assert len(chain) == 2
    assert chain[0].id == sample_skill.id
    assert chain[1].id == next_skill.id

def test_skill_validation_errors(db):
    """Teste les validations du modèle Skill."""
    # Tester la validation du type de compétence
    with pytest.raises(ValueError):
        Skill(
            name='Invalid Skill',
            type='INVALID_TYPE',  # Type invalide
            slot='1'
        )
    
    # Tester la validation du type d'arme
    with pytest.raises(ValueError):
        Skill(
            name='Invalid Weapon Skill',
            type=SkillType.WEAPON,
            weapon_type='INVALID_WEAPON',  # Type d'arme invalide
            slot='1'
        )

def test_skill_availability(db, sample_skill, sample_profession):
    """Teste la vérification de disponibilité par profession."""
    # La compétence devrait être disponible pour la profession de test
    assert sample_skill.is_available_for_profession(sample_profession.id) is True
    
    # La compétence ne devrait pas être disponible pour une autre profession
    assert sample_skill.is_available_for_profession('OtherProfession') is False
