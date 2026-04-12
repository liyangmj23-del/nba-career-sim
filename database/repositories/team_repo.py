from dataclasses import dataclass
from typing import Optional
from database.connection import db


@dataclass
class TeamRecord:
    team_id: int
    full_name: str
    abbreviation: str
    nickname: str
    city: str
    state: Optional[str] = None
    year_founded: Optional[int] = None
    conference: Optional[str] = None
    division: Optional[str] = None
    arena: Optional[str] = None
    is_active: int = 1
    updated_at: Optional[str] = None


class TeamRepository:
    def get_all(self, active_only: bool = True) -> list[TeamRecord]:
        sql = "SELECT * FROM teams"
        params: tuple = ()
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY conference, division, full_name"
        with db() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [TeamRecord(**dict(r)) for r in rows]

    def get_by_id(self, team_id: int) -> Optional[TeamRecord]:
        with db() as conn:
            row = conn.execute(
                "SELECT * FROM teams WHERE team_id = ?", (team_id,)
            ).fetchone()
        return TeamRecord(**dict(row)) if row else None

    def get_by_abbreviation(self, abbr: str) -> Optional[TeamRecord]:
        with db() as conn:
            row = conn.execute(
                "SELECT * FROM teams WHERE abbreviation = ?", (abbr.upper(),)
            ).fetchone()
        return TeamRecord(**dict(row)) if row else None

    def upsert(self, data: dict) -> None:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "team_id")
        sql = (
            f"INSERT INTO teams ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(team_id) DO UPDATE SET {updates}, "
            f"updated_at=CURRENT_TIMESTAMP"
        )
        with db() as conn:
            conn.execute(sql, list(data.values()))

    def update(self, team_id: int, fields: dict) -> bool:
        if not fields:
            return False
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [team_id]
        with db() as conn:
            cur = conn.execute(
                f"UPDATE teams SET {set_clause}, updated_at=CURRENT_TIMESTAMP "
                f"WHERE team_id=?",
                values,
            )
        return cur.rowcount > 0
