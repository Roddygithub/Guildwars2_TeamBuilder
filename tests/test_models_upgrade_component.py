"""Tests unitaires pour le modèle UpgradeComponent."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.upgrade_component import (
    UpgradeComponent,
    UpgradeComponentType,
    InfusionUpgradeFlag,
    Rune,
    Sigil,
    Relic
)
from app.models.item import Item, ItemType, Rarity
from app.models.armor import Armor
from app.models.weapon import Weapon

# ===== FIXTURES =====

@pytest.fixture
def sample_item(db):
    """Crée un objet de base pour le composant d'amélioration."""
    item = Item(
        id=1001,
        name="Test Upgrade Component",
        type=ItemType.UPGRADE_COMPONENT,
        rarity=Rarity.EXOTIC,
        level=80
    )
    db.add(item)
    db.commit()
    return item

@pytest.fixture
def sample_upgrade_component(db, sample_item):
    """Crée un composant d'amélioration de test."""
    component = UpgradeComponent(
        name="Superior Rune of the Scholar",
        name_fr="Rune supérieure de l'érudit",
        description="Increases power and ferocity.",
        description_fr="Augmente la puissance et la férocité.",
        icon="https://render.guildwars2.com/file/...",
        chat_link="[&AgFpXAAA]",
        type=UpgradeComponentType.RUNE,
        level=60,
        rarity="Exotic",
        vendor_value=1000,
        flags=["SoulBindOnUse"],
        restrictions=["Light Armor", "Medium Armor", "Heavy Armor"],
        details={
            "type": "Rune",
            "bonuses": [
                "+25 à tous les attributs",
                "+35 à la puissance",
                "+50 à la précision",
                "+65 à la puissance",
                "+100 à la précision",
                "+10% aux dégâts infligés lorsque la vie est supérieure à 90%"
            ]
        },
        item_id=sample_item.id
    )
    db.add(component)
    db.commit()
    return component

@pytest.fixture
def sample_armor(db):
    """Crée une armure de test."""
    item = Item(
        id=2001,
        name="Test Armor",
        type=ItemType.ARMOR,
        rarity=Rarity.EXOTIC,
        level=80
    )
    db.add(item)
    db.commit()
    
    armor = Armor(
        name="Test Armor",
        type="Coat",
        weight_class="Heavy",
        defense=100,
        item_id=item.id
    )
    db.add(armor)
    db.commit()
    return armor

@pytest.fixture
def sample_weapon(db):
    """Crée une arme de test."""
    item = Item(
        id=2002,
        name="Test Weapon",
        type=ItemType.WEAPON,
        rarity=Rarity.EXOTIC,
        level=80
    )
    db.add(item)
    db.commit()
    
    from app.models.weapon import Weapon as WeaponModel, WeaponType, DamageType
    weapon = WeaponModel(
        name="Test Greatsword",
        type=WeaponType.GREATSWORD,
        damage_type=DamageType.PHYSICAL,
        min_power=1000,
        max_power=1100,
        item_id=item.id
    )
    db.add(weapon)
    db.commit()
    return weapon

# ===== TESTS =====

def test_upgrade_component_creation(db, sample_upgrade_component):
    """Teste la création d'un composant d'amélioration avec des valeurs de base."""
    component = db.query(UpgradeComponent).filter_by(name="Superior Rune of the Scholar").first()
    
    assert component is not None
    assert component.name == "Superior Rune of the Scholar"
    assert component.name_fr == "Rune supérieure de l'érudit"
    assert component.type == UpgradeComponentType.RUNE
    assert component.level == 60
    assert component.rarity == "Exotic"
    assert component.vendor_value == 1000
    assert "SoulBindOnUse" in component.flags
    assert len(component.details["bonuses"]) == 6

def test_upgrade_component_required_fields(db, sample_item):
    """Teste que les champs requis sont obligatoires."""
    # Test sans nom
    with pytest.raises(IntegrityError):
        component = UpgradeComponent(
            type=UpgradeComponentType.RUNE,
            level=60,
            rarity="Exotic",
            item_id=sample_item.id
        )
        db.add(component)
        db.commit()
    db.rollback()
    
    # Test sans type
    with pytest.raises(IntegrityError):
        component = UpgradeComponent(
            name="Test Rune",
            level=60,
            rarity="Exotic",
            item_id=sample_item.id
        )
        db.add(component)
        db.commit()
    db.rollback()
    
    # Test sans rareté
    with pytest.raises(IntegrityError):
        component = UpgradeComponent(
            name="Test Rune",
            type=UpgradeComponentType.RUNE,
            level=60,
            item_id=sample_item.id
        )
        db.add(component)
        db.commit()
    db.rollback()

def test_upgrade_component_enum_validation():
    """Teste la validation des champs Enum."""
    # Test des valeurs d'énumération UpgradeComponentType
    assert UpgradeComponentType.RUNE.value == "Rune"
    assert UpgradeComponentType.SIGIL.value == "Sigil"
    assert UpgradeComponentType.RELIC.value == "Relic"
    assert UpgradeComponentType.GEM.value == "Gem"
    assert UpgradeComponentType.JEWEL.value == "Jewel"
    
    # Test des valeurs d'énumération InfusionUpgradeFlag
    assert InfusionUpgradeFlag.AGONY.value == "Agony"
    assert InfusionUpgradeFlag.DEFENSE.value == "Defense"
    assert InfusionUpgradeFlag.INFUSION.value == "Infusion"
    assert InfusionUpgradeFlag.OFFENSE.value == "Offense"
    assert InfusionUpgradeFlag.UTILITY.value == "Utility"
    assert InfusionUpgradeFlag.UNIVERSAL.value == "Universal"

def test_upgrade_component_armor_relationship(db, sample_upgrade_component, sample_armor):
    """Teste la relation entre les composants d'amélioration et les armures."""
    # Ajouter le composant à l'armure
    sample_armor.upgrades.append(sample_upgrade_component)
    db.commit()
    
    # Vérifier que la relation fonctionne dans les deux sens
    component = db.query(UpgradeComponent).get(sample_upgrade_component.id)
    assert len(component.armors) == 1
    assert component.armors[0].id == sample_armor.id
    
    armor = db.query(Armor).get(sample_armor.id)
    assert len(armor.upgrades) == 1
    assert armor.upgrades[0].id == sample_upgrade_component.id

def test_upgrade_component_weapon_relationship(db, sample_upgrade_component, sample_weapon):
    """Teste la relation entre les composants d'amélioration et les armes."""
    # Ajouter le composant à l'arme
    sample_weapon.upgrades.append(sample_upgrade_component)
    db.commit()
    
    # Vérifier que la relation fonctionne dans les deux sens
    component = db.query(UpgradeComponent).get(sample_upgrade_component.id)
    assert len(component.weapons) == 1
    assert component.weapons[0].id == sample_weapon.id
    
    weapon = db.query(Weapon).get(sample_weapon.id)
    assert len(weapon.upgrades) == 1
    assert weapon.upgrades[0].id == sample_upgrade_component.id

def test_upgrade_component_item_relationship(db, sample_upgrade_component, sample_item):
    """Teste la relation entre UpgradeComponent et Item."""
    component = db.query(UpgradeComponent).get(sample_upgrade_component.id)
    
    # Vérifier que la relation avec Item fonctionne
    assert component.item is not None
    assert component.item.id == sample_item.id
    assert component.item.name == "Test Upgrade Component"
    
    # Vérifier que l'item a bien la relation avec le composant
    item = db.query(Item).get(sample_item.id)
    assert item.upgrade_component is not None
    assert item.upgrade_component.id == sample_upgrade_component.id

def test_upgrade_component_default_values(db, sample_item):
    """Teste les valeurs par défaut des champs optionnels."""
    component = UpgradeComponent(
        name="Test Component",
        type=UpgradeComponentType.GEM,
        rarity="Masterwork",
        item_id=sample_item.id
    )
    
    assert component.name_fr is None
    assert component.description is None
    assert component.description_fr is None
    assert component.icon is None
    assert component.chat_link is None
    assert component.level == 0
    assert component.vendor_value == 0
    assert component.flags is None
    assert component.restrictions is None
    assert component.details is None

def test_rune_subclass(db, sample_item):
    """Teste la création d'une sous-classe Rune."""
    rune = Rune(
        name="Rune of the Scholar",
        type=UpgradeComponentType.RUNE,
        rarity="Exotic",
        level=60,
        bonuses=[
            "+25 à tous les attributs",
            "+35 à la puissance",
            "+50 à la précision",
            "+65 à la puissance",
            "+100 à la précision",
            "+10% aux dégâts infligés lorsque la vie est supérieure à 90%"
        ],
        item_id=sample_item.id
    )
    db.add(rune)
    db.commit()
    
    # Vérifier que la rune a été correctement enregistrée
    db_rune = db.query(Rune).filter_by(name="Rune of the Scholar").first()
    assert db_rune is not None
    assert len(db_rune.bonuses) == 6
    assert "+10% aux dégâts" in db_rune.bonuses[5]

def test_sigil_subclass(db, sample_item):
    """Teste la création d'une sous-classe Sigil."""
    sigil = Sigil(
        name="Sigil of Force",
        type=UpgradeComponentType.SIGIL,
        rarity="Exotic",
        level=60,
        suffix="of Force",
        item_id=sample_item.id
    )
    db.add(sigil)
    db.commit()
    
    # Vérifier que le cachet a été correctement enregistré
    db_sigil = db.query(Sigil).filter_by(name="Sigil of Force").first()
    assert db_sigil is not None
    assert db_sigil.suffix == "of Force"

def test_relic_subclass(db, sample_item):
    """Teste la création d'une sous-classe Relic."""
    relic = Relic(
        name="Relic of the Thief",
        type=UpgradeComponentType.RELIC,
        rarity="Exotic",
        level=80,
        active_skill_id=12345,
        item_id=sample_item.id
    )
    db.add(relic)
    db.commit()
    
    # Vérifier que la relique a été correctement enregistrée
    db_relic = db.query(Relic).filter_by(name="Relic of the Thief").first()
    assert db_relic is not None
    assert db_relic.active_skill_id == 12345
