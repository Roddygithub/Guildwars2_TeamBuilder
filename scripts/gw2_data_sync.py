#!/usr/bin/env python3
"""Script de synchronisation des données GW2.

Ce script permet de synchroniser les données de l'API GW2 avec la base de données locale.
Il peut être utilisé en ligne de commande ou importé comme module.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.gw2_data_service import GW2DataService
from app.database import init_async_db as init_db

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gw2_sync.log')
    ]
)

logger = logging.getLogger(__name__)

async def sync_all_data(force: bool = False) -> None:
    """Synchronise toutes les données GW2.
    
    Args:
        force: Si True, force la synchronisation même si les données sont à jour
    """
    service = None
    try:
        # Initialiser la base de données de manière asynchrone
        await init_db()
        
        # Initialiser le service
        service = GW2DataService()
        await service.initialize()
        
        # Lancer la synchronisation
        logger.info("Démarrage de la synchronisation des données GW2...")
        results = await service.sync_all_data(force=force)
        
        # Afficher les résultats
        logger.info("\nRésumé de la synchronisation:")
        logger.info("=" * 50)
        
        for entity, result in results.items():
            if isinstance(result, dict):
                status = result.get('status', 'inconnu')
                total = result.get('total', 0)
                processed = result.get('processed', 0)
                
                if status == 'success':
                    logger.info(f"{entity.capitalize()}: {processed}/{total} synchronisés avec succès")
                elif status == 'not_implemented':
                    logger.warning(f"{entity.capitalize()}: Non implémenté")
                else:
                    error = result.get('error', 'Erreur inconnue')
                    logger.error(f"{entity.capitalize()}: Échec - {error}")
        
        logger.info("=" * 50)
        logger.info("Synchronisation terminée")
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        if service:
            await service.close()

async def clear_cache() -> None:
    """Vide le cache de l'API GW2."""
    service = None
    try:
        service = GW2DataService()
        await service.initialize()
        
        logger.info("Vidage du cache de l'API GW2...")
        result = await service.clear_cache()
        
        if result["status"] == "success":
            logger.info(f"Cache vidé avec succès: {result['deleted_entries']} entrées supprimées")
        else:
            logger.error(f"Erreur lors du vidage du cache: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Erreur lors du vidage du cache: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        if service:
            await service.close()

async def show_cache_info() -> None:
    """Affiche des informations sur le cache."""
    service = None
    try:
        service = GW2DataService()
        await service.initialize()
        
        logger.info("Récupération des informations sur le cache...")
        result = await service.get_cache_info()
        
        if result["status"] == "success":
            cache_info = result["cache_info"]
            logger.info("\nInformations sur le cache:")
            logger.info("=" * 50)
            
            if not cache_info["enabled"]:
                logger.info("Le cache est désactivé")
            else:
                logger.info(f"Dossier du cache: {cache_info['cache_dir']}")
                logger.info(f"Nombre d'entrées: {cache_info['count']}")
                logger.info(f"Taille totale: {cache_info['total_size_mb']:.2f} Mo")
        else:
            logger.error(f"Erreur lors de la récupération des informations du cache: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations du cache: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        if service:
            await service.close()

def parse_arguments() -> argparse.Namespace:
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Outil de synchronisation des données GW2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # Commande: sync
    sync_parser = subparsers.add_parser('sync', help='Synchroniser les données GW2')
    sync_parser.add_argument(
        '--force', 
        action='store_true',
        help='Forcer la synchronisation même si les données sont à jour'
    )
    
    # Commande: clear-cache
    clear_parser = subparsers.add_parser('clear-cache', help='Vider le cache de l\'API GW2')
    
    # Commande: cache-info
    info_parser = subparsers.add_parser('cache-info', help='Afficher des informations sur le cache')
    
    # Arguments généraux
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Activer les logs détaillés (niveau DEBUG)'
    )
    
    return parser.parse_args()

def main() -> None:
    """Fonction principale."""
    args = parse_arguments()
    
    # Configurer le niveau de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter la commande demandée
    if args.command == 'sync':
        asyncio.run(sync_all_data(force=args.force))
    elif args.command == 'clear-cache':
        asyncio.run(clear_cache())
    elif args.command == 'cache-info':
        asyncio.run(show_cache_info())
    else:
        print("Commande non reconnue. Utilisez --help pour voir les commandes disponibles.")
        sys.exit(1)

if __name__ == "__main__":
    main()
