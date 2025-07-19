"""Script pour ajouter des exemples de builds à la base de données."""
import logging
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.build_sql import Build
from app.models.build import (
    BuildData, ProfessionType, RoleType, TraitLine, EquipmentItem
)
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_builds() -> list[BuildData]:
    """Crée une liste d'exemples de builds pour différentes professions et rôles."""
    # Format: (name, profession, role, buffs, roles, description)
    builds_data = [
        # Guardian
        ("Heal Firebrand", "guardian", "heal", {"quickness", "might"}, {"heal", "quickness"}, "Heal/Quickness Firebrand avec un bon uptime sur les buffs"),
        ("DPS Dragonhunter", "guardian", "dps", {"might"}, {"dps"}, "DPS pur avec des pics de dégâts élevés"),
        ("Support Firebrand", "guardian", "support", {"stability", "aegis"}, {"support", "tank"}, "Support avec stabilité et aegis"),
        
        # Warrior
        ("Banner Berserker", "warrior", "dps", {"might"}, {"dps"}, "DPS avec bannières pour l'utilité"),
        ("Banner Bladesworn", "warrior", "support", {"might"}, {"support"}, "Support avec bannières et soins"),
        
        # Revenant
        ("Alacrity Renegade", "revenant", "support", {"alacrity", "might"}, {"support", "alacrity"}, "Support Alacrity avec bonnes capacités de contrôle"),
        ("DPS Vindicator", "revenant", "dps", set(), {"dps"}, "DPS avec une bonne survie"),
        
        # Ranger
        ("Heal Druid", "ranger", "heal", {"might"}, {"heal"}, "Heal avec un bon uptime sur les buffs"),
        ("DPS Soulbeast", "ranger", "dps", set(), {"dps"}, "DPS avec des dégâts constants"),
        ("Support Untamed", "ranger", "support", set(), {"support"}, "Support avec contrôle de foule"),
        
        # Thief
        ("DPS Daredevil", "thief", "dps", set(), {"dps"}, "DPS très mobile avec esquive infinie"),
        ("DPS Deadeye", "thief", "dps", set(), {"dps"}, "DPS à distance avec des pics de dégâts"),
        
        # Engineer
        ("Quickness Scrapper", "engineer", "support", {"quickness", "might"}, {"support", "quickness"}, "Support Quickness avec soins"),
        ("DPS Holosmith", "engineer", "dps", set(), {"dps"}, "DPS avec des phases de burst"),
        
        # Necromancer
        ("Heal Scourge", "necromancer", "heal", set(), {"heal"}, "Heal avec barrière et contrôle de foule"),
        ("DPS Reaper", "necromancer", "dps", set(), {"dps"}, "DPS en mêlée avec une bonne survie"),
        ("Support Scourge", "necromancer", "support", set(), {"support"}, "Support avec barrière et revive"),
        
        # Elementalist
        ("Heal Tempest", "elementalist", "heal", {"might"}, {"heal"}, "Heal avec des soins de zone"),
        ("DPS Catalyst", "elementalist", "dps", set(), {"dps"}, "DPS avec des dégâts de zone"),
        
        # Mesmer
        ("Quickness Chronomancer", "mesmer", "support", {"quickness", "alacrity"}, {"support", "quickness"}, "Support Quickness/Alacrity avec contrôle"),
        ("DPS Virtuoso", "mesmer", "dps", set(), {"dps"}, "DPS à distance avec des dégâts stables")
    ]
    
    builds = []
    for name, profession, role, buffs, roles, description in builds_data:
        build = BuildData(
            name=name,
            profession=ProfessionType(profession),
            role=RoleType(role),
            specializations=[
                TraitLine(id=1, name="Ligne 1", traits=[1, 2, 3]),
                TraitLine(id=2, name="Ligne 2", traits=[1, 2, 3]),
                TraitLine(id=3, name="Ligne 3", traits=[1, 2, 3])
            ],
            skills=[0, 0, 0, 0, 0],  # Compétences par défaut
            equipment={
                "Helm": EquipmentItem(id=1, name="Casque de base"),
                "Shoulders": EquipmentItem(id=2, name="Épaulières de base"),
                "Coat": EquipmentItem(id=3, name="Manteau de base"),
                "Gloves": EquipmentItem(id=4, name="Gants de base"),
                "Leggings": EquipmentItem(id=5, name="Pantalon de base"),
                "Boots": EquipmentItem(id=6, name="Bottes de base"),
                "WeaponA1": EquipmentItem(id=7, name="Arme principale 1"),
                "WeaponA2": EquipmentItem(id=8, name="Arme principale 2"),
                "WeaponB1": EquipmentItem(id=9, name="Arme secondaire 1"),
                "WeaponB2": EquipmentItem(id=10, name="Arme secondaire 2"),
                "Backpack": EquipmentItem(id=11, name="Sac à dos de base"),
                "Accessory1": EquipmentItem(id=12, name="Accessoire 1"),
                "Accessory2": EquipmentItem(id=13, name="Accessoire 2"),
                "Amulet": EquipmentItem(id=14, name="Amulette de base"),
                "Ring1": EquipmentItem(id=15, name="Anneau 1"),
                "Ring2": EquipmentItem(id=16, name="Anneau 2"),
            },
            description=description
        )
        builds.append(build)
    
    return builds

def add_sample_builds_to_db(db: Session):
    """Ajoute les exemples de builds à la base de données."""
    try:
        # Vérifier si des builds existent déjà
        existing_builds = db.query(Build).count()
        if existing_builds > 0:
            logger.warning(f"Il y a déjà {existing_builds} builds dans la base de données. Voulez-vous vraiment continuer ? (o/n)")
            if input().lower() != 'o':
                logger.info("Annulation de l'ajout des exemples de builds.")
                return
        
        # Créer les exemples de builds
        sample_builds = create_sample_builds()
        
        # Ajouter chaque build à la session
        for build_data in sample_builds:
            build = Build.from_pydantic(build_data)
            db.add(build)
            logger.info(f"Ajout du build: {build.name} ({build.profession} - {build.role})")
        
        # Valider les changements
        db.commit()
        logger.info(f"{len(sample_builds)} exemples de builds ont été ajoutés avec succès.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de l'ajout des exemples de builds: {str(e)}", exc_info=True)
        raise

def main():
    """Fonction principale."""
    try:
        # Créer une session de base de données
        db = SessionLocal()
        
        # Ajouter les exemples de builds
        add_sample_builds_to_db(db)
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Fermer la session
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
