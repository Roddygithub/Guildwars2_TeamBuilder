"""Tests unitaires pour le modèle Armor."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.armor import (
    Armor, 
    ArmorType, 
    WeightClass, 
    InfusionSlotFlag,
    ProfessionArmor
)
from app.models.profession import Profession
from app.models.item import Item, Rarity

# ===== FIXTURES =====

@pytest.fixture
def sample_item(db):
    """Crée un objet de base pour l'armure."""
    item = Item(
        id=1001,
        name="Test Armor Item",
        type=ItemType.ARMOR,
        rarity=Rarity.EXOTIC,
        level=80
    )
    db.add(item)
    db.commit()
    return item

@pytest.fixture
def sample_armor(db, sample_item):
    """Crée une armure de test."""
    armor = Armor(
        name="Zojja's Epaulets",
        name_fr="Spallières de Zojja",
        description="Magical shoulder armor that enhances your power.",
        description_fr="Armure d'épaules magique qui améliore votre puissance.",
        icon="https://render.guildwars2.com/file/...",
        chat_link="[&AgFpXAAA]",
        type=ArmorType.SHOULDERS,
        weight_class=WeightClass.LIGHT,
        defense=134,
        infusion_slots=[
            {"flags": [InfusionSlotFlag.UTILITY], "item_id": 37130},
            {"flags": [InfusionSlotFlag.UTILITY], "item_id": 37130}
        ],
        infusion_upgrade_flags=["Defense", "Infusion"],
        suffix_item_id=24564,
        secondary_suffix_item_id="",
        stat_choices=[136, 150, 171, 189],
        game_types=["Activity", "Dungeon", "Pve", "Wvw"],
        flags=["SoulBindOnUse"],
        restrictions=["Elementalist", "Mesmer", "Necromancer"],
        rarity="Exotic",
        level=80,
        default_skin=600,
        details={
            "weight_class": "Light",
            "defense": 134,
            "infusion_slots": [
                {"flags": ["Utility"], "item_id": 37130},
                {"flags": ["Utility"], "item_id": 37130}
            ],
            "suffix_item_id": 24564,
            "secondary_suffix_item_id": "",
            "stat_choices": [136, 150, 171, 189]
        },
        item_id=sample_item.id
    )
    db.add(armor)
    db.commit()
    return armor

@pytest.fixture
def sample_profession(db):
    """Crée une profession de test."""
    prof = Profession(
        id="Elementalist",
        name="Elementalist",
        icon="https://render.guildwars2.com/file/...",
        icon_big="https://render.guildwars2.com/file/...",
        profession="Elementalist",
        weapons={}
    )
    db.add(prof)
    db.commit()
    return prof

# ===== TESTS =====

def test_armor_creation(db, sample_armor):
    """Teste la création d'une armure avec des valeurs de base."""
    armor = db.query(Armor).filter_by(name="Zojja's Epaulets").first()
    
    assert armor is not None
    assert armor.name == "Zojja's Epaulets"
    assert armor.name_fr == "Spallières de Zojja"
    assert armor.type == ArmorType.SHOULDERS
    assert armor.weight_class == WeightClass.LIGHT
    assert armor.defense == 134
    assert armor.rarity == "Exotic"
    assert armor.level == 80
    assert len(armor.infusion_slots) == 2
    assert armor.infusion_slots[0]["flags"] == [InfusionSlotFlag.UTILITY]
    assert armor.suffix_item_id == 24564
    assert "Elementalist" in armor.restrictions
    assert "SoulBindOnUse" in armor.flags

def test_armor_required_fields(db, sample_item):
    """Teste que les champs requis sont obligatoires."""
    # Test sans nom
    with pytest.raises(IntegrityError):
        armor = Armor(
            type=ArmorType.HELM,
            weight_class=WeightClass.HEAVY,
            item_id=sample_item.id
        )
        db.add(armor)
        db.commit()
    db.rollback()
    
    # Test sans type
    with pytest.raises(IntegrityError):
        armor = Armor(
            name="Test Armor",
            weight_class=WeightClass.HEAVY,
            item_id=sample_item.id
        )
        db.add(armor)
        db.commit()
    db.rollback()
    
    # Test sans classe de poids
    with pytest.raises(IntegrityError):
        armor = Armor(
            name="Test Armor",
            type=ArmorType.HELM,
            item_id=sample_item.id
        )
        db.add(armor)
        db.commit()
    db.rollback()

def test_armor_enum_validation():
    """Teste la validation des champs Enum."""
    # Test des valeurs d'énumération ArmorType
    assert ArmorType.HELM == "Helm"
    assert ArmorType.COAT == "Coat"
    assert ArmorType.LEGGINGS == "Leggings"
    
    # Test des valeurs d'énumération WeightClass
    assert WeightClass.LIGHT == "Light"
    assert WeightClass.MEDIUM == "Medium"
    assert WeightClass.HEAVY == "Heavy"
    
    # Test des valeurs d'énumération InfusionSlotFlag
    assert InfusionSlotFlag.DEFENSE == "Defense"
    assert InfusionSlotFlag.OFFENSE == "Offense"
    assert InfusionSlotFlag.UTILITY == "Utility"

def test_armor_profession_relationship(db, sample_armor, sample_profession):
    """Teste la relation entre les armures et les professions."""
    # Créer une entrée dans la table d'association
    prof_armor = ProfessionArmor(
        profession_id=sample_profession.id,
        armor_id=sample_armor.id,
        slot="Shoulders"
    )
    
    db.add(prof_armor)
    db.commit()
    
    # Vérifier que la relation fonctionne dans les deux sens
    armor = db.query(Armor).get(sample_armor.id)
    assert len(armor.profession_armors) == 1
    assert armor.profession_armors[0].profession_id == sample_profession.id
    assert armor.profession_armors[0].slot == "Shoulders"
    
    # Vérifier la relation inverse
    prof = db.query(Profession).get(sample_profession.id)
    assert len(prof.available_armors) == 1
    assert prof.available_armors[0].armor_id == sample_armor.id

def test_armor_item_relationship(db, sample_armor, sample_item):
    """Teste la relation entre Armor et Item."""
    armor = db.query(Armor).get(sample_armor.id)
    
    # Vérifier que la relation avec Item fonctionne
    assert armor.item is not None
    assert armor.item.id == sample_item.id
    assert armor.item.name == "Test Armor Item"
    
    # Vérifier que l'item a bien la relation avec l'armure
    item = db.query(Item).get(sample_item.id)
    assert item.armor is not None
    assert item.armor.id == sample_armor.id

def test_armor_default_values(db, sample_item):
    """Teste les valeurs par défaut des champs optionnels."""
    armor = Armor(
        name="Test Default Armor",
        type=ArmorType.HELM,
        weight_class=WeightClass.MEDIUM,
        item_id=sample_item.id
    )
    
    assert armor.name_fr is None
    assert armor.description is None
    assert armor.description_fr is None
    assert armor.icon is None
    assert armor.chat_link is None
    assert armor.defense == 0
    assert armor.infusion_slots is None
    assert armor.infusion_upgrade_flags is None
    assert armor.suffix_item_id is None
    assert armor.secondary_suffix_item_id is None
    assert armor.stat_choices is None
    assert armor.game_types is None
    assert armor.flags is None
    assert armor.restrictions is None
    assert armor.default_skin is None
    assert armor.details is None
