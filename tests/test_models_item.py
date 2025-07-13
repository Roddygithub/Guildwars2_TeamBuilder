"""Tests unitaires pour le modèle Item."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.item import Item, ItemType, Rarity
from app.models.item_stats import ItemStats
from app.models.item_stat_mapping import ItemStatMapping

# ===== FIXTURES =====

@pytest.fixture
def sample_item_stats(db):
    """Crée des statistiques d'objet de test."""
    stats = ItemStats(
        id=1,
        name="Berserker's",
        attributes={"Power": 63, "Precision": 45, "Ferocity": 45}
    )
    db.add(stats)
    db.commit()
    return stats

@pytest.fixture
def sample_item(db, sample_item_stats):
    """Crée un objet de test avec des statistiques."""
    item = Item(
        id=12345,
        name="Berserker's Draconic Coat",
        name_fr="Manteau draconique berserker",
        description="A powerful coat for adventurers.",
        description_fr="Un manteau puissant pour les aventuriers.",
        icon="https://render.guildwars2.com/file/...",
        type=ItemType.ARMOR,
        level=80,
        rarity=Rarity.EXOTIC,
        vendor_value=1000,
        flags=["SoulBindOnUse"],
        restrictions=["Norn", "Sylvari"],
        details={"weight_class": "Heavy", "defense": 300},
        stats_id=sample_item_stats.id
    )
    db.add(item)
    
    # Créer un mappage de statistiques
    mapping = ItemStatMapping(
        item_id=item.id,
        stat_id=sample_item_stats.id,
        is_default=True
    )
    db.add(mapping)
    db.commit()
    
    return item

# ===== TESTS =====

def test_create_item_basic(db):
    """Teste la création d'un objet avec des champs de base."""
    item = Item(
        id=1001,
        name="Test Item",
        type=ItemType.WEAPON,
        rarity=Rarity.RARE
    )
    db.add(item)
    db.commit()
    
    assert item.id == 1001
    assert item.name == "Test Item"
    assert item.type == ItemType.WEAPON
    assert item.rarity == Rarity.RARE
    assert item.level == 0  # Valeur par défaut
    assert item.vendor_value == 0  # Valeur par défaut

def test_item_required_fields(db):
    """Teste que les champs requis sont obligatoires."""
    # Test sans nom
    with pytest.raises(IntegrityError):
        item = Item(type=ItemType.WEAPON, rarity=Rarity.BASIC)
        db.add(item)
        db.commit()
    db.rollback()
    
    # Test sans type
    with pytest.raises(IntegrityError):
        item = Item(name="Test Item", rarity=Rarity.BASIC)
        db.add(item)
        db.commit()
    db.rollback()
    
    # Test sans rareté
    with pytest.raises(IntegrityError):
        item = Item(name="Test Item", type=ItemType.WEAPON)
        db.add(item)
        db.commit()
    db.rollback()

def test_item_enum_validation(db):
    """Teste la validation des champs Enum."""
    # Test avec un type d'objet valide
    item = Item(name="Valid Item", type=ItemType.ARMOR, rarity=Rarity.EXOTIC)
    db.add(item)
    db.commit()
    
    # Test avec une rareté valide
    item = Item(name="Valid Rarity", type=ItemType.WEAPON, rarity=Rarity.LEGENDARY)
    db.add(item)
    db.commit()
    
    # Test avec un type invalide (devrait échouer)
    with pytest.raises(ValueError):
        Item(name="Invalid Type", type="InvalidType", rarity=Rarity.BASIC)
    
    # Test avec une rareté invalide (devrait échouer)
    with pytest.raises(ValueError):
        Item(name="Invalid Rarity", type=ItemType.WEAPON, rarity="InvalidRarity")

def test_item_to_dict(db, sample_item):
    """Teste la méthode to_dict pour la sérialisation."""
    item_dict = sample_item.to_dict()
    
    # Vérifie les champs de base
    assert item_dict["id"] == 12345
    assert item_dict["name"] == "Berserker's Draconic Coat"
    assert item_dict["name_fr"] == "Manteau draconique berserker"
    assert item_dict["type"] == "Armor"
    assert item_dict["level"] == 80
    assert item_dict["rarity"] == "Exotic"
    assert item_dict["vendor_value"] == 1000
    assert item_dict["flags"] == ["SoulBindOnUse"]
    assert item_dict["restrictions"] == ["Norn", "Sylvari"]
    assert item_dict["details"]["weight_class"] == "Heavy"
    
    # Vérifie les statistiques
    assert item_dict["stats"]["name"] == "Berserker's"
    assert item_dict["stats"]["attributes"]["Power"] == 63

def test_item_relationships(db, sample_item, sample_item_stats):
    """Teste les relations de l'objet avec d'autres modèles."""
    # Vérifie la relation avec ItemStats
    assert sample_item.stats is not None
    assert sample_item.stats.id == sample_item_stats.id
    
    # Vérifie la relation avec ItemStatMapping
    assert len(sample_item.stat_mappings) == 1
    assert sample_item.stat_mappings[0].stat_id == sample_item_stats.id
    assert sample_item.stat_mappings[0].is_default is True

def test_item_enum_values():
    """Teste les valeurs des énumérations."""
    # Vérifie que toutes les valeurs d'énumération sont correctes
    assert ItemType.ARMOR.value == "Armor"
    assert ItemType.WEAPON.value == "Weapon"
    assert ItemType.TRINKET.value == "Trinket"
    
    assert Rarity.BASIC.value == "Basic"
    assert Rarity.EXOTIC.value == "Exotic"
    assert Rarity.LEGENDARY.value == "Legendary"

def test_item_default_values(db):
    """Teste les valeurs par défaut des champs optionnels."""
    item = Item(
        id=2001,
        name="Default Values Test",
        type=ItemType.CONSUMABLE,
        rarity=Rarity.BASIC
    )
    
    assert item.description is None
    assert item.description_fr is None
    assert item.icon is None
    assert item.level == 0
    assert item.vendor_value == 0
    assert item.flags is None
    assert item.restrictions is None
    assert item.details is None
    assert item.stats_id is None
