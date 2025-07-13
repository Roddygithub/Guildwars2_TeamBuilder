"""Tests de performance des requêtes SQLAlchemy complexes.

Ce module contient des tests pour évaluer les performances des requêtes impliquant
plusieurs relations entre les modèles.
"""

import time
import logging
import pytest
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, func

# Configuration du logger
logger = logging.getLogger(__name__)

def log_query_time(description, start_time):
    """Log le temps d'exécution d'une requête."""
    duration = (time.time() - start_time) * 1000  # en millisecondes
    logger.info(f"{description}: {duration:.2f} ms")
    return duration

class TestQueryPerformance:
    """Tests de performance des requêtes complexes."""

    def test_skill_weapon_loading(self, db):
        """Test le chargement des compétences avec leurs armes associées."""
        # Test avec chargement paresseux (lazy loading)
        start = time.time()
        skills = db.execute(
            select(Skill)
            .where(Skill.type == "Weapon")
            .limit(10)
        ).scalars().all()
        
        # Accès aux armes (déclenche le lazy loading)
        for skill in skills:
            _ = skill.weapons
        
        lazy_time = log_query_time("Chargement paresseux (lazy loading)", start)
        
        # Test avec chargement immédiat (eager loading)
        start = time.time()
        skills = db.execute(
            select(Skill)
            .where(Skill.type == "Weapon")
            .options(selectinload(Skill.weapons))
            .limit(10)
        ).scalars().all()
        
        # Les armes sont déjà chargées
        for skill in skills:
            _ = skill.weapons
        
        eager_time = log_query_time("Chargement immédiat (eager loading)", start)
        
        # Vérification que le chargement immédiat est plus rapide
        assert eager_time < lazy_time * 0.5, "Le chargement immédiat devrait être plus rapide"

    def test_profession_weapon_skills(self, db):
        """Test le chargement des compétences d'arme par profession."""
        start = time.time()
        
        # Requête optimisée avec jointures
        result = db.execute(
            select(Profession, Weapon, Skill)
            .select_from(Profession)
            .join(ProfessionWeaponType, Profession.id == ProfessionWeaponType.profession_id)
            .join(Weapon, Weapon.type == ProfessionWeaponType.weapon_type)
            .join(ProfessionWeaponSkill, ProfessionWeaponType.id == ProfessionWeaponSkill.weapon_type_id)
            .join(Skill, Skill.id == ProfessionWeaponSkill.skill_id)
            .where(Profession.id == "Guardian")
            .order_by(Weapon.name, Skill.slot)
        ).all()
        
        log_query_time("Chargement des compétences d'arme par profession", start)
        
        # Vérification des résultats
        assert len(result) > 0, "Aucun résultat trouvé pour le Gardien"
        
        # Vérification du chargement des relations
        for profession, weapon, skill in result:
            assert isinstance(profession, Profession)
            assert isinstance(weapon, Weapon)
            assert isinstance(skill, Skill)

    def test_skill_traits_loading(self, db):
        """Test le chargement des compétences avec leurs traits associés."""
        start = time.time()
        
        # Requête avec chargement des traits
        skills = db.execute(
            select(Skill)
            .options(selectinload(Skill.traits))
            .where(Skill.traits.any())
            .limit(10)
        ).scalars().all()
        
        log_query_time("Chargement des compétences avec leurs traits", start)
        
        # Vérification que les traits sont chargés
        for skill in skills:
            assert hasattr(skill, 'traits')
            assert isinstance(skill.traits, list)

    def test_complex_query_with_aggregation(self, db):
        """Test une requête complexe avec agrégation."""
        start = time.time()
        
        # Compter le nombre de compétences par type d'arme et par profession
        result = db.execute(
            select(
                Profession.name.label('profession'),
                Weapon.type.label('weapon_type'),
                func.count(Skill.id).label('skill_count')
            )
            .select_from(Profession)
            .join(ProfessionWeaponType, Profession.id == ProfessionWeaponType.profession_id)
            .join(Weapon, Weapon.type == ProfessionWeaponType.weapon_type)
            .join(ProfessionWeaponSkill, ProfessionWeaponType.id == ProfessionWeaponSkill.weapon_type_id)
            .join(Skill, Skill.id == ProfessionWeaponSkill.skill_id)
            .group_by(Profession.name, Weapon.type)
            .order_by(Profession.name, Weapon.type)
        ).all()
        
        log_query_time("Requête d'agrégation: compétences par arme et profession", start)
        
        # Vérification des résultats
        assert len(result) > 0, "Aucun résultat trouvé"
        
        # Affichage des résultats pour analyse
        logger.info("\nCompétences par arme et profession:")
        for row in result:
            logger.info(f"{row.profession:15} | {row.weapon_type:20} | {row.skill_count:3} compétences")

    def test_loading_strategies_comparison(self, db):
        """Compare différentes stratégies de chargement."""
        # 1. Lazy loading (par défaut)
        start = time.time()
        skills = db.execute(
            select(Skill)
            .where(Skill.type == "Weapon")
            .limit(5)
        ).scalars().all()
        
        # Accès aux relations (déclenche des requêtes supplémentaires)
        for skill in skills:
            _ = skill.weapons
            _ = skill.traits
        
        lazy_time = log_query_time("Lazy loading (sans optimisation)", start)
        
        # 2. Eager loading avec joinedload
        start = time.time()
        skills = db.execute(
            select(Skill)
            .where(Skill.type == "Weapon")
            .options(
                joinedload(Skill.weapons),
                joinedload(Skill.traits)
            )
            .limit(5)
        ).unique().scalars().all()
        
        # Les relations sont déjà chargées
        for skill in skills:
            _ = skill.weapons
            _ = skill.traits
        
        joined_time = log_query_time("Eager loading avec joinedload", start)
        
        # 3. Eager loading avec selectinload
        start = time.time()
        skills = db.execute(
            select(Skill)
            .where(Skill.type == "Weapon")
            .options(
                selectinload(Skill.weapons),
                selectinload(Skill.traits)
            )
            .limit(5)
        ).scalars().all()
        
        # Les relations sont déjà chargées
        for skill in skills:
            _ = skill.weapons
            _ = skill.traits
        
        selectin_time = log_query_time("Eager loading avec selectinload", start)
        
        # Affichage des résultats
        logger.info(f"\nComparaison des stratégies de chargement (plus petit est mieux):")
        logger.info(f"- Lazy loading: {lazy_time:.2f} ms")
        logger.info(f"- Eager (joinedload): {joined_time:.2f} ms")
        logger.info(f"- Eager (selectinload): {selectin_time:.2f} ms")
        
        # Vérification que le selectinload est plus rapide que le lazy loading
        assert selectin_time < lazy_time * 0.7, "selectinload devrait être plus rapide que le lazy loading"

# Import des modèles à la fin pour éviter les problèmes d'importation circulaire
from app.models import (
    Skill, Weapon, Profession, ProfessionWeaponType, ProfessionWeaponSkill
)
