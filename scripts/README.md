# Scripts de gestion des données GW2

Ce répertoire contient des scripts pour gérer la synchronisation des données avec l'API Guild Wars 2.

## Scripts disponibles

### `gw2_data_sync.py`

Script principal pour synchroniser les données de l'API GW2 avec la base de données locale.

#### Utilisation

```bash
# Afficher l'aide
python -m scripts.gw2_data_sync --help

# Synchroniser les données (mise à jour si nécessaire)
python -m scripts.gw2_data_sync sync

# Forcer la synchronisation complète des données
python -m scripts.gw2_data_sync sync --force

# Vider le cache de l'API GW2
python -m scripts.gw2_data_sync clear-cache

# Afficher des informations sur le cache
python -m scripts.gw2_data_sync cache-info

# Activer les logs détaillés (mode verbeux)
python -m scripts.gw2_data_sync --verbose [command]
```

#### Options

- `sync`: Synchronise les données GW2 avec la base de données locale
  - `--force`: Force la synchronisation même si les données sont à jour
- `clear-cache`: Vide le cache de l'API GW2
- `cache-info`: Affiche des informations sur le cache
- `-v, --verbose`: Active les logs détaillés (niveau DEBUG)

## Configuration

Le script utilise les variables d'environnement suivantes (optionnelles) :

- `GW2_API_KEY`: Clé API GW2 pour accéder aux endpoints authentifiés
- `GW2_API_BASE_URL`: URL de base de l'API GW2 (par défaut: https://api.guildwars2.com)
- `GW2_CACHE_DIR`: Répertoire de cache (par défaut: `data/cache/gw2api`)
- `GW2_CACHE_TTL`: Durée de vie du cache en secondes (par défaut: 3600)

## Journalisation

Les journaux sont enregistrés dans le fichier `gw2_sync.log` dans le répertoire courant.

## Exemples d'utilisation avancée

### Synchronisation complète des données

```bash
# Forcer une synchronisation complète avec logs détaillés
python -m scripts.gw2_data_sync --verbose sync --force
```

### Vérification de l'état du cache

```bash
# Voir l'état actuel du cache
python -m scripts.gw2_data_sync cache-info

# Vider le cache si nécessaire
python -m scripts.gw2_data_sync clear-cache
```

### Utilisation en tant que module

Vous pouvez également importer et utiliser les fonctions du script dans votre code Python :

```python
import asyncio
from scripts.gw2_data_sync import sync_all_data, clear_cache, show_cache_info

# Synchroniser les données
asyncio.run(sync_all_data(force=True))

# Vider le cache
asyncio.run(clear_cache())

# Afficher les informations du cache
asyncio.run(show_cache_info())
```

## Dépannage

### Erreurs de connexion

Si vous rencontrez des erreurs de connexion à l'API GW2, vérifiez :

1. Votre connexion Internet
2. Que l'API GW2 est accessible depuis votre réseau
3. Que vous n'avez pas dépassé les limites de taux (rate limits)

### Problèmes de cache

Si vous rencontrez des problèmes avec le cache :

1. Essayez de vider le cache avec `clear-cache`
2. Vérifiez les permissions du répertoire de cache
3. Assurez-vous qu'il y a suffisamment d'espace disque disponible

## Remarques

- La première synchronisation peut prendre un certain temps car elle télécharge toutes les données nécessaires
- Les synchronisations suivantes seront plus rapides grâce au cache
- Il est recommandé d'exécuter régulièrement la synchronisation pour maintenir les données à jour
