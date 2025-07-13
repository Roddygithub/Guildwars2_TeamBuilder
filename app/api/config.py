"""Configuration pour l'intégration avec l'API Guild Wars 2."""

from enum import Enum
from typing import Dict, List, Optional, Any
import os
from pydantic import Field, HttpUrl, validator
from pydantic_settings import BaseSettings

class GW2APIVersion(str, Enum):
    """Versions disponibles de l'API GW2."""
    V2 = "v2"
    V1 = "v1"
    LATEST = V2

class GW2APISettings(BaseSettings):
    """Paramètres de configuration pour l'API GW2."""
    
    # URL de base de l'API GW2
    api_base_url: str = "https://api.guildwars2.com"
    
    # Version de l'API à utiliser
    api_version: GW2APIVersion = GW2APIVersion.LATEST
    
    # Clé API GW2 (optionnelle, nécessaire pour les endpoints authentifiés)
    api_key: Optional[str] = Field(default=None, env="GW2_API_KEY")
    
    # Paramètres de cache
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 heure en secondes
    cache_dir: str = "data/cache/gw2api"
    
    # Paramètres de requête
    request_timeout: int = 30  # secondes
    max_retries: int = 3
    retry_delay: float = 1.0  # secondes
    
    # Paramètres de taux d'appel (rate limiting)
    rate_limit_enabled: bool = True
    requests_per_second: int = 5
    
    # Paramètres de journalisation
    log_requests: bool = True
    log_responses: bool = False
    log_errors: bool = True
    
    class Config:
        env_prefix = "GW2_API_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def base_url(self) -> str:
        """Retourne l'URL de base complète avec la version de l'API."""
        return f"{self.api_base_url}/{self.api_version.value}"
    
    @property
    def headers(self) -> Dict[str, str]:
        """Retourne les en-têtes HTTP par défaut pour les requêtes API."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "Guildwars2-TeamBuilder/1.0 (https://github.com/yourusername/guildwars2-teambuilder)",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers

# Instance de configuration globale
settings = GW2APISettings()

def configure_api(**kwargs) -> None:
    """Configure les paramètres de l'API GW2.
    
    Args:
        **kwargs: Paramètres de configuration à mettre à jour
    """
    global settings
    
    # Mettre à jour uniquement les paramètres valides
    valid_fields = set(GW2APISettings.__annotations__.keys())
    updates = {k: v for k, v in kwargs.items() if k in valid_fields}
    
    # Mettre à jour les paramètres
    settings = GW2APISettings(**{**settings.dict(), **updates})
    
    # Créer le répertoire de cache si nécessaire
    if settings.cache_enabled and settings.cache_dir:
        os.makedirs(settings.cache_dir, exist_ok=True)
