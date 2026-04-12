from dataclasses import dataclass, field
from typing import Optional
from database.connection import db


@dataclass
class PlayerRecord:
    player_id: int
    first_name: str
    last_name: str
    full_name: str
    birthdate: Optional[str] = None
    country: Optional[str] = None
    height_inches: Optional[float] = None
    weight_lbs: Optional[float] = None
    position: Optional[str] = None
    jersey_number: Optional[str] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_pick: Optional[int] = None
    school: Optional[str] = None
    from_year: Optional[int] = None
    to_year: Optional[int] = None
    is_active: int = 1
    is_custom: int = 0
    current_team_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class AttributeRecord:
    player_id: int
    season_year: int
    speed: int = 50
    strength: int = 50
    vertical: int = 50
    endurance: int = 50
    ball_handling: int = 50
    shooting_2pt: int = 50
    shooting_3pt: int = 50
    free_throw: int = 50
    passing: int = 50
    post_moves: int = 50
    perimeter_def: int = 50
    interior_def: int = 50
    steal_tendency: int = 50
    block_tendency: int = 50
    basketball_iq: int = 50
    clutch_factor: int = 50
    leadership: int = 50
    work_ethic: int = 50
    media_handling: int = 50
    overall_rating: int = 50
    health: int = 100
    morale: int = 75
    fatigue: int = 0
    attr_id: Optional[int] = None


class PlayerRepository:
    # ── 球员基础信息 ─────────────────────────────────────────────────────────

    def get_all(self, active_only: bool = True) -> list[PlayerRecord]:
        sql = "SELECT * FROM players"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY full_name"
        with db() as conn:
            rows = conn.execute(sql).fetchall()
        return [PlayerRecord(**dict(r)) for r in rows]

    def get_by_id(self, player_id: int) -> Optional[PlayerRecord]:
        with db() as conn:
            row = conn.execute(
                "SELECT * FROM players WHERE player_id=?", (player_id,)
            ).fetchone()
        return PlayerRecord(**dict(row)) if row else None

    def get_by_team(self, team_id: int) -> list[PlayerRecord]:
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM players WHERE current_team_id=? AND is_active=1 "
                "ORDER BY position, full_name",
                (team_id,),
            ).fetchall()
        return [PlayerRecord(**dict(r)) for r in rows]

    def search(self, query: str) -> list[PlayerRecord]:
        like = f"%{query}%"
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM players WHERE full_name LIKE ? ORDER BY is_active DESC, full_name",
                (like,),
            ).fetchall()
        return [PlayerRecord(**dict(r)) for r in rows]

    def upsert(self, data: dict) -> None:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "player_id")
        sql = (
            f"INSERT INTO players ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(player_id) DO UPDATE SET {updates}, "
            f"updated_at=CURRENT_TIMESTAMP"
        )
        with db() as conn:
            conn.execute(sql, list(data.values()))

    def update(self, player_id: int, fields: dict) -> bool:
        if not fields:
            return False
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [player_id]
        with db() as conn:
            cur = conn.execute(
                f"UPDATE players SET {set_clause}, updated_at=CURRENT_TIMESTAMP "
                f"WHERE player_id=?",
                values,
            )
        return cur.rowcount > 0

    def count(self, active_only: bool = True) -> int:
        sql = "SELECT COUNT(*) FROM players"
        if active_only:
            sql += " WHERE is_active=1"
        with db() as conn:
            return conn.execute(sql).fetchone()[0]

    # ── 球员属性 ──────────────────────────────────────────────────────────────

    def get_attributes(self, player_id: int, season_year: int) -> Optional[AttributeRecord]:
        with db() as conn:
            row = conn.execute(
                "SELECT * FROM player_attributes WHERE player_id=? AND season_year=?",
                (player_id, season_year),
            ).fetchone()
        return AttributeRecord(**dict(row)) if row else None

    def upsert_attributes(self, data: dict) -> None:
        """data 必须包含 player_id 和 season_year"""
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        updates = ", ".join(
            f"{k}=excluded.{k}" for k in data
            if k not in ("player_id", "season_year", "attr_id")
        )
        sql = (
            f"INSERT INTO player_attributes ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(player_id, season_year) DO UPDATE SET {updates}"
        )
        with db() as conn:
            conn.execute(sql, list(data.values()))

    def update_attributes(self, player_id: int, season_year: int, fields: dict) -> bool:
        if not fields:
            return False
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [player_id, season_year]
        with db() as conn:
            cur = conn.execute(
                f"UPDATE player_attributes SET {set_clause} "
                f"WHERE player_id=? AND season_year=?",
                values,
            )
        return cur.rowcount > 0
