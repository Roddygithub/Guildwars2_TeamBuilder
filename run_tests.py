"""Script pour exécuter les tests unitaires avec affichage détaillé des résultats."""

import unittest
import sys
import os

def run_tests():
    """Exécute les tests unitaires et affiche les résultats."""
    # Ajout du répertoire racine au PYTHONPATH
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Découverte et exécution des tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Exécution des tests avec un test runner personnalisé
    test_runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = test_runner.run(test_suite)
    
    # Affichage d'un résumé
    print("\n" + "="*80)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    print(f"Tests ignorés: {len(result.skipped)}")
    print("="*80)
    
    # Affichage des échecs
    if result.failures:
        print("\nÉCHECS:")
        for failure in result.failures:
            print(f"\n{failure[0]}")
            print(failure[1])
    
    # Affichage des erreurs
    if result.errors:
        print("\nERREURS:")
        for error in result.errors:
            print(f"\n{error[0]}")
            print(error[1])
    
    # Code de sortie approprié
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    run_tests()
