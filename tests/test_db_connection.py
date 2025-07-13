"""Test de connexion à la base de données."""

from sqlalchemy import text

def test_db_connection(db):
    """Vérifie que la connexion à la base de données fonctionne."""
    # Vérifie que la session est valide
    assert db is not None
    
    # Vérifie que la connexion est active
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1
    
    # Vérifie que les tables ont été créées
    from sqlalchemy import inspect
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    assert len(tables) > 0, "Aucune table n'a été créée dans la base de données de test"
    print(f"Tables créées : {tables}")

def test_profession_model(db):
    """Teste la création d'un modèle Profession."""
    from app.models.profession import Profession
    
    # Création d'une profession de test
    profession = Profession(
        id="TestProfession",
        name="Test Profession",
        name_fr="Profession de test",
        icon="test_icon.png"
    )
    
    # Ajout à la base de données
    db.add(profession)
    db.commit()
    
    # Vérification
    assert profession.id == "TestProfession"
    assert profession.name == "Test Profession"
    assert profession.name_fr == "Profession de test"
    assert profession.icon == "test_icon.png"
    
    # Nettoyage
    db.delete(profession)
    db.commit()
