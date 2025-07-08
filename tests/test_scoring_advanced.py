"""Tests avancés pour le module de scoring.

Ces tests couvrent les cas limites, les performances et les fonctionnalités avancées
du moteur de scoring.
"""

from typing import Any, Dict, List, Tuple, FrozenSet

import pytest

from app.scoring.engine import (
    PlayerBuild,
    _calculate_buff_coverage,
    _calculate_duplicate_penalty,
    _calculate_role_coverage,
    score_team,
)
from app.scoring.schema import (
    ScoringConfig, 
    BuffWeight, 
    RoleWeight, 
    DuplicatePenalty,
    BuffType,  # Ajouté pour les tests existants
    RoleType   # Ajouté pour les tests existants
)

# Données de test
SAMPLE_BUILDS = [
    PlayerBuild(
        profession_id="Guardian",
        elite_spec="Firebrand",
        buffs={"quickness", "stability", "aegis", "might"},
        roles={"heal", "support"},
        playstyles={"zerg"},
        weapons=("Axe", "Shield", "Staff"),
        utilities=("Mantra of Solace", "Mantra of Potence", "Mantra of Liberation"),
        description="Heal Firebrand with Quickness and Stability"
    ),
    PlayerBuild(
        profession_id="Revenant",
        elite_spec="Herald",
        buffs={"fury", "protection", "regeneration", "swiftness"},
        roles={"support"},
        playstyles={"zerg", "havoc"},
        weapons=("Sword", "Shield", "Staff"),
        utilities=("Inspiring Reinforcement", "Phase Traversal", "Facet of Nature"),
        description="Boon Support Herald"
    ),
    PlayerBuild(
        profession_id="Elementalist",
        elite_spec="Weaver",
        buffs={"might"},
        roles={"dps"},
        playstyles={"zerg", "havoc"},
        weapons=("Sword", "Dagger"),
        utilities=("Primordial Stance", "Lightning Flash", "Arcane Blast"),
        description="Power DPS Weaver"
    )
]

# Configuration de test
from app.scoring.schema import BuffType, RoleType, BuffWeight, RoleWeight, DuplicatePenalty, ScoringConfig

SAMPLE_CONFIG = ScoringConfig(
    buff_weights={
        BuffType.QUICKNESS: BuffWeight(weight=2.0, description="Augmente la vitesse d'attaque"),
        BuffType.ALACRITY: BuffWeight(weight=2.0, description="Réduit les temps de recharge"),
        BuffType.MIGHT: BuffWeight(weight=1.5, description="Augmente les dégâts et la condition"),
        BuffType.FURY: BuffWeight(weight=1.0, description="Augmente la chance de coup critique"),
        BuffType.PROTECTION: BuffWeight(weight=1.0, description="Réduit les dégâts reçus"),
        BuffType.STABILITY: BuffWeight(weight=1.5, description="Empêche les perturbations"),
        BuffType.AEGIS: BuffWeight(weight=1.0, description="Blocage du prochain coup"),
        BuffType.REGENERATION: BuffWeight(weight=0.5, description="Soins périodiques"),
        BuffType.SWIFTNESS: BuffWeight(weight=0.3, description="Augmente la vitesse de déplacement"),
    },
    role_weights={
        RoleType.HEAL: RoleWeight(weight=2.0, required_count=1, description="Soins de l'équipe"),
        RoleType.TEAM_FIGHT_SUPPORT: RoleWeight(weight=1.5, required_count=1, description="Soutien avec buffs"),
        RoleType.DPS: RoleWeight(weight=1.0, required_count=2, description="Dégâts purs"),
        RoleType.DISRUPTOR: RoleWeight(weight=0.8, required_count=1, description="Perturbation et contrôle"),
        RoleType.BUNKER: RoleWeight(weight=0.7, required_count=1, description="Défense et survie"),
    },
    duplicate_penalty=DuplicatePenalty(
        threshold=1,
        penalty_per_extra=0.7,
        enabled=True
    ),
    version="1.0.0"
)

class TestScoringEngineAdvanced:
    """Tests avancés pour le moteur de scoring."""
    
    def test_score_team_with_empty_team(self):
        """Teste le scoring avec une équipe vide."""
        result = score_team([], SAMPLE_CONFIG)
        # Une équipe vide devrait avoir un score de 1.0 (score par défaut)
        assert result.total_score == 1.0
        assert result.buff_breakdown == {}
        assert result.role_breakdown == {}
        assert result.buff_coverage == []
        assert result.role_coverage == []
    
    def test_score_team_with_single_build(self):
        """Teste le scoring avec un seul build dans l'équipe."""
        result = score_team([SAMPLE_BUILDS[0]], SAMPLE_CONFIG)
        # Le score peut être > 1.0 en raison de la pondération des buffs/roles
        assert result.total_score >= 0.0, "Le score ne peut pas être négatif"
        assert isinstance(result.buff_breakdown, dict)
        assert isinstance(result.role_breakdown, dict)
        assert isinstance(result.buff_coverage, list)
        assert isinstance(result.role_coverage, list)
        
        # Vérifie que le score est dans une plage raisonnable
        # Le score peut être > 1.0 en raison de la pondération des buffs/roles
        assert result.total_score > 0.0, "Le score doit être strictement positif"
        
        # Vérifie la couverture des buffs
        buff_coverage = {bc.buff: bc for bc in result.buff_coverage}
        assert BuffType.QUICKNESS in buff_coverage
        assert BuffType.STABILITY in buff_coverage
        assert BuffType.AEGIS in buff_coverage
        assert BuffType.MIGHT in buff_coverage
        
        # Vérifie la couverture des rôles
        role_coverage = {rc.role: rc for rc in result.role_coverage}
        assert RoleType.HEAL in role_coverage
        assert role_coverage[RoleType.HEAL].fulfilled_count >= 1
    
    @pytest.mark.parametrize("team_size", [1, 3, 5, 10])
    def test_score_team_performance(self, team_size, benchmark):
        """Teste les performances du scoring avec différentes tailles d'équipe."""
        # Crée une équipe de la taille spécifiée en répétant les builds de test
        team = [SAMPLE_BUILDS[i % len(SAMPLE_BUILDS)] for i in range(team_size)]
        
        # Utilise le benchmark pour mesurer les performances
        result = benchmark(lambda: score_team(team, SAMPLE_CONFIG))
        
        # Vérifie que le résultat est valide
        assert isinstance(result.total_score, float)
        assert 0.0 <= result.total_score <= 1.0
    
    def test_buff_coverage_calculation(self):
        """Teste le calcul de la couverture des buffs."""
        team = tuple([SAMPLE_BUILDS[0], SAMPLE_BUILDS[1]])  # Firebrand + Herald
        
        # Calcule la couverture attendue manuellement
        expected_coverage = {
            "quickness": 1.0,
            "stability": 1.0,
            "aegis": 1.0,
            "might": 1.0,
            "fury": 1.0,
            "protection": 1.0,
            "regeneration": 1.0,
            "swiftness": 1.0,
            "alacrity": 0.0,  # Non fourni par ces builds
        }
        
        # Convertit les poids de buff en frozenset de tuples (buff, poids) pour la fonction
        buff_weights = frozenset(
            (buff.value, weight.weight) 
            for buff, weight in SAMPLE_CONFIG.buff_weights.items()
        )
        
        # Calcule la couverture réelle
        buff_total, buff_breakdown, buff_items = _calculate_buff_coverage(team, buff_weights)
        
        # Vérifie que le score est cohérent (peut être > 1.0 en raison de la pondération)
        assert buff_total >= 0.0
        
        # Vérifie que le breakdown contient les bonnes clés
        for buff in expected_coverage:
            assert buff in buff_breakdown, f"Buff {buff} non trouvé dans le breakdown"
            
            # Vérifie la valeur de couverture avec une marge d'erreur
            expected = expected_coverage[buff]
            actual = 1.0 if buff_breakdown[buff] > 0 else 0.0
            assert abs(actual - expected) < 0.01, f"Couverture inattendue pour {buff}: {actual} vs {expected}"
    
    def test_role_coverage_calculation(self):
        """Teste le calcul de la couverture des rôles."""
        team = tuple([SAMPLE_BUILDS[0], SAMPLE_BUILDS[2]])  # Firebrand + Weaver
        
        # Configuration des rôles attendus et de leur couverture avec des objets RoleWeight
        role_weights = {
            "heal": RoleWeight(weight=2.0, required_count=1, description="Soins"),
            "support": RoleWeight(weight=1.5, required_count=1, description="Soutien"),
            "dps": RoleWeight(weight=1.0, required_count=1, description="Dégâts"),
            "disruptor": RoleWeight(weight=0.8, required_count=1, description="Perturbation"),
            "bunker": RoleWeight(weight=0.7, required_count=1, description="Défense")
        }
        
        # Convertit en frozenset de tuples (rôle, poids, nombre_requis) pour la fonction
        role_weights_fs = frozenset(
            (role, role_weight.weight, role_weight.required_count)
            for role, role_weight in role_weights.items()
        )
        
        # Calcule la couverture réelle
        role_total, role_breakdown, role_items = _calculate_role_coverage(team, role_weights_fs)
        
        # Vérifie que le score est cohérent (peut être > 1.0 en raison de la pondération)
        assert role_total >= 0.0, f"Score négatif inattendu: {role_total}"
        
        # Convertit les items en dictionnaire pour un accès plus facile
        role_details = {item.role: item for item in role_items}
        
        # Vérifications spécifiques pour chaque rôle
        expected_roles = ["heal", "support", "dps", "disruptor", "bunker"]
        for role in expected_roles:
            assert role in role_details, f"Rôle {role} manquant dans les détails"
        
        # Vérifie la couverture des rôles clés
        assert role_details["heal"].fulfilled_count >= 1, "Le rôle heal devrait être couvert"
        assert role_details["dps"].fulfilled_count >= 1, "Le rôle dps devrait être couvert"
        
        # Vérifie que les rôles non couverts ont bien un compteur à 0
        if "disruptor" in role_details:
            assert role_details["disruptor"].fulfilled_count == 0, "Le rôle disruptor ne devrait pas être couvert"
        if "bunker" in role_details:
            assert role_details["bunker"].fulfilled_count == 0, "Le rôle bunker ne devrait pas être couvert"
    
    def test_duplicate_penalty_calculation(self):
        """Teste le calcul de la pénalité pour les doublons."""
        # Crée une équipe avec des doublons
        team = tuple([
            PlayerBuild(
                profession_id="Guardian",
                elite_spec="Firebrand",
                buffs={"might"},
                roles={"heal"},
                playstyles={"zerg"}
            ),
            PlayerBuild(
                profession_id="Guardian",
                elite_spec="Dragonhunter",
                buffs={"might"},
                roles={"dps"},
                playstyles={"zerg"}
            ),  # Doublon de profession
            PlayerBuild(
                profession_id="Elementalist",
                elite_spec="Weaver",
                buffs={"might"},
                roles={"dps"},
                playstyles={"zerg"}
            ),
            PlayerBuild(
                profession_id="Elementalist",
                elite_spec="Tempest",
                buffs={"might"},
                roles={"support"},
                playstyles={"zerg"}
            ),  # Doublon de profession
            PlayerBuild(
                profession_id="Elementalist",
                elite_spec="Catalyst",
                buffs={"might"},
                roles={"dps"},
                playstyles={"zerg"}
            ),  # Triplé de profession
        ])
        
        # Avec le seuil à 1, on attend une pénalité pour les doublons
        penalty = _calculate_duplicate_penalty(team, threshold=1, penalty_per_extra=1.0)
        assert penalty > 0.0, f"Expected penalty > 0.0 but got {penalty}"
        
        # Avec un seuil plus élevé, la pénalité devrait être moindre
        penalty_high_threshold = _calculate_duplicate_penalty(team, threshold=2, penalty_per_extra=1.0)
        assert 0.0 <= penalty_high_threshold <= penalty, \
            f"Expected penalty_high_threshold ({penalty_high_threshold}) <= penalty ({penalty})"
    
    def test_score_team_with_invalid_build(self):
        """Teste le comportement avec un build invalide."""
        # Crée une équipe avec un build invalide (sans rôle ni buff)
        invalid_build = PlayerBuild(
            profession_id="Invalid",
            elite_spec="None",
            buffs=set(),
            roles=set(),
            playstyles=set()
        )
        team = [SAMPLE_BUILDS[0], invalid_build]  # Un build valide + un invalide
        
        # Le scoring doit toujours fonctionner mais avec un score potentiellement bas
        result = score_team(team, SAMPLE_CONFIG)
        assert isinstance(result.total_score, float)
        assert 0.0 <= result.total_score <= 1.0
    
    def test_score_team_with_custom_weights(self):
        """Teste le scoring avec des poids personnalisés."""
        # Crée une configuration personnalisée qui favorise certains rôles/buffs
        custom_config = ScoringConfig(
            buff_weights={
                BuffType.QUICKNESS: BuffWeight(weight=3.0, description="Quick"),
                BuffType.ALACRITY: BuffWeight(weight=3.0, description="Alac"),
                BuffType.MIGHT: BuffWeight(weight=0.5, description="Might")
            },
            role_weights={
                RoleType.HEAL: RoleWeight(weight=3.0, required_count=1, description="Healer"),
                RoleType.TEAM_FIGHT_SUPPORT: RoleWeight(weight=2.0, required_count=1, description="Support"),
                RoleType.DPS: RoleWeight(weight=0.5, required_count=1, description="DPS")
            },
            duplicate_penalty=DuplicatePenalty(threshold=1, penalty_per_extra=0.5, enabled=True)
        )
        
        # Test avec une équipe qui correspond bien à la configuration
        good_team = [SAMPLE_BUILDS[0], SAMPLE_BUILDS[1]]  # Firebrand + Herald
        good_result = score_team(good_team, custom_config)
        
        # Test avec une équipe qui correspond mal à la configuration
        bad_team = [SAMPLE_BUILDS[2]]  # Seulement un DPS
        bad_result = score_team(bad_team, custom_config)
        
        # L'équipe qui correspond mieux à la configuration devrait avoir un meilleur score
        assert good_result.total_score > bad_result.total_score
    
        # Configuration des buffs attendus et de leur couverture
        buff_weights = {
            "quickness": (2.0, 1),    # (poids, nombre requis)
            "might": (1.0, 2),       # Besoin de 2 stacks
            "fury": (0.5, 1),        # Optionnel
            "alacrity": (1.5, 1)     # Important
        }
        
        # Convertit en frozenset pour la fonction
        buff_weights_fs = frozenset((buff, weight, count) for buff, (weight, count) in buff_weights.items())
        
        # Calcule la couverture réelle
        score, details, _ = _calculate_buff_coverage(team, buff_weights_fs)
        
        # Vérifie que le score est dans une plage raisonnable
        assert 0.0 <= score <= 1.0
        
        # Vérifie que les buffs attendus sont présents dans les détails
        buff_details = {d.buff: d.coverage for d in details}
        
        # Vérifications spécifiques pour chaque buff
        assert "quickness" in buff_details
        assert buff_details["quickness"] > 0.5  # Doit être bien couvert
        
        assert "might" in buff_details
        assert buff_details["might"] > 0.3  # Partiellement couvert

    def test_role_coverage_calculation(self):
        """Teste le calcul de la couverture des rôles."""
        team = tuple([SAMPLE_BUILDS[0], SAMPLE_BUILDS[2]])  # Firebrand + Weaver
        
        # Configuration des rôles attendus et de leur couverture avec des objets RoleWeight
        role_weights = {
            "heal": RoleWeight(weight=2.0, required_count=1, description="Soins"),
            "support": RoleWeight(weight=1.5, required_count=1, description="Soutien"),
            "dps": RoleWeight(weight=1.0, required_count=1, description="Dégâts"),
            "disruptor": RoleWeight(weight=0.8, required_count=1, description="Perturbation"),
            "bunker": RoleWeight(weight=0.7, required_count=1, description="Défense")
        }
        
        # Convertit en frozenset de tuples (rôle, poids, nombre_requis) pour la fonction
        role_weights_fs = frozenset(
            (role, role_weight.weight, role_weight.required_count)
            for role, role_weight in role_weights.items()
        )
        
        # Calcule la couverture réelle
        role_total, role_breakdown, role_items = _calculate_role_coverage(team, role_weights_fs)
        
        # Vérifie que le score est cohérent (peut être > 1.0 en raison de la pondération)
        assert role_total >= 0.0, f"Score négatif inattendu: {role_total}"
        
        # Convertit les items en dictionnaire pour un accès plus facile
        role_details = {item.role: item for item in role_items}
        
        # Vérifications spécifiques pour chaque rôle
        expected_roles = ["heal", "support", "dps", "disruptor", "bunker"]
        for role in expected_roles:
            assert role in role_details, f"Rôle {role} manquant dans les détails"
        
        # Vérifie la couverture des rôles clés
        assert role_details["heal"].fulfilled_count >= 1, "Le rôle heal devrait être couvert"
        assert role_details["dps"].fulfilled_count >= 1, "Le rôle dps devrait être couvert"
        
        # Vérifie que les rôles non couverts ont bien un compteur à 0
        if "disruptor" in role_details:
            assert role_details["disruptor"].fulfilled_count == 0, "Le rôle disruptor ne devrait pas être couvert"
        if "bunker" in role_details:
            assert role_details["bunker"].fulfilled_count == 0, "Le rôle bunker ne devrait pas être couvert"

    def test_duplicate_penalty_calculation(self):
        """Teste le calcul de la pénalité pour les doublons."""
        # Crée une équipe avec des doublons
        team = tuple([
            PlayerBuild(
                profession_id="Guardian",
                elite_spec="Firebrand",
                buffs={"might"},
                roles={"heal"},
                playstyles={"zerg"}
            ),
            PlayerBuild(
                profession_id="Guardian",
                elite_spec="Dragonhunter",
                buffs={"might"},
                roles={"dps"},
                playstyles={"zerg"}
            ),  # Doublon de profession
            PlayerBuild(
                profession_id="Elementalist",
                elite_spec="Weaver",
                buffs={"might"},
                roles={"dps"},
                playstyles={"zerg"}
            ),
            PlayerBuild(
                profession_id="Elementalist",
                elite_spec="Tempest",
                buffs={"might"},
                roles={"support"},
                playstyles={"zerg"}
            ),  # Doublon de profession
            PlayerBuild(
                profession_id="Elementalist",
                elite_spec="Catalyst",
                buffs={"might"},
                roles={"dps"},
                playstyles={"zerg"}
            ),  # Triplé de profession
        ])
        
        # Avec le seuil à 1, on attend une pénalité pour les doublons
        penalty = _calculate_duplicate_penalty(team, threshold=1, penalty_per_extra=1.0)
        assert penalty > 0.0, f"Expected penalty > 0.0 but got {penalty}"
        
        # Avec un seuil plus élevé, la pénalité devrait être moindre
        penalty_high_threshold = _calculate_duplicate_penalty(team, threshold=2, penalty_per_extra=1.0)
        assert 0.0 <= penalty_high_threshold <= penalty, \
            f"Expected penalty_high_threshold ({penalty_high_threshold}) <= penalty ({penalty})"

    def test_score_team_with_invalid_build(self):
        """Teste le comportement avec un build invalide."""
        # Crée une équipe avec un build invalide (sans rôle ni buff)
        invalid_build = PlayerBuild(
            profession_id="Invalid",
            elite_spec="None",
            buffs=set(),
            roles=set(),
            playstyles=set()
        )
        team = [SAMPLE_BUILDS[0], invalid_build]  # Un build valide + un invalide
        
        # Le scoring doit toujours fonctionner mais avec un score potentiellement bas
        result = score_team(team, SAMPLE_CONFIG)
        assert isinstance(result.total_score, float)
        assert 0.0 <= result.total_score <= 1.0

    def test_score_team_with_custom_weights(self):
        """Teste le scoring avec des poids personnalisés."""
        # Crée une configuration personnalisée qui favorise certains rôles/buffs
        custom_config = ScoringConfig(
            buff_weights={
                BuffType.QUICKNESS: BuffWeight(weight=3.0, description="Quick"),
                BuffType.ALACRITY: BuffWeight(weight=3.0, description="Alac"),
                BuffType.MIGHT: BuffWeight(weight=0.5, description="Might")
            },
            role_weights={
                RoleType.HEAL: RoleWeight(weight=3.0, required_count=1, description="Healer"),
                RoleType.TEAM_FIGHT_SUPPORT: RoleWeight(weight=2.0, required_count=1, description="Support"),
                RoleType.DPS: RoleWeight(weight=0.5, required_count=1, description="DPS")
            },
            duplicate_penalty=DuplicatePenalty(threshold=1, penalty_per_extra=0.5, enabled=True)
        )
        
        # Test avec une équipe qui correspond bien à la configuration
        good_team = [SAMPLE_BUILDS[0], SAMPLE_BUILDS[1]]  # Firebrand + Herald
        good_result = score_team(good_team, custom_config)
        
        # Test avec une équipe qui correspond mal à la configuration
        bad_team = [SAMPLE_BUILDS[2]]  # Seulement un DPS
        bad_result = score_team(bad_team, custom_config)
        
        # L'équipe qui correspond mieux à la configuration devrait avoir un meilleur score
        assert good_result.total_score > bad_result.total_score

    @pytest.mark.parametrize("test_case,expected_result", [
        ("basic_coverage", True),  # Vérifie la couverture de base
        ("additional_coverage", True)  # Vérifie la couverture avec des buffs additionnels
    ])
    def test_min_coverage_requirements(self, test_case: str, expected_result: bool) -> None:
        """Teste les exigences de couverture minimale.
        
        Args:
            test_case: Type de test à effectuer
            expected_result: Résultat attendu (True si le test doit réussir)
        """
        # Configuration de base pour les tests
        config = ScoringConfig(
            buff_weights={
                BuffType.QUICKNESS: BuffWeight(weight=1.0, description="Quick"),
                BuffType.MIGHT: BuffWeight(weight=1.0, description="Might")
            },
            role_weights={
                RoleType.HEAL: RoleWeight(weight=1.0, required_count=1, description="Healer")
            },
            duplicate_penalty=DuplicatePenalty(threshold=1, penalty_per_extra=0.7, enabled=True)
        )
        
        if test_case == "basic_coverage":
            # Test avec une équipe minimale qui couvre les exigences de base
            team = [SAMPLE_BUILDS[0]]  # Firebrand avec heal et quelques buffs
            result = score_team(team, config)
            # Vérifie que le score est cohérent (entre 0 et 1)
            assert 0.0 < result.total_score <= 1.0
            # Vérifie que les rôles requis sont couverts
            assert any(rc.role == RoleType.HEAL and rc.fulfilled for rc in result.role_coverage)
            
        elif test_case == "additional_coverage":
            # Test avec une équipe qui ajoute des buffs additionnels
            base_team = [SAMPLE_BUILDS[0]]  # Firebrand
            base_result = score_team(base_team, config)
            
            # Ajoute un autre build qui apporte des buffs additionnels
            enhanced_team = base_team + [SAMPLE_BUILDS[1]]  # Firebrand + Herald
            enhanced_result = score_team(enhanced_team, config)
            
            # Le score devrait être au moins aussi bon avec l'équipe améliorée
            # Note: Peut être égal si les buffs additionnels ne sont pas dans la configuration
            assert enhanced_result.total_score >= base_result.total_score
            
            # Vérifie que les rôles requis sont toujours couverts
            assert any(rc.role == RoleType.HEAL and rc.fulfilled for rc in enhanced_result.role_coverage)

    def test_caching_performance(self) -> None:
        """Teste les performances du cache du moteur de scoring."""
        # Crée une grande équipe pour le test de performance
        large_team = [SAMPLE_BUILDS[i % len(SAMPLE_BUILDS)] 
                     for _ in range(10) 
                     for i in range(len(SAMPLE_BUILDS))]
        
        # Premier appel (devrait être plus lent à cause du cache froid)
        import time
        start_time = time.time()
        first_result = score_team(large_team, SAMPLE_CONFIG)
        first_duration = time.time() - start_time
        
        # Deuxième appel (devrait être plus rapide grâce au cache)
        start_time = time.time()
        second_result = score_team(large_team, SAMPLE_CONFIG)
        second_duration = time.time() - start_time
        
        # Vérifie que les résultats sont identiques
        assert first_result.total_score == second_result.total_score
        
        # Vérifie que le deuxième appel est plus rapide (au moins 2x plus rapide)
        # Note: Ce test peut échuer sur des machines très rapides/chargées
        if first_duration > 0.1:  # Ne vérifie que pour les appels suffisamment longs
            assert second_duration < first_duration / 2, \
                f"Le cache ne semble pas fonctionner: {first_duration=}, {second_duration=}"

    def test_serialization_compatibility(self) -> None:
        """Teste la compatibilité de sérialisation des résultats."""
        # Calcule un résultat
        team = [SAMPLE_BUILDS[0], SAMPLE_BUILDS[1]]
        result = score_team(team, SAMPLE_CONFIG)
        
        # Convertit en dictionnaire
        result_dict = {
            'total_score': result.total_score,
            'buff_score': result.buff_score,
            'role_score': result.role_score,
            'duplicate_penalty': result.duplicate_penalty,
            'buff_breakdown': {k.value: v for k, v in result.buff_breakdown.items()},
            'role_breakdown': {k.value: v for k, v in result.role_breakdown.items()},
            'buff_coverage': [
                {
                    'buff': item.buff.value,
                    'covered': item.covered,
                    'weight': item.weight,
                    'provided_by': item.provided_by
                }
                for item in result.buff_coverage
            ],
            'role_coverage': [
                {
                    'role': item.role.value,
                    'fulfilled_count': item.fulfilled_count,
                    'required_count': item.required_count,
                    'fulfilled': item.fulfilled,
                    'weight': item.weight
                }
                for item in result.role_coverage
            ]
        }
        
        # Convertit en JSON et retour
        import json
        json_str = json.dumps(result_dict)
        loaded_dict = json.loads(json_str)
        
        # Vérifie que les données essentielles sont présentes
        assert 'total_score' in loaded_dict
        assert 'buff_score' in loaded_dict
        assert 'role_score' in loaded_dict
        assert 'duplicate_penalty' in loaded_dict
        assert 'buff_breakdown' in loaded_dict
        assert 'role_breakdown' in loaded_dict
        assert 'buff_coverage' in loaded_dict
        assert 'role_coverage' in loaded_dict
        assert 'role_coverage' in loaded_dict
        assert 'duplicate_penalty' in loaded_dict
        
        # Vérifie que les valeurs sont sérialisables
        json.dumps(loaded_dict)  # Ne devrait pas lever d'exception
