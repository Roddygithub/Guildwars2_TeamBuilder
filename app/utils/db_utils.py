"""Utilitaires pour la gestion des sessions et transactions SQLAlchemy."""
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from sqlalchemy.orm import Session
from fastapi import Depends

from ..database import SessionLocal

F = TypeVar('F', bound=Callable[..., Any])

def with_session(func: F) -> F:
    """Décorateur pour gérer automatiquement le cycle de vie des sessions SQLAlchemy.
    
    Ce décorateur s'assure que :
    - Une nouvelle session est créée si aucune n'est fournie
    - La session est correctement fermée après utilisation
    - Les erreurs sont propagées correctement
    
    Exemple d'utilisation:
        ```python
        @with_session
        def get_skills(session: Session = None):
            return session.query(Skill).all()
            
        # Ou avec un paramètre de requête
        @with_session
        def get_skill(skill_id: int, session: Session = None):
            return session.query(Skill).get(skill_id)
        ```
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_provided = 'session' in kwargs and kwargs['session'] is not None
        session = kwargs.get('session') or SessionLocal()
        
        try:
            # Si la session n'était pas fournie, on l'ajoute aux kwargs
            if not session_provided:
                kwargs['session'] = session
                
            result = func(*args, **kwargs)
            
            # On commit uniquement si la session a été créée ici
            if not session_provided:
                session.commit()
                
            return result
            
        except Exception as e:
            # On rollback en cas d'erreur
            if not session_provided and session.in_transaction():
                session.rollback()
            raise
            
        finally:
            # On ferme la session uniquement si on l'a créée
            if not session_provided:
                session.close()
    
    return cast(F, wrapper)

class SessionManager:
    """Gestionnaire de contexte pour les transactions SQLAlchemy.
    
    Exemple d'utilisation:
        ```python
        with SessionManager() as session:
            skill = session.query(Skill).get(1)
            skill.name = "Nouveau nom"
        # La transaction est automatiquement commitée si aucune erreur ne s'est produite
        ```
    """
    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self._is_owner = session is None
        
    def __enter__(self) -> Session:
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None and self._is_owner:
                self.session.commit()
            elif self._is_owner and self.session.in_transaction():
                self.session.rollback()
        finally:
            if self._is_owner:
                self.session.close()

def get_db() -> Session:
    """Fournit une instance de session pour l'injection de dépendances FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Alias pour la compatibilité avec le code existant
db_session = get_db
