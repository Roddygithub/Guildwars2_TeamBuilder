# Optimisations du modèle Skill

Ce document décrit les optimisations apportées au modèle `Skill` pour améliorer les performances et la maintenabilité du code.

## Table des matières

1. [Gestion des sessions](#gestion-des-sessions)
2. [Chargement par lots (Batch Loading)](#chargement-par-lots-batch-loading)
3. [Mise en cache](#mise-en-cache)
4. [Meilleures pratiques](#meilleures-pratiques)
5. [Tests de performance](#tests-de-performance)
6. [Dépannage](#dépannage)

## Gestion des sessions

### Ancienne approche (à éviter)

```python
def get_related_skills(self):
    from sqlalchemy.orm import Session
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        # Code utilisant la session
        return result
    finally:
        db.close()
```

### Nouvelle approche (recommandée)

```python
from ..utils.db_utils import with_session

@with_session
def get_related_skills(self, session: Session = None):
    # Code utilisant la session
    return result
```

**Avantages** :
- Gestion automatique du cycle de vie des sessions
- Évite les fuites de connexion
- Code plus propre et plus maintenable

## Chargement par lots (Batch Loading)

### Problème

Le chargement d'objets liés un par un génère de nombreuses requêtes SQL (problème N+1).

### Solution

Utilisation de `selectinload` et de requêtes optimisées pour charger plusieurs objets en une seule requête.

**Exemple** :

```python
# Au lieu de :
for skill_id in skill_ids:
    skill = session.query(Skill).get(skill_id)  # N+1 queries

# Utilisez :
skills = session.query(Skill).filter(Skill.id.in_(skill_ids)).all()  # 1 query
```

## Mise en cache

### Méthodes avec cache

1. `get_skill_facts(include_traited=True)`
   - Cache: 128 entrées
   - Invalidation manuelle avec `clear_cache()`

2. `get_skill_facts_by_type(fact_type, include_traited=True)`
   - Cache: 512 entrées
   - Partage le cache avec `get_skill_facts()`

3. `get_skill_fact_value(fact_type, attribute=None, default=None)`
   - Cache: 1024 entrées
   - Utilise le cache de `get_skill_facts_by_type()`

### Exemple d'utilisation

```python
# Premier appel - met en cache le résultat
facts = skill.get_skill_facts()

# Appels suivants - utilise le cache
cached_facts = skill.get_skill_facts()

# Invalider le cache si nécessaire
skill.clear_cache()
```

## Meilleures pratiques

### Pour les requêtes fréquentes

```python
# Bon
with SessionManager() as session:
    skills = skill.get_related_skills(session=session)

# Moins efficace (crée une nouvelle session)
skills = skill.get_related_skills()
```

### Pour les données fréquemment accédées

```python
# Utilise le cache automatiquement
damage = skill.get_skill_fact_value('Damage', 'dmg_multiplier')
```

### Pour les mises à jour

```python
# Après modification des données
skill.clear_cache()  # Invalide le cache si nécessaire
```

## Tests de performance

Un ensemble de tests de performance est disponible pour valider les optimisations :

```bash
# Exécuter tous les tests
pytest tests/performance/test_skill_performance.py -v

# Exécuter un test spécifique
pytest tests/performance/test_skill_performance.py::TestSkillPerformance::test_get_related_skills_performance -v
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
