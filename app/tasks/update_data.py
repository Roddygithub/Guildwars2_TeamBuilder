"""Task to update Guild Wars 2 reference data via official ArenaNet API.
Run daily via Windsurf scheduled task defined in windsurf.yaml.
"""
from __future__ import annotations

import logging
from typing import Any, List

import requests
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Profession, Specialization, Skill

API_BASE = "https://api.guildwars2.com/v2"
HEADERS = {"Accept-Language": "en"}  # Could be parameterized
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_json(endpoint: str) -> List[Any]:
    url = f"{API_BASE}/{endpoint}"
    logger.info("Fetching %s", url)
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()

def upsert_professions(db: Session) -> None:
    ids = fetch_json("professions")
    data = fetch_json(f"professions?ids={','.join(ids)}")

    for item in data:
        db_prof = db.get(Profession, item["id"])
        if db_prof:
            db_prof.name = item["name"]
            db_prof.data = item
        else:
            db_prof = Profession(id=item["id"], name=item["name"], data=item)
            db.add(db_prof)
    db.commit()
    logger.info("Upserted %d professions", len(data))

def upsert_specializations(db: Session) -> None:
    ids = fetch_json("specializations")
    # Trim to 200 per request (API limit) – chunking
    chunk_size = 200
    for i in range(0, len(ids), chunk_size):
        chunk_ids = ids[i : i + chunk_size]
        data = fetch_json(f"specializations?ids={','.join(map(str, chunk_ids))}")
        for item in data:
            db_spec = db.get(Specialization, item["id"])
            if db_spec:
                db_spec.name = item["name"]
                db_spec.profession_id = item.get("profession")
                db_spec.data = item
            else:
                db_spec = Specialization(
                    id=item["id"],
                    name=item["name"],
                    profession_id=item.get("profession"),
                    data=item,
                )
                db.add(db_spec)
        db.commit()
    logger.info("Upserted %d specializations", len(ids))

def upsert_skills(db: Session) -> None:
    ids = fetch_json("skills")
    chunk_size = 200
    for i in range(0, len(ids), chunk_size):
        chunk_ids = ids[i : i + chunk_size]
        data = fetch_json(f"skills?ids={','.join(map(str, chunk_ids))}&lang=en")
        for item in data:
            db_skill = db.get(Skill, item["id"])
            if db_skill:
                db_skill.name = item["name"]
                db_skill.profession_id = item.get("profession")
                db_skill.data = item
            else:
                db_skill = Skill(
                    id=item["id"],
                    name=item["name"],
                    profession_id=item.get("profession"),
                    data=item,
                )
                db.add(db_skill)
        db.commit()
    logger.info("Upserted %d skills", len(ids))

def run_update() -> None:
    logger.info("Starting GW2 data update task …")
    init_db()
    with SessionLocal() as db:
        upsert_professions(db)
        upsert_specializations(db)
        upsert_skills(db)
    logger.info("Data update complete.")


if __name__ == "__main__":
    run_update()
