"""Tests for the PyGAD-based genetic optimizer."""
from __future__ import annotations

import time
from typing import List, Set, Tuple

import pytest

from app.optimizer.genetic import optimize_genetic as deap_optimize
from app.optimizer.pygad_optimizer import optimize_genetic as pygad_optimize
from app.scoring.engine import PlayerBuild
from app.scoring.schema import ScoringConfig, RoleWeight, BuffWeight, DuplicatePenalty


def create_test_builds(count: int = 20) -> List[PlayerBuild]:
    """Create a list of test player builds."""
    professions = ["guardian", "warrior", "elementalist", "thief", "ranger",
                  "engineer", "necromancer", "mesmer", "revenant"]
    
    builds = []
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


def create_test_config() -> ScoringConfig:
    """Create a test scoring configuration."""
    return ScoringConfig(
        role_weights={
            "dps": RoleWeight(weight=1.0, required_count=2),
            "heal": RoleWeight(weight=2.0, required_count=1),
            "support": RoleWeight(weight=1.5, required_count=1),
            "zerg": RoleWeight(weight=0.8, required_count=3),
            "havoc": RoleWeight(weight=1.0, required_count=2),
        },
        buff_weights={
            "might": BuffWeight(weight=1.0),
            "quickness": BuffWeight(weight=1.5),
            "alacrity": BuffWeight(weight=1.2),
            "fury": BuffWeight(weight=1.0),
            "stability": BuffWeight(weight=1.2),
            "aegis": BuffWeight(weight=1.1),
        },
        duplicate_penalty=DuplicatePenalty(threshold=1, penalty_per_extra=0.5),
    )


def test_pygad_optimizer_basic():
    """Test that the PyGAD optimizer returns valid results."""
    config = create_test_config()
    candidates = create_test_builds(30)
    
    # Run with a small population and few generations for quick testing
    results = pygad_optimize(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=50,
        generations=10,
        random_seed=42,
    )
    
    # Basic assertions
    assert len(results) > 0
    for score_result, team in results:
        assert len(team) == 5
        assert score_result.total_score > 0
        assert score_result.role_breakdown is not None
        assert score_result.buff_breakdown is not None


def test_pygad_vs_deap_consistency():
    """Test that PyGAD and DEAP produce similar results."""
    config = create_test_config()
    candidates = create_test_builds(20)
    
    # Run both optimizers with the same seed
    pygad_results = pygad_optimize(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=100,
        generations=20,
        random_seed=42,
    )
    
    deap_results = deap_optimize(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=100,
        generations=20,
        random_seed=42,
    )
    
    # Both should find teams with similar scores
    assert len(pygad_results) > 0
    assert len(deap_results) > 0
    
    # Top scores should be similar (within 10%)
    pygad_best = pygad_results[0][0].total_score
    deap_best = deap_results[0][0].total_score
    assert abs(pygad_best - deap_best) / max(pygad_best, deap_best) < 0.1


def test_optimizer_performance():
    """Test the performance of the PyGAD optimizer."""
    config = create_test_config()
    candidates = create_test_builds(50)
    
    # Time the optimization
    start_time = time.time()
    results = pygad_optimize(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=100,
        generations=50,
        random_seed=42,
    )
    elapsed = time.time() - start_time
    
    print(f"\nPyGAD optimization took {elapsed:.2f} seconds")
    print(f"Best score: {results[0][0].total_score:.2f}")
    
    # Basic validation
    assert len(results) > 0
    assert all(len(team) == 5 for _, team in results)
    assert elapsed < 10.0  # Should complete in under 10 seconds


if __name__ == "__main__":
    # Quick performance comparison between DEAP and PyGAD
    config = create_test_config()
    candidates = create_test_builds(50)
    
    print("Running DEAP optimizer...")
    start = time.time()
    deap_results = deap_optimize(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=200,
        generations=50,
        random_seed=42,
    )
    deap_time = time.time() - start
    print(f"DEAP: {deap_time:.2f}s - Best score: {deap_results[0][0].total_score:.2f}")
    
    print("\nRunning PyGAD optimizer...")
    start = time.time()
    pygad_results = pygad_optimize(
        team_size=5,
        candidates=candidates,
        config=config,
        population_size=200,
        generations=50,
        random_seed=42,
    )
    pygad_time = time.time() - start
    print(f"PyGAD: {pygad_time:.2f}s - Best score: {pygad_results[0][0].total_score:.2f}")
    
    print(f"\nSpeedup: {deap_time/pygad_time:.2f}x")
    print(f"Score difference: {abs(pygad_results[0][0].total_score - deap_results[0][0].total_score):.2f}")
    print(f"PyGAD best team score: {pygad_results[0][0].total_score:.2f}")
    print("Roles:", {r.role: f"{r.fulfilled_count}/{r.required_count}" for r in pygad_results[0][0].role_breakdown})
    print("Buffs:", {b.buff: b.covered for b in pygad_results[0][0].buff_breakdown})
