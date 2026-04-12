import json
from dataclasses import dataclass
from typing import Optional
from database.connection import db


@dataclass
class EventLogRecord:
    event_id: int
    save_id: int
    player_id: int
    season_year: int
    week_number: int
    event_key: str
    category: str
    severity: str
    title: str
    narrative_text: str
    attribute_delta: dict
    stat_delta: dict
    is_player_choice: int = 0
    choice_made: Optional[str] = None
    created_at: Optional[str] = None


class EventLogRepository:
    def _row_to_record(self, row) -> EventLogRecord:
        d = dict(row)
        d["attribute_delta"] = json.loads(d.get("attribute_delta") or "{}")
        d["stat_delta"] = json.loads(d.get("stat_delta") or "{}")
        return EventLogRecord(**d)

    def append(self, data: dict) -> int:
        d = dict(data)
        for key in ("attribute_delta", "stat_delta"):
            if key in d and isinstance(d[key], dict):
                d[key] = json.dumps(d[key], ensure_ascii=False)
        cols = ", ".join(d.keys())
        placeholders = ", ".join("?" * len(d))
        with db() as conn:
            cur = conn.execute(
                f"INSERT INTO event_log ({cols}) VALUES ({placeholders})",
                list(d.values()),
            )
            return cur.lastrowid

    def get_by_save(
        self,
        save_id: int,
        season_year: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 200,
    ) -> list[EventLogRecord]:
        sql = "SELECT * FROM event_log WHERE save_id=?"
        params: list = [save_id]
        if season_year:
            sql += " AND season_year=?"
            params.append(season_year)
        if category:
            sql += " AND category=?"
            params.append(category)
        sql += " ORDER BY season_year, week_number DESC LIMIT ?"
        params.append(limit)
        with db() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_record(r) for r in rows]

    def get_by_week(self, save_id: int, season_year: int, week: int) -> list[EventLogRecord]:
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM event_log WHERE save_id=? AND season_year=? AND week_number=? "
                "ORDER BY event_id",
                (save_id, season_year, week),
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def get_milestones(self, save_id: int) -> list[EventLogRecord]:
        return self.get_by_save(save_id, category="career_milestones", limit=100)
