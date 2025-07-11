"""Module de cache pour l'API GW2.

Ce module fournit une interface pour mettre en cache les réponses de l'API GW2
et gérer leur expiration.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Type, Generic, Union
from datetime import datetime, timedelta

import aiohttp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Base

# Type générique pour les modèles SQLAlchemy
ModelType = TypeVar("ModelType", bound=Base)

class GW2APICache:
    """Classe pour gérer le cache des appels à l'API GW2.
    
    Cette classe permet de mettre en cache les réponses de l'API GW2 dans un dossier
    local et/ou dans la base de données, avec une durée d'expiration configurable.
    """
    
    def __init__(
        self, 
        cache_dir: str = "data/cache",
        default_ttl: int = 7 * 24 * 60 * 60,  # 7 jours par défaut
        use_disk_cache: bool = True,
        use_db_cache: bool = True
    ):
        """Initialise le cache.
        
        Args:
            cache_dir: Dossier pour stocker le cache sur disque
            default_ttl: Durée de vie par défaut en secondes
            use_disk_cache: Si True, utilise le cache disque
            use_db_cache: Si True, utilise le cache en base de données
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.use_disk_cache = use_disk_cache
        self.use_db_cache = use_db_cache
        
        # Créer le dossier de cache s'il n'existe pas
        if use_disk_cache and not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Génère une clé de cache unique à partir d'un endpoint et de paramètres."""
        key_parts = [endpoint]
        if params:
            # Trier les paramètres pour assurer une clé cohérente
            for k, v in sorted(params.items()):
                key_parts.append(f"{k}={v}")
        
        # Créer un hachage de la clé pour un nom de fichier sûr
        key_str = "&".join(key_parts)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Retourne le chemin du fichier de cache pour une clé donnée."""
        return self.cache_dir / f"{key}.json"
    
    async def get_from_api(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None,
        session: Optional[aiohttp.ClientSession] = None,
        ttl: Optional[int] = None
    ) -> Any:
        """Récupère des données depuis l'API GW2 avec mise en cache.
        
        Args:
            endpoint: Endpoint de l'API (ex: 'items', 'skills/42')
            params: Paramètres de la requête
            session: Session HTTP asynchrone (optionnelle)
            ttl: Durée de vie du cache en secondes (optionnel)
            
        Returns:
            Les données désérialisées de la réponse
        """
        ttl = ttl or self.default_ttl
        cache_key = self._get_cache_key(endpoint, params)
        
        # Essayer de récupérer depuis le cache
        cached_data = await self.get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Si non trouvé dans le cache, faire l'appel API
        url = f"{settings.GW2_API_BASE_URL}/{endpoint}"
        
        # Utiliser la session fournie ou en créer une nouvelle
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True
        
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Mettre en cache la réponse
                await self.set_in_cache(cache_key, data, ttl)
                
                return data
        finally:
            if close_session and not session.closed:
                await session.close()
    
    async def get_from_cache(self, key: str) -> Optional[Any]:
        """Récupère des données depuis le cache.
        
        Args:
            key: Clé de cache
            
        Returns:
            Les données en cache ou None si expirées ou non trouvées
        """
        # Essayer le cache disque
        if self.use_disk_cache:
            cache_path = self._get_cache_path(key)
            
            if cache_path.exists():
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # Vérifier l'expiration
                    if 'expires_at' in cache_data and cache_data['expires_at'] < time.time():
                        return None
                    
                    return cache_data.get('data')
                except (json.JSONDecodeError, IOError):
                    # En cas d'erreur, supprimer le fichier corrompu
                    if cache_path.exists():
                        cache_path.unlink()
        
        # TODO: Implémenter le cache en base de données
        # if self.use_db_cache:
        #     pass
        
        return None
    
    async def set_in_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Stocke des données dans le cache.
        
        Args:
            key: Clé de cache
            data: Données à mettre en cache (doivent être sérialisables en JSON)
            ttl: Durée de vie en secondes (optionnel, utilise la valeur par défaut si non spécifié)
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        cache_data = {
            'data': data,
            'expires_at': expires_at,
            'cached_at': time.time(),
            'ttl': ttl
        }
        
        # Mettre en cache sur disque
        if self.use_disk_cache:
            cache_path = self._get_cache_path(key)
            
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            except IOError as e:
                # Log l'erreur mais ne pas échouer
                print(f"Erreur lors de l'écriture dans le cache disque: {e}")
        
        # TODO: Implémenter le cache en base de données
        # if self.use_db_cache:
        #     pass
    
    async def clear_expired(self) -> int:
        """Supprime les entrées de cache expirées.
        
        Returns:
            Nombre d'entrées supprimées
        """
        count = 0
        
        # Nettoyer le cache disque
        if self.use_disk_cache and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if 'expires_at' in cache_data and cache_data['expires_at'] < time.time():
                        cache_file.unlink()
                        count += 1
                except (json.JSONDecodeError, IOError):
                    # Supprimer les fichiers corrompus
                    cache_file.unlink()
                    count += 1
        
        # TODO: Nettoyer le cache en base de données
        
        return count
    
    async def clear_all(self) -> int:
        """Vide complètement le cache.
        
        Returns:
            Nombre d'entrées supprimées
        """
        count = 0
        
        # Vider le cache disque
        if self.use_disk_cache and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    cache_file.unlink()
                    count += 1
                except OSError:
                    pass
        
        # TODO: Vider le cache en base de données
        
        return count
