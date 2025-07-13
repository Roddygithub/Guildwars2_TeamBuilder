"""Exceptions personnalisées pour l'application GW2 Team Builder.

Ce module définit des exceptions personnalisées pour gérer les erreurs spécifiques
de l'application, comme les erreurs de validation des modèles.
"""

from typing import Any

class GW2TeamBuilderError(Exception):
    """Classe de base pour toutes les exceptions personnalisées de l'application.
    
    Attributes:
        message (str): Message d'erreur détaillé
        status_code (int, optional): Code d'état HTTP associé à l'erreur
        payload (dict, optional): Données supplémentaires sur l'erreur
    """
    
    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
    
    def to_dict(self) -> dict:
        """Convertit l'exception en dictionnaire pour la sérialisation JSON.
        
        Returns:
            dict: Représentation de l'erreur sous forme de dictionnaire
        """
        rv = dict(self.payload or {})
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(GW2TeamBuilderError):
    """Exception levée lorsqu'une validation échoue.
    
    Utilisée pour signaler des erreurs de validation de données, par exemple
    lors de la validation des champs d'un modèle avant son enregistrement.
    """
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        payload = {'field': field, 'value': value}
        if 'payload' in kwargs:
            payload.update(kwargs['payload'])
        super().__init__(
            message=message,
            status_code=kwargs.get('status_code', 400),
            payload=payload
        )


class NotFoundError(GW2TeamBuilderError):
    """Exception levée lorsqu'une ressource demandée n'est pas trouvée."""
    
    def __init__(self, resource: str, id: Any = None, **kwargs):
        message = f"{resource} non trouvé"
        if id is not None:
            message += f" avec l'ID: {id}"
        super().__init__(
            message=message,
            status_code=kwargs.get('status_code', 404),
            payload=kwargs.get('payload')
        )


class DatabaseError(GW2TeamBuilderError):
    """Exception levée lorsqu'une erreur de base de données se produit."""
    
    def __init__(self, message: str = "Erreur de base de données", **kwargs):
        super().__init__(
            message=message,
            status_code=kwargs.get('status_code', 500),
            payload=kwargs.get('payload')
        )


class APIError(GW2TeamBuilderError):
    """Exception levée lorsqu'une erreur d'API se produit."""
    
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        super().__init__(
            message=message,
            status_code=status_code,
            payload=kwargs.get('payload')
        )
