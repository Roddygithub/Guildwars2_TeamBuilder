"""Optimiseur simple qui échantillonne des équipes aléatoires et conserve les meilleures.

Ce module fournit une implémentation de référence pour l'optimisation d'équipes
en utilisant une approche par échantillonnage aléatoire. Il est conçu comme une
solution de base avant de passer à des algorithmes plus sophistiqués comme les
algorithmes génétiques.

Exemple d'utilisation:
    ```python
    config = ScoringConfig(...)
    best_teams = optimize(
        team_size=5,
        samples=1000,
        top_n=5,
        config=config
    )
    ```
"""
from __future__ import annotations

import functools
import itertools
import logging
import math
import os
import random
import sys
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.database import SessionLocal
from app.models import Profession  # Import direct du modèle SQLAlchemy
from app.scoring.engine import PlayerBuild, score_team
from app.scoring.schema import ScoringConfig, TeamScoreResult

# Configuration du logger
logger = logging.getLogger(__name__)

# Cache pour les candidats par défaut (1 heure de durée de vie)
_DEFAULT_CACHE_TTL = 3600  # secondes
_candidates_cache = {}
_candidates_cache_timestamp = 0

#: Dictionnaire de correspondance entre les professions et leurs métadonnées (buffs et rôles par défaut).
#: Format: {"NomProfession": (set(buffs), set(roles))}
_PROFESSION_METADATA = {
    "Guardian": ({"quickness", "might"}, {"heal", "quickness"}),
    "Warrior": ({"might"}, {"dps"}),
    "Revenant": ({"alacrity", "might"}, {"dps", "alacrity"}),
    "Ranger": (set(), {"dps"}),
    "Thief": (set(), {"dps"}),
    "Engineer": ({"quickness"}, {"dps", "quickness"}),
    "Necromancer": (set(), {"dps"}),
    "Elementalist": (set(), {"dps"}),
    "Mesmer": ({"alacrity"}, {"heal", "alacrity"}),
}


def _get_cached_candidates() -> List[PlayerBuild]:
    """Récupère les candidats en cache ou les charge depuis la base de données.
    
    Returns:
        Une liste de PlayerBuild, mise en cache avec une durée de vie limitée.
    """
    global _candidates_cache, _candidates_cache_timestamp
    
    # Vérifier si le cache est toujours valide
    current_time = time.time()
    if current_time - _candidates_cache_timestamp < _DEFAULT_CACHE_TTL and _candidates_cache:
        logger.debug("Utilisation des candidats en cache")
        return _candidates_cache
    
    # Charger les candidats depuis la base de données
    with SessionLocal() as db:
        candidates = _load_candidates_from_db(db)
    
    # Mettre à jour le cache
    _candidates_cache = candidates
    _candidates_cache_timestamp = current_time
    
    return candidates

def _load_candidates_from_db(db: Session) -> List[PlayerBuild]:
    """Charge les candidats depuis la base de données.
    
    Args:
        db: Session SQLAlchemy pour accéder à la base de données.
        
    Returns:
        Une liste de PlayerBuild chargée depuis la base de données.
    """
    logger.info("Chargement des candidats depuis la base de données...")
    
    try:
        # Vérifier si la table des builds existe
        inspector = inspect(db.get_bind())
        table_names = inspector.get_table_names()
        
        if 'builds' not in table_names:
            logger.warning("La table 'builds' n'existe pas dans la base de données")
            return _get_default_candidates()
        
        # Récupérer les builds depuis la base de données
        try:
            logger.debug("Récupération des builds depuis la base de données")
            from app.models.build_sql import Build
            from app.models.build import BuildData
            
            db_builds = db.query(Build).all()
            
            if not db_builds:
                logger.warning("Aucun build trouvé dans la base de données")
                return _get_default_candidates()
            
            # Convertir les builds de la base de données en objets PlayerBuild
            builds: List[PlayerBuild] = []
            for db_build in db_builds:
                try:
                    # Utiliser les rôles et buffs du build s'ils sont disponibles
                    # Sinon, utiliser les valeurs par défaut de la profession
                    buffs = set()
                    roles = {db_build.role}
                    
                    # Si c'est un rôle de support, ajouter les buffs correspondants
                    if db_build.role == 'quickness':
                        buffs.add('quickness')
                    elif db_build.role == 'alacrity':
                        buffs.add('alacrity')
                    
                    build = PlayerBuild(
                        profession_id=db_build.profession.value,
                        elite_spec=db_build.name.split()[-1] if ' ' in db_build.name else '',
                        buffs=buffs,
                        roles=roles,
                        description=db_build.description or f"Build {db_build.name}",
                        source=db_build.source or ""
                    )
                    builds.append(build)
                    logger.debug(f"Build chargé: {db_build.name} ({db_build.profession} - {db_build.role})")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement du build {db_build.name}: {str(e)}")
                    continue
            
            logger.info(f"{len(builds)} builds chargés avec succès depuis la base de données")
            return builds
            
        except Exception as query_error:
            logger.error(f"Erreur lors de la récupération des builds: {str(query_error)}")
            logger.error(f"Type d'erreur: {type(query_error).__name__}")
            logger.error(f"Traceback complet: {query_error}")
            return _get_default_candidates()
            
    except Exception as e:
        logger.error(f"Erreur critique lors du chargement des candidats: {str(e)}")
        return _get_default_candidates()

def _get_default_candidates() -> List[PlayerBuild]:
    """Retourne les candidats par défaut basés sur _PROFESSION_METADATA.
    
    Returns:
        Une liste de PlayerBuild avec des valeurs par défaut.
    """
    logger.warning("Utilisation des valeurs par défaut pour les professions")
    return [
        PlayerBuild(
            profession_id=prof_name.lower(),
            buffs=buffs,
            roles=roles,
            description=f"Build par défaut pour {prof_name}"
        )
        for prof_name, (buffs, roles) in _PROFESSION_METADATA.items()
    ]

def _default_candidates(db: Session) -> List[PlayerBuild]:
    """Fonction wrapper pour maintenir la compatibilité avec le code existant."""
    return _get_cached_candidates()


def optimize_team(
    team_size: int,
    samples: int,
    top_n: int,
    config: ScoringConfig,
    candidates: Sequence[PlayerBuild] | None = None,
    random_seed: int | None = None,
) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
    """Alias pour la fonction optimize pour maintenir la compatibilité.
    
    Voir la documentation de la fonction optimize pour plus de détails.
    """
    return optimize(team_size, samples, top_n, config, candidates, random_seed)


def _evaluate_team(combo: Sequence[PlayerBuild], config: ScoringConfig) -> Optional[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
    """Évalue une seule équipe et retourne son score.
    
    Args:
        combo: La combinaison de builds à évaluer.
        config: Configuration du calcul des scores.
        
    Returns:
        Un tuple (score, équipe) si l'évaluation réussit, None sinon.
    """
    try:
        team = list(combo)
        result = score_team(team, config)
        return (result, team)
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation d'une équipe: {str(e)}")
        return None

def optimize(
    team_size: int,
    samples: int,
    top_n: int,
    config: ScoringConfig,
    candidates: Sequence[PlayerBuild] | None = None,
    random_seed: int | None = None,
    early_stop_threshold: float = 0.9,  # Score de 90% pour l'arrêt anticipé
    min_samples_before_stop: int = 100,  # Nombre minimum d'échantillons avant d'envisager l'arrêt
    max_workers: int | None = None,     # Nombre maximum de workers pour le traitement parallèle
) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
    """Trouve les meilleures équipes en échantillonnant des combinaisons aléatoires.
    
    Cette fonction évalue plusieurs combinaisons de builds et retourne les `top_n`
    équipes ayant les meilleurs scores selon la configuration fournie.
    
    Args:
        team_size: Nombre de joueurs par équipe.
        samples: Nombre maximum de combinaisons à évaluer.
        top_n: Nombre d'équipes à retourner (les mieux notées).
        config: Configuration du calcul des scores.
        candidates: Liste optionnelle de builds candidats. Si None, utilise les builds par défaut.
        random_seed: Graine pour le générateur de nombres aléatoires (pour la reproductibilité).
        early_stop_threshold: Score (0-1) à partir duquel on peut arrêter l'optimisation plus tôt.
        min_samples_before_stop: Nombre minimum d'échantillons à évaluer avant d'envisager l'arrêt anticipé.
        
    Returns:
        Une liste de tuples (score, équipe) triée par score décroissant, où :
        - score: Un objet TeamScoreResult contenant le score et les détails de l'évaluation.
        - équipe: Une séquence de PlayerBuild représentant la composition d'équipe.
        
    Raises:
        ValueError: Si le nombre de candidats est insuffisant pour former une équipe.
        
    Example:
        >>> config = ScoringConfig(...)
        >>> # Trouver les 3 meilleures équipes de 5 joueurs parmi 1000 échantillons
        >>> best_teams = optimize(5, 1000, 3, config)
        >>> for score, team in best_teams:
        ...     print(f"Score: {score.total_score:.2f}")
        ...     print(f"  Composition: {[p.profession_id for p in team]}")
    """
    start_time = time.time()
    logger.info(f"Début de l'optimisation pour une équipe de {team_size} joueurs")
    
    if random_seed is not None:
        random.seed(random_seed)
        logger.info(f"Graine aléatoire initialisée: {random_seed}")

    try:
        # Utiliser le cache pour les candidats
        if candidates is None:
            logger.debug("Récupération des candidats depuis le cache...")
            candidates = _get_cached_candidates()
            logger.info(f"{len(candidates)} candidats récupérés (cache: {time.time() - start_time:.2f}s)")

        if not candidates:
            logger.error("Aucun candidat disponible pour former une équipe")
            return []
            
        if len(candidates) < team_size:
            error_msg = f"Pas assez de candidats ({len(candidates)}) pour former une équipe de {team_size} joueurs"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Limiter la taille du pool de candidats pour améliorer les performances
        max_candidates = min(100, len(candidates))
        if len(candidates) > max_candidates:
            logger.info(f"Réduction du pool de {len(candidates)} à {max_candidates} candidats")
            candidates = random.sample(candidates, max_candidates)

        best: List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]] = []
        total_combinations = math.comb(len(candidates), team_size)
        
        # Ajuster la limite en fonction du nombre de combinaisons possibles
        limit = min(samples, total_combinations, 5000)  # Limite réduite à 5000 pour de meilleures performances
        
        logger.info(f"Combinaisons possibles: {total_combinations}, Limite: {limit}, Taille équipe: {team_size}")
        
        # Préparer les combinaisons
        if total_combinations <= limit:
            logger.info("Évaluation de toutes les combinaisons possibles")
            # Créer une liste à partir de l'itérateur pour permettre l'utilisation de len()
            combinations = list(itertools.combinations(candidates, team_size))
            is_random = False
        else:
            logger.info(f"Échantillonnage aléatoire de {limit} combinaisons")
            # Si on a un grand nombre de combinaisons, on en prend un échantillon aléatoire
            seen = set()
            combinations = []
            while len(combinations) < limit and len(combinations) < total_combinations:
                combo = tuple(sorted(random.sample(candidates, team_size), key=lambda x: x.profession_id))
                if combo not in seen:
                    seen.add(combo)
                    combinations.append(combo)
            is_random = True
        
        # Détecter le nombre optimal de workers
        if max_workers is None:
            # Utiliser le nombre de cœurs disponibles, avec un minimum de 2 et un maximum de 8
            # Sur les machines avec peu de cœurs, on peut être plus agressif
            cpu_count = os.cpu_count() or 4
            if cpu_count <= 4:
                max_workers = cpu_count * 2  # Hyperthreading
            else:
                max_workers = min(8, max(4, cpu_count))
            
            logger.debug(f"Détection automatique: {cpu_count} cœurs CPU -> {max_workers} workers")
        
        # Ajuster dynamiquement la taille des lots en fonction du nombre de workers
        # et de la taille totale de l'échantillon
        chunk_size = max(1, min(
            100,  # Taille maximale d'un lot
            limit // (max_workers * 2) if max_workers else 10,  # Au moins 2 lots par worker
            10   # Taille minimale d'un lot
        ))
        logger.debug(f"Taille des lots: {chunk_size} combinaisons par lot")
        
        logger.info(f"Démarrage du traitement parallèle avec {max_workers} workers")
        
        best_score = 0.0
        early_stop = False
        processed = 0
        
        # Créer un gestionnaire de tâches parallèles
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Préparer les tâches par lots
            futures = []
            batch_results = []
            
            # Fonction pour traiter un lot de combinaisons
            def process_batch(batch: List[Tuple[int, Any]]) -> List[Tuple[TeamScoreResult, Sequence[PlayerBuild]]]:
                batch_results = []
                for idx, combo in batch:
                    result = _evaluate_team(combo, config)
                    if result is not None:
                        batch_results.append(result)
                return batch_results
            
            # Soumettre les tâches par lots
            for i in range(0, len(combinations), chunk_size):
                if early_stop:
                    break
                
                batch = list(enumerate(combinations[i:i+chunk_size], i + 1))
                futures.append(executor.submit(process_batch, batch))
            
            # Traiter les résultats au fur et à mesure de leur disponibilité
            for future in as_completed(futures):
                if early_stop:
                    future.cancel()
                    continue
                    
                try:
                    results = future.result()
                    # Mettre à jour les résultats
                    for result in results:
                        if result is not None:
                            score, team = result
                            best.append((score, team))
                            
                            # Mettre à jour le meilleur score
                            if score.total_score > best_score:
                                best_score = score.total_score
                    
                    # Mettre à jour le compteur et vérifier l'arrêt anticipé
                    processed += chunk_size
                    
                    # Vérifier l'arrêt anticipé après min_samples_before_stop évaluations
                    if processed >= min_samples_before_stop and best_score >= early_stop_threshold:
                        logger.info(f"Arrêt anticipé: Score de {best_score:.2f} atteint (seuil: {early_stop_threshold:.2f})")
                        early_stop = True
                        # Annuler les tâches restantes
                        for f in futures:
                            f.cancel()
                        break
                    
                    # Afficher la progression
                    if processed % 100 == 0 or processed == 1 or processed >= limit:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed if elapsed > 0 else 0
                        logger.info(
                            f"Progression: {min(processed, limit)}/{limit} "
                            f"({min(processed, limit)/limit*100:.1f}%) - "
                            f"{rate:.1f} évaluations/s - Meilleur score: {best_score:.2f}"
                        )
                            
                except Exception as e:
                    logger.error(f"Erreur lors du traitement d'un lot: {str(e)}")
                    continue
        
        # Trier par score et retourner les top_n meilleures équipes
        if best:
            best.sort(key=lambda x: x[0].total_score, reverse=True)
            best = best[:top_n]
            elapsed = time.time() - start_time
            
            logger.info(
                f"Optimisation terminée en {elapsed:.2f}s ({len(best)} équipes, "
                f"{len(best)/elapsed:.1f} équipes/s) - Meilleur score: {best[0][0].total_score:.2f}"
            )
            if early_stop:
                logger.info(f"Arrêt anticipé après {i} évaluations (score atteint: {best_score:.2f})")
            
            return best
        else:
            logger.warning("Aucune équipe valide n'a pu être générée")
            return []
            
    except Exception as e:
        logger.error(f"Erreur critique dans optimize: {str(e)}", exc_info=True)
        raise
