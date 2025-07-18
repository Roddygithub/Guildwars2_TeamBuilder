"""Script pour peupler la table 'professions' avec des données de test."""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.append(str(Path(__file__).parent))
from app.config import settings

def populate_professions():
    """Peuple la table 'professions' avec des données de test."""
    # Configuration de la connexion à la base de données
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Vérifier si la table 'professions' existe
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='professions';")
            )
            if not result.fetchone():
                print("La table 'professions' n'existe pas. Création de la table...")
                # Créer la table 'professions' si elle n'existe pas
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS professions (
                        id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        name_fr VARCHAR(50),
                        name_de VARCHAR(50),
                        name_es VARCHAR(50),
                        icon VARCHAR(255),
                        icon_big VARCHAR(255),
                        icon_armor VARCHAR(255),
                        weapon_sword INTEGER,
                        description TEXT,
                        description_fr TEXT,
                        description_de TEXT,
                        description_es TEXT,
                        playable BOOLEAN DEFAULT 1,
                        specialization_ids JSON,
                        training_track_ids JSON,
                        flags JSON,
                        created DATETIME,
                        updated DATETIME
                    )
                """))
                conn.commit()
        
        # Données de test pour les professions
        professions_data = [
            {
                "id": "Guardian",
                "name": "Guardian",
                "name_fr": "Gardien",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 1,
                "description": "Masters of protective magic, guardians are devoted fighters who protect their allies and smite their enemies by drawing from the power of their virtues.",
                "description_fr": "Maîtres de la magie protectrice, les Gardiens sont des combattants dévoués qui protègent leurs alliés et frappent leurs ennemis en puisant dans le pouvoir de leurs vertus.",
                "playable": True,
                "specialization_ids": [6, 42, 27],
                "training_track_ids": [],
                "flags": ["HeavyArmor", "Supports"]
            },
            {
                "id": "Warrior",
                "name": "Warrior",
                "name_fr": "Guerrier",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 2,
                "description": "Warriors are masters of weaponry who rely on speed, strength, toughness, and heavy armor to survive in battle.",
                "description_fr": "Les Guerriers sont des maîtres en armement qui comptent sur la vitesse, la force, l'endurance et une lourde armure pour survivre au combat.",
                "playable": True,
                "specialization_ids": [18, 19, 20],
                "training_track_ids": [],
                "flags": ["HeavyArmor", "Damage"]
            },
            {
                "id": "Revenant",
                "name": "Revenant",
                "name_fr": "Revenant",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 3,
                "description": "Revenants channel the power of the Mists. These warrior scholars summon the essence of the Mists to empower their weapons and channel powerful abilities.",
                "description_fr": "Les Revenants canalisent le pouvoir des Brumes. Ces érudits guerriers invoquent l'essence des Brumes pour renforcer leurs armes et canaliser des capacités puissantes.",
                "playable": True,
                "specialization_ids": [52, 34, 63],
                "training_track_ids": [],
                "flags": ["HeavyArmor", "Support"]
            },
            {
                "id": "Ranger",
                "name": "Ranger",
                "name_fr": "Rôdeur",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 4,
                "description": "Rangers rely on a keen eye, a steady hand, and the power of nature. Their elite specialization is the Druid, a healer who draws on the power of the stars and natural energies.",
                "description_fr": "Les Rôdeurs comptent sur un œil perçant, une main sûre et le pouvoir de la nature. Leur spécialisation d'élite est le Druide, un guérisseur qui puise dans le pouvoir des étoiles et des énergies naturelles.",
                "playable": True,
                "specialization_ids": [5, 55, 72],
                "training_track_ids": [],
                "flags": ["MediumArmor", "Pet"]
            },
            {
                "id": "Thief",
                "name": "Thief",
                "name_fr": "Voleur",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 5,
                "description": "Thieves are agile fighters who use stealth, mobility, and trickery to defeat their enemies. They can steal items from foes and use them in combat.",
                "description_fr": "Les Voleurs sont des combattants agiles qui utilisent la discrétion, la mobilité et la ruse pour vaincre leurs ennemis. Ils peuvent voler des objets à leurs ennemis et les utiliser en combat.",
                "playable": True,
                "specialization_ids": [7, 58, 70],
                "training_track_ids": [],
                "flags": ["MediumArmor", "Stealth"]
            },
            {
                "id": "Engineer",
                "name": "Engineer",
                "name_fr": "Ingénieur",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 6,
                "description": "Engineers are masters of mechanical constructs and alchemy. They use a variety of kits and gadgets to control the battlefield and support their allies.",
                "description_fr": "Les Ingénieurs sont des maîtres des constructions mécaniques et de l'alchimie. Ils utilisent une variété de kits et de gadgets pour contrôler le champ de bataille et soutenir leurs alliés.",
                "playable": True,
                "specialization_ids": [43, 47, 57],
                "training_track_ids": [],
                "flags": ["MediumArmor", "Gadgets"]
            },
            {
                "id": "Necromancer",
                "name": "Necromancer",
                "name_fr": "Nécromancien",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 7,
                "description": "Necromancers are dark spellcasters who manipulate the forces of life and death. They can summon minions and drain the life force of their enemies.",
                "description_fr": "Les Nécromanciens sont des lanceurs de sorts obscurs qui manipulent les forces de la vie et de la mort. Ils peuvent invoquer des serviteurs et drainer la force vitale de leurs ennemis.",
                "playable": True,
                "specialization_ids": [2, 50, 60],
                "training_track_ids": [],
                "flags": ["LightArmor", "Minions"]
            },
            {
                "id": "Elementalist",
                "name": "Elementalist",
                "name_fr": "Élémentaliste",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 8,
                "description": "Elementalists are versatile spellcasters who channel elemental forces, making fire, air, earth, and water do their bidding.",
                "description_fr": "Les Élémentalistes sont des lanceurs de sorts polyvalents qui canalisent les forces élémentaires, faisant du feu, de l'air, de la terre et de l'eau leurs alliés.",
                "playable": True,
                "specialization_ids": [41, 48, 56],
                "training_track_ids": [],
                "flags": ["LightArmor", "Attunements"]
            },
            {
                "id": "Mesmer",
                "name": "Mesmer",
                "name_fr": "Envoûteur",
                "icon": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_big": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "icon_armor": "https://render.guildwars2.com/file/0D9E6BD66DA0017B79AD8B56B3E3058650F8B522/156626.png",
                "weapon_sword": 9,
                "description": "Mesmers are magical duelists who wield deception as a weapon. Using powerful illusions, clones, and phantasmal magic to ensure that their enemies can't believe their own eyes.",
                "description_fr": "Les Envoûteurs sont des duellistes magiques qui utilisent la tromperie comme arme. Utilisant des illusions puissantes, des clones et une magie phantasmatique pour s'assurer que leurs ennemis ne croient pas leurs propres yeux.",
                "playable": True,
                "specialization_ids": [40, 59, 62],
                "training_track_ids": [],
                "flags": ["LightArmor", "Illusions"]
            }
        ]
        
        # Préparer la requête d'insertion
        insert_stmt = text("""
            INSERT OR REPLACE INTO professions (
                id, name, name_fr, name_de, name_es, icon, icon_big, icon_armor,
                weapon_sword, description, description_fr, description_de, description_es,
                playable, specialization_ids, training_track_ids, flags, created, updated
            ) VALUES (
                :id, :name, :name_fr, :name_de, :name_es, :icon, :icon_big, :icon_armor,
                :weapon_sword, :description, :description_fr, :description_de, :description_es,
                :playable, :specialization_ids, :training_track_ids, :flags, :created, :updated
            )
        """)
        
        # Obtenir la date actuelle
        now = datetime.utcnow()
        
        # Insérer chaque profession
        for prof in professions_data:
            # Préparer les données pour l'insertion
            prof_data = {
                "id": prof["id"],
                "name": prof["name"],
                "name_fr": prof.get("name_fr"),
                "name_de": None,
                "name_es": None,
                "icon": prof.get("icon"),
                "icon_big": prof.get("icon_big"),
                "icon_armor": prof.get("icon_armor"),
                "weapon_sword": prof.get("weapon_sword"),
                "description": prof.get("description"),
                "description_fr": prof.get("description_fr"),
                "description_de": None,
                "description_es": None,
                "playable": 1 if prof.get("playable", True) else 0,
                "specialization_ids": json.dumps(prof.get("specialization_ids", [])),
                "training_track_ids": json.dumps(prof.get("training_track_ids", [])),
                "flags": json.dumps(prof.get("flags", [])),
                "created": now,
                "updated": now
            }
            
            # Exécuter l'insertion
            session.execute(insert_stmt, prof_data)
        
        # Valider les changements
        session.commit()
        print(f"{len(professions_data)} professions ont été ajoutées avec succès à la base de données.")
        
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Début du peuplement de la table 'professions'...")
    populate_professions()
    print("Terminé.")
