"""Client pour l'API Guild Wars 2.

Ce module fournit une interface pour interagir avec l'API officielle de Guild Wars 2,
en gérant la mise en cache, la limitation de débit et la gestion des erreurs.
"""

import asyncio
import aiohttp
import aiofiles
import json
import logging
import time
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Type, Callable, Awaitable
from urllib.parse import urlencode, urljoin

from .config import settings

# Type générique pour les réponses de l'API
T = TypeVar('T')

logger = logging.getLogger(__name__)

class GW2APIError(Exception):
    """Exception de base pour les erreurs de l'API GW2."""
    pass

class RateLimitExceeded(GW2APIError):
    """Exception levée lorsque la limite de taux est dépassée."""
    pass

class APIUnavailable(GW2APIError):
    """Exception levée lorsque l'API est indisponible."""
    pass

class NotFoundError(GW2APIError):
    """Exception levée lorsqu'une ressource n'est pas trouvée."""
    pass

class GW2APIClient:
    """Client pour interagir avec l'API Guild Wars 2."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialise le client API.
        
        Args:
            session: Session HTTP à utiliser (optionnel)
        """
        self._session = session
        self._last_request_time = 0
        self._rate_limit_semaphore = asyncio.Semaphore(settings.requests_per_second)
        self._cache: Dict[str, Dict] = {}
        
        # Créer le répertoire de cache s'il n'existe pas
        if settings.cache_enabled and settings.cache_dir:
            os.makedirs(settings.cache_dir, exist_ok=True)
    
    async def _ensure_session(self) -> None:
        """S'assure qu'une session HTTP est disponible."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=settings.headers)
    
    async def close(self) -> None:
        """Ferme la session HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def __del__(self):
        """Nettoyage à la destruction de l'instance."""
        if self._session and not self._session.closed:
            if self._session._connector is not None and self._session._connector_owner:
                self._session._connector._close()
            self._session._connector = None
    
    async def _get_cache_path(self, cache_key: str) -> Path:
        """Génère un chemin de fichier de cache à partir d'une clé."""
        # Créer un hachage de la clé pour le nom de fichier
        cache_hash = hashlib.md5(cache_key.encode('utf-8')).hexdigest()
        return Path(settings.cache_dir) / f"{cache_hash}.json"
    
    async def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Charge des données depuis le cache disque."""
        if not settings.cache_enabled or not settings.cache_dir:
            return None
        
        cache_path = await self._get_cache_path(cache_key)
        
        # Vérifier si le fichier de cache existe et n'est pas expiré
        if cache_path.exists():
            file_stat = cache_path.stat()
            if time.time() - file_stat.st_mtime < settings.cache_ttl:
                try:
                    async with aiofiles.open(cache_path, 'r', encoding='utf-8') as f:
                        data = json.loads(await f.read())
                        if settings.log_requests:
                            logger.debug(f"Données chargées depuis le cache: {cache_key}")
                        return data
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Erreur lors de la lecture du cache {cache_path}: {e}")
                    # Supprimer le fichier de cache corrompu
                    try:
                        cache_path.unlink()
                    except OSError:
                        pass
        
        return None
    
    async def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """Enregistre des données dans le cache disque."""
        if not settings.cache_enabled or not settings.cache_dir:
            return
        
        cache_path = await self._get_cache_path(cache_key)
        
        try:
            # Créer le répertoire parent si nécessaire
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire les données dans le fichier de cache
            async with aiofiles.open(cache_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
            if settings.log_requests:
                logger.debug(f"Données enregistrées dans le cache: {cache_key}")
                
        except (OSError, TypeError) as e:
            logger.error(f"Erreur lors de l'écriture dans le cache {cache_path}: {e}")
    
    async def _rate_limit(self) -> None:
        """Applique la limitation de débit (rate limiting)."""
        if not settings.rate_limit_enabled:
            return
        
        async with self._rate_limit_semaphore:
            now = time.time()
            elapsed = now - self._last_request_time
            
            # Attendre si nécessaire pour respecter la limite de débit
            if elapsed < 1.0 / settings.requests_per_second:
                wait_time = (1.0 / settings.requests_per_second) - elapsed
                if settings.log_requests:
                    logger.debug(f"Attente de {wait_time:.3f}s pour respecter la limite de débit")
                await asyncio.sleep(wait_time)
            
            self._last_request_time = time.time()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_key_extra: str = "",
        **kwargs
    ) -> Any:
        """Effectue une requête HTTP vers l'API GW2.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Point de terminaison de l'API (sans la base URL)
            params: Paramètres de requête
            use_cache: Si True, utilise le cache si disponible
            cache_key_extra: Chaîne supplémentaire pour la clé de cache
            **kwargs: Arguments supplémentaires pour aiohttp.request
            
        Returns:
            La réponse désérialisée de l'API
            
        Raises:
            RateLimitExceeded: Si la limite de taux est dépassée
            APIUnavailable: Si l'API est indisponible
            NotFoundError: Si la ressource demandée n'existe pas
            GW2APIError: Pour les autres erreurs de l'API
        """
        await self._ensure_session()
        
        # Construire l'URL complète
        url = urljoin(settings.base_url, endpoint.lstrip('/'))
        
        # Préparer les paramètres de requête
        params = params or {}
        
        # Créer une clé de cache unique pour cette requête
        cache_key = f"{method}:{endpoint}:{urlencode(sorted(params.items()))}:{cache_key_extra}"
        
        # Essayer de charger depuis le cache si activé
        if use_cache and method.upper() == 'GET':
            cached_data = await self._load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Appliquer la limitation de débit
        await self._rate_limit()
        
        # Journalisation de la requête
        if settings.log_requests:
            logger.info(f"Requête {method.upper()} vers {url} avec paramètres: {params}")
        
        # Effectuer la requête avec gestion des réessais
        last_error = None
        
        for attempt in range(settings.max_retries + 1):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=settings.request_timeout,
                    **kwargs
                ) as response:
                    # Journalisation de la réponse
                    if settings.log_responses:
                        logger.debug(f"Réponse de {url}: {response.status}")
                    
                    # Gérer les erreurs HTTP
                    if response.status == 429:  # Too Many Requests
                        retry_after = float(response.headers.get('Retry-After', '1'))
                        if attempt < settings.max_retries:
                            logger.warning(
                                f"Limite de débit dépassée, nouvel essai dans {retry_after}s "
                                f"(tentative {attempt + 1}/{settings.max_retries})"
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise RateLimitExceeded(
                                f"Limite de débit dépassée après {settings.max_retries} tentatives"
                            )
                    
                    if response.status == 404:  # Not Found
                        raise NotFoundError(f"Ressource non trouvée: {endpoint}")
                    
                    if response.status >= 500:  # Erreurs serveur
                        if attempt < settings.max_retries:
                            logger.warning(
                                f"Erreur serveur {response.status}, nouvel essai... "
                                f"(tentative {attempt + 1}/{settings.max_retries})"
                            )
                            await asyncio.sleep(settings.retry_delay * (2 ** attempt))
                            continue
                        else:
                            raise APIUnavailable(
                                f"Erreur serveur {response.status} après {settings.max_retries} tentatives"
                            )
                    
                    # Pour les autres erreurs, lever une exception
                    response.raise_for_status()
                    
                    # Lire et parser la réponse
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    # Mettre en cache la réponse si nécessaire
                    if use_cache and method.upper() == 'GET' and response.status == 200:
                        await self._save_to_cache(cache_key, data)
                    
                    return data
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < settings.max_retries:
                    logger.warning(
                        f"Erreur de connexion: {e}, nouvel essai... "
                        f"(tentative {attempt + 1}/{settings.max_retries})"
                    )
                    await asyncio.sleep(settings.retry_delay * (2 ** attempt))
                else:
                    raise APIUnavailable(
                        f"Échec après {settings.max_retries} tentatives: {e}"
                    ) from e
        
        # Si on arrive ici, toutes les tentatives ont échoué
        raise last_error or GW2APIError("Échec inconnu de la requête API")
    
    # Méthodes pratiques pour les requêtes HTTP courantes
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_key_extra: str = "",
        **kwargs
    ) -> Any:
        """Effectue une requête GET vers l'API GW2."""
        return await self._make_request(
            'GET', endpoint, params=params, use_cache=use_cache,
            cache_key_extra=cache_key_extra, **kwargs
        )
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Effectue une requête POST vers l'API GW2."""
        return await self._make_request('POST', endpoint, json=data, **kwargs)
    
    # Méthodes pour les endpoints spécifiques de l'API GW2
    
    async def get_build(self) -> Dict[str, Any]:
        """Récupère les informations de build actuelles du jeu."""
        return await self.get('/v2/build')
    
    async def get_items(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Récupère les détails des objets spécifiés."""
        if not item_ids:
            return []
        
        # L'API GW2 a une limite de 200 IDs par requête
        chunk_size = 200
        results = []
        
        for i in range(0, len(item_ids), chunk_size):
            chunk = item_ids[i:i + chunk_size]
            items = await self.get('/v2/items', params={'ids': ','.join(map(str, chunk))})
            results.extend(items)
        
        return results
        
    async def get_itemstats(self, stat_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Récupère les statistiques d'objets spécifiées ou toutes si aucun ID n'est fourni.
        
        Args:
            stat_ids: Liste des IDs de statistiques à récupérer. Si None, récupère toutes les statistiques.
            
        Returns:
            Une liste de dictionnaires contenant les données des statistiques demandées.
        """
        if stat_ids is None:
            # Récupérer tous les IDs de statistiques disponibles
            stat_ids = await self.get('/v2/itemstats')
            if not stat_ids:
                return []
        
        # L'API GW2 a une limite de 200 IDs par requête
        chunk_size = 200
        results = []
        
        for i in range(0, len(stat_ids), chunk_size):
            chunk = stat_ids[i:i + chunk_size]
            stats = await self.get('/v2/itemstats', params={'ids': ','.join(map(str, chunk))})
            results.extend(stats)
        
        return results
    
    async def get_skills(self, skill_ids: List[int]) -> List[Dict[str, Any]]:
        """Récupère les détails des compétences spécifiées."""
        if not skill_ids:
            return []
        
        chunk_size = 200
        results = []
        
        for i in range(0, len(skill_ids), chunk_size):
            chunk = skill_ids[i:i + chunk_size]
            skills = await self.get('/v2/skills', params={'ids': ','.join(map(str, chunk))})
            results.extend(skills)
        
        return results
    
    async def get_traits(self, trait_ids: List[int]) -> List[Dict[str, Any]]:
        """Récupère les détails des traits spécifiés."""
        if not trait_ids:
            return []
        
        chunk_size = 200
        results = []
        
        for i in range(0, len(trait_ids), chunk_size):
            chunk = trait_ids[i:i + chunk_size]
            traits = await self.get('/v2/traits', params={'ids': ','.join(map(str, chunk))})
            results.extend(traits)
        
        return results
    
    async def get_specializations(self, spec_ids: List[int]) -> List[Dict[str, Any]]:
        """Récupère les détails des spécialisations spécifiées."""
        if not spec_ids:
            return []
        
        chunk_size = 200
        results = []
        
        for i in range(0, len(spec_ids), chunk_size):
            chunk = spec_ids[i:i + chunk_size]
            specs = await self.get('/v2/specializations', params={'ids': ','.join(map(str, chunk))})
            results.extend(specs)
        
        return results
    
    async def get_professions(self) -> List[str]:
        """Récupère la liste de toutes les professions."""
        return await self.get('/v2/professions')
    
    async def get_profession(self, profession_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une profession spécifique."""
        return await self.get(f'/v2/professions/{profession_id}')
    
    # Méthodes pour la gestion du cache
    
    async def clear_cache(self, prefix: str = "") -> int:
        """Vide le cache, éventuellement filtré par préfixe.
        
        Args:
            prefix: Préfixe des clés de cache à supprimer (vide pour tout supprimer)
            
        Returns:
            Nombre de fichiers de cache supprimés
        """
        if not settings.cache_enabled or not settings.cache_dir:
            return 0
        
        cache_dir = Path(settings.cache_dir)
        if not cache_dir.exists():
            return 0
        
        deleted = 0
        for cache_file in cache_dir.glob("*.json"):
            if not prefix or cache_file.name.startswith(prefix):
                try:
                    cache_file.unlink()
                    deleted += 1
                except OSError as e:
                    logger.error(f"Erreur lors de la suppression du cache {cache_file}: {e}")
        
        if deleted > 0 and settings.log_requests:
            logger.info(f"Cache vidé: {deleted} fichiers supprimés")
        
        return deleted
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Retourne des informations sur l'état du cache."""
        if not settings.cache_enabled or not settings.cache_dir:
            return {"enabled": False}
        
        cache_dir = Path(settings.cache_dir)
        if not cache_dir.exists():
            return {"enabled": True, "cache_dir": str(cache_dir), "count": 0}
        
        cache_files = list(cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
        
        return {
            "enabled": True,
            "cache_dir": str(cache_dir),
            "count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }
