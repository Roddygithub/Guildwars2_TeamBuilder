"""Tests pour le modèle Build."""
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, StatementError
from app.database import SessionLocal, engine, Base
from app.models.build_sql import Build
from app.models.build import ProfessionType, RoleType, TraitLine, EquipmentItem

# Créer les tables dans la base de données de test
@pytest.fixture(scope="module")
def db():
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Nettoyer la base de données après les tests
        Base.metadata.drop_all(bind=engine)

# Test de création d'un build
def test_create_build(db: Session):
    # Données de test
    build_data = {
        "name": "Test Build",
        "profession": ProfessionType.GUARDIAN,
        "role": RoleType.DPS,
        "specializations": [
            {"id": 1, "name": "Dragonhunter", "traits": [1, 2, 3]},
            {"id": 2, "name": "Zeal", "traits": [4, 5, 6]},
            {"id": 3, "name": "Radiance", "traits": [7, 8, 9]}
        ],
        "skills": [1, 2, 3, 4, 5],
        "equipment": {
            "Helm": {"id": 1, "name": "Exotic Helm", "infusions": [], "upgrades": []}
        },
        "description": "Build de test pour Guardian DPS"
    }
    
    # Création du build
    build = Build(**build_data)
    
    # Ajout à la base de données
    db.add(build)
    db.commit()
    db.refresh(build)
    
    # Vérifications
    assert build.id is not None
    assert build.name == "Test Build"
    assert build.profession == ProfessionType.GUARDIAN
    assert build.role == RoleType.DPS
    assert len(build.specializations) == 3
    assert len(build.skills) == 5
    assert "Helm" in build.equipment
    
    # Nettoyage
    db.delete(build)
    db.commit()

# Test de récupération d'un build
def test_get_build(db: Session):
    # Créer un build de test
    build = Build(
        name="Test Get Build",
        profession=ProfessionType.ELEMENTALIST,
        role=RoleType.HEAL,
        specializations=[],
        skills=[],
        equipment={},
        description="Build de test pour la récupération"
    )
    db.add(build)
    db.commit()
    db.refresh(build)
    
    # Récupérer le build
    retrieved = db.query(Build).filter(Build.id == build.id).first()
    
    # Vérifications
    assert retrieved is not None
    assert retrieved.name == "Test Get Build"
    assert retrieved.profession == ProfessionType.ELEMENTALIST
    assert retrieved.role == RoleType.HEAL
    
    # Vérifier les valeurs par défaut
    assert retrieved.created_at is not None
    assert retrieved.updated_at is not None
    assert retrieved.is_public is False
    
    # Nettoyage
    db.delete(build)
    db.commit()

# Test de mise à jour d'un build
def test_update_build(db: Session):
    # Créer un build de test
    build = Build(
        name="Test Update Build",
        profession=ProfessionType.WARRIOR,
        role=RoleType.QUICKNESS,
        specializations=[],
        skills=[],
        equipment={}
    )
    db.add(build)
    db.commit()
    
    # Mettre à jour le build
    build.name = "Updated Build Name"
    build.role = RoleType.ALACRITY
    build.is_public = True
    db.commit()
    db.refresh(build)
    
    # Vérifier les mises à jour
    updated = db.query(Build).filter(Build.id == build.id).first()
    assert updated.name == "Updated Build Name"
    assert updated.role == RoleType.ALACRITY
    assert updated.is_public is True
    
    # Nettoyage
    db.delete(build)
    db.commit()

# Test de suppression d'un build
def test_delete_build(db: Session):
    # Créer un build de test
    build = Build(
        name="Test Delete Build",
        profession=ProfessionType.RANGER,
        role=RoleType.HEAL,
        specializations=[],
        skills=[],
        equipment={}
    )
    db.add(build)
    db.commit()
    build_id = build.id
    
    # Supprimer le build
    db.delete(build)
    db.commit()
    
    # Vérifier que le build a bien été supprimé
    deleted = db.query(Build).filter(Build.id == build_id).first()
    assert deleted is None

# Test de validation des données
def test_build_validation(db: Session):
    # Test avec des données valides
    valid_build = Build(
        name="Valid Build",
        profession=ProfessionType.MESMER,
        role=RoleType.ALACRITY,
        specializations=[],
        skills=[1, 2, 3, 4, 5],
        equipment={
            "Helm": {"id": 1, "name": "Exotic Helm", "infusions": [], "upgrades": []},
            "Chest": {"id": 2, "name": "Exotic Chest", "infusions": [], "upgrades": []}
        },
        is_public=True,
        description="Un build valide avec tout le nécessaire"
    )
    db.add(valid_build)
    db.commit()
    
    # Vérifier que le build a été correctement enregistré
    assert valid_build.id is not None
    
    # Nettoyage
    db.delete(valid_build)
    db.commit()

# Test des contraintes de la base de données
def test_database_constraints(db: Session):
    # Test de la contrainte NOT NULL sur le nom
    with pytest.raises(IntegrityError):
        build = Build(
            name=None,  # Ceci devrait échouer
            profession=ProfessionType.ENGINEER,
            role=RoleType.DPS,
            specializations=[],
            skills=[],
            equipment={}
        )
        db.add(build)
        db.commit()
    db.rollback()
    
    # Test de la contrainte NOT NULL sur la profession
    with pytest.raises(IntegrityError):
        build = Build(
            name="Build sans profession",
            profession=None,  # Ceci devrait échouer
            role=RoleType.DPS,
            specializations=[],
            skills=[],
            equipment={}
        )
        db.add(build)
        db.commit()
    db.rollback()
    
    # Test de la contrainte NOT NULL sur le rôle
    with pytest.raises(IntegrityError):
        build = Build(
            name="Build sans rôle",
            profession=ProfessionType.THIEF,
            role=None,  # Ceci devrait échouer
            specializations=[],
            skills=[],
            equipment={}
        )
        db.add(build)
        db.commit()
    db.rollback()

# Test de la méthode to_dict()
def test_to_dict_method(db: Session):
    # Créer un build avec des données complètes
    build = Build(
        name="Test to_dict",
        profession=ProfessionType.NECROMANCER,
        role=RoleType.DPS,
        specializations=[
            {"id": 1, "name": "Reaper", "traits": [1, 2, 3]},
            {"id": 2, "name": "Spite", "traits": [4, 5, 6]},
            {"id": 3, "name": "Soul Reaping", "traits": [7, 8, 9]}
        ],
        skills=[1, 2, 3, 4, 5],
        equipment={
            "Weapon": {"id": 10, "name": "Greatsword", "infusions": [], "upgrades": []}
        },
        is_public=True,
        description="Test de la méthode to_dict"
    )
    
    # Convertir en dictionnaire
    build_dict = build.to_dict()
    
    # Vérifier les champs principaux
    assert build_dict["name"] == "Test to_dict"
    assert build_dict["profession"] == "necromancer"  # Vérifie la valeur en minuscules
    assert build_dict["role"] == "dps"  # Vérifie la valeur en minuscules
    assert build_dict["is_public"] is True
    assert build_dict["description"] == "Test de la méthode to_dict"
    
    # Vérifier les listes et dictionnaires
    assert len(build_dict["specializations"]) == 3
    assert len(build_dict["skills"]) == 5
    assert "Weapon" in build_dict["equipment"]
    
    # Vérifier les champs de date
    assert "created_at" in build_dict
    assert "updated_at" in build_dict

# Test de la méthode from_dict()
def test_from_dict_method():
    # Données pour créer un build
    build_data = {
        "name": "Test from_dict",
        "profession": "ELEMENTALIST",
        "role": "HEAL",
        "specializations": [
            {"id": 1, "name": "Tempest", "traits": [1, 2, 3]}
        ],
        "skills": [1, 2, 3, 4, 5],
        "equipment": {
            "Weapon": {"id": 11, "name": "Warhorn", "infusions": [], "upgrades": []}
        },
        "is_public": True,
        "description": "Test de la méthode from_dict"
    }
    
    # Créer un build à partir du dictionnaire
    build = Build.from_dict(build_data)
    
    # Vérifier les champs
    assert build.name == "Test from_dict"
    assert build.profession == ProfessionType.ELEMENTALIST
    assert build.role == RoleType.HEAL
    assert len(build.specializations) == 1
    assert len(build.skills) == 5
    assert "Weapon" in build.equipment
    assert build.is_public is True
    assert build.description == "Test de la méthode from_dict"

# Test des valeurs par défaut
def test_default_values(db: Session):
    # Créer un build avec uniquement les champs requis
    build = Build(
        name="Build avec valeurs par défaut",
        profession=ProfessionType.ENGINEER,
        role=RoleType.DPS
    )
    
    # Ajouter à la session pour initialiser les valeurs par défaut
    db.add(build)
    db.flush()  # Force l'initialisation des valeurs par défaut
    
    # Vérifier les valeurs par défaut après ajout à la session
    assert build.specializations == []
    assert build.skills == []
    assert build.equipment == {}
    assert build.is_public is False
    assert build.description is None
    assert build.created_at is not None
    assert build.updated_at is not None
    
    # Nettoyage
    db.rollback()  # Annuler les changements pour ne pas affecter les autres tests
