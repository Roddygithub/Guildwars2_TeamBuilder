# Tests d'Intégration GW2 Data Service

Ce répertoire contient les tests d'intégration pour le service de données GW2. Ces tests vérifient le bon fonctionnement de la synchronisation des données avec l'API GW2 et leur stockage en base de données.

## Structure des Tests

- `test_gw2_data_service.py` : Contient les tests d'intégration principaux pour le `GW2DataService`
- `conftest.py` : Configuration partagée pour les tests (fixtures, etc.)
- `data/` : Données de test (à ajouter si nécessaire)

## Prérequis

- Python 3.8+
- Bibliothèques de test (installées via `pip install -r requirements-dev.txt`)
- Une clé API GW2 valide (optionnelle pour les tests mockés)

## Configuration

1. Créez un fichier `.env` à la racine du projet avec les variables suivantes :
   ```
   # Clé API GW2 (optionnelle pour les tests mockés)
   GW2_API_KEY=votre_cle_api
   
   # Configuration de la base de données de test
   TEST_DATABASE_URL=sqlite:///:memory:
   ```

## Exécution des Tests

### Tous les tests
```bash
pytest -v
```

### Tests spécifiques
```bash
# Tests d'une classe spécifique
pytest -v tests/test_gw2_data_service.py::TestGW2DataServiceIntegration

# Un test spécifique
pytest -v tests/test_gw2_data_service.py::TestGW2DataServiceIntegration::test_sync_professions

# Tests avec marqueurs
pytest -v -m "not slow"  # Exclure les tests lents
pytest -v -m performance  # Uniquement les tests de performance
```

### Couverture de code
```bash
pytest --cov=app --cov-report=html
```

## Écrire de Nouveaux Tests

1. **Fixtures** : Utilisez les fixtures existantes (`db_session`, `gw2_service`) pour configurer l'environnement de test.

2. **Mocking** : Utilisez `unittest.mock` pour simuler les appels API et isoler les tests.

3. **Marqueurs** : Utilisez les marqueurs appropriés pour catégoriser vos tests :
   - `@pytest.mark.slow` pour les tests lents
   - `@pytest.mark.integration` pour les tests d'intégration
   - `@pytest.mark.performance` pour les tests de performance
   - `@pytest.mark.api` pour les tests nécessitant un accès à l'API GW2

4. **Assertions** : Utilisez des assertions claires et descriptives pour faciliter le débogage.

## Bonnes Pratiques

- **Isolation** : Chaque test doit être indépendant et ne pas dépendre de l'état créé par d'autres tests.
- **Nettoyage** : Utilisez les fixtures pour nettoyer les ressources après chaque test.
- **Données de test** : Utilisez des données de test réalistes mais minimales.
- **Documentation** : Commentez les tests complexes pour expliquer leur objectif.

## Dépannage

### Erreurs de base de données
- Assurez-vous que les migrations sont à jour
- Vérifiez que la base de données de test est correctement configurée

### Problèmes de mock
- Vérifiez que les mocks sont correctement configurés avant l'appel à la méthode testée
- Utilisez `pytest --pdb` pour déboguer les tests en cas d'échec

### Tests lents
- Marquez les tests lents avec `@pytest.mark.slow`
- Utilisez `pytest -m "not slow"` pour les exclure lors des exécutions rapides
