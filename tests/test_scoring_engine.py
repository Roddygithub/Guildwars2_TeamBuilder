"""Tests unitaires pour le moteur de scoring."""
import pytest
from app.scoring.engine import PlayerBuild, score_team
from app.scoring.schema import BuffWeight, RoleWeight, DuplicatePenalty, ScoringConfig


def make_config() -> ScoringConfig:
    return ScoringConfig(
        buff_weights={
            "might": BuffWeight(weight=1.0),
            "quickness": BuffWeight(weight=1.5),
            "stability": BuffWeight(weight=1.2),
            "aegis": BuffWeight(weight=1.1),
        },
        role_weights={
            "heal": RoleWeight(required_count=1, weight=2.0),
            "dps": RoleWeight(required_count=2, weight=1.0),
            "support": RoleWeight(required_count=1, weight=1.5),
            "zerg": RoleWeight(required_count=3, weight=0.8),
            "havoc": RoleWeight(required_count=2, weight=1.0),
        },
        duplicate_penalty=DuplicatePenalty(threshold=1, penalty_per_extra=0.5),
    )


def create_basic_build(profession: str, buffs: set, roles: set, **kwargs) -> PlayerBuild:
    """Crée un build de base avec des valeurs par défaut pour les tests."""
    defaults = {
        "elite_spec": None,
        "playstyles": set(),
        "description": "",
        "weapons": [],
        "utilities": []
    }
    defaults.update(kwargs)
    return PlayerBuild(profession, buffs, roles, **defaults)


def test_full_coverage_scores_max():
    """Teste qu'une équipe avec tous les buffs et rôles requis obtient le score maximum."""
    config = make_config()
    team = [
        create_basic_build("guardian", {"might", "quickness"}, {"heal", "support"}),
        create_basic_build("warrior", {"stability"}, {"dps", "zerg"}),
        create_basic_build("elementalist", {"aegis"}, {"dps", "zerg", "havoc"}),
        create_basic_build("thief", set(), {"dps", "havoc"}),
    ]
    result = score_team(team, config)
    
    # Calcul détaillé du score attendu
    # Buffs: 1.0 (might) + 1.5 (quickness) + 1.2 (stability) + 1.1 (aegis) = 4.8
    # 
    # Rôles:
    # - heal: 2.0 (1/1 requis) = 2.0
    # - dps: 1.0 (3/2 requis, mais plafonné à 1.0) = 1.0
    # - support: 1.5 (1/1 requis) = 1.5
    # - zerg: 0.8 * (2/3 requis) = 0.8 * 0.666... = 0.533...
    # - havoc: 1.0 (2/2 requis) = 1.0
    # Total rôles: 2.0 + 1.0 + 1.5 + 0.533... + 1.0 = 6.033...
    #
    # Duplicatas: 0
    #
    # Score total: 4.8 + 6.033... ≈ 10.833...
    assert result.total_score == pytest.approx(10.833, abs=0.01)


def test_missing_buff_reduces_score():
    """Teste que les buffs manquants réduisent le score."""
    config = make_config()
    team = [
        create_basic_build("guardian", {"might"}, {"heal"}),
        create_basic_build("warrior", set(), {"dps"}),
        create_basic_build("elementalist", set(), {"dps"}),
    ]
    result = score_team(team, config)
    # Buffs: 1.0 (might) + 0 (quickness manquant) + 0 (stability manquant) + 0 (aegis manquant) = 1.0
    # Rôles: 2.0 (heal) + 1.0 (dps) = 3.0
    # Duplicatas: 0
    assert result.total_score == 4.0


def test_duplicate_penalty():
    """Teste que les doublons de profession sont pénalisés."""
    config = make_config()
    team = [
        create_basic_build("guardian", {"might", "quickness"}, {"heal"}),
        create_basic_build("guardian", set(), {"dps"}),  # doublon
        create_basic_build("warrior", set(), {"dps"}),
    ]
    result = score_team(team, config)
    # Buffs: 1.0 + 1.5 = 2.5
    # Rôles: 2.0 + 1.0 = 3.0
    # Pénalité doublon: -0.5
    assert result.total_score == 5.0


def test_wvw_specific_roles():
    """Teste les rôles spécifiques au WvW."""
    config = make_config()
    team = [
        create_basic_build("firebrand", {"stability", "aegis"}, {"support", "zerg"}, elite_spec="Firebrand"),
        create_basic_build("scourge", {"barrier"}, {"dps", "zerg"}, elite_spec="Scourge"),
        create_basic_build("spellbreaker", {"might"}, {"dps", "havoc"}, elite_spec="Spellbreaker"),
        create_basic_build("herald", {"fury", "protection"}, {"support", "havoc"}, elite_spec="Herald"),
    ]
    result = score_team(team, config)
    
    # Vérifie que les rôles WvW sont correctement évalués
    role_coverage = {rc.role: (rc.fulfilled_count, rc.required_count) 
                    for rc in result.role_coverage}
    
    # Vérifie que les rôles spécifiques au WvW sont présents
    assert "zerg" in role_coverage
    assert "havoc" in role_coverage
    
    # Vérifie que les builds avec des spécialisations d'élite sont correctement identifiés
    assert team[0].elite_spec == "Firebrand"
    assert team[1].elite_spec == "Scourge"
    assert team[2].elite_spec == "Spellbreaker"
    assert team[3].elite_spec == "Herald"


def test_playstyles():
    """Teste que les playstyles sont correctement gérés."""
    zerg_build = create_basic_build("guardian", set(), set(), playstyles={"zerg"})
    havoc_build = create_basic_build("thief", set(), set(), playstyles={"havoc"})
    
    assert "zerg" in zerg_build.playstyles
    assert "havoc" in havoc_build.playstyles
    assert "roaming" not in zerg_build.playstyles  # 5.5 - 0.5
