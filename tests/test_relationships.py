"""Tests unitaires pour les relations entre modèles."""

import pytest
from sqlalchemy.exc import IntegrityError

# Import des modèles à tester
from app.models.profession import Profession
from app.models.specialization import Specialization
from app.models.trait import Trait, TraitTier
from app.models.weapon import Weapon, WeaponType, WeaponFlag
from app.models.skill import Skill, SkillType
from app.models.item import Item, ItemType, Rarity
from app.models.profession_weapon import ProfessionWeaponType

# Tests pour les relations Profession <-> Specialization
def test_profession_specialization_relationship(db):
    """Teste la relation entre Profession et Specialization."""
    # Création d'une profession
    profession = Profession(
        id="TestProfession",
        name="Test Profession"
    )
    db.add(profession)
    
    # Création de deux spécialisations pour cette profession
    spec1 = Specialization(
        id=1,
        name="Test Spec 1",
        profession_id="TestProfession",
        elite=False
    )
    spec2 = Specialization(
        id=2,
        name="Test Spec 2",
        profession_id="TestProfession",
        elite=True
    )
    
    db.add_all([spec1, spec2])
    db.commit()
    
    # Vérification des relations
    assert len(profession.specializations) == 2
    assert spec1 in profession.specializations
    assert spec2 in profession.specializations
    assert spec1.profession == profession
    assert spec2.profession == profession
    
    # Vérification que la suppression en cascade fonctionne
    db.delete(profession)
    db.commit()
    
    # Vérification que les spécialisations ont bien été supprimées
    assert db.query(Specialization).count() == 0

# Tests pour les relations Specialization <-> Trait
def test_specialization_trait_relationship(db):
    """Teste la relation entre Specialization et Trait."""
    # Création d'une profession et d'une spécialisation
    profession = Profession(id="TestProfession", name="Test Profession")
    specialization = Specialization(
        id=1,
        name="Test Spec",
        profession_id="TestProfession"
    )
    
    # Création de plusieurs traits pour cette spécialisation
    trait1 = Trait(
        id=1,
        name="Trait 1",
        specialization_id=1,
        tier=TraitTier.MINOR,
        slot=1
    )
    
    trait2 = Trait(
        id=2,
        name="Trait 2",
        specialization_id=1,
        tier=TraitTier.MAJOR,
        slot=1
    )
    
    db.add_all([profession, specialization, trait1, trait2])
    db.commit()
    
    # Vérification des relations
    assert len(specialization.traits) == 2
    assert trait1 in specialization.traits
    assert trait2 in specialization.traits
    assert trait1.specialization == specialization
    assert trait2.specialization == specialization
    
    # Vérification que la suppression en cascade fonctionne
    db.delete(specialization)
    db.commit()
    
    # Vérification que les traits ont bien été supprimés
    assert db.query(Trait).count() == 0

# Tests pour les relations Profession <-> Weapon
def test_profession_weapon_relationship(db):
    """Teste la relation entre Profession et Weapon via ProfessionWeaponType."""
    # Création d'une profession
    profession = Profession(
        id="TestProfession",
        name="Test Profession"
    )
    
    # Création d'une arme
    weapon = Weapon(
        id=1,
        name="Test Weapon",
        type=WeaponType.SWORD,
        damage_type="Physical",
        min_power=100,
        max_power=200,
        rarity=Rarity.EXOTIC,
        level=80
    )
    
    # Création d'un type d'arme de profession
    prof_weapon = ProfessionWeaponType(
        profession_id="TestProfession",
        weapon_type=WeaponType.SWORD.value,
        hand="MainHand"
    )
    
    db.add_all([profession, weapon, prof_weapon])
    db.commit()
    
    # Vérification des relations
    assert len(profession.weapon_types) == 1
    assert prof_weapon in profession.weapon_types
    assert prof_weapon.profession == profession
    
    # Vérification que la suppression en cascade fonctionne
    db.delete(profession)
    db.commit()
    
    # Vérification que le type d'arme de profession a été supprimé
    assert db.query(ProfessionWeaponType).count() == 0
    
    # Vérification que l'arme n'a pas été supprimée (relation non-cascade)
    assert db.query(Weapon).count() == 1

# Tests pour les relations Weapon <-> Skill
def test_weapon_skill_relationship(db):
    """Teste la relation entre Weapon et Skill."""
    # Création d'une arme
    weapon = Weapon(
        id=1,
        name="Test Weapon",
        type=WeaponType.STAFF,
        damage_type="Fire",
        min_power=100,
        max_power=200,
        rarity=Rarity.EXOTIC,
        level=80
    )
    
    # Création de compétences pour cette arme
    skill1 = Skill(
        id=1,
        name="Skill 1",
        type=SkillType.WEAPON,
        weapon_type=WeaponType.STAFF.value,
        slot=1
    )
    
    skill2 = Skill(
        id=2,
        name="Skill 2",
        type=SkillType.WEAPON,
        weapon_type=WeaponType.STAFF.value,
        slot=2
    )
    
    # Ajout des compétences à l'arme via la relation many-to-many
    weapon.skills = [skill1, skill2]
    
    db.add(weapon)
    db.commit()
    
    # Vérification des relations
    assert len(weapon.skills) == 2
    assert skill1 in weapon.skills
    assert skill2 in weapon.skills
    assert weapon in skill1.weapons
    assert weapon in skill2.weapons
    
    # Vérification que la suppression de l'arme ne supprime pas les compétences
    # mais supprime bien les entrées dans la table d'association
    db.delete(weapon)
    db.commit()
    
    # Vérification que les compétences n'ont pas été supprimées
    assert db.query(Skill).count() == 2
    
    # Vérification que la table d'association a été vidée
    # (nécessite une requête SQL directe car pas de modèle pour la table d'association)
    result = db.execute("SELECT COUNT(*) FROM weapon_skills").scalar()
    assert result == 0

# Tests pour les relations Item <-> Weapon
def test_item_weapon_relationship(db):
    """Teste la relation entre Item et Weapon."""
    # Création d'un item
    item = Item(
        id=1,
        name="Test Item",
        type=ItemType.WEAPON,
        rarity=Rarity.EXOTIC,
        level=80
    )
    
    # Création d'une arme liée à cet item
    weapon = Weapon(
        id=1,
        name="Test Weapon",
        type=WeaponType.SWORD,
        damage_type="Physical",
        min_power=100,
        max_power=200,
        rarity=Rarity.EXOTIC,
        level=80,
        item_id=1
    )
    
    db.add_all([item, weapon])
    db.commit()
    
    # Vérification des relations
    assert item.weapon == weapon
    assert weapon.item == item
    
    # Vérification que la suppression de l'item supprime aussi l'arme (cascade)
    db.delete(item)
    db.commit()
    
    # Vérification que l'arme a bien été supprimée
    assert db.query(Weapon).count() == 0

# Tests pour les contraintes d'intégrité
def test_integrity_constraints(db):
    """Teste les contraintes d'intégrité des relations."""
    # Tentative de créer un trait avec un ID de spécialisation inexistant
    with pytest.raises(IntegrityError):
        trait = Trait(
            id=1,
            name="Invalid Trait",
            specialization_id=999,  # N'existe pas
            tier=TraitTier.MINOR,
            slot=1
        )
        db.add(trait)
        db.commit()
    
    db.rollback()
    
    # Tentative de créer une spécialisation avec un ID de profession inexistant
    with pytest.raises(IntegrityError):
        spec = Specialization(
            id=1,
            name="Invalid Spec",
            profession_id="InvalidProfession",  # N'existe pas
            elite=False
        )
        db.add(spec)
        db.commit()
    
    db.rollback()
    
    # Tentative de créer une arme avec un ID d'item inexistant
    with pytest.raises(IntegrityError):
        weapon = Weapon(
            id=1,
            name="Invalid Weapon",
            type=WeaponType.SWORD,
            damage_type="Physical",
            min_power=100,
            max_power=200,
            rarity=Rarity.EXOTIC,
            level=80,
            item_id=999  # N'existe pas
        )
        db.add(weapon)
        db.commit()
    
    db.rollback()
