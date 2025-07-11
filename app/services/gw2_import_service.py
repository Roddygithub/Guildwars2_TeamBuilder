"""Service d'importation des données depuis l'API GW2."""

import logging
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Callable
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.config import settings
from app.core.exceptions import ValidationError, ImportError
from app.core.logging import setup_logger
from app.models.base import Base
from app.services.mapping.gw2_api_mapper import GW2APIMapper

# Configuration du logger
logger = setup_logger(__name__)

# Type générique pour les modèles SQLAlchemy
T = TypeVar('T', bound=Base)

class GW2ImportService(Generic[T]):
    """Service de base pour l'importation des données depuis l'API GW2."""
    
    # URL de base de l'API GW2 v2
    API_BASE_URL = "https://api.guildwars2.com/v2"
    
    # Dossier de cache pour les réponses de l'API
    CACHE_DIR = Path("data/cache/gw2api")
    
    def __init__(self, model_class: Type[T], endpoint: str, language: str = "en"):
        """
        Initialise le service d'importation pour un modèle spécifique.
        
        Args:
            model_class: La classe du modèle SQLAlchemy à utiliser
            endpoint: Le point de terminaison de l'API GW2 (ex: 'traits', 'skills')
            language: La langue à utiliser pour les données localisées (fr, en, de, es, etc.)
        """
        self.model_class = model_class
        self.endpoint = endpoint
        self.language = language
        self.cache_dir = self.CACHE_DIR / endpoint
        
        # Créer le répertoire de cache s'il n'existe pas
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_all_ids(self, use_cache: bool = True) -> List[int]:
        """
        Récupère tous les IDs disponibles pour ce point de terminaison.
        
        Args:
            use_cache: Si True, utilise le cache local si disponible
            
        Returns:
            Liste des IDs disponibles
            
        Raises:
            ImportError: Si la récupération des IDs échoue
        """
        cache_file = self.cache_dir / "all_ids.json"
        
        # Vérifier le cache
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Erreur lors de la lecture du cache des IDs: {e}")
        
        # Récupérer les IDs depuis l'API
        try:
            url = f"{self.API_BASE_URL}/{self.endpoint}"
            logger.debug(f"Récupération des IDs depuis {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            ids = response.json()
            
            # Mettre en cache le résultat
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(ids, f, ensure_ascii=False, indent=2)
            except OSError as e:
                logger.warning(f"Impossible d'écrire dans le cache: {e}")
            
            return ids
            
        except requests.RequestException as e:
            error_msg = f"Échec de la récupération des IDs depuis l'API GW2: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg) from e
    
    def get_by_id(self, id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Récupère les données d'un élément spécifique par son ID.
        
        Args:
            id: L'ID de l'élément à récupérer
            use_cache: Si True, utilise le cache local si disponible
            
        Returns:
            Dictionnaire contenant les données de l'élément
            
        Raises:
            ImportError: Si la récupération des données échoue
        """
        cache_file = self.cache_dir / f"{id}.json"
        
        # Vérifier le cache
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Erreur lors de la lecture du cache pour l'ID {id}: {e}")
        
        # Récupérer les données depuis l'API
        try:
            url = f"{self.API_BASE_URL}/{self.endpoint}/{id}?lang={self.language}"
            logger.debug(f"Récupération des données pour l'ID {id} depuis {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Mettre en cache le résultat
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except OSError as e:
                logger.warning(f"Impossible d'écrire dans le cache pour l'ID {id}: {e}")
            
            return data
            
        except requests.RequestException as e:
            error_msg = f"Échec de la récupération des données pour l'ID {id}: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg) from e
    
    def import_all(self, db: Session, batch_size: int = 50) -> Dict[str, int]:
        """
        Importe ou met à jour tous les éléments depuis l'API GW2.
        
        Args:
            db: Session de base de données SQLAlchemy
            batch_size: Nombre d'éléments à traiter par lot
            
        Returns:
            Dictionnaire avec les statistiques d'importation
        """
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
        }
        
        try:
            # Initialiser le mapper
            mapper = GW2APIMapper(db)
            
            # Récupérer tous les IDs disponibles
            ids = self.get_all_ids()
            stats['total'] = len(ids)
            
            logger.info(f"Début de l'importation de {stats['total']} {self.endpoint}")
            
            # Traiter les éléments par lots
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i + batch_size]
                logger.debug(f"Traitement du lot {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
                
                for id in batch:
                    try:
                        # Récupérer les données depuis l'API
                        data = self.get_by_id(id)
                        
                        # Utiliser le mapper pour convertir les données en modèle
                        instance = self._map_with_mapper(mapper, data)
                        
                        # Vérifier si l'élément existe déjà
                        existing = db.query(self.model_class).get(id)
                        
                        if existing:
                            # Mettre à jour l'instance existante
                            self._update_existing(existing, instance)
                            stats['updated'] += 1
                        else:
                            # Ajouter la nouvelle instance
                            db.add(instance)
                            stats['created'] += 1
                        
                        # Valider et sauvegarder les modifications
                        db.commit()
                        
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Erreur lors de l'importation de l'ID {id}: {e}", exc_info=True)
                        stats['errors'] += 1
                        
                        # En cas d'erreur, attendre un peu avant de réessayer
                        time.sleep(1)
                
                # Petite pause entre les lots pour éviter de surcharger l'API
                time.sleep(0.5)
            
            logger.info(
                f"Importation terminée: {stats['created']} créés, "
                f"{stats['updated']} mis à jour, {stats['errors']} erreurs"
            )
            
            return stats
            
        except Exception as e:
            db.rollback()
            error_msg = f"Erreur critique lors de l'importation: {e}"
            logger.error(error_msg, exc_info=True)
            raise ImportError(error_msg) from e
    
    def _map_with_mapper(self, mapper: GW2APIMapper, data: Dict[str, Any]) -> T:
        """
        Utilise le GW2APIMapper pour convertir les données de l'API en modèle.
        
        Cette méthode doit être surchargée par les classes filles.
        """
        raise NotImplementedError("La méthode _map_with_mapper doit être implémentée par les classes filles")
    
    def _update_existing(self, existing: T, new_data: T) -> None:
        """
        Met à jour une instance existante avec de nouvelles données.
        
        Args:
            existing: Instance existante à mettre à jour
            new_data: Nouvelles données à appliquer
        ""
        for key, value in new_data.__dict__.items():
            if not key.startswith('_'):  # Ignorer les attributs privés
                setattr(existing, key, value)


class ProfessionImportService(GW2ImportService):
    """Service d'importation pour les professions."""
    
    def __init__(self, language: str = "en"):
        from app.models.profession import Profession
        super().__init__(Profession, 'professions', language)
    
    def _map_with_mapper(self, mapper: GW2APIMapper, data: Dict[str, Any]) -> Any:
        """Utilise le mapper pour convertir les données en modèle Profession."""
        return mapper.map_profession(data)


class SpecializationImportService(GW2ImportService):
    """Service d'importation pour les spécialisations."""
    
    def __init__(self, language: str = "en"):
        from app.models.specialization import Specialization
        super().__init__(Specialization, 'specializations', language)
    
    def _map_with_mapper(self, mapper: GW2APIMapper, data: Dict[str, Any]) -> Any:
        """Utilise le mapper pour convertir les données en modèle Specialization."""
        return mapper.map_specialization(data)


class TraitImportService(GW2ImportService):
    """Service d'importation pour les traits."""
    
    def __init__(self, language: str = "en"):
        from app.models.trait import Trait
        super().__init__(Trait, 'traits', language)
    
    def _map_with_mapper(self, mapper: GW2APIMapper, data: Dict[str, Any]) -> Any:
        """Utilise le mapper pour convertir les données en modèle Trait."""
        return mapper.map_trait(data)


class SkillImportService(GW2ImportService):
    """Service d'importation pour les compétences."""
    
    def __init__(self, language: str = "en"):
        from app.models.skill import Skill
        super().__init__(Skill, 'skills', language)
    
    def _map_with_mapper(self, mapper: GW2APIMapper, data: Dict[str, Any]) -> Any:
        """Utilise le mapper pour convertir les données en modèle Skill."""
        return mapper.map_skill(data)


class ItemStatsImportService(GW2ImportService):
    """Service d'importation pour les statistiques d'objets."""
    
    def __init__(self, language: str = "en"):
        from app.models.item import ItemStats
        super().__init__(ItemStats, 'itemstats', language)
    
    def _map_with_mapper(self, mapper: GW2APIMapper, data: Dict[str, Any]) -> Any:
        """Utilise le mapper pour convertir les données en modèle ItemStats."""
        return mapper.map_itemstat(data)


def import_all_data(db: Session, language: str = "en") -> Dict[str, Dict[str, int]]:
    """
    Importe toutes les données depuis l'API GW2.
    
    Args:
        db: Session de base de données
        language: Langue à utiliser pour les données localisées
        
    Returns:
        Dictionnaire avec les statistiques d'importation par type de données
    """
    import_services = [
        ProfessionImportService(language),
        SpecializationImportService(language),
        TraitImportService(language),
        SkillImportService(language),
        ItemStatsImportService(language),
    ]
    
    results = {}
    
    for service in import_services:
        try:
            logger.info(f"Début de l'importation des {service.endpoint}")
            stats = service.import_all(db)
            results[service.endpoint] = stats
            logger.info(f"Importation des {service.endpoint} terminée: {stats}")
        except Exception as e:
            logger.error(f"Échec de l'importation des {service.endpoint}: {e}", exc_info=True)
            results[service.endpoint] = {"error": str(e)}
    
    return results
