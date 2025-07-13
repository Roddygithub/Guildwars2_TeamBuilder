"""Tests unitaires pour les modÃ¨les de base de donnÃ©es."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Import des modÃ¨les Ã  tester
from app.models.profession import Profession
from app.models.specialization import Specialization
from app.models.trait import Trait, TraitTier, TraitSlot, TraitType
from app.models.weapon import Weapon, WeaponType, WeaponFlag, DamageType
from app.models.skill import Skill, SkillType
from app.models.item import Item, ItemType, Rarity
from app.models.armor import Armor, WeightClass, ArmorType
from app.models.trinket import Trinket, TrinketType
from app.models.upgrade_component import (
    UpgradeComponent, 
    UpgradeComponentType, 
    InfusionUpgradeFlag
)

# Tests pour le modÃ¨le Profession
def test_create_profession(db):
    """Teste la crÃ©ation d'une profession."""
    # CrÃ©ation d'une profession de test avec uniquement les champs valides
    profession = Profession(
        id="TestProfession",
        name="Test Profession",
        name_fr="Profession de test",
        icon="test_icon.png",
        icon_big="test_icon_big.png",
        description="Description de test",
        playable=True
    )
    
    # Ajout Ã  la base de donnÃ©es
    db.add(profession)
    db.commit()
    
    # VÃ©rification que la profession a bien Ã©tÃ© ajoutÃ©e
    assert profession.id == "TestProfession"
    assert profession.name == "Test Profession"
    assert profession.name_fr == "Profession de test"
    assert profession.icon == "test_icon.png"
    assert profession.icon_big == "test_icon_big.png"
    assert profession.description == "Description de test"
    assert profession.playable is True
    
    # VÃ©rification que la date de crÃ©ation a Ã©tÃ© dÃ©finie
    assert profession.created is not None
    assert isinstance(profession.created, datetime)
    
    # VÃ©rification que la date de mise Ã  jour a Ã©tÃ© dÃ©finie
    assert profession.updated is not None
    assert isinstance(profession.updated, datetime)

# Tests pour le modÃ¨le Specialization
def test_create_specialization(db):
    """Teste la crÃ©ation d'une spÃ©cialisation."""
    # CrÃ©ation d'une profession parente
    profession = Profession(
        id="TestProfession",
        name="Test Profession"
    )
    db.add(profession)
    db.commit()
    
    # CrÃ©ation d'une spÃ©cialisation de test
    specialization = Specialization(
        id=1,
        name="Test Specialization",
        name_fr="SpÃ©cialisation de test",
        profession_id="TestProfession",
        elite=True,
        icon="test_icon.png",
        background="test_background.png",
        minor_traits=[1, 2, 3],
        major_traits=[4, 5, 6, 7, 8, 9],
        weapon_trait=10
    )
    
    # Ajout Ã  la base de donnÃ©es
    db.add(specialization)
    db.commit()
    
    # VÃ©rification que la spÃ©cialisation a bien Ã©tÃ© ajoutÃ©e
    assert specialization.id == 1
    assert specialization.name == "Test Specialization"
    assert specialization.name_fr == "SpÃ©cialisation de test"
    assert specialization.profession_id == "TestProfession"
    assert specialization.elite is True
    assert specialization.icon == "test_icon.png"
    assert specialization.background == "test_background.png"
    assert specialization.minor_traits == [1, 2, 3]
    assert specialization.major_traits == [4, 5, 6, 7, 8, 9]
    assert specialization.weapon_trait == 10
    
    # RafraÃ®chir les objets depuis la base de donnÃ©es
    db.refresh(specialization)
    db.refresh(profession)
    
    # VÃ©rification de la relation avec la profession
    assert specialization.profession_id == profession.id
    assert specialization.profession == profession
    assert specialization in profession.specializations

# Tests pour le modÃ¨le Trait
def test_create_trait(db):
    """Teste la crÃ©ation d'un trait."""
    # CrÃ©ation d'une profession et d'une spÃ©cialisation parentes
    profession = Profession(id="TestProfession", name="Test Profession")
    db.add(profession)
    
    specialization = Specialization(
        id=1,
        name="Test Specialization",
        profession_id="TestProfession"
    )
    db.add(specialization)
    db.commit()
    
    # CrÃ©ation d'un trait de test
    trait = Trait(
        id=1,
        name="Test Trait",
        name_fr="Trait de test",
        description="Test description",
        description_fr="Description de test",
        icon="test_icon.png",
        specialization_id=1,
        type=TraitType.CORE,  # Ajout du champ type obligatoire
        tier=TraitTier.MAJOR,
        slot=TraitSlot.ADEPT,  # Utilisation de l'Ã©numÃ©ration TraitSlot
        facts=[{"type": "AttributeAdjust", "value": 100}],
        traited_facts=[{"type": "Buff", "status": "Might"}],
        categories=["Power", "Condition"]
    )
    
    # Ajout Ã  la base de donnÃ©es
    db.add(trait)
    db.commit()
    
    # VÃ©rification que le trait a bien Ã©tÃ© ajoutÃ©
    assert trait.id == 1
    assert trait.name == "Test Trait"
    assert trait.name_fr == "Trait de test"
    assert trait.description == "Test description"
    assert trait.description_fr == "Description de test"
    assert trait.icon == "test_icon.png"
    assert trait.specialization_id == 1
    assert trait.tier == TraitTier.MAJOR
    assert trait.slot == TraitSlot.ADEPT
    assert trait.facts == [{"type": "AttributeAdjust", "value": 100}]
    assert trait.traited_facts == [{"type": "Buff", "status": "Might"}]
    assert trait.categories == ["Power", "Condition"]
    
    # VÃ©rification de la relation avec la spÃ©cialisation
    assert trait.specialization == specialization
    assert trait in specialization.traits

# Tests pour le modÃ¨le Weapon
def test_create_weapon(db):
    """Teste la crÃ©ation d'une arme."""
    # CrÃ©ation d'un item parent
    item = Item(
        id=1,
        name="Test Weapon Item",
        type=ItemType.WEAPON,
        rarity=Rarity.EXOTIC,  # Utilisation directe de l'énumération
        level=80,
        vendor_value=100,
        flags=["SoulBindOnUse"],
        restrictions=[],
        description="Test weapon item description",
        description_fr="Description de l'arme de test",
        details={
            "game_types": ["Activity", "Dungeon", "Pve", "Wvw"],
            "default_skin": 1000
        }
    )
    db.add(item)
    db.commit()
    
    # CrÃ©ation d'une arme de test
    weapon = Weapon(
        id=1,
        name="Test Weapon",
        name_fr="Arme de test",
        description="Test weapon description",
        description_fr="Description de l'arme de test",
        icon="test_icon.png",
        type=WeaponType.STAFF,
        damage_type=DamageType.FIRE,  # Type de dégâts,
        min_power=100,
        max_power=200,
        defense=0,
        attributes={"Power": 100, "Precision": 50},
        flags=[WeaponFlag.TWO_HAND.value],
        game_types=["Activity", "Dungeon", "Pve", "Wvw"],
        restrictions=[],
        rarity=Rarity.EXOTIC,  # Utilisation directe de l'énumération
        level=80,
        item_id=1
    )
    
    # Ajout Ã  la base de donnÃ©es
    db.add(weapon)
    db.commit()
    
    # VÃ©rification que l'arme a bien Ã©tÃ© ajoutÃ©e
    assert weapon.id == 1
    assert weapon.name == "Test Weapon"
    assert weapon.name_fr == "Arme de test"
    assert weapon.description == "Test weapon description"
    assert weapon.description_fr == "Description de l'arme de test"
    assert weapon.icon == "test_icon.png"
    assert weapon.type == WeaponType.STAFF
    assert weapon.damage_type == DamageType.FIRE
    assert weapon.min_power == 100
    assert weapon.max_power == 200
    assert weapon.defense == 0
    assert weapon.attributes == {"Power": 100, "Precision": 50}
    assert weapon.flags == [WeaponFlag.TWO_HAND.value]
    assert weapon.game_types == ["Activity", "Dungeon", "Pve", "Wvw"]
    assert weapon.restrictions == []
    assert weapon.rarity == Rarity.EXOTIC  # Comparaison directe avec l'objet Enum
    assert weapon.level == 80
    assert weapon.item_id == 1
    
    # VÃ©rification de la relation avec l'item
    assert weapon.item == item
    assert item.weapon == weapon

def test_weapon_required_fields(db):
    """Teste que les champs requis pour une arme sont bien dÃ©finis."""
    # Tentative de crÃ©ation d'une arme sans champs requis
    with pytest.raises(IntegrityError):
        weapon = Weapon()
        db.add(weapon)
        db.commit()
    
    db.rollback()
    
    # CrÃ©ation d'une arme avec uniquement les champs requis
    weapon = Weapon(
        id=1,
        name="Test Weapon",
        type=WeaponType.STAFF,
        damage_type=DamageType.FIRE,  # Type de dégâts,
        min_power=100,
        max_power=200,
        rarity=Rarity.EXOTIC,  # Utilisation directe de l'énumération
        level=80
    )
    
    db.add(weapon)
    db.commit()
    
    assert weapon.id == 1
    assert weapon.name == "Test Weapon"
    assert weapon.type == WeaponType.STAFF
    assert weapon.damage_type == DamageType.FIRE
    assert weapon.min_power == 100
    assert weapon.max_power == 200
    assert weapon.rarity == Rarity.EXOTIC  # Comparaison directe avec l'objet Enum
    assert weapon.level == 80

# Tests pour le modÃ¨le Skill
def test_create_skill(db):
    """Teste la crÃ©ation d'une compÃ©tence."""
    # CrÃ©ation d'une profession parente
    profession = Profession(id="TestProfession", name="Test Profession")
    db.add(profession)
    
    # CrÃ©ation d'une spÃ©cialisation parente
    specialization = Specialization(
        id=1,
        name="Test Specialization",
        profession_id="TestProfession"
    )
    db.add(specialization)
    db.commit()
    
    # CrÃ©ation d'une compÃ©tence de test
    skill = Skill(
        id=1,
        name="Test Skill",
        name_fr="CompÃ©tence de test",
        description="Test skill description",
        description_fr="Description de la compÃ©tence de test",
        icon="test_icon.png",
        type=SkillType.WEAPON,
        weapon_type=WeaponType.STAFF.value,
        slot=1,
        professions=["Elementalist"],
        categories=["Damage", "Fire"],
        attunement="Fire",
        dual_wield=None,
        flip_skill=None,
        next_chain=None,
        prev_chain=None,
        tooltip_skill=None,
        transform_skills=[],
        bundle_skills=[],
        cost=0,
        recharge=0,
        combo_finisher=None,
        combo_field=None,
        flags=["NoUnderwater"],
        facts=[{"type": "Damage", "dmg_multiplier": 0.8, "hit_count": 1}],
        traited_facts=[],
        profession_id="Elementalist",
        specialization_id=1
    )
    
    # Ajout Ã  la base de donnÃ©es
    db.add(skill)
    db.commit()
    
    # VÃ©rification que la compÃ©tence a bien Ã©tÃ© ajoutÃ©e
    assert skill.id == 1
    assert skill.name == "Test Skill"
    assert skill.name_fr == "CompÃ©tence de test"
    assert skill.description == "Test skill description"
    assert skill.description_fr == "Description de la compÃ©tence de test"
    assert skill.icon == "test_icon.png"
    assert skill.type == SkillType.WEAPON
    assert skill.weapon_type == WeaponType.STAFF.value
    assert skill.slot == 1
    assert skill.professions == ["Elementalist"]
    assert skill.categories == ["Damage", "Fire"]
    assert skill.attunement == "Fire"
    assert skill.dual_wield is None
    assert skill.flip_skill is None
    assert skill.next_chain is None
    assert skill.prev_chain is None
    assert skill.tooltip_skill is None
    assert skill.transform_skills == []
    assert skill.bundle_skills == []
    assert skill.cost == 0
    assert skill.recharge == 0
    assert skill.combo_finisher is None
    assert skill.combo_field is None
    assert skill.flags == ["NoUnderwater"]
    assert skill.facts == [{"type": "Damage", "dmg_multiplier": 0.8, "hit_count": 1}]
    assert skill.traited_facts == []
    assert skill.profession_id == "Elementalist"
    assert skill.specialization_id == 1
    
    # VÃ©rification des relations
    assert skill.profession == profession
    assert skill.specialization == specialization
    assert skill in profession.skills
    assert skill in specialization.skills

# Tests pour le modÃ¨le Item
def test_create_item(db):
    """Teste la crÃ©ation d'un item."""
    # CrÃ©ation d'un item de test
    item = Item(
        id=1,
        name="Test Item",
        name_fr="Objet de test",
        description="Test item description",
        description_fr="Description de l'objet de test",
        icon="test_icon.png",
        type=ItemType.WEAPON,
        level=80,
        rarity=Rarity.EXOTIC,  # Utilisation directe de l'énumération
        vendor_value=100,
        flags=["SoulBindOnUse"],
        restrictions=[],
        details={
            "game_types": ["Activity", "Dungeon", "Pve", "Wvw"],
            "default_skin": 1000
        }
    )
    
    # Ajout Ã  la base de donnÃ©es
    db.add(item)
    db.commit()
    
    # VÃ©rification que l'item a bien Ã©tÃ© ajoutÃ©
    assert item.id == 1
    assert item.name == "Test Item"
    assert item.name_fr == "Objet de test"
    assert item.description == "Test item description"
    assert item.description_fr == "Description de l'objet de test"
    assert item.icon == "test_icon.png"
    assert item.type == ItemType.WEAPON
    assert item.level == 80
    assert item.rarity == Rarity.EXOTIC
    assert item.vendor_value == 100
    assert item.flags == ["SoulBindOnUse"]
    assert item.restrictions == []
    assert item.details == {
        "game_types": ["Activity", "Dungeon", "Pve", "Wvw"],
        "default_skin": 1000
    }
    assert item.created is not None
    assert item.updated is not None

def test_item_required_fields(db):
    """Teste que les champs requis pour un item sont bien dÃ©finis."""
    # Tentative de crÃ©ation d'un item sans champs requis
    with pytest.raises(IntegrityError):
        item = Item()
        db.add(item)
        db.commit()
    
    db.rollback()
    
    # CrÃ©ation d'un item avec uniquement les champs requis
    item = Item(
        id=1,
        name="Test Item",
        type=ItemType.WEAPON,
        rarity=Rarity.BASIC,
        level=0
    )
    
    db.add(item)
    db.commit()
    
    assert item.id == 1
    assert item.name == "Test Item"
    assert item.type == ItemType.WEAPON
    assert item.rarity == Rarity.BASIC
    assert item.level == 0



