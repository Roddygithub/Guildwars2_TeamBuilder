"""
⚠️  ATTENTION : Ce fichier de test est actuellement désactivé ⚠️

Les modules d'optimisation génétique (genetic et pygad_optimizer) ont été désactivés
car ils ne font plus partie de l'approche actuelle du projet.

Si vous souhaitez réactiver ces tests, vous devrez :
1. Implémenter les modules manquants dans app/optimizer/
2. Mettre à jour les imports dans ce fichier
3. Retirer le décorateur @pytest.mark.skip des fonctions de test
"""
from __future__ import annotations

import time
from typing import List, Set, Tuple
import warnings

import pytest

# Ces imports sont commentés car les modules ne sont plus disponibles
# from app.optimizer.genetic import optimize_genetic as deap_optimize
# from app.optimizer.pygad_optimizer import optimize_genetic as pygad_optimize
# from app.scoring.engine import PlayerBuild
# from app.scoring.schema import ScoringConfig, RoleWeight, BuffWeight, DuplicatePenalty

# Avertissement pour indiquer que les tests sont désactivés
warnings.warn(
    "Les tests d'optimisation génétique sont actuellement désactivés. "
    "Voir le fichier test_pygad_optimizer.py pour plus d'informations.",
    ImportWarning,
    stacklevel=2
)

# Classes factices pour éviter les erreurs de compilation
class PlayerBuild:
    pass

class ScoringConfig:
    pass

class RoleWeight:
    pass

class BuffWeight:
    pass

class DuplicatePenalty:
    pass


@pytest.mark.skip(reason="Tests d'optimisation génétique désactivés")
def create_test_builds(count: int = 20) -> List[PlayerBuild]:
    """Create a list of test player builds."""
    # Cette fonction est désactivée car les modules d'optimisation ne sont plus disponibles
    return []
    for i in range(count):
        prof = professions[i % len(professions)]
        build = PlayerBuild(
            profession_id=prof,
            buffs={"might", "quickness"} if i % 4 == 0 else {"fury", "alacrity"},
            roles={"dps"},
            elite_spec=f"{prof}_elite" if i % 3 == 0 else "",
            playstyles={"zerg"} if i % 2 == 0 else {"havoc"},
            description=f"Test build {i} for {prof}",
            weapons=[f"{prof}_weapon1", f"{prof}_weapon2"],
            utilities=[f"{prof}_utility1", f"{prof}_utility2"],
        )
        builds.append(build)
    return builds


@pytest.mark.skip(reason="Tests d'optimisation génétique désactivés")
def create_test_config() -> ScoringConfig:
    """Create a test scoring configuration."""
    # Cette fonction est désactivée car les modules d'optimisation ne sont plus disponibles
    return ScoringConfig()


@pytest.mark.skip(reason="Tests d'optimisation génétique désactivés")
def test_pygad_optimizer_basic():
    """Test that the PyGAD optimizer returns valid results."""
    # Ce test est désactivé car les modules d'optimisation ne sont plus disponibles
    pass


@pytest.mark.skip(reason="Tests d'optimisation génétique désactivés")
def test_pygad_vs_deap_consistency():
    """Test that PyGAD and DEAP produce similar results."""
    # Ce test est désactivé car les modules d'optimisation ne sont plus disponibles
    pass


@pytest.mark.skip(reason="Tests d'optimisation génétique désactivés")
def test_optimizer_performance():
    """Test the performance of the PyGAD optimizer."""
    # Ce test est désactivé car les modules d'optimisation ne sont plus disponibles
    pass


if __name__ == "__main__":
    print("⚠️  Les tests d'optimisation génétique sont actuellement désactivés.")
    print("Pour les réactiver, consultez le fichier test_pygad_optimizer.py pour plus d'informations.")
