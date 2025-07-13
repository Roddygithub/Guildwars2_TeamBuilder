"""Tests pour le module sql_debug."""
import time
import logging
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.utils.sql_debug import QueryAnalyzer, sql_profiler, log_sql_statements

# Modèle de test
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="posts")

User.posts = relationship("Post", back_populates="user")

# Tests pour QueryAnalyzer

def test_query_analyzer_init():
    """Teste l'initialisation de QueryAnalyzer."""
    mock_session = MagicMock(spec=Session)
    analyzer = QueryAnalyzer(mock_session)
    
    assert analyzer.session is mock_session
    assert analyzer.queries == []
    assert analyzer._enabled is False

def test_query_analyzer_start_stop():
    """Teste l'activation et la désactivation de l'analyseur."""
    mock_session = MagicMock()
    mock_engine = MagicMock(spec=Engine)
    mock_session.bind = mock_engine
    
    analyzer = QueryAnalyzer(mock_session)
    
    # Tester start()
    analyzer.start()
    assert analyzer._enabled is True
    assert len(mock_engine.listeners['before_cursor_execute']) == 1
    assert len(mock_engine.listeners['after_cursor_execute']) == 1
    
    # Tester stop()
    analyzer.stop()
    assert analyzer._enabled is False

def test_query_analyzer_record_query():
    """Teste l'enregistrement des requêtes."""
    mock_session = MagicMock()
    mock_engine = MagicMock()
    mock_session.bind = mock_engine
    
    analyzer = QueryAnalyzer(mock_session)
    analyzer.start()
    
    # Simuler l'exécution d'une requête
    mock_conn = MagicMock()
    mock_conn.info = {'query_start_time': [time.time() - 0.1]}
    
    # Appeler manuellement les écouteurs
    for listener in mock_engine.listeners['before_cursor_execute']:
        listener(mock_conn, None, "SELECT * FROM users", None, None, False)
    
    for listener in mock_engine.listeners['after_cursor_execute']:
        listener(mock_conn, None, "SELECT * FROM users", None, None, False)
    
    # Vérifier que la requête a été enregistrée
    assert len(analyzer.queries) == 1
    query = analyzer.queries[0]
    assert query['statement'] == "SELECT * FROM users"
    assert isinstance(query['duration'], float)
    assert query['duration'] > 0
    
    # Tester get_slow_queries
    slow_queries = analyzer.get_slow_queries(threshold=0.05)
    assert len(slow_queries) == 1
    
    # Tester get_duplicate_queries
    analyzer.queries.append(analyzer.queries[0].copy())
    duplicates = analyzer.get_duplicate_queries()
    assert len(duplicates) == 1
    assert len(duplicates["SELECT * FROM users"]) == 2
    
    # Tester generate_report
    report = analyzer.generate_report()
    assert "Rapport d'analyse des requêtes SQL" in report
    assert "Requêtes en double: 2" in report

# Tests pour sql_profiler

def test_sql_profiler():
    """Teste le gestionnaire de contexte sql_profiler."""
    mock_session = MagicMock()
    mock_engine = MagicMock()
    mock_session.bind = mock_engine
    
    with sql_profiler(mock_session) as profiler:
        assert profiler._enabled is True
        assert len(mock_engine.listeners['before_cursor_execute']) == 1
    
    # Vérifier que le profiler est désactivé après le contexte
    assert profiler._enabled is False

# Tests pour log_sql_statements

def test_log_sql_statements():
    """Teste l'activation du logging des requêtes SQL."""
    mock_engine = MagicMock(spec=Engine)
    mock_logger = MagicMock()
    
    with patch('app.utils.sql_debug.logger', mock_logger):
        log_sql_statements(mock_engine, level=logging.DEBUG)
    
    # Vérifier que les écouteurs ont été configurés
    assert len(mock_engine.echo_property.mock_calls) > 0
    assert mock_logger.setLevel.called_with(logging.DEBUG)

# Test d'intégration avec une base de données en mémoire

def test_integration_with_sqlite():
    """Teste l'intégration avec une base de données SQLite en mémoire."""
    # Créer une base de données SQLite en mémoire
    engine = create_engine('sqlite:///:memory:')
    SessionLocal = sessionmaker(bind=engine)
    
    # Créer les tables
    Base.metadata.create_all(engine)
    
    # Tester avec un profiler
    with sql_profiler(SessionLocal()) as profiler:
        session = SessionLocal()
        
        # Créer un utilisateur
        user = User(name="Test User")
        session.add(user)
        session.commit()
        
        # Faire une requête
        users = session.query(User).filter(User.name == "Test User").all()
        assert len(users) == 1
        assert users[0].name == "Test User"
        
        session.close()
    
    # Vérifier que les requêtes ont été enregistrées
    assert len(profiler.queries) >= 2  # Au moins INSERT et SELECT
    
    # Générer un rapport
    report = profiler.generate_report()
    assert "Rapport d'analyse des requêtes SQL" in report
