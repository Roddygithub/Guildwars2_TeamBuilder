"""
Commandes CLI pour l'import/export de builds.

Ce module contient les différentes commandes disponibles dans l'interface en ligne de commande.
"""
from typing import Dict, Type, Any
from abc import ABC, abstractmethod
from pathlib import Path
import json
import yaml

from fastapi import HTTPException

class BaseCommand(ABC):
    """Classe de base pour les commandes CLI."""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> int:
        """Exécute la commande.
        
        Returns:
            int: Code de sortie (0 pour succès, >0 pour erreur)
        """
        pass
    
    def load_build(self, file_path: str) -> dict:
        """Charge un build depuis un fichier.
        
        Args:
            file_path: Chemin vers le fichier du build
            
        Returns:
            dict: Données du build
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            json.JSONDecodeError: Si le fichier n'est pas un JSON valide
            ValueError: Si le format du build est invalide
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
            
        # Détecter le format en fonction de l'extension
        if path.suffix.lower() in ('.yaml', '.yml'):
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:  # Par défaut, on suppose du JSON
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def save_build(self, build_data: dict, file_path: str, format: str = 'json') -> None:
        """Enregistre un build dans un fichier.
        
        Args:
            build_data: Données du build à enregistrer
            file_path: Chemin de destination
            format: Format de sortie (json ou yaml)
            
        Raises:
            ValueError: Si le format n'est pas supporté
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'yaml':
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(build_data, f, default_flow_style=False, allow_unicode=True)
        else:  # JSON par défaut
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(build_data, f, indent=2, ensure_ascii=False)
    
    def handle_http_error(self, e: HTTPException) -> int:
        """Gère les erreurs HTTP de l'API.
        
        Args:
            e: Exception HTTP
            
        Returns:
            int: Code de sortie approprié
        """
        status_code = getattr(e, 'status_code', 500)
        detail = getattr(e, 'detail', str(e))
        
        print(f"Erreur {status_code}: {detail}")
        
        # Mapper les codes d'erreur HTTP vers des codes de sortie
        error_mapping = {
            400: 1,  # Erreur de validation
            401: 4,  # Non autorisé
            403: 4,  # Interdit
            404: 2,  # Non trouvé
            422: 1,  # Erreur de validation
            500: 5,  # Erreur serveur
        }
        
        return error_mapping.get(status_code // 100 * 100, 5)  # Par défaut: erreur inconnue

# Dictionnaire des commandes disponibles
COMMANDS: Dict[str, Type[BaseCommand]] = {}

def register_command(name: str) -> callable:
    """Décorateur pour enregistrer une commande.
    
    Args:
        name: Nom de la commande
    """
    def decorator(cls: Type[BaseCommand]) -> Type[BaseCommand]:
        COMMANDS[name] = cls
        return cls
    return decorator
