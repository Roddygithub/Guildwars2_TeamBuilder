"""Automatic build generation based on playstyle and allowed professions.

This is a minimal placeholder implementation. It maps each profession to a small
set of pre-defined builds tagged with buffs/roles, filtered by playstyle.
A future version will fetch real templates from ArenaNet API, but this is
sufficient for the optimizer prototype.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Profession
from app.scoring.engine import PlayerBuild
from app.data.builds_metadata import get_builds




def generate_builds(
    playstyle: str,
    allowed_professions: List[str] | None = None,
    session: Session | None = None,
) -> List[PlayerBuild]:
    """Génère des builds de joueur basés sur le style de jeu et les professions autorisées.
    
    Args:
        playstyle: Style de jeu (zerg, havoc, roaming, etc.)
        allowed_professions: Liste des noms de professions autorisées (None pour toutes)
        session: Session SQLAlchemy (optionnelle)
        
    Returns:
        Liste des builds correspondant aux critères
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    builds: List[PlayerBuild] = []

    profs_query = session.query(Profession).all()
    for prof in profs_query:
        if allowed_professions and prof.name not in allowed_professions:
            continue

        for build_data in get_builds(prof.name):
            # Vérifier si le build correspond au style de jeu demandé
            if playstyle in build_data["playstyles"]:
                # Créer le build avec toutes les métadonnées disponibles
                build = PlayerBuild(
                    profession_id=prof.id,
                    buffs=set(build_data["buffs"]),
                    roles=set(build_data["roles"]),
                    elite_spec=build_data.get("elite_spec"),
                    playstyles=set(build_data.get("playstyles", [])),
                    description=build_data.get("description", ""),
                    weapons=build_data.get("weapons", []),
                    utilities=build_data.get("utilities", [])
                )
                builds.append(build)

    if close_session:
        session.close()

    return builds
