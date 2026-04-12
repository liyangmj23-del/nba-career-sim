import json
from dataclasses import dataclass
from typing import Optional
from database.connection import db


@dataclass
class SaveState:
    save_id: int
    save_name: str
    player_id: int
    current_team_id: Optional[int]
    current_season: int
    current_week: int
    current_age: Optional[int]
    career_year: int
    total_salary: float
    career_earnings: float
    game_mode: str
    difficulty: str
    state_json: dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def get_state(self, key: str, default=None):
        return self.state_json.get(key, default)

    def set_state(self, key: str, value) -> None:
        self.state_json[key] = value


class SaveRepository:
    def _row_to_save(self, row) -> SaveState:
        d = dict(row)
        d["state_json"] = json.loads(d.get("state_json") or "{}")
        return SaveState(**d)

    def create(self, data: dict) -> int:
        if "state_json" in data and isinstance(data["state_json"], dict):
            data = dict(data)
            data["state_json"] = json.dumps(data["state_json"], ensure_ascii=False)
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        with db() as conn:
            cur = conn.execute(
                f"INSERT INTO save_states ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
            return cur.lastrowid

    def get_by_id(self, save_id: int) -> Optional[SaveState]:
        with db() as conn:
            row = conn.execute(
                "SELECT * FROM save_states WHERE save_id=?", (save_id,)
            ).fetchone()
        return self._row_to_save(row) if row else None

    def get_all(self) -> list[SaveState]:
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM save_states ORDER BY updated_at DESC"
            ).fetchall()
        return [self._row_to_save(r) for r in rows]

    def update(self, save_id: int, fields: dict) -> bool:
        if "state_json" in fields and isinstance(fields["state_json"], dict):
            fields = dict(fields)
            fields["state_json"] = json.dumps(fields["state_json"], ensure_ascii=False)
        fields["updated_at"] = "CURRENT_TIMESTAMP"
        set_clause = ", ".join(
            f"{k}={k}" if k == "updated_at" else f"{k}=?"
            for k in fields
        )
        values = [v for k, v in fields.items() if k != "updated_at"] + [save_id]
        with db() as conn:
            cur = conn.execute(
                f"UPDATE save_states SET {set_clause}, updated_at=CURRENT_TIMESTAMP "
                f"WHERE save_id=?",
                values,
            )
        return cur.rowcount > 0

    def delete(self, save_id: int) -> bool:
        with db() as conn:
            cur = conn.execute("DELETE FROM save_states WHERE save_id=?", (save_id,))
        return cur.rowcount > 0
