"""Service pour la gestion des données GW2.

Ce service fournit une interface de haut niveau pour accéder et manipuler
les données de Guild Wars 2, en utilisant le cache local et l'API officielle.
"""

import asyncio
import json
import logging
import uuid
import pickle
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple, Union, TypeVar, Type
from functools import wraps

# Pour la gestion du cache distribué
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    import warnings
    warnings.warn("Le module redis n'est pas installé. Le cache distribué ne sera pas disponible.")

# Type générique pour les méthodes de cache
T = TypeVar('T')

def redis_cache(
    key_func: Optional[Callable[..., str]] = None,
    ttl: int = 86400,  # 24h par défaut
    prefix: str = "gw2tb:",
    compress: bool = True
) -> Callable:
    """Décorateur pour mettre en cache le résultat d'une méthode avec Redis.
    
    Args:
        key_func: Fonction pour générer la clé de cache à partir des arguments
        ttl: Durée de vie du cache en secondes
        prefix: Préfixe pour les clés de cache
        compress: Si True, compresse les données avec pickle
        
    Returns:
        Le décorateur à appliquer à la méthode
    """
    def decorator(method: Callable[..., T]) -> Callable[..., T]:
        @wraps(method)
        async def wrapper(self, *args, **kwargs) -> T:
            # Si Redis n'est pas disponible, on exécute simplement la méthode
            if not hasattr(self, 'redis_client') or self.redis_client is None:
                return await method(self, *args, **kwargs)
                
            # Générer la clé de cache
            if key_func is not None:
                cache_key = f"{prefix}{key_func(*args, **kwargs)}"
            else:
                # Par défaut, on utilise le nom de la méthode et les arguments
                cache_key = f"{prefix}{method.__name__}:{str(args)}:{str(kwargs)}"
            
            try:
                # Essayer de récupérer depuis le cache
                cached_data = await self.redis_client.get(cache_key)
                if cached_data is not None:
                    if compress:
                        cached_data = pickle.loads(cached_data)
                    logger.debug(f"Cache hit pour la clé: {cache_key}")
                    return cached_data
                    
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du cache Redis: {e}")
            
            # Si le cache est vide ou en cas d'erreur, exécuter la méthode
            result = await method(self, *args, **kwargs)
            
            try:
                # Mettre en cache le résultat
                if result is not None:
                    value = pickle.dumps(result) if compress else str(result)
                    await self.redis_client.setex(cache_key, ttl, value)
                    logger.debug(f"Résultat mis en cache avec la clé: {cache_key} (TTL: {ttl}s)")
                    
            except Exception as e:
                logger.warning(f"Erreur lors de l'écriture dans le cache Redis: {e}")
            
            return result
            
        return wrapper
    return decorator
import os

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.api import GW2APIClient, GW2APIError, configure_api
from app.database import get_db, Base, engine
from app.models import (
    Profession, Specialization, Skill, Trait, 
    Weapon, Armor, Trinket, UpgradeComponent,
    ItemStats, ItemStat, Item, ItemType
)
from app.game_mechanics import (
    GameMode, RoleType, AttributeType, DamageType, 
    BuffType, BoonType, ConditionType, SkillCategory
)

logger = logging.getLogger(__name__)

class GW2DataService:
    """Service pour la gestion des données GW2."""
    
    def __init__(self, db_session: Optional[Session] = None, api_client: Optional[GW2APIClient] = None):
        """Initialise le service de données GW2.
        
        Args:
            db_session: Session SQLAlchemy (optionnel)
            api_client: Client API GW2 (optionnel)
        """
        self._db = db_session
        self._api = api_client or GW2APIClient()
        self._initialized = False
    
    @property
    def db(self) -> Session:
        """Retourne une session de base de données."""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    async def initialize(self) -> None:
        """Initialise le service (vérifie la connexion à l'API, etc.)."""
        if self._initialized:
            return
        
        try:
            # Vérifier la connexion à l'API
            build_info = await self._api.get_build()
            logger.info(f"Connecté à l'API GW2 (build {build_info.get('id')})")
            
            # Vérifier la connexion à la base de données
            self.db.execute(text("SELECT 1"))
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service GW2Data: {e}")
            raise
    
    async def close(self) -> None:
        """Ferme les ressources du service."""
        if self._api:
            await self._api.close()
        
        if self._db:
            try:
                self._db.close()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de la session DB: {e}")
    
    # Méthodes pour la synchronisation des données
    
    async def sync_all_data(self, force: bool = False) -> Dict[str, Any]:
        """Synchronise toutes les données depuis l'API GW2.
        
        Args:
            force: Si True, force la synchronisation même si les données sont à jour
            
        Returns:
            Un dictionnaire avec les résultats de la synchronisation
        """
        results = {}
        
        try:
            # Vérifier si la synchronisation est nécessaire
            if not force and not await self._needs_sync():
                logger.info("Les données sont à jour, pas besoin de synchronisation")
                return {"status": "up_to_date", "message": "Les données sont déjà à jour"}
            
            # Synchroniser les données de base dans l'ordre de dépendance
            results["professions"] = await self.sync_professions()
            results["specializations"] = await self.sync_specializations()
            results["skills"] = await self.sync_skills()
            results["traits"] = await self.sync_traits()
            results["items"] = await self.sync_items()
            results["item_stats"] = await self.sync_itemstats()
            
            # Mettre à jour la date de dernière synchronisation
            await self._update_last_sync_time()
            
            logger.info("Synchronisation des données GW2 terminée avec succès")
            results["status"] = "success"
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des données GW2: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            raise
        
        return results
    
    async def _needs_sync(self) -> bool:
        """Vérifie si une synchronisation est nécessaire."""
        # TODO: Implémenter la logique pour vérifier si une synchronisation est nécessaire
        # Par exemple, vérifier la date de dernière synchronisation
        return True
    
    async def _update_last_sync_time(self) -> None:
        """Met à jour l'horodatage de la dernière synchronisation."""
        # TODO: Implémenter la mise à jour de l'horodatage de synchronisation
        pass
    
    # Méthodes pour la synchronisation des professions
    
    async def sync_professions(self) -> Dict[str, Any]:
        """Synchronise les données des professions depuis l'API GW2."""
        logger.info("Début de la synchronisation des professions...")
        
        try:
            # Récupérer la liste des professions depuis l'API
            profession_ids = await self._api.get_professions()
            
            # Récupérer les détails de chaque profession
            professions_data = []
            for prof_id in profession_ids:
                try:
                    prof_data = await self._api.get_profession(prof_id)
                    professions_data.append(prof_data)
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération de la profession {prof_id}: {e}")
            
            # Traiter les données des professions
            processed = 0
            for prof_data in professions_data:
                try:
                    await self._process_profession_data(prof_data)
                    processed += 1
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la profession {prof_data.get('id')}: {e}")
            
            logger.info(f"Synchronisation des professions terminée: {processed}/{len(professions_data)} traitées")
            return {
                "total": len(professions_data),
                "processed": processed,
                "status": "success" if processed > 0 else "error"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des professions: {e}", exc_info=True)
            return {
                "total": 0,
                "processed": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def _process_profession_data(self, prof_data: Dict[str, Any]) -> Profession:
        """Traite les données d'une profession et les enregistre en base."""
        db = self.db
        
        # Vérifier si la profession existe déjà
        profession = db.query(Profession).filter_by(id=prof_data['id']).first()
        
        if not profession:
            profession = Profession(id=prof_data['id'])
            db.add(profession)
        
        # Mettre à jour les propriétés de base
        profession.name = prof_data.get('name', '')
        profession.icon = prof_data.get('icon')
        profession.icon_big = prof_data.get('icon_big')
        profession.weapon_skills = prof_data.get('weapons', {})
        profession.flags = prof_data.get('flags', [])
        profession.specializations = prof_data.get('specializations', [])
        profession.training = prof_data.get('training', [])
        profession.skills = prof_data.get('skills', [])
        
        # Extraire et traiter les armes de la profession
        weapon_data = prof_data.get('weapons', {})
        if weapon_data:
            # TODO: Traiter les données des armes spécifiques à la profession
            pass
        
        db.commit()
        return profession
    
    # Méthodes pour la synchronisation des spécialisations
    
    async def sync_specializations(self) -> Dict[str, Any]:
        """Synchronise les données des spécialisations depuis l'API GW2."""
        logger.info("Début de la synchronisation des spécialisations...")
        
        try:
            # Récupérer les IDs de toutes les spécialisations
            spec_ids = await self._get_all_specialization_ids()
            
            # Récupérer les détails de chaque spécialisation
            specs_data = await self._api.get_specializations(spec_ids)
            
            # Traiter les données des spécialisations
            processed = 0
            for spec_data in specs_data:
                try:
                    await self._process_specialization_data(spec_data)
                    processed += 1
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la spécialisation {spec_data.get('id')}: {e}")
            
            logger.info(f"Synchronisation des spécialisations terminée: {processed}/{len(specs_data)} traitées")
            return {
                "total": len(specs_data),
                "processed": processed,
                "status": "success" if processed > 0 else "error"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des spécialisations: {e}", exc_info=True)
            return {
                "total": 0,
                "processed": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def _get_all_specialization_ids(self) -> List[int]:
        """Récupère les IDs de toutes les spécialisations via les professions."""
        # Récupérer d'abord toutes les professions
        profession_ids = await self._api.get_professions()
        all_spec_ids = set()
        
        # Pour chaque profession, récupérer les IDs de spécialisation
        for prof_id in profession_ids:
            try:
                prof_data = await self._api.get_profession(prof_id)
                for spec_type in ["specializations", "training"]:
                    for item in prof_data.get(spec_type, []):
                        if "id" in item:
                            all_spec_ids.add(item["id"])
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des spécialisations pour {prof_id}: {e}")
        
        return list(all_spec_ids)
    
    async def _process_specialization_data(self, spec_data: Dict[str, Any]) -> Specialization:
        """Traite les données d'une spécialisation et les enregistre en base."""
        db = self.db
        
        # Vérifier si la spécialisation existe déjà
        spec = db.query(Specialization).filter_by(id=spec_data['id']).first()
        
        if not spec:
            spec = Specialization(id=spec_data['id'])
            db.add(spec)
        
        # Mettre à jour les propriétés de base
        spec.name = spec_data.get('name', '')
        spec.profession = spec_data.get('profession')
        spec.elite = spec_data.get('elite', False)
        spec.icon = spec_data.get('icon')
        spec.background = spec_data.get('background')
        spec.minor_traits = spec_data.get('minor_traits', [])
        spec.major_traits = spec_data.get('major_traits', [])
        spec.weapon_trait = spec_data.get('weapon_trait')
        
        db.commit()
        return spec
    
    # Méthodes pour la synchronisation des compétences et traits
    
    async def sync_skills(self) -> Dict[str, Any]:
        """Synchronise les données des compétences depuis l'API GW2.
        
        Returns:
            Un dictionnaire contenant les résultats de la synchronisation
        """
        logger.info("Début de la synchronisation des compétences...")
        
        try:
            # Récupérer tous les IDs de compétences depuis l'API
            skill_ids = await self._api.get('/v2/skills')
            
            if not skill_ids:
                logger.warning("Aucune compétence trouvée dans l'API GW2")
                return {"total": 0, "processed": 0, "status": "error", "error": "Aucune compétence trouvée"}
            
            logger.info(f"Récupération des détails pour {len(skill_ids)} compétences...")
            
            # Récupérer les détails des compétences par lots
            chunk_size = 200  # Limite de l'API GW2
            processed = 0
            errors = 0
            
            for i in range(0, len(skill_ids), chunk_size):
                chunk = skill_ids[i:i + chunk_size]
                
                try:
                    # Récupérer les détails du lot actuel
                    skills_data = await self._api.get_skills(chunk)
                    
                    # Traiter chaque compétence du lot
                    for skill_data in skills_data:
                        try:
                            await self._process_skill_data(skill_data)
                            processed += 1
                            
                            # Journaliser la progression tous les 50 éléments
                            if processed % 50 == 0:
                                logger.info(f"Traitement en cours: {processed}/{len(skill_ids)} compétences")
                                
                        except Exception as e:
                            errors += 1
                            logger.error(f"Erreur lors du traitement de la compétence {skill_data.get('id')}: {e}")
                            
                except Exception as e:
                    errors += 1
                    logger.error(f"Erreur lors de la récupération du lot de compétences: {e}")
            
            # Journaliser les résultats
            logger.info(f"Synchronisation des compétences terminée: {processed} traitées, {errors} erreurs")
            
            return {
                "total": len(skill_ids),
                "processed": processed,
                "errors": errors,
                "status": "success" if errors == 0 else "partial" if processed > 0 else "error"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des compétences: {e}", exc_info=True)
            return {
                "total": 0,
                "processed": 0,
                "errors": 1,
                "status": "error",
                "error": str(e)
            }
    
    async def _process_skill_data(self, skill_data: Dict[str, Any]) -> Skill:
        """Traite les données d'une compétence et les enregistre en base.
        
        Args:
            skill_data: Données brutes de la compétence depuis l'API
            
        Returns:
            L'objet Skill créé ou mis à jour
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        
        db = self.db
        mapper = GW2APIMapper(db)
        
        try:
            # Convertir les données de l'API en modèle interne
            skill = mapper.map_skill(skill_data)
            
            # Valider que les champs obligatoires sont présents
            if not skill.name or not skill.type:
                raise ValueError(f"Données de compétence invalides: champs obligatoires manquants dans {skill_data}")
            
            # Sauvegarder les modifications
            db.commit()
            
            # Journaliser la création/mise à jour
            logger.debug(f"Compétence {'mise à jour' if skill.id else 'créée'}: {skill.name} (ID: {skill.id})")
            
            return skill
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            db.rollback()
            logger.error(f"Erreur lors du traitement de la compétence {skill_data.get('id')}: {e}")
            raise
    
    async def sync_traits(self) -> Dict[str, Any]:
        """Synchronise les données des traits depuis l'API GW2.
        
        Returns:
            Un dictionnaire contenant les résultats de la synchronisation
        """
        logger.info("Début de la synchronisation des traits...")
        
        try:
            # Récupérer tous les IDs de traits depuis l'API
            trait_ids = await self._api.get('/v2/traits')
            
            if not trait_ids:
                logger.warning("Aucun trait trouvé dans l'API GW2")
                return {"total": 0, "processed": 0, "status": "error", "error": "Aucun trait trouvé"}
            
            logger.info(f"Récupération des détails pour {len(trait_ids)} traits...")
            
            # Récupérer les détails des traits par lots
            chunk_size = 200  # Limite de l'API GW2
            processed = 0
            errors = 0
            
            for i in range(0, len(trait_ids), chunk_size):
                chunk = trait_ids[i:i + chunk_size]
                
                try:
                    # Récupérer les détails du lot actuel
                    traits_data = await self._api.get_traits(chunk)
                    
                    # Traiter chaque trait du lot
                    for trait_data in traits_data:
                        try:
                            await self._process_trait_data(trait_data)
                            processed += 1
                            
                            # Journaliser la progression tous les 50 éléments
                            if processed % 50 == 0:
                                logger.info(f"Traitement en cours: {processed}/{len(trait_ids)} traits")
                                
                        except Exception as e:
                            errors += 1
                            logger.error(f"Erreur lors du traitement du trait {trait_data.get('id')}: {e}")
                            
                except Exception as e:
                    errors += 1
                    logger.error(f"Erreur lors de la récupération du lot de traits: {e}")
            
            # Journaliser les résultats
            logger.info(f"Synchronisation des traits terminée: {processed} traités, {errors} erreurs")
            
            return {
                "total": len(trait_ids),
                "processed": processed,
                "errors": errors,
                "status": "success" if errors == 0 else "partial" if processed > 0 else "error"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des traits: {e}", exc_info=True)
            return {
                "total": 0,
                "processed": 0,
                "errors": 1,
                "status": "error",
                "error": str(e)
            }
    
    async def _process_trait_data(self, trait_data: Dict[str, Any]) -> 'Trait':
        """Traite les données d'un trait et les enregistre en base.
        
        Args:
            trait_data: Données brutes du trait depuis l'API
            
        Returns:
            L'objet Trait créé ou mis à jour
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        from app.models.trait import Trait
        
        db = self.db
        mapper = GW2APIMapper(db)
        
        try:
            # Convertir les données de l'API en modèle interne
            trait = mapper.map_trait(trait_data)
            
            # Valider que les champs obligatoires sont présents
            if not trait.name or not trait.type or not trait.tier:
                raise ValueError(f"Données de trait invalides: champs obligatoires manquants dans {trait_data}")
            
            # Sauvegarder les modifications
            db.commit()
            
            # Journaliser la création/mise à jour
            logger.debug(f"Trait {'mis à jour' if trait.id else 'créé'}: {trait.name} (ID: {trait.id})")
            
            return trait
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            db.rollback()
            logger.error(f"Erreur lors du traitement du trait {trait_data.get('id')}: {e}")
            raise
    
    # Méthodes pour la synchronisation des objets et statistiques
    
    async def sync_items(self) -> Dict[str, Any]:
        """Synchronise les données des objets depuis l'API GW2.
        
        Returns:
            Un dictionnaire contenant les résultats de la synchronisation
        """
        logger.info("Début de la synchronisation des objets...")
        
        try:
            # Récupérer tous les IDs d'objets depuis l'API
            item_ids = await self._api.get('/v2/items')
            
            if not item_ids:
                logger.warning("Aucun objet trouvé dans l'API GW2")
                return {"total": 0, "processed": 0, "status": "error", "error": "Aucun objet trouvé"}
            
            logger.info(f"Récupération des détails pour {len(item_ids)} objets...")
            
            # Récupérer les détails des objets par lots
            chunk_size = 200  # Limite de l'API GW2
            processed = 0
            errors = 0
            stats = {
                'weapons': 0,
                'armor': 0,
                'trinkets': 0,
                'upgrades': 0,
                'consumables': 0,
                'gizmos': 0,
                'tools': 0,
                'minis': 0,
                'other': 0
            }
            
            for i in range(0, len(item_ids), chunk_size):
                chunk = item_ids[i:i + chunk_size]
                
                try:
                    # Récupérer les détails du lot actuel
                    items_data = await self._api.get_items(chunk)
                    
                    # Traiter chaque objet du lot
                    for item_data in items_data:
                        try:
                            item_type = item_data.get('type', '').lower()
                            
                            # Dispatcher vers le bon gestionnaire selon le type d'objet
                            if item_type == 'weapon':
                                await self._process_weapon_data(item_data)
                                stats['weapons'] += 1
                            elif item_type == 'armor':
                                await self._process_armor_data(item_data)
                                stats['armor'] += 1
                            elif item_type in ['accessory', 'amulet', 'ring', 'back']:
                                await self._process_trinket_data(item_data)
                                stats['trinkets'] += 1
                            elif item_type in ['upgradecomponent', 'rune', 'sigil']:
                                await self._process_upgrade_component_data(item_data)
                                stats['upgrades'] += 1
                            elif item_type in ['consumable', 'food']:
                                await self._process_consumable_data(item_data)
                                stats['consumables'] += 1
                            elif item_type == 'gizmo':
                                await self._process_gizmo_data(item_data)
                                stats['gizmos'] += 1
                            elif item_type in ['tool', 'gathering']:
                                await self._process_tool_data(item_data)
                                stats['tools'] += 1
                            elif item_type == 'mini':
                                await self._process_mini_data(item_data)
                                stats['minis'] += 1
                            else:
                                # Pour les autres types d'objets, on les enregistre simplement
                                await self._process_generic_item_data(item_data)
                                stats['other'] += 1
                            
                            processed += 1
                            
                            # Journaliser la progression tous les 50 éléments
                            if processed % 50 == 0:
                                logger.info(f"Traitement en cours: {processed}/{len(item_ids)} objets")
                                
                        except Exception as e:
                            errors += 1
                            logger.error(f"Erreur lors du traitement de l'objet {item_data.get('id')} ({item_data.get('type', 'inconnu')}): {e}")
                            
                except Exception as e:
                    errors += 1
                    logger.error(f"Erreur lors de la récupération du lot d'objets: {e}")
            
            # Journaliser les résultats
            logger.info(f"Synchronisation des objets terminée: {processed} traités, {errors} erreurs")
            logger.info(f"Détail par type: {stats}")
            
            return {
                "total": len(item_ids),
                "processed": processed,
                "errors": errors,
                "stats": stats,
                "status": "success" if errors == 0 else "partial" if processed > 0 else "error"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des objets: {e}", exc_info=True)
            return {
                "total": 0,
                "processed": 0,
                "errors": 1,
                "status": "error",
                "error": str(e)
            }
    
    async def _process_weapon_data(self, weapon_data: Dict[str, Any]) -> 'Item':
        """Traite les données d'une arme et les enregistre en base.
        
        Args:
            weapon_data: Données brutes de l'arme depuis l'API
            
        Returns:
            L'objet Item contenant les données de l'arme créé ou mis à jour
            
        Raises:
            ValueError: Si les données de l'arme sont invalides ou incomplètes
            Exception: Pour toute autre erreur survenue lors du traitement
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        
        if not hasattr(self, 'db') or self.db is None:
            raise RuntimeError("La base de données n'est pas initialisée")
            
        db = self.db
        mapper = GW2APIMapper(db)
        
        # Journaliser les données brutes pour le débogage
        item_id = weapon_data.get('id', 'inconnu')
        logger.debug(f"Traitement de l'arme ID: {item_id}, données: {json.dumps(weapon_data, default=str, ensure_ascii=False)[:500]}...")
        
        try:
            # Vérifier si weapon_data est un dictionnaire
            if not isinstance(weapon_data, dict):
                error_msg = f"Données d'arme invalides: attendu un dictionnaire, reçu {type(weapon_data).__name__}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Vérifier les champs obligatoires dans les données brutes
            required_fields = ['id', 'name', 'type', 'rarity']
            missing_fields = [field for field in required_fields if field not in weapon_data]
            if missing_fields:
                error_msg = f"Champs obligatoires manquants dans les données de l'arme {item_id}: {', '.join(missing_fields)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Convertir les données de l'API en modèle interne
            try:
                item = mapper.map_item(weapon_data)
            except Exception as map_error:
                error_msg = f"Échec du mappage de l'arme {item_id}: {str(map_error)}"
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg) from map_error
            
            # Valider que les champs obligatoires sont présents après le mappage
            if not item.name or not item.type or not item.rarity:
                error_msg = f"Données d'arme invalides après mappage pour l'arme {item_id}: champs obligatoires manquants"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Vérifier que l'arme a bien des détails d'arme
            if not hasattr(item, 'weapon') or not item.weapon:
                error_msg = f"Détails d'arme manquants pour l'arme {item_id} (type: {item.type})"
                logger.warning(error_msg)
                # Créer des détails vides plutôt que d'échouer
                item.weapon = mapper._map_weapon_details({})
            
            # Sauvegarder les modifications
            try:
                db.commit()
                logger.debug(f"Arme {'mise à jour' if item.id else 'créée'}: {item.name} (ID: {item.id})")
            except Exception as commit_error:
                error_msg = f"Échec de la sauvegarde de l'arme {item_id}: {str(commit_error)}"
                logger.error(error_msg, exc_info=True)
                db.rollback()
                raise RuntimeError(error_msg) from commit_error
            
            return item
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Erreur lors du rollback pour l'arme {item_id}: {str(rollback_error)}", exc_info=True)
                
            # Si ce n'est pas déjà une ValueError, envelopper dans une exception plus descriptive
            if not isinstance(e, (ValueError, RuntimeError)):
                error_msg = f"Erreur inattendue lors du traitement de l'arme {item_id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e
            raise  # Relancer l'exception originale si c'est déjà une ValueError ou RuntimeError
    
    async def _process_armor_data(self, armor_data: Dict[str, Any]) -> 'Armor':
        """Traite les données d'une armure et les enregistre en base.
        
        Args:
            armor_data: Données brutes de l'armure depuis l'API
            
        Returns:
            L'objet Armor créé ou mis à jour
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        
        db = self.db
        mapper = GW2APIMapper(db)
        
        try:
            # Convertir les données de l'API en modèle interne
            armor = mapper.map_armor(armor_data)
            
            # Valider que les champs obligatoires sont présents
            if not armor.name or not armor.type or not armor.rarity:
                raise ValueError(f"Données d'armure invalides: champs obligatoires manquants dans {armor_data}")
            
            # Sauvegarder les modifications
            db.commit()
            
            # Journaliser la création/mise à jour
            logger.debug(f"Armure {'mise à jour' if armor.id else 'créée'}: {armor.name} (ID: {armor.id})")
            
            return armor
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            db.rollback()
            logger.error(f"Erreur lors du traitement de l'armure {armor_data.get('id')}: {e}")
            raise
    
    async def _process_trinket_data(self, trinket_data: Dict[str, Any]) -> 'Trinket':
        """Traite les données d'un bijou et les enregistre en base.
        
        Args:
            trinket_data: Données brutes du bijou depuis l'API
            
        Returns:
            L'objet Trinket créé ou mis à jour
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        
        db = self.db
        mapper = GW2APIMapper(db)
        
        try:
            # Convertir les données de l'API en modèle interne
            trinket = mapper.map_trinket(trinket_data)
            
            # Valider que les champs obligatoires sont présents
            if not trinket.name or not trinket.type or not trinket.rarity:
                raise ValueError(f"Données de bijou invalides: champs obligatoires manquants dans {trinket_data}")
            
            # Sauvegarder les modifications
            db.commit()
            
            # Journaliser la création/mise à jour
            logger.debug(f"Bijou {'mis à jour' if trinket.id else 'créé'}: {trinket.name} (ID: {trinket.id})")
            
            return trinket
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            db.rollback()
            logger.error(f"Erreur lors du traitement du bijou {trinket_data.get('id')}: {e}")
            raise
    
    async def _process_upgrade_component_data(self, upgrade_data: Dict[str, Any]) -> 'UpgradeComponent':
        """Traite les données d'un composant d'amélioration et les enregistre en base.
        
        Args:
            upgrade_data: Données brutes du composant depuis l'API
            
        Returns:
            L'objet UpgradeComponent créé ou mis à jour
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        
        db = self.db
        mapper = GW2APIMapper(db)
        
        try:
            # Convertir les données de l'API en modèle interne
            upgrade = mapper.map_upgrade_component(upgrade_data)
            
            # Valider que les champs obligatoires sont présents
            if not upgrade.name or not upgrade.type or not upgrade.rarity:
                raise ValueError(f"Données de composant d'amélioration invalides: champs obligatoires manquants dans {upgrade_data}")
            
            # Sauvegarder les modifications
            db.commit()
            
            # Journaliser la création/mise à jour
            logger.debug(f"Composant d'amélioration {'mis à jour' if upgrade.id else 'créé'}: {upgrade.name} (ID: {upgrade.id})")
            
            return upgrade
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            db.rollback()
            logger.error(f"Erreur lors du traitement du composant d'amélioration {upgrade_data.get('id')}: {e}")
            raise
    
    async def _process_consumable_data(self, consumable_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données d'un consommable.
        
        Args:
            consumable_data: Données brutes du consommable depuis l'API
            
        Returns:
            Les données du consommable traitées
        """
        # Pour l'instant, on se contente de logger les consommables
        logger.debug(f"Consommable traité: {consumable_data.get('name')} (ID: {consumable_data.get('id')})")
        return consumable_data
    
    async def _process_gizmo_data(self, gizmo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données d'un gizmo.
        
        Args:
            gizmo_data: Données brutes du gizmo depuis l'API
            
        Returns:
            Les données du gizmo traitées
        """
        # Pour l'instant, on se contente de logger les gizmos
        logger.debug(f"Gizmo traité: {gizmo_data.get('name')} (ID: {gizmo_data.get('id')})")
        return gizmo_data
    
    async def _process_tool_data(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données d'un outil.
        
        Args:
            tool_data: Données brutes de l'outil depuis l'API
            
        Returns:
            Les données de l'outil traitées
        """
        # Pour l'instant, on se contente de logger les outils
        logger.debug(f"Outil traité: {tool_data.get('name')} (ID: {tool_data.get('id')})")
        return tool_data
    
    async def _process_mini_data(self, mini_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données d'une mini-figurine.
        
        Args:
            mini_data: Données brutes de la mini-figurine depuis l'API
            
        Returns:
            Les données de la mini-figurine traitées
        """
        # Pour l'instant, on se contente de logger les mini-figurines
        logger.debug(f"Mini-figurine traitée: {mini_data.get('name')} (ID: {mini_data.get('id')})")
        return mini_data
    
    async def _process_generic_item_data(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données d'un objet générique.
        
        Args:
            item_data: Données brutes de l'objet depuis l'API
            
        Returns:
            Les données de l'objet traitées
        """
        # Pour l'instant, on se contente de logger les objets non gérés spécifiquement
        logger.debug(f"Objet générique traité: {item_data.get('name')} (ID: {item_data.get('id')}, Type: {item_data.get('type', 'inconnu')})")
        return item_data
        
    async def sync_itemstats(self) -> Dict[str, Any]:
        """Synchronise les données des statistiques d'objets depuis l'API GW2.
        
        Returns:
            Un dictionnaire contenant les résultats de la synchronisation
        """
        logger.info("Début de la synchronisation des statistiques d'objets...")
        
        try:
            # Récupérer tous les IDs de statistiques d'objets depuis l'API
            itemstat_ids = await self._api.get('/v2/itemstats')
            
            if not itemstat_ids:
                logger.warning("Aucune statistique d'objet trouvée dans l'API GW2")
                return {"total": 0, "processed": 0, "status": "error", "error": "Aucune statistique d'objet trouvée"}
            
            logger.info(f"Récupération des détails pour {len(itemstat_ids)} statistiques d'objets...")
            
            # Récupérer les détails des statistiques par lots
            chunk_size = 200  # Limite de l'API GW2
            processed = 0
            errors = 0
            
            for i in range(0, len(itemstat_ids), chunk_size):
                chunk = itemstat_ids[i:i + chunk_size]
                
                try:
                    # Récupérer les détails du lot actuel
                    itemstats_data = await self._api.get_itemstats(chunk)
                    
                    # Traiter chaque statistique du lot
                    for itemstat_data in itemstats_data:
                        try:
                            await self._process_itemstat_data(itemstat_data)
                            processed += 1
                            
                            # Journaliser la progression tous les 20 éléments
                            if processed % 20 == 0:
                                logger.info(f"Traitement en cours: {processed}/{len(itemstat_ids)} statistiques d'objets")
                                
                        except Exception as e:
                            errors += 1
                            logger.error(f"Erreur lors du traitement de la statistique d'objet {itemstat_data.get('id')}: {e}")
                            
                except Exception as e:
                    errors += 1
                    logger.error(f"Erreur lors de la récupération du lot de statistiques d'objets: {e}")
            
            # Journaliser les résultats
            logger.info(f"Synchronisation des statistiques d'objets terminée: {processed} traitées, {errors} erreurs")
            
            return {
                "total": len(itemstat_ids),
                "processed": processed,
                "errors": errors,
                "status": "success" if errors == 0 else "partial" if processed > 0 else "error"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des statistiques d'objets: {e}", exc_info=True)
            return {
                "total": 0,
                "processed": 0,
                "errors": 1,
                "status": "error",
                "error": str(e)
            }
    
    async def _process_itemstat_data(self, itemstat_data: Dict[str, Any]) -> 'ItemStats':
        """Traite les données d'une statistique d'objet et les enregistre en base.
        
        Args:
            itemstat_data: Données brutes de la statistique d'objet depuis l'API
            
        Returns:
            L'objet ItemStats créé ou mis à jour
        """
        from app.services.mapping.gw2_api_mapper import GW2APIMapper
        from app.models.item_stats import ItemStats  # Import explicite pour éviter les problèmes de référence circulaire
        
        db = self.db
        mapper = GW2APIMapper(db)
        
        try:
            item_id = itemstat_data.get('id')
            item_name = itemstat_data.get('name', 'Sans nom')
            logger.debug(f"[DEBUG] Début du traitement de la statistique d'objet: ID={item_id}, Nom='{item_name}'")
            logger.debug(f"[DEBUG] Données brutes reçues: {itemstat_data}")
            
            # Vérifier si les données nécessaires sont présentes
            if not item_id:
                error_msg = "ID manquant dans les données de la statistique d'objet"
                logger.error(f"[ERREUR] {error_msg}")
                raise ValueError(error_msg)
                
            # Vérifier si la statistique existe déjà en base
            existing_stat = db.query(ItemStats).get(item_id)
            if existing_stat:
                logger.debug(f"[DEBUG] Statistique existante trouvée: ID={existing_stat.id}, Nom='{existing_stat.name}'")
                # Afficher les attributs actuels pour le débogage
                attrs = {attr: getattr(existing_stat, attr, None) 
                        for attr in ['power', 'precision', 'toughness', 'vitality', 'condition_damage', 
                                   'ferocity', 'healing_power', 'concentration', 'expertise']}
                logger.debug(f"[DEBUG] Attributs actuels: {attrs}")
            
            # Convertir les données de l'API en modèle interne
            logger.debug("[DEBUG] Appel de mapper.map_itemstat...")
            try:
                itemstat = mapper.map_itemstat(itemstat_data)
                logger.debug(f"[DEBUG] Données après mappage: {itemstat.to_dict() if hasattr(itemstat, 'to_dict') else itemstat}")
            except Exception as map_err:
                logger.error(f"[ERREUR] Échec du mappage de la statistique ID={item_id}: {str(map_err)}")
                logger.debug(f"[DEBUG] Traceback du mappage: {traceback.format_exc()}")
                raise
            
            # Gérer le cas où le nom est vide
            if not itemstat.name:
                # Utiliser un nom par défaut basé sur l'ID
                itemstat.name = f"Statistiques-{item_id}"
                logger.warning(f"[ATTENTION] Statistique d'objet sans nom, utilisation du nom par défaut: {itemstat.name} (ID: {item_id})")
                
                # Si la description est vide également, on peut en créer une basique
                if not itemstat.description:
                    itemstat.description = f"Statistiques d'objet personnalisées (ID: {item_id})"
                    if not itemstat.description_fr:
                        itemstat.description_fr = itemstat.description
            
            # Afficher des informations de débogage sur l'objet avant la sauvegarde
            logger.debug(f"[DEBUG] Statistique d'objet avant sauvegarde - ID: {itemstat.id}, Nom: {itemstat.name}")
            
            # Afficher les attributs de la statistique
            attributes = {}
            for attr in ['power', 'precision', 'toughness', 'vitality', 'concentration', 
                        'condition_damage', 'expertise', 'ferocity', 'healing_power', 'armor',
                        'boon_duration', 'critical_chance', 'critical_damage', 'condition_duration']:
                if hasattr(itemstat, attr):
                    val = getattr(itemstat, attr, 0)
                    if val:  # N'afficher que les attributs non nuls
                        attributes[attr] = val
            
            logger.debug(f"[DEBUG] Attributs non nuls de la statistique: {attributes}")
            
            # Vérifier la cohérence des données
            if not any(attributes.values()):
                logger.warning(f"[ATTENTION] Aucun attribut non nul trouvé pour la statistique ID={item_id}")
                logger.debug(f"[DEBUG] Données complètes: {itemstat.__dict__ if hasattr(itemstat, '__dict__') else 'Pas de __dict__'}")
            
            # Sauvegarder les modifications
            logger.debug("[DEBUG] Tentative de sauvegarde en base de données...")
            try:
                db.add(itemstat)
                logger.debug("[DEBUG] Objet ajouté à la session, commit en cours...")
                db.commit()
                logger.debug("[DEBUG] Commit réussi")
            except Exception as save_error:
                logger.error(f"[ERREUR] Échec de la sauvegarde de la statistique: {save_error}", exc_info=True)
                logger.error(f"[ERREUR] Type d'erreur: {type(save_error).__name__}")
                logger.error(f"[ERREUR] Arguments: {getattr(save_error, 'args', 'Pas d\'arguments')}")
                logger.error(f"[ERREUR] Données problématiques: {itemstat_data}")
                try:
                    db.rollback()
                    logger.debug("[DEBUG] Rollback effectué après erreur")
                except Exception as rollback_err:
                    logger.error(f"[ERREUR] Échec du rollback: {rollback_err}")
                raise
            
            # Récupérer l'objet fraîchement sauvegardé pour vérification
            try:
                saved_stat = db.query(ItemStats).get(itemstat.id)
                if saved_stat:
                    logger.debug(f"[DEBUG] Statistique d'objet après sauvegarde - ID: {saved_stat.id}, Nom: {saved_stat.name}")
                    # Vérifier les attributs après sauvegarde
                    saved_attrs = {attr: getattr(saved_stat, attr, None) 
                                 for attr in ['power', 'precision', 'toughness', 'vitality', 'condition_damage', 
                                            'ferocity', 'healing_power', 'concentration', 'expertise']
                                 if getattr(saved_stat, attr, 0) != 0}
                    logger.debug(f"[DEBUG] Attributs après sauvegarde: {saved_attrs}")
                else:
                    logger.warning(f"[ATTENTION] Impossible de récupérer la statistique ID={itemstat.id} après sauvegarde")
            except Exception as verify_error:
                logger.error(f"[ERREUR] Échec de la vérification de la sauvegarde: {verify_error}", exc_info=True)
                logger.error(f"[ERREUR] Type: {type(verify_error).__name__}, Args: {getattr(verify_error, 'args', 'Pas d\'arguments')}")
            
            # Journaliser la création/mise à jour
            action = "mise à jour" if existing_stat else "créée"
            logger.info(f"[SUCCÈS] Statistique d'objet {action}: {itemstat.name} (ID: {itemstat.id})")
            
            return itemstat
            
        except Exception as e:
            # En cas d'erreur, annuler les modifications et relancer l'exception
            logger.error(f"[ERREUR CRITIQUE] Échec du traitement de la statistique ID={item_id}, Nom='{item_name}': {e}", exc_info=True)
            logger.error(f"[DEBUG] Données en échec: {itemstat_data}")
            
            # Annuler les modifications non validées
            try:
                if db:
                    db.rollback()
                    logger.debug("[DEBUG] Rollback effectué")
            except Exception as rollback_error:
                logger.error(f"[ERREUR] Échec du rollback: {rollback_error}")
            
            # Relancer l'exception avec plus de contexte
            error_msg = f"Erreur lors du traitement de la statistique ID={item_id}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    async def sync_all(self) -> Dict[str, Any]:
        """Synchronise toutes les données depuis l'API GW2 de manière séquentielle.
        
        Cette méthode exécute les synchronisations dans un ordre logique pour respecter
        les dépendances entre les différentes entités.
        
        Returns:
            Un dictionnaire contenant les résultats de chaque étape de synchronisation
        """
        logger.info("Début de la synchronisation complète des données GW2...")
        
        # Dictionnaire pour stocker les résultats de chaque étape
        results = {}
        
        try:
            # 1. Synchroniser les données de base du jeu (règles, mécaniques, etc.)
            logger.info("Étape 1/6: Synchronisation des données de base du jeu...")
            results["game_mechanics"] = await self.sync_game_mechanics()
            
            # 2. Synchroniser les professions et spécialisations
            logger.info("Étape 2/6: Synchronisation des professions et spécialisations...")
            results["professions"] = await self.sync_professions()
            
            # 3. Synchroniser les compétences
            logger.info("Étape 3/6: Synchronisation des compétences...")
            results["skills"] = await self.sync_skills()
            
            # 4. Synchroniser les traits
            logger.info("Étape 4/6: Synchronisation des traits...")
            results["traits"] = await self.sync_traits()
            
            # 5. Synchroniser les statistiques d'objets
            logger.info("Étape 5/6: Synchronisation des statistiques d'objets...")
            results["itemstats"] = await self.sync_itemstats()
            
            # 6. Synchroniser les objets (armes, armures, bijoux, etc.)
            logger.info("Étape 6/6: Synchronisation des objets...")
            results["items"] = await self.sync_items()
            
            # Vérifier s'il y a eu des erreurs
            has_errors = any(
                isinstance(result, dict) and result.get("status") == "error" 
                for result in results.values()
            )
            
            # Préparer le rapport de synchronisation
            status = "error" if has_errors else "success"
            logger.info(f"Synchronisation complète terminée avec le statut: {status}")
            
            return {
                "status": status,
                "results": results
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la synchronisation complète: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "error": error_msg,
                "results": results  # Inclure les résultats partiels
            }
    
    # Méthodes utilitaires
    
    async def _paginated_api_call(self, endpoint: str, page_size: int = 200) -> List[Any]:
        """Effectue un appel API avec pagination.
        
        Args:
            endpoint: L'endpoint de l'API à appeler (sans le /v2/ initial)
            page_size: Nombre d'éléments par page (max 200)
            
        Returns:
            Une liste contenant tous les éléments récupérés
        """
        all_items = []
        page = 0
        total_items = None
        
        # S'assurer que la taille de page ne dépasse pas la limite de l'API
        page_size = min(200, max(1, page_size))
        
        logger.debug(f"Début de la récupération paginée pour {endpoint} (page_size={page_size})")
        
        try:
            while True:
                # Construire les paramètres de pagination
                params = {
                    'page': page,
                    'page_size': page_size
                }
                
                # Effectuer l'appel API
                response = await self._api.get(f'/v2/{endpoint}', params=params)
                
                # Pour la première page, récupérer le nombre total d'éléments
                if page == 0:
                    total_items = int(response.headers.get('X-Result-Total', '0'))
                    logger.debug(f"Total d'éléments à récupérer: {total_items}")
                
                # Ajouter les éléments de la page courante
                items = response.json()
                if not items:
                    break
                    
                all_items.extend(items)
                logger.debug(f"Page {page + 1} récupérée: {len(items)} éléments")
                
                # Vérifier si on a tout récupéré
                if len(all_items) >= total_items or len(items) < page_size:
                    break
                    
                # Préparer la page suivante
                page += 1
                
                # Petite pause pour éviter de surcharger l'API
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération paginée de {endpoint}: {e}")
            raise
            
        logger.debug(f"Récupération paginée terminée: {len(all_items)} éléments au total")
        return all_items
    
    async def _get_or_create(self, model, **kwargs):
        """Récupère un objet ou le crée s'il n'existe pas."""
        instance = self.db.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            self.db.add(instance)
        return instance
        
    async def _batch_process(
        self, 
        items: List[Any], 
        process_func: Callable,
        batch_size: int = 100,
        commit_between_batches: bool = True
    ) -> Dict[str, int]:
        """Traite une liste d'éléments par lots.
        
        Args:
            items: Liste des éléments à traiter
            process_func: Fonction à appliquer à chaque élément (doit accepter un seul argument)
            batch_size: Taille des lots (défaut: 100)
            commit_between_batches: Si True, effectue un commit entre chaque lot
            
        Returns:
            Un dictionnaire contenant des statistiques sur le traitement
        """
        total = len(items)
        if total == 0:
            return {"total": 0, "processed": 0, "errors": 0, "status": "success"}
            
        processed = 0
        errors = 0
        batch_count = (total + batch_size - 1) // batch_size
        
        logger.info(f"Traitement de {total} éléments par lots de {batch_size} ({batch_count} lots)")
        
        for i in range(0, total, batch_size):
            batch = items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                # Traiter chaque élément du lot
                for item in batch:
                    try:
                        await process_func(item)
                        processed += 1
                        
                        # Journaliser la progression tous les 10 éléments
                        if processed % 10 == 0:
                            logger.debug(f"Traitement en cours: {processed}/{total} éléments")
                            
                    except Exception as e:
                        errors += 1
                        logger.error(f"Erreur lors du traitement de l'élément: {e}", exc_info=True)
                        continue
                
                # Valider les modifications du lot
                if commit_between_batches:
                    self.db.commit()
                    logger.debug(f"Lot {batch_num}/{batch_count} traité et validé")
                
            except Exception as e:
                # En cas d'erreur, annuler les modifications du lot courant
                self.db.rollback()
                logger.error(f"Erreur lors du traitement du lot {batch_num}/{batch_count}: {e}", exc_info=True)
                errors += len(batch)  # Compter toutes les erreurs du lot
        
        # Valider les modifications restantes si nécessaire
        if not commit_between_batches and (processed > 0 or errors > 0):
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erreur lors de la validation finale: {e}", exc_info=True)
                return {
                    "total": total,
                    "processed": processed,
                    "errors": total,  # Tout échoue si le commit final échoue
                    "status": "error",
                    "error": str(e)
                }
        
        # Déterminer le statut global
        status = "error"
        if errors == 0:
            status = "success"
        elif processed > 0:
            status = "partial"
        
        logger.info(f"Traitement par lots terminé: {processed} succès, {errors} erreurs sur {total} éléments")
        
        return {
            "total": total,
            "processed": processed,
            "errors": errors,
            "status": status
        }
    
    async def _batch_api_request(
        self,
        endpoint: str,
        item_ids: List[Union[int, str]],
        batch_size: int = 200,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Dict[Union[int, str], Any]:
        """Effectue une requête par lots à l'API GW2 avec gestion des erreurs et réessais.
        
        Args:
            endpoint: L'endpoint de l'API (sans le /v2/ initial)
            item_ids: Liste des identifiants des éléments à récupérer
            batch_size: Nombre d'identifiants par lot (max 200)
            max_retries: Nombre maximum de tentatives en cas d'échec
            retry_delay: Délai initial entre les tentatives (en secondes)
            **kwargs: Arguments supplémentaires à passer à _cached_api_call
            
        Returns:
            Un dictionnaire {item_id: données} pour les éléments récupérés avec succès
        """
        if not item_ids:
            return {}
            
        # S'assurer que la taille des lots ne dépasse pas la limite de l'API
        batch_size = min(200, max(1, batch_size))
        total_items = len(item_ids)
        results = {}
        
        logger.info(f"Début de la récupération par lots pour {endpoint} ({total_items} éléments, lots de {batch_size})")
        
        # Traiter les éléments par lots
        for i in range(0, total_items, batch_size):
            batch = item_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_items + batch_size - 1) // batch_size
            
            logger.debug(f"Traitement du lot {batch_num}/{total_batches} ({len(batch)} éléments)")
            
            # Essayer plusieurs fois en cas d'échec
            for attempt in range(1, max_retries + 1):
                try:
                    # Effectuer la requête pour ce lot
                    params = kwargs.pop('params', {})
                    params['ids'] = ','.join(str(item_id) for item_id in batch)
                    
                    # Utiliser _cached_api_call pour bénéficier du cache
                    response = await self._cached_api_call(
                        f"/v2/{endpoint}",
                        params=params,
                        **kwargs
                    )
                    
                    # Ajouter les résultats au dictionnaire de sortie
                    for item in response:
                        if 'id' in item:
                            results[item['id']] = item
                    
                    # Si on arrive ici, la requête a réussi, on passe au lot suivant
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Si c'est la dernière tentative ou une erreur non récupérable, on relève l'exception
                    if attempt == max_retries or \
                       '404' in error_msg or '401' in error_msg or '403' in error_msg:
                        logger.error(
                            f"Échec du traitement du lot {batch_num} après {attempt} tentatives: {error_msg}"
                        )
                        # On continue avec le lot suivant même en cas d'échec
                        break
                    
                    # Calculer le délai d'attente avec backoff exponentiel
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Tentative {attempt}/{max_retries} échouée pour le lot {batch_num}. "
                        f"Nouvelle tentative dans {wait_time:.1f}s..."
                    )
                    
                    # Attendre avant de réessayer
                    await asyncio.sleep(wait_time)
        
        logger.info(f"Récupération par lots terminée: {len(results)}/{total_items} éléments récupérés avec succès")
        return results
    
    async def _cached_api_call(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        cache_ttl: int = 86400,  # 24h par défaut
        force_refresh: bool = False
    ) -> Any:
        """Effectue un appel API avec mise en cache.
        
        Args:
            endpoint: L'endpoint de l'API à appeler (avec le /v2/ initial)
            params: Paramètres de la requête
            cache_ttl: Durée de vie du cache en secondes
            force_refresh: Si True, force le rafraîchissement du cache
            
        Returns:
            La réponse de l'API (décodée depuis JSON)
        """
        if params is None:
            params = {}
            
        # Générer une clé de cache unique basée sur l'endpoint et les paramètres
        cache_key = f"{endpoint}:{str(sorted(params.items()))}"
        
        # Vérifier si la réponse est en cache et toujours valide
        if not force_refresh and hasattr(self, '_api_cache'):
            cached_data = self._api_cache.get(cache_key)
            if cached_data and (time.time() - cached_data['timestamp']) < cache_ttl:
                logger.debug(f"Récupération depuis le cache: {cache_key}")
                return cached_data['data']
        
        try:
            # Effectuer l'appel API
            logger.debug(f"Appel API vers {endpoint} avec les paramètres: {params}")
            response = await self._api.get(endpoint, params=params)
            data = response.json()
            
            # Mettre en cache le résultat
            if not hasattr(self, '_api_cache'):
                self._api_cache = {}
                
            self._api_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            
            return data
            
        except Exception as e:
            # En cas d'erreur, essayer de renvoyer les données en cache si disponibles
            if not force_refresh and hasattr(self, '_api_cache') and cache_key in self._api_cache:
                logger.warning(f"Erreur API, utilisation des données en cache pour {cache_key}: {e}")
                return self._api_cache[cache_key]['data']
            raise
    
    async def clear_cache(self) -> Dict[str, Any]:
        """Vide le cache du client API et le cache interne."""
        try:
            # Vider le cache du client API
            api_cache_info = await self._api.clear_cache()
            
            # Vider le cache interne
            internal_cache_entries = 0
            if hasattr(self, '_api_cache'):
                internal_cache_entries = len(self._api_cache)
                del self._api_cache
                self._api_cache = {}
            
            return {
                "status": "success",
                "message": "Caches vidés avec succès",
                "api_cache_cleared": True,
                "internal_cache_entries_cleared": internal_cache_entries
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du cache: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_api_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Gère les erreurs d'API de manière centralisée.
        
        Args:
            error: L'exception qui a été levée
            context: Contexte supplémentaire pour le message d'erreur
            
        Returns:
            Un dictionnaire contenant les détails de l'erreur
        """
        error_id = str(uuid.uuid4())
        error_type = error.__class__.__name__
        error_msg = str(error)
        
        # Journaliser l'erreur avec plus de détails
        logger.error(
            f"Erreur API [{error_id}]: {error_type} - {error_msg}"
            f"{f' (Contexte: {context})' if context else ''}",
            exc_info=True
        )
        
        # Déterminer le type d'erreur et fournir un message adapté
        error_category = "unknown"
        if "404" in error_msg or "Not Found" in error_msg:
            error_category = "not_found"
        elif "401" in error_msg or "403" in error_msg:
            error_category = "unauthorized"
        elif "429" in error_msg or "Too Many Requests" in error_msg:
            error_category = "rate_limit"
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            error_category = "timeout"
        
        # Construire la réponse d'erreur
        error_response = {
            "status": "error",
            "error_id": error_id,
            "error_type": error_type,
            "error_category": error_category,
            "message": f"Une erreur est survenue lors de l'accès à l'API GW2: {error_msg}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Ajouter des conseils en fonction du type d'erreur
        if error_category == "not_found":
            error_response["suggestion"] = "La ressource demandée n'existe pas ou n'est pas accessible."
        elif error_category == "unauthorized":
            error_response["suggestion"] = "Vérifiez que votre clé API est valide et dispose des autorisations nécessaires."
        elif error_category == "rate_limit":
            error_response["suggestion"] = "Limite de requêtes atteinte. Veuillez réessayer plus tard ou utilisez une clé API avec des limites plus élevées."
        elif error_category == "timeout":
            error_response["suggestion"] = "Le délai d'attente de la requête a expiré. Vérifiez votre connexion Internet et réessayez."
        else:
            error_response["suggestion"] = "Une erreur inattendue s'est produite. Veuillez réessayer plus tard."
        
        return error_response
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Retourne des informations sur le cache."""
        try:
            # Récupérer les informations du cache de l'API
            api_cache_info = await self._api.get_cache_info()
            
            # Calculer les informations du cache interne
            internal_cache_info = {
                'entries': len(self._api_cache) if hasattr(self, '_api_cache') else 0,
                'size_bytes': sum(
                    len(str(k)) + len(str(v)) 
                    for k, v in getattr(self, '_api_cache', {}).items()
                )
            }
            
            return {
                "status": "success",
                "api_cache": api_cache_info,
                "internal_cache": internal_cache_info,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return await self._handle_api_error(e, "Récupération des informations du cache")

# Instance globale du service
gw2_data_service = GW2DataService()

# Fonctions utilitaires pour une utilisation simplifiée

async def get_gw2_data_service() -> GW2DataService:
    """Retourne une instance du service de données GW2."""
    service = GW2DataService()
    await service.initialize()
    return service

async def close_gw2_data_service() -> None:
    """Ferme les ressources du service de données GW2."""
    await gw2_data_service.close()

# Initialisation du service - Ne plus exécuter automatiquement au chargement du module
# L'initialisation se fera à la demande via get_gw2_data_service()

# Pour les tests et l'exécution directe
if __name__ == "__main__":
    async def main():
        service = GW2DataService()
        try:
            await service.initialize()
            print("Service GW2Data initialisé avec succès")
            # Faire quelque chose avec le service...
        except Exception as e:
            print(f"Erreur: {e}")
        finally:
            await service.close()
    
    import asyncio
    asyncio.run(main())
