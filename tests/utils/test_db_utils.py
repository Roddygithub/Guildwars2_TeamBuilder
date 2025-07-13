"""Tests pour le module db_utils."""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.utils.db_utils import with_session, SessionManager, get_db

# Tests pour le décorateur with_session

def test_with_session_without_session():
    """Teste le décorateur with_session sans session fournie."""
    # Créer un mock pour la session
    mock_session = MagicMock(spec=Session)
    
    # Fonction de test
    @with_session
    def test_func(session=None):
        session.add("test")
        return "success"
    
    # Tester avec patch pour simuler la création d'une session
    with patch('app.utils.db_utils.SessionLocal', return_value=mock_session):
        result = test_func()
        
        # Vérifier que la session a été utilisée correctement
        mock_session.add.assert_called_once_with("test")
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        assert result == "success"

def test_with_session_with_session():
    """Teste le décorateur with_session avec une session fournie."""
    mock_session = MagicMock(spec=Session)
    
    @with_session
    def test_func(session=None):
        session.add("test")
        return "success"
    
    result = test_func(session=mock_session)
    
    # Vérifier que la session fournie a été utilisée
    mock_session.add.assert_called_once_with("test")
    mock_session.commit.assert_not_called()  # Pas de commit car la session a été fournie
    mock_session.close.assert_not_called()  # Pas de close car la session a été fournie
    assert result == "success"

def test_with_session_exception():
    """Teste le comportement en cas d'exception."""
    mock_session = MagicMock(spec=Session)
    mock_session.in_transaction.return_value = True
    
    @with_session
    def test_func(session=None):
        raise ValueError("Test error")
    
    with patch('app.utils.db_utils.SessionLocal', return_value=mock_session):
        with pytest.raises(ValueError, match="Test error"):
            test_func()
        
        # Vérifier que rollback a été appelé
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

# Tests pour SessionManager

def test_session_manager_context():
    """Teste le gestionnaire de contexte SessionManager."""
    mock_session = MagicMock(spec=Session)
    mock_session.in_transaction.return_value = False
    
    with SessionManager(mock_session) as session:
        assert session is mock_session
    
    # Vérifier que commit a été appelé car c'est le propriétaire de la session
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()

def test_session_manager_exception():
    """Teste le gestionnaire de contexte avec une exception."""
    mock_session = MagicMock(spec=Session)
    mock_session.in_transaction.return_value = True
    
    with pytest.raises(ValueError, match="Test error"):
        with SessionManager(mock_session) as session:
            # S'assurer que la session est bien le mock
            assert session is mock_session
            # Lever une exception pour tester le rollback
            raise ValueError("Test error")
    
    # Vérifier que rollback a été appelé
    mock_session.rollback.assert_called_once()
    # La session ne devrait pas être fermée car elle a été fournie
    mock_session.close.assert_not_called()

# Tests pour get_db

def test_get_db():
    """Teste la fonction get_db pour l'injection de dépendances FastAPI."""
    mock_session = MagicMock(spec=Session)
    
    with patch('app.utils.db_utils.SessionLocal', return_value=mock_session):
        # get_db est un générateur
        db_gen = get_db()
        
        # Récupérer la session
        db = next(db_gen)
        assert db is mock_session
        
        # Simuler la fin de la requête en fermant le générateur
        with pytest.raises(StopIteration):
            next(db_gen)  # La deuxième itération devrait lever StopIteration
        
        # Vérifier que close a été appelé
        mock_session.close.assert_called_once()
