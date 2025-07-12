# Optimisations des modèles Weapon et ProfessionWeaponType

Ce document décrit les optimisations apportées aux modèles `Weapon` et `ProfessionWeaponType` pour améliorer les performances et la maintenabilité du code.

## Table des matières

1. [Gestion des sessions](#gestion-des-sessions)
2. [Chargement par lots (Batch Loading)](#chargement-par-lots-batch-loading)
3. [Mise en cache](#mise-en-cache)
4. [Méthodes utilitaires](#méthodes-utilitaires)
5. [Meilleures pratiques](#meilleures-pratiques)
6. [Tests de performance](#tests-de-performance)
7. [Dépannage](#dépannage)

## Gestion des sessions

### Approche optimisée

Utilisation du décorateur `@with_session` pour une gestion automatique des sessions :

```python
from ..utils.db_utils import with_session

@with_session
def get_weapons_by_type(self, weapon_type: str, session: Session = None) -> List['Weapon']:
    return session.query(Weapon).filter(Weapon.type == weapon_type).all()
```

**Avantages** :
- Gestion automatique du cycle de vie des sessions
- Évite les fuites de connexion
- Code plus propre et plus maintenable

## Chargement par lots (Batch Loading)

### Problème

Le chargement d'objets liés un par un génère de nombreuses requêtes SQL (problème N+1).

### Solution

Utilisation de `joinedload` et de requêtes optimisées pour charger plusieurs objets en une seule requête.

**Exemple** :

```python
# Chargement optimisé des armes avec leurs compétences
weapons = session.query(Weapon).options(
    joinedload(Weapon.skills)
).filter(Weapon.id.in_(weapon_ids)).all()
```

## Mise en cache

### Méthodes avec cache

1. `get_skills_by_type()` - Cache des compétences par type
   - Taille max: 128 entrées
   - Invalidation manuelle avec `clear_cache()`

2. `get_profession_weapons()` - Cache des armes par profession
   - Invalidation manuelle avec `clear_cache()`

### Exemple d'utilisation

```python
# Premier appel - met en cache le résultat
weapons = weapon_type.get_weapons()

# Appels suivants - utilise le cache
cached_weapons = weapon_type.get_weapons()

# Invalider le cache si nécessaire
weapon_type.clear_cache()
```

## Méthodes utilitaires

### Récupération optimisée

```python
# Récupérer une arme par son ID avec chargement optimisé des relations
weapon = Weapon.get_by_id(weapon_id)

# Charger plusieurs armes en une seule requête
weapons = Weapon.batch_load_by_ids([1, 2, 3])

# Récupérer les compétences par slot
skills = weapon_type.get_skills_by_slot('1')
```

### Sérialisation

```python
# Sérialisation de base (sans les relations)
weapon_dict = weapon.to_dict(include_related=False)

# Sérialisation complète (avec les relations)
weapon_dict = weapon.to_dict(include_related=True)
```

## Meilleures pratiques

### Pour les requêtes fréquentes

```python
# Bon - utilise le chargement optimisé
with SessionManager() as session:
    weapons = Weapon.batch_load_by_ids(weapon_ids, session=session)

# Moins efficace (charge les relations une par une)
weapons = [Weapon.get_by_id(id) for id in weapon_ids]
```

### Pour la gestion du cache

```python
# Invalider le cache après des mises à jour
weapon.clear_cache()
weapon_type.clear_cache()

# Utiliser des clés de cache uniques
cache_key = f"{weapon_id}_{skill_type}"
```

## Tests de performance

Un ensemble de tests de performance est disponible pour valider les optimisations :

```bash
# Exécuter tous les tests
pytest tests/performance/test_weapon_performance.py -v

# Exécuter un test spécifique
pytest tests/performance/test_weapon_performance.py::TestWeaponPerformance::test_get_skills_by_type -v
```

### Métriques mesurées

1. **Temps d'exécution** : Temps moyen, minimum et maximum
2. **Utilisation du cache** : Comparaison des performances avec/sans cache
3. **Chargement par lots** : Comparaison avec l'approche un par un

## Dépannage

### Le cache ne se met pas à jour

- Vérifiez que vous appelez `clear_cache()` après avoir modifié les données
- Assurez-vous que les paramètres d'appel sont identiques (le cache est sensible aux arguments)

### Performances médiocres

1. Vérifiez que vous utilisez `@with_session` pour les méthodes accédant à la base de données
2. Utilisez le chargement par lots pour les relations
3. Vérifiez que les index sont correctement définis sur les colonnes fréquemment utilisées dans les requêtes

### Fuites de mémoire

- Assurez-vous que toutes les sessions sont correctement fermées
- Utilisez `with SessionManager() as session:` pour une gestion automatique des sessions
- Surveillez l'utilisation de la mémoire avec des outils comme `memory_profiler` si nécessaire

## Exemple complet

```python
# Chargement optimisé d'une arme avec ses relations
weapon = Weapon.get_by_id(123)

# Récupération des compétences avec mise en cache
weapon_skills = weapon.get_skills_by_type('weapon')

# Chargement par lots de plusieurs armes
weapons = Weapon.batch_load_by_ids([1, 2, 3])

# Récupération des armes par profession
profession_weapons = ProfessionWeaponType.batch_load_by_profession('Guardian')

# Sérialisation en JSON
weapon_data = weapon.to_dict(include_related=True)
```
