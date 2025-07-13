"""Script pour peupler la base de données avec des données de test pour GuildWars2 TeamBuilder."""
import os
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Importer les modèles
from app.models.base import Base
from app.models.skill import Skill, SkillType
from app.models.weapon import Weapon, WeaponType, DamageType, WeaponFlag
from app.models.profession import Profession
from app.models.specialization import Specialization
from app.models.trait import Trait, TraitTier, TraitSlot

# Configuration de la base de données
DB_PATH = 'gw2_teambuilder.db'
DB_URL = f'sqlite:///{DB_PATH}'

def create_test_profession(session):
    """Crée une profession de test."""
    profession = Profession(
        id='Elementalist',
        name='Elementalist',
        name_fr='Élémentaliste',
        icon='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        icon_big='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        icon_armor='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        description='A master of arcane lore, the elementalist wields the power of the elements: air, fire, earth, and water.',
        playable=True,
        specialization_ids=[],  # Rempli après la création des spécialisations
        created=datetime.utcnow().isoformat(),
        updated=datetime.utcnow().isoformat()
    )
    session.add(profession)
    return profession

def create_test_specialization(session, profession):
    """Crée une spécialisation de test."""
    specialization = Specialization(
        id=41,  # ID factice pour les tests
        name='Tempest',
        name_fr='Tempétueux',
        profession_id=profession.id,
        elite=True,
        minor_traits=[],  # Rempli après la création des traits
        major_traits=[],  # Rempli après la création des traits
        weapon_trait=None,  # Aucun trait d'arme par défaut
        icon='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        background='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        profession_icon=profession.icon,
        profession_icon_big=profession.icon_big,
        description='A master of the elements who wields a warhorn and attunes to the elements to provide support and area damage.',
        description_fr='Un maître des éléments qui manie un cor de guerre et se lie aux éléments pour fournir du soutien et des dégâts de zone.',
        playable=True,
        created=datetime.utcnow().isoformat(),
        updated=datetime.utcnow().isoformat()
    )
    session.add(specialization)
    return specialization

def create_test_trait(session, specialization):
    """Crée un trait de test.
    
    Args:
        session: Session SQLAlchemy
        specialization: La spécialisation à laquelle associer le trait
        
    Returns:
        Trait: Le trait créé avec des valeurs de test
    """
    # Préparer les données sérialisables
    tier = TraitTier.MAJOR.value  # Convertir l'énumération en chaîne
    slot = TraitSlot.ADEPT.value  # Convertir l'énumération en chaîne
    
    trait = Trait(
        id=1234,  # ID factice pour les tests
        name='Tempest Defense',
        name_fr='Défense du tempétueux',
        description='Gain access to shouts and their respective trait skills.',
        description_fr='Accès aux cris et à leurs compétences de traits respectives.',
        icon='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        specialization_id=specialization.id,
        type='Core',  # Type de trait (Core/Elite/Profession)
        tier=tier,  # Utiliser la valeur convertie
        slot=slot,  # Utiliser la valeur convertie
        categories=['Offense', 'Power'],  # Catégories du trait
        facts=[{"type": "AttributeAdjust", "target": "Power", "value": 100}],
        traited_facts=[]
    )
    session.add(trait)
    return trait

def create_test_weapon(session):
    """Crée une arme de test.
    
    Returns:
        Weapon: L'arme créée avec des valeurs de test
    """
    # Convertir les énumérations en leurs valeurs pour la sérialisation JSON
    weapon_type = WeaponType.STAFF.value  # Convertir l'énumération en chaîne
    damage_type = DamageType.FIRE.value   # Convertir l'énumération en chaîne
    flags = [flag.value for flag in [WeaponFlag.TWO_HAND]]  # Convertir chaque élément de la liste
    
    # Créer d'abord un Item associé car Weapon a une contrainte de clé étrangère vers Item
    from app.models.item import Item
    
    # Créer un item factice pour l'arme
    item = Item(
        id=1000,  # ID factice
        name='Zodiac Staff',
        name_fr='Bâton du zodiaque',
        type='Weapon',
        level=80,
        rarity='Exotic',
        vendor_value=1000,
        flags=flags,
        restrictions=[],
        description='This staff shimmers with the light of the stars.',
        description_fr='Ce bâton scintille de la lumière des étoiles.',
        details={
            'game_types': ["Activity", "Dungeon", "Pve", "Wvw"],
            'default_skin': 1000
        }
    )
    session.add(item)
    session.flush()  # Pour obtenir l'ID de l'item
    
    # Créer l'arme avec toutes les valeurs requises
    weapon = Weapon(
        id=1,  # ID factice pour les tests
        name='Zodiac Staff',
        name_fr='Bâton du zodiaque',
        type=weapon_type,  # Utiliser la valeur convertie
        damage_type=damage_type,  # Utiliser la valeur convertie
        min_power=900,
        max_power=1000,
        defense=0,
        attributes={"Power": 100, "Precision": 50},  # Déjà sérialisable
        flags=flags,  # Utiliser la liste convertie
        game_types=["Activity", "Dungeon", "Pve", "Wvw"],  # Déjà sérialisable
        restrictions=[],  # Déjà sérialisable
        rarity='Exotic',  # Rareté requise
        level=80,  # Niveau requis
        description='This staff shimmers with the light of the stars.',
        description_fr='Ce bâton scintille de la lumière des étoiles.',
        icon='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        item_id=item.id  # Lier à l'item créé
    )
    session.add(weapon)
    return weapon

def create_test_skill(session, profession, specialization, weapon):
    """Crée une compétence de test.
    
    Args:
        session: Session SQLAlchemy
        profession: La profession associée à la compétence
        specialization: La spécialisation associée à la compétence
        weapon: L'arme associée à la compétence
        
    Returns:
        Skill: La compétence créée avec des valeurs de test
    """
    # Convertir les énumérations en leurs valeurs pour la sérialisation JSON
    skill_type = SkillType.WEAPON.value  # Convertir l'énumération en chaîne
    
    # S'assurer que weapon.type est une chaîne et non une énumération
    weapon_type = weapon.type if isinstance(weapon.type, str) else weapon.type.value
    
    # Utiliser datetime.now avec timezone pour éviter les avertissements de dépréciation
    now = datetime.now().isoformat()
    
    skill = Skill(
        id=5501,  # ID factice pour les tests
        name='Flame Burst',
        name_fr='Explosion de flammes',
        description='Release a fiery explosion that burns foes.',
        description_fr="Libère une explosion de flammes qui enflamme les ennemis.",
        icon='https://render.guildwars2.com/file/1EE1CC990457BCB7E9CC4C8430F544D9FBB24E9A/156631.png',
        type=skill_type,  # Utiliser la valeur convertie
        weapon_type=weapon_type,  # Utiliser la valeur convertie
        slot='3',
        initiative=0,
        energy=0,
        professions=[profession.id],
        categories=["Damage", "Fire"],
        recharge=8.0,
        combo_finisher='Blast',
        combo_field='Fire',
        facts=[
            {"type": "Damage", "dmg_multiplier": 0.8, "hit_count": 1, "text": "Damage"},
            {"type": "Buff", "duration": 5, "status": "Burning", "description": "Causes a burning condition.", "apply_count": 1}
        ],
        traited_facts=[],
        created=now,
        updated=now,
        profession_id=profession.id,
        specialization_id=specialization.id
    )
    session.add(skill)
    return skill

def clear_tables(session):
    """Vide les tables de la base de données."""
    try:
        print("Vidage des tables existantes...")
        # Désactiver les contraintes de clé étrangère temporairement
        session.execute(text('PRAGMA foreign_keys=OFF'))
        
        # Vider les tables dans l'ordre inverse des dépendances
        session.execute(text('DELETE FROM skills'))
        session.execute(text('DELETE FROM traits'))
        session.execute(text('DELETE FROM specializations'))
        session.execute(text('DELETE FROM weapons'))
        session.execute(text('DELETE FROM professions'))
        
        # Réactiver les contraintes de clé étrangère
        session.execute(text('PRAGMA foreign_keys=ON'))
        session.commit()
        print("Tables vidées avec succès.")
        return True
    except Exception as e:
        print(f"Erreur lors du vidage des tables: {e}")
        session.rollback()
        return False

def populate_database():
    """Peuple la base de données avec des données de test."""
    print(f"Peuplement de la base de données à l'emplacement: {os.path.abspath(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("Erreur: La base de données n'existe pas. Veuillez d'abord exécuter init_db.py")
        return False
    
    try:
        # Créer le moteur SQLAlchemy
        engine = create_engine(DB_URL)
        
        # Créer une session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Vider les tables existantes
        if not clear_tables(session):
            return False
        
        # Créer les données de test
        print("Création des données de test...")
        
        # Créer une profession
        profession = create_test_profession(session)
        
        # Créer une spécialisation
        specialization = create_test_specialization(session, profession)
        
        # Mettre à jour l'ID de spécialisation dans la profession
        profession.specialization_ids = [specialization.id]
        
        # Créer un trait
        trait = create_test_trait(session, specialization)
        
        # Mettre à jour les IDs de traits dans la spécialisation
        specialization.trait_ids = [trait.id]
        
        # Créer une arme
        weapon = create_test_weapon(session)
        
        # Créer une compétence
        skill = create_test_skill(session, profession, specialization, weapon)
        
        # Valider les modifications
        session.commit()
        
        print("Données de test ajoutées avec succès!")
        return True
        
    except Exception as e:
        print(f"Erreur lors du peuplement de la base de données: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("=== Peuplement de la base de données GuildWars2 TeamBuilder avec des données de test ===\n")
    
    try:
        if populate_database():
            print("\nBase de données peuplée avec succès!")
        else:
            print("\nÉchec du peuplement de la base de données.")
    except Exception as e:
        print(f"\nERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
