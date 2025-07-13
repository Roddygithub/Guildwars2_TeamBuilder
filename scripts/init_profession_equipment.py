"""
Script d'initialisation des équipements par profession pour Guild Wars 2.

Ce script peuple les tables profession_weapon_types et profession_trinket_types
avec les armes et accessoires de base pour chaque profession.
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from app.database import Base, get_db
from app.models.profession import Profession
from app.models.weapon import WeaponType
from app.models.trinket import TrinketType
from app.models.profession_weapon import ProfessionWeaponType
from app.models.profession_trinket import ProfessionTrinketType
from app.models.weapon import WeaponType
from app.models.profession_weapon import ProfessionWeaponType
from app.models.trinket import TrinketType
from app.models.profession_trinket import ProfessionTrinketType

# Configuration de la base de données
SQLALCHEMY_DATABASE_URL = "sqlite:///gw2_teambuilder.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Mappage des armes par profession
PROFESSION_WEAPONS = {
    "Guardian": [
        (WeaponType.SWORD, "MainHand"),
        (WeaponType.GREATSWORD, "TwoHand"),
        (WeaponType.MACE, "MainHand"),
        (WeaponType.STAFF, "TwoHand"),
        (WeaponType.SCEPTER, "MainHand"),
        (WeaponType.SHIELD, "OffHand"),
        (WeaponType.TORCH, "OffHand"),
        (WeaponType.FOCUS, "OffHand"),
    ],
    "Warrior": [
        (WeaponType.AXE, "MainHand"),
        (WeaponType.GREATSWORD, "TwoHand"),
        (WeaponType.HAMMER, "TwoHand"),
        (WeaponType.LONGBOW, "TwoHand"),
        (WeaponType.MACE, "MainHand"),
        (WeaponType.RIFLE, "TwoHand"),
        (WeaponType.SWORD, "MainHand"),
    ],
    "Engineer": [
        (WeaponType.PISTOL, "MainHand"),
        (WeaponType.SHIELD, "OffHand"),
        (WeaponType.RIFLE, "TwoHand"),
    ],
    "Ranger": [
        (WeaponType.AXE, "MainHand"),
        (WeaponType.GREATSWORD, "TwoHand"),
        (WeaponType.LONGBOW, "TwoHand"),
        (WeaponType.SHORTBOW, "TwoHand"),
        (WeaponType.SWORD, "MainHand"),
        (WeaponType.WARHORN, "OffHand"),
        (WeaponType.DAGGER, "MainHand"),
        (WeaponType.TORCH, "OffHand"),
    ],
    "Thief": [
        (WeaponType.DAGGER, "MainHand"),
        (WeaponType.PISTOL, "MainHand"),
        (WeaponType.SHORTBOW, "TwoHand"),
        (WeaponType.SWORD, "MainHand"),
        (WeaponType.STAFF, "TwoHand"),
        (WeaponType.PISTOL, "OffHand"),
    ],
    "Elementalist": [
        (WeaponType.DAGGER, "MainHand"),
        (WeaponType.STAFF, "TwoHand"),
        (WeaponType.SCEPTER, "MainHand"),
        (WeaponType.FOCUS, "OffHand"),
        (WeaponType.DAGGER, "OffHand"),
        (WeaponType.WARHORN, "OffHand"),
    ],
    "Mesmer": [
        (WeaponType.GREATSWORD, "TwoHand"),
        (WeaponType.SWORD, "MainHand"),
        (WeaponType.STAFF, "TwoHand"),
        (WeaponType.SCEPTER, "MainHand"),
        (WeaponType.PISTOL, "OffHand"),
        (WeaponType.SWORD, "OffHand"),
        (WeaponType.FOCUS, "OffHand"),
        (WeaponType.TORCH, "OffHand"),
    ],
    "Necromancer": [
        (WeaponType.AXE, "MainHand"),
        (WeaponType.DAGGER, "MainHand"),
        (WeaponType.STAFF, "TwoHand"),
        (WeaponType.SCEPTER, "MainHand"),
        (WeaponType.WARHORN, "OffHand"),
        (WeaponType.DAGGER, "OffHand"),
    ],
    "Revenant": [
        (WeaponType.SWORD, "MainHand"),
        (WeaponType.HAMMER, "TwoHand"),
        (WeaponType.MACE, "MainHand"),
        (WeaponType.STAFF, "TwoHand"),
        (WeaponType.AXE, "MainHand"),
        (WeaponType.SHIELD, "OffHand"),
        (WeaponType.SWORD, "OffHand"),
    ],
}

# Mappage des accessoires par profession
PROFESSION_TRINKETS = {
    "Guardian": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Warrior": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Engineer": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Ranger": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Thief": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Elementalist": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Mesmer": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Necromancer": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
    "Revenant": [TrinketType.AMULET, TrinketType.RING, TrinketType.ACCESSORY],
}

def init_profession_weapons(session: Session):
    """Initialise les armes par profession."""
    print("Initialisation des armes par profession...")
    
    # Vider la table existante
    session.query(ProfessionWeaponType).delete()
    
    for profession_name, weapons in PROFESSION_WEAPONS.items():
        profession = session.query(Profession).filter(Profession.id == profession_name).first()
        if not profession:
            print(f"Attention: Profession {profession_name} non trouvée")
            continue
            
        for weapon_type, hand in weapons:
            # Convertir l'énumération en chaîne de caractères
            weapon_type_str = weapon_type.value if hasattr(weapon_type, 'value') else str(weapon_type)
            
            # Vérifier si cette entrée existe déjà pour éviter les doublons
            existing = session.query(ProfessionWeaponType).filter_by(
                profession_id=profession.id,
                weapon_type=weapon_type_str,
                hand=hand
            ).first()
            
            if not existing:
                weapon = ProfessionWeaponType(
                    profession_id=profession.id,
                    weapon_type=weapon_type_str,
                    hand=hand,
                    specialization_id=None,  # Pour les armes de base, pas de spécialisation
                    is_elite=False,
                )
                session.add(weapon)
    
    session.commit()
    print(f"Armes initialisées pour {len(PROFESSION_WEAPONS)} professions")

def init_profession_trinkets(session: Session):
    """Initialise les accessoires par profession."""
    print("Initialisation des accessoires par profession...")
    
    # Vider la table existante
    session.query(ProfessionTrinketType).delete()
    
    for profession_name, trinket_types in PROFESSION_TRINKETS.items():
        profession = session.query(Profession).filter(Profession.id == profession_name).first()
        if not profession:
            print(f"Attention: Profession {profession_name} non trouvée")
            continue
            
        for trinket_type in trinket_types:
            # Convertir l'énumération en chaîne de caractères
            trinket_type_str = trinket_type.value if hasattr(trinket_type, 'value') else str(trinket_type)
            
            # Vérifier si cette entrée existe déjà pour éviter les doublons
            existing = session.query(ProfessionTrinketType).filter_by(
                profession_id=profession.id,
                trinket_type=trinket_type_str
            ).first()
            
            if not existing:
                trinket = ProfessionTrinketType(
                    profession_id=profession.id,
                    trinket_type=trinket_type_str,
                    is_aquatic=False,
                )
                session.add(trinket)
    
    session.commit()
    print(f"Accessoires initialisés pour {len(PROFESSION_TRINKETS)} professions")

def main():
    print("Début de l'initialisation des équipements par profession...")
    
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    # Initialiser une session
    db = Session(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Initialiser les armes et accessoires
        init_profession_weapons(db)
        init_profession_trinkets(db)
        print("Initialisation terminée avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'initialisation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
