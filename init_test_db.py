"""Script pour initialiser la base de données avec des données de test."""
import sys
from pathlib import Path
import json
from datetime import datetime

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app.database import SessionLocal, init_db, Base, engine
from app.models.skill import Skill, SkillType
from app.models.weapon import Weapon, WeaponType
from app.models.profession import Profession
from app.models.specialization import Specialization

def create_test_data():
    """Crée des données de test pour la base de données."""
    print("Création des données de test...")
    db = SessionLocal()
    
    try:
        # Créer des professions de test
        professions = [
            Profession(
                id="Guardian",
                name="Gardien",
                icon="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png",
                icon_big="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png",
                specializations=["Zeal", "Radiance", "Valor", "Honor", "Virtues", "Dragonhunter", "Firebrand", "Willbender"]
            ),
            Profession(
                id="Warrior",
                name="Guerrier",
                icon="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png",
                icon_big="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png",
                specializations=["Strength", "Arms", "Defense", "Tactics", "Discipline", "Berserker", "Spellbreaker", "Bladesworn"]
            )
        ]
        
        # Créer des spécialisations de test
        specializations = [
            Specialization(
                id=42,
                name="Dragonhunter",
                profession="Guardian",
                elite=True,
                icon="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png"
            ),
            Specialization(
                id=52,
                name="Berserker",
                profession="Warrior",
                elite=True,
                icon="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png"
            )
        ]
        
        # Créer des armes de test
        weapons = [
            Weapon(
                id=1,
                name="Sword",
                type=WeaponType.SWORD,
                damage_type="Physical",
                min_power=900,
                max_power=1000,
                defense=0,
                attributes={"Precision": 120, "Ferocity": 85}
            ),
            Weapon(
                id=2,
                name="Greatsword",
                type=WeaponType.GREATSWORD,
                damage_type="Physical",
                min_power=1000,
                max_power=1100,
                defense=0,
                attributes={"Power": 179, "Precision": 128}
            )
        ]
        
        # Créer des compétences de test
        skills = [
            Skill(
                id=1,
                name="Rayon de justice",
                type=SkillType.WEAPON,
                description="Un rayon de lumière frappe vos ennemis, infligeant des dégâts et des brûlures.",
                icon="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png",
                professions=["Guardian"],
                weapon_type=WeaponType.SWORD,
                slot="Weapon_1",
                recharge=5,
                facts=json.dumps([
                    {"type": "Damage", "dmg_multiplier": 1.0, "hits": 1},
                    {"type": "Buff", "status": "Burning", "duration": 3, "description": "Brûlure infligée"}
                ])
            ),
            Skill(
                id=2,
                name="Coup de taille",
                type=SkillType.WEAPON,
                description="Une attaque rapide qui inflige des dégâts supplémentaires aux ennemis avec peu de points de vie.",
                icon="https://render.guildwars2.com/file/0CDBCA7C808C1BDEA3B0EFDCCE9F2CB6078034B/156633.png",
                professions=["Warrior"],
                weapon_type=WeaponType.SWORD,
                slot="Weapon_1",
                recharge=0,
                facts=json.dumps([
                    {"type": "Damage", "dmg_multiplier": 0.8, "hits": 1},
                    {"type": "Damage", "dmg_multiplier": 0.4, "hits": 1, "description": "Dégâts supplémentaires sous 50% de vie"}
                ])
            )
        ]
        
        # Ajouter les objets à la session
        db.add_all(professions)
        db.add_all(specializations)
        db.add_all(weapons)
        db.add_all(skills)
        
        # Valider les changements
        db.commit()
        
        print("Données de test créées avec succès!")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création des données de test: {e}")
        raise
    finally:
        db.close()

def main():
    """Fonction principale pour initialiser la base de données."""
    print("Initialisation de la base de données...")
    
    # Créer toutes les tables
    print("Création des tables...")
    Base.metadata.create_all(bind=engine)
    
    # Initialiser la base de données
    init_db()
    
    # Créer des données de test
    create_test_data()
    
    print("Initialisation terminée avec succès!")

if __name__ == "__main__":
    main()
