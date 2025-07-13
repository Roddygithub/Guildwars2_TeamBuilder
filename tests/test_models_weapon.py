"""Tests unitaires pour le modèle Weapon."""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.weapon import (
    Weapon, 
    WeaponType, 
    DamageType, 
    WeaponSlot, 
    WeaponFlag,
    ProfessionWeapon
)
from app.models.item import Rarity, ItemType
from app.models.profession import Profession
from app.models.specialization import Specialization
from app.models.skill import Skill

# ===== FIXTURES =====

@pytest.fixture
def sample_weapon():
    """Crée une arme de test sans la sauvegarder en base."""
    return Weapon(
        id=1001,
        name="Dragon's Rage",
        name_fr="Colère du dragon",
        description="A powerful greatsword that burns enemies.",
        description_fr="Une puissante épée à deux mains qui enflamme les ennemis.",
        icon="https://render.guildwars2.com/file/...",
        type=WeaponType.GREATSWORD,
        damage_type=DamageType.FIRE,
        min_power=1000,
        max_power=1100,
        defense=0,
        attributes={"Power": 179, "Precision": 128},
        flags=[WeaponFlag.MAINHAND.value, WeaponFlag.TWO_HAND.value],
        rarity=Rarity.EXOTIC,
        level=80,
        default_skin=42,
        game_types=["Activity", "Dungeon", "Pve", "Wvw"],
        restrictions=["Norn", "Sylvari", "Human", "Charr", "Asura"],
        details={
            "damage_type": "Physical",
            "min_power": 1000,
            "max_power": 1100,
            "defense": 0,
            "infusion_slots": [],
            "infix_upgrade": {
                "id": 1,
                "attributes": [
                    {"attribute": "Power", "modifier": 179},
                    {"attribute": "Precision", "modifier": 128}
                ]
            },
            "secondary_suffix_item_id": ""
        },
        chat_link="[&AgFpXAAA]"
    )

@pytest.fixture
def sample_profession(db):
    """Crée une profession de test."""
    prof = Profession(
        id="Guardian",
        name="Guardian",
        name_fr="Gardien",
        icon="https://render.guildwars2.com/file/...",
        icon_big="https://render.guildwars2.com/file/...",
        icon_armor="https://render.guildwars2.com/file/...",
        description="A profession that uses virtues to protect allies and smite foes.",
        playable=True,
        specialization_ids=[1, 2, 3],
        training_track_ids=[],
        flags=["CanWieldGreatsword"]
    )
    db.add(prof)
    db.commit()
    return prof

@pytest.fixture
def sample_specialization(db, sample_profession):
    """Crée une spécialisation de test."""
    spec = Specialization(
        id=1,
        name="Dragonhunter",
        profession_id=sample_profession.id,
        elite=True,
        icon="https://render.guildwars2.com/file/..."
    )
    db.add(spec)
    db.commit()
    return spec

@pytest.fixture
def sample_skill(db):
    """Crée une compétence de test."""
    skill = Skill(
        id=1,
        name="Dragon's Maw",
        description="Create a field that damages and pulls in foes.",
        icon="https://render.guildwars2.com/file/...",
        type="Elite",
        slot="Elite",
        weapon_type=WeaponType.GREATSWORD
    )
    db.add(skill)
    db.commit()
    return skill

# ===== TESTS =====

def test_weapon_creation(db, sample_weapon):
    """Teste la création d'une arme avec des valeurs de base."""
    db.add(sample_weapon)
    db.commit()
    
    weapon = db.query(Weapon).get(1001)
    assert weapon is not None
    assert weapon.name == "Dragon's Rage"
    assert weapon.type == WeaponType.GREATSWORD
    assert weapon.damage_type == DamageType.FIRE
    assert weapon.min_power == 1000
    assert weapon.max_power == 1100
    assert weapon.defense == 0
    assert weapon.rarity == "Exotic"
    assert weapon.level == 80
    assert weapon.vendor_value == 261
    assert WeaponFlag.MAINHAND in weapon.flags
    assert WeaponFlag.TWO_HAND in weapon.flags

def test_weapon_required_fields(db):
    """Teste que les champs requis sont obligatoires."""
    # Test sans nom
    with pytest.raises(IntegrityError):
        weapon = Weapon(type=WeaponType.SWORD, damage_type=DamageType.PHYSICAL)
        db.add(weapon)
        db.commit()
    db.rollback()
    
    # Test sans type
    with pytest.raises(IntegrityError):
        weapon = Weapon(name="Test Weapon", damage_type=DamageType.PHYSICAL)
        db.add(weapon)
        db.commit()
    db.rollback()
    
    # Test sans type de dégâts
    with pytest.raises(IntegrityError):
        weapon = Weapon(name="Test Weapon", type=WeaponType.SWORD)
        db.add(weapon)
        db.commit()
    db.rollback()

def test_weapon_enum_validation():
    """Teste la validation des champs Enum."""
    # Test des valeurs d'énumération WeaponType
    assert WeaponType.SWORD.value == "Sword"
    assert WeaponType.GREATSWORD.value == "Greatsword"
    assert WeaponType.STAFF.value == "Staff"
    
    # Test des valeurs d'énumération DamageType
    assert DamageType.PHYSICAL.value == "Physical"
    assert DamageType.FIRE.value == "Fire"
    assert DamageType.ICE.value == "Ice"
    
    # Test des valeurs d'énumération WeaponSlot
    assert WeaponSlot.WEAPON_A1.value == "WeaponA1"
    assert WeaponSlot.WEAPON_A2.value == "WeaponA2"
    
    # Test des valeurs d'énumération WeaponFlag
    assert WeaponFlag.MAINHAND.value == "Mainhand"
    assert WeaponFlag.OFFHAND.value == "Offhand"
    assert WeaponFlag.TWO_HAND.value == "TwoHand"

def test_weapon_profession_relationship(db, sample_weapon, sample_profession, sample_specialization):
    """Teste la relation entre les armes et les professions."""
    # Créer un type d'arme pour la profession
    from app.models.profession import ProfessionWeaponType
    weapon_type = ProfessionWeaponType(
        profession_id=sample_profession.id,
        weapon_type=WeaponType.GREATSWORD,
        name="Greatsword",
        damage_type=DamageType.PHYSICAL
    )
    
    # Créer une entrée dans la table d'association
    prof_weapon = ProfessionWeapon(
        profession_id=sample_profession.id,
        weapon_id=sample_weapon.id,
        weapon_type=weapon_type,
        slot=WeaponSlot.WEAPON_A1,
        specialization_id=sample_specialization.id
    )
    
    # Ajouter les objets à la session et valider
    db.add_all([sample_weapon, weapon_type, prof_weapon])
    db.commit()
    
    # Rafraîchir les objets depuis la base de données
    db.refresh(sample_weapon)
    db.refresh(prof_weapon)
    
    # Vérifier que la relation fonctionne dans les deux sens
    weapon = db.query(Weapon).get(sample_weapon.id)
    assert weapon is not None
    assert len(weapon.profession_weapons) == 1
    
    # Vérifier les propriétés de la relation
    prof_weapon = weapon.profession_weapons[0]
    assert prof_weapon.profession_id == sample_profession.id
    assert prof_weapon.slot == WeaponSlot.WEAPON_A1
    assert prof_weapon.specialization_id == sample_specialization.id
    assert prof_weapon.weapon_type_id == weapon_type.id
    
    # Vérifier la relation avec le type d'arme
    assert prof_weapon.weapon_type is not None
    assert prof_weapon.weapon_type.weapon_type == WeaponType.GREATSWORD
    
    # Vérifier la relation inverse (profession -> armes)
    profession = db.query(Profession).get(sample_profession.id)
    assert profession is not None
    assert any(pw.weapon_id == sample_weapon.id for pw in profession.available_weapons)

def test_weapon_skills_relationship(db, sample_weapon, sample_skill):
    """Teste la relation many-to-many entre les armes et les compétences."""
    # Ajouter la compétence à l'arme
    sample_weapon.skills.append(sample_skill)
    db.add(sample_weapon)
    db.commit()
    
    # Vérifier que la relation fonctionne
    weapon = db.query(Weapon).get(sample_weapon.id)
    assert len(weapon.skills) == 1
    assert weapon.skills[0].id == sample_skill.id
    assert weapon.skills[0].name == "Dragon's Maw"
    
    # Vérifier la relation inverse
    skill = db.query(Skill).get(sample_skill.id)
    assert len(skill.weapons) == 1
    assert skill.weapons[0].id == sample_weapon.id

def test_weapon_default_values(db, sample_item):
    """Teste les valeurs par défaut des champs optionnels."""
    # Créer une arme avec uniquement les champs obligatoires
    weapon = Weapon(
        name="Test Weapon",
        type=WeaponType.SWORD,
        rarity=Rarity.BASIC,
        item_id=sample_item.id
    )
    
    db.add(weapon)
    db.commit()
    db.refresh(weapon)
    
    # Vérifier que l'arme a été créée avec succès
    assert weapon.id is not None
    
    # Vérifier les valeurs par défaut
    assert weapon.description is None
    assert weapon.description_fr is None
    assert weapon.icon is None
    assert weapon.damage_type is None
    assert weapon.min_power is None
    assert weapon.max_power is None
    assert weapon.defense is None
    assert weapon.attributes is None
    assert weapon.infusion_slots is None
    assert weapon.infusion_upgrade_flags is None
    assert weapon.suffix_item_id is None
    assert weapon.secondary_suffix_item_id is None
    assert weapon.stat_choices is None
    assert weapon.game_types is None
    assert weapon.flags is None
    assert weapon.restrictions is None
    assert weapon.level == 0  # Valeur par défaut
    assert weapon.default_skin is None
    assert weapon.details is None
    assert weapon.chat_link is None
    assert weapon.chat_link is None
