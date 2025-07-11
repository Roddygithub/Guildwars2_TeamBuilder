# Service de Données GW2

## Vue d'ensemble
Le `GW2DataService` est un service complet pour interagir avec l'API Guild Wars 2, gérer le cache des données et synchroniser les informations avec une base de données locale. Il fournit une interface de haut niveau pour accéder aux données du jeu de manière efficace et fiable.

## Fonctionnalités Principales

### 1. Synchronisation des Données
- Récupération et mise à jour des données depuis l'API GW2
- Gestion des dépendances entre les différentes entités (professions, compétences, etc.)
- Mise en cache intelligente pour réduire les appels API inutiles

### 2. Gestion du Cache
- Cache en mémoire pour les requêtes fréquentes
- Support pour Redis comme solution de cache distribué
- Invalidation automatique du cache basée sur la durée de vie (TTL)

### 3. Gestion des Erreurs
- Gestion centralisée des erreurs d'API
- Tentatives automatiques avec backoff exponentiel
- Journalisation détaillée pour le débogage

## Installation et Configuration

### Prérequis
- Python 3.8+
- Base de données SQLite/PostgreSQL (selon la configuration)
- Redis (optionnel pour le cache distribué)

### Installation des Dépendances
```bash
# Dépendances principales
pip install -r requirements.txt

# Pour le support Redis (optionnel)
pip install redis
```

### Configuration
Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```ini
# Clé API GW2 (obligatoire)
GW2_API_KEY=votre_cle_api

# Configuration de la base de données (optionnel, SQLite par défaut)
DATABASE_URL=sqlite:///gw2_team_builder.db

# Configuration Redis (optionnel)
REDIS_URL=redis://localhost:6379/0
```

## Utilisation de Base

### Initialisation du Service
```python
from app.services.gw2_data_service import get_gw2_data_service

# Obtenir une instance du service
service = get_gw2_data_service()

# Initialisation explicite (si nécessaire)
await service.initialize()
```

### Synchronisation des Données
```python
# Synchronisation complète des données
result = await service.sync_all()
print(f"Synchronisation terminée : {result}")

# Synchronisation spécifique (ex: compétences)
result = await service.sync_skills()
print(f"Compétences synchronisées : {result['processed']} éléments")
```

### Utilisation du Cache
```python
# Obtenir des informations sur le cache
cache_info = await service.get_cache_info()
print(f"Taille du cache : {cache_info['api_cache']['size']} octets")

# Vider le cache
await service.clear_cache()
```

## Méthodes Avancées

### Requêtes par Lots
```python
# Récupérer plusieurs compétences par leurs IDs
skill_ids = [1, 2, 3, 4, 5]
skills = await service._batch_api_request("skills", skill_ids)
for skill_id, skill_data in skills.items():
    print(f"Compétence {skill_id}: {skill_data.get('name')}")
```

### Utilisation du Cache Redis
Pour activer le cache distribué avec Redis, assurez-vous que Redis est installé et configuré, puis utilisez le décorateur `@redis_cache` :

```python
from app.services.gw2_data_service import redis_cache

class MonService:
    @redis_cache(ttl=3600)  # Cache de 1 heure
    async def get_skill_details(self, skill_id: int):
        # Logique pour récupérer les détails d'une compétence
        return await self._api.get_skill(skill_id)
```

## Gestion des Erreurs
Le service inclut une gestion d'erreurs robuste qui peut être utilisée comme suit :

```python
try:
    await service.sync_all()
except Exception as e:
    error_info = await service._handle_api_error(e, "Synchronisation complète")
    print(f"Erreur {error_info['error_id']}: {error_info['message']}")
    print(f"Suggestion: {error_info.get('suggestion', 'Aucune suggestion disponible')}")
```

## Journalisation
Le service utilise le module `logging` de Python. Pour configurer la journalisation :

```python
import logging

# Configurer le niveau de journalisation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GW2DataService")

# Pour un débogage détaillé
# logging.basicConfig(level=logging.DEBUG)
```

## Bonnes Pratiques

1. **Utilisation du Cache** : Toujours privilégier les méthodes mises en cache pour les requêtes fréquentes.
2. **Gestion des Erreurs** : Toujours envelopper les appels au service dans des blocs try/except.
3. **Fermeture des Ressources** : Appeler `close()` sur le service lorsqu'il n'est plus nécessaire.
4. **Synchronisation** : Effectuer les synchronisations complètes pendant les périodes de faible charge.

## Dépannage

### Problèmes de Connexion
- Vérifiez que votre clé API est valide et a les permissions nécessaires
- Assurez-vous que le service GW2 API est accessible depuis votre réseau

### Problèmes de Performances
- Activez le cache Redis pour les déploiements en production
- Ajustez la taille des lots pour les requêtes par lots en fonction de votre charge

### Problèmes de Données
- Vérifiez les logs pour les erreurs de validation des données
- Utilisez `clear_cache()` si vous soupçonnez des données obsolètes

## Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
