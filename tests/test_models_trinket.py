"""Tests unitaires pour le modèle Trinket."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.trinket import (
    Trinket, 
    TrinketType, 
    InfusionSlotFlag,
    ProfessionTrinket
)
from app.models.profession import Profession
from app.models.item import Item, ItemType, Rarity

# ===== FIXTURES =====

@pytest.fixture
def sample_item(db):
    """Crée un objet de base pour le bijou."""
    item = Item(
        id=1001,
        name="Test Trinket Item",
        type=ItemType.TRINKET,
        rarity=Rarity.EXOTIC,
        level=80
    )
    db.add(item)
    db.commit()
    return item

@pytest.fixture
def sample_trinket(db, sample_item):
    """Crée un bijou de test."""
    trinket = Trinket(
        name="Berserker's Ruby Orichalcum Earring",
        name_fr="Boucle d'oreille en orichalque rubis du Berserker",
        description="A powerful earring that enhances your combat abilities.",
        description_fr="Une puissante boucle d'oreille qui améliore vos capacités de combat.",
        icon="https://render.guildwars2.com/file/...",
        chat_link="[&AgFpXAAA]",
        type=TrinketType.ACCESSORY,
        level=80,
        rarity="Exotic",
        vendor_value=1000,
        default_skin=42,
        details={
            "infusion_slots": [
                {"flags": [InfusionSlotFlag.UTILITY.value], "item_id": 37130}
            ],
            "infix_upgrade": {
                "id": 147,
                "attributes": [
                    {"attribute": "Power", "modifier": 63},
                    {"attribute": "Precision", "modifier": 45},
                    {"attribute": "Ferocity", "modifier": 45}
                ]
            },
            "suffix_item_id": 24563,
            "secondary_suffix_item_id": ""
        },
        infusion_slots=[
            {"flags": [InfusionSlotFlag.UTILITY.value], "item_id": 37130}
        ],
        infusion_upgrade_flags=["Infusion"],
        suffix_item_id=24563,
        secondary_suffix_item_id="",
        stat_choices=[136, 150, 171, 189],
        game_types=["Activity", "Dungeon", "Pve", "Wvw"],
        flags=["SoulBindOnUse"],
        restrictions=["Elementalist", "Mesmer", "Necromancer"],
        item_id=sample_item.id
    )
    db.add(trinket)
    db.commit()
    return trinket

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

def test_trinket_creation(db, sample_trinket):
    """Teste la création d'un bijou avec des valeurs de base."""
    trinket = db.query(Trinket).filter_by(name="Berserker's Ruby Orichalcum Earring").first()
    
    assert trinket is not None
    assert trinket.name == "Berserker's Ruby Orichalcum Earring"
    assert trinket.name_fr == "Boucle d'oreille en orichalque rubis du Berserker"
    assert trinket.type == TrinketType.ACCESSORY
    assert trinket.rarity == "Exotic"
    assert trinket.level == 80
    assert trinket.vendor_value == 1000
    assert len(trinket.infusion_slots) == 1
    assert trinket.infusion_slots[0]["flags"] == [InfusionSlotFlag.UTILITY.value]
    assert trinket.suffix_item_id == 24563
    assert "Elementalist" in trinket.restrictions
    assert "SoulBindOnUse" in trinket.flags

def test_trinket_required_fields(db, sample_item):
    """Teste que les champs requis sont obligatoires."""
    # Test sans nom
    with pytest.raises(IntegrityError):
        trinket = Trinket(
            type=TrinketType.RING,
            item_id=sample_item.id
        )
        db.add(trinket)
        db.commit()
    db.rollback()
    
    # Test sans type
    with pytest.raises(IntegrityError):
        trinket = Trinket(
            name="Test Ring",
            item_id=sample_item.id
        )
        db.add(trinket)
        db.commit()
    db.rollback()
    
    # Test sans item_id
    with pytest.raises(IntegrityError):
        trinket = Trinket(
            name="Test Ring",
            type=TrinketType.RING
        )
        db.add(trinket)
        db.commit()
    db.rollback()

def test_trinket_enum_validation():
    """Teste la validation des champs Enum."""
    # Test des valeurs d'énumération TrinketType
    assert TrinketType.ACCESSORY.value == "Accessory"
    assert TrinketType.AMULET.value == "Amulet"
    assert TrinketType.RING.value == "Ring"
    assert TrinketType.BACK.value == "Back"
    
    # Test des valeurs d'énumération InfusionSlotFlag
    assert InfusionSlotFlag.DEFENSE.value == "Defense"
    assert InfusionSlotFlag.OFFENSE.value == "Offense"
    assert InfusionSlotFlag.UTILITY.value == "Utility"
    assert InfusionSlotFlag.AGONY.value == "Agony"
    assert InfusionSlotFlag.UNIVERSAL.value == "Universal"

def test_trinket_profession_relationship(db, sample_trinket, sample_profession):
    """Teste la relation entre les bijoux et les professions."""
    # Créer une entrée dans la table d'association
    prof_trinket = ProfessionTrinket(
        profession_id=sample_profession.id,
        trinket_id=sample_trinket.id,
        slot="Accessory1"
    )
    
    db.add(prof_trinket)
    db.commit()
    
    # Vérifier que la relation fonctionne dans les deux sens
    trinket = db.query(Trinket).get(sample_trinket.id)
    assert len(trinket.profession_trinkets) == 1
    assert trinket.profession_trinkets[0].profession_id == sample_profession.id
    assert trinket.profession_trinkets[0].slot == "Accessory1"
    
    # Vérifier la relation inverse
    prof = db.query(Profession).get(sample_profession.id)
    assert len(prof.available_trinkets) == 1
    assert prof.available_trinkets[0].trinket_id == sample_trinket.id

def test_trinket_item_relationship(db, sample_trinket, sample_item):
    """Teste la relation entre Trinket et Item."""
    trinket = db.query(Trinket).get(sample_trinket.id)
    
    # Vérifier que la relation avec Item fonctionne
    assert trinket.item is not None
    assert trinket.item.id == sample_item.id
    assert trinket.item.name == "Test Trinket Item"
    
    # Vérifier que l'item a bien la relation avec le bijou
    item = db.query(Item).get(sample_item.id)
    assert item.trinket is not None
    assert item.trinket.id == sample_trinket.id

def test_trinket_default_values(db, sample_item):
    """Teste les valeurs par défaut des champs optionnels."""
    trinket = Trinket(
        name="Test Default Trinket",
        type=TrinketType.RING,
        item_id=sample_item.id
    )
    
    assert trinket.name_fr is None
    assert trinket.description is None
    assert trinket.description_fr is None
    assert trinket.icon is None
    assert trinket.chat_link is None
    assert trinket.level == 0
    assert trinket.vendor_value == 0
    assert trinket.default_skin is None
    assert trinket.details is None
    assert trinket.infusion_slots is None
    assert trinket.infusion_upgrade_flags is None
    assert trinket.suffix_item_id is None
    assert trinket.secondary_suffix_item_id is None
    assert trinket.stat_choices is None
    assert trinket.game_types is None
    assert trinket.flags is None
    assert trinket.restrictions is None
