"""API routes for team suggestions using the simple optimizer."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.optimizer.simple import optimize
from app.scoring.engine import PlayerBuild
from app.scoring.schema import (
    BuffWeight,
    DuplicatePenalty,
    RoleWeight,
    ScoringConfig,
    TeamScoreResult,
)

router = APIRouter(prefix="/teams", tags=["teams"])


class SuggestRequest(BaseModel):
    team_size: int = Field(10, ge=1, description="Number of players in the team")
    samples: int = Field(500, gt=0, le=20000, description="Number of random samples")
    top_n: int = Field(5, gt=0, le=50, description="How many best teams to return")
    algorithm: str = Field("sampling", description="Algorithm to use: sampling or genetic")
    generations: int | None = Field(
        None,
        description="Generations for genetic algorithm (ignored for sampling)",
    )
    population: int | None = Field(
        None,
        description="Population size for genetic algorithm (ignored for sampling)",
    )
    playstyle: str = Field("raid_guild", description="Playstyle: raid_guild, bus, roaming_solo, roaming_group, havoc")
    allowed_professions: List[str] | None = Field(
        None,
        description="Whitelist of profession names players can play. If omitted, all professions are allowed.",
    )


class TeamSuggestion(BaseModel):
    professions: List[str]
    score: TeamScoreResult


class SuggestResponse(BaseModel):
    teams: List[TeamSuggestion]


# Default scoring config for WvW
_DEFAULT_CONFIG = ScoringConfig(
    buff_weights={
        # Buffs de base
        "might": BuffWeight(weight=1.0),
        "fury": BuffWeight(weight=0.8),
        "quickness": BuffWeight(weight=1.2),
        "alacrity": BuffWeight(weight=1.0),
        "swiftness": BuffWeight(weight=0.5),
        "vigor": BuffWeight(weight=0.7),
        "protection": BuffWeight(weight=1.0),
        "regeneration": BuffWeight(weight=0.8),
        "resolution": BuffWeight(weight=0.6),
        "stability": BuffWeight(weight=1.5),  # Très important en WvW
        "aegis": BuffWeight(weight=1.0),
        "resistance": BuffWeight(weight=0.9),
        
        # Buffs spécifiques au WvW
        "superspeed": BuffWeight(weight=0.8),
        "stealth": BuffWeight(weight=0.7),
        "barrier": BuffWeight(weight=0.9),
        "invulnerability": BuffWeight(weight=1.2),
        "unblockable": BuffWeight(weight=0.5),
        "reflection": BuffWeight(weight=0.8),
        "stun_break": BuffWeight(weight=0.9),
        "condition_cleanse": BuffWeight(weight=1.1),
        "boon_rip": BuffWeight(weight=0.9),
        "boon_corrupt": BuffWeight(weight=0.9),
    },
    role_weights={
        # Rôles de base
        "heal": RoleWeight(required_count=1, weight=2.0, description="Soigneur principal"),
        "quickness": RoleWeight(required_count=1, weight=1.5, description="Fournit la rapidité"),
        "alacrity": RoleWeight(required_count=1, weight=1.5, description="Fournit l'alacrité"),
        "dps": RoleWeight(required_count=3, weight=1.0, description="Dégâts"),
        "tank": RoleWeight(required_count=1, weight=1.2, description="Tank principal"),
        
        # Rôles spécifiques au WvW
        "zerg": RoleWeight(required_count=3, weight=1.2, description="Spécialisation pour les grands groupes"),
        "havoc": RoleWeight(required_count=1, weight=1.5, description="Petit groupe mobile"),
        "roamer": RoleWeight(required_count=1, weight=1.0, description="Joueur autonome"),
        "bomber": RoleWeight(required_count=1, weight=1.3, description="Dégâts de zone"),
        "support": RoleWeight(required_count=2, weight=1.2, description="Soutien polyvalent"),
        "bunker": RoleWeight(required_count=1, weight=1.1, description="Défense de point"),
        "pusher": RoleWeight(required_count=1, weight=1.1, description="Pression offensive"),
        "disruptor": RoleWeight(required_count=1, weight=1.0, description="Désorganisation ennemie"),
        "scout": RoleWeight(required_count=1, weight=0.8, description="Renseignement et détection"),
        "captain": RoleWeight(required_count=1, weight=1.0, description="Leader de groupe"),
        "backline": RoleWeight(required_count=2, weight=1.0, description="Dégâts à distance"),
        "frontline": RoleWeight(required_count=3, weight=1.1, description="Combat rapproché"),
        "midline": RoleWeight(required_count=1, weight=1.0, description="Soutien et contrôle"),
        "plus_one": RoleWeight(required_count=1, weight=0.9, description="Renfort rapide"),
        "solo_dueler": RoleWeight(required_count=1, weight=0.9, description="Combat en 1v1"),
        "team_fighter": RoleWeight(required_count=2, weight=1.2, description="Combat en groupe"),
        "side_noder": RoleWeight(required_count=1, weight=1.0, description="Contrôle de points"),
        "roamer_plus_one": RoleWeight(required_count=1, weight=1.0, description="Flanc + renfort"),
        "team_fight_support": RoleWeight(required_count=2, weight=1.2, description="Soutien en combat d'équipe")
    },
    duplicate_penalty=DuplicatePenalty(threshold=2, penalty_per_extra=0.5),  # Pénalité plus forte pour éviter les doublons
)


@router.post("/suggest", response_model=SuggestResponse)
def suggest_teams(payload: SuggestRequest) -> SuggestResponse:  # noqa: D401
    # Generate candidate builds based on user constraints
    from app.builds.generator import generate_builds

    candidates = generate_builds(
        playstyle=payload.playstyle,
        allowed_professions=payload.allowed_professions,
    )

    try:
        if payload.algorithm == "genetic":
            from app.optimizer.genetic import optimize_genetic

            generations = payload.generations or 40
            population = payload.population or 200
            raw = optimize_genetic(
                team_size=payload.team_size,
                candidates=candidates,
                config=_DEFAULT_CONFIG,
                population_size=population,
                generations=generations,
            )
            best = raw[: payload.top_n]
        else:
            best = optimize(
                team_size=payload.team_size,
                samples=payload.samples,
                top_n=payload.top_n,
                config=_DEFAULT_CONFIG,
                candidates=candidates,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    suggestions: List[TeamSuggestion] = []
    for result, builds in best:
        suggestions.append(
            TeamSuggestion(
                professions=[b.profession_id for b in builds],
                score=result,
            )
        )
    return SuggestResponse(teams=suggestions)
