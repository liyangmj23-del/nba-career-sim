"""
数据库 Schema：建表 DDL + 初始化入口
运行方式：python -m database.schema
"""
from database.connection import db

DDL = """
-- ══════════════════════════════════════════════════════
-- 球队
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS teams (
    team_id        INTEGER PRIMARY KEY,
    full_name      TEXT NOT NULL,
    abbreviation   TEXT NOT NULL,
    nickname       TEXT NOT NULL,
    city           TEXT NOT NULL,
    state          TEXT,
    year_founded   INTEGER,
    conference     TEXT CHECK(conference IN ('East','West')),
    division       TEXT,
    arena          TEXT,
    is_active      INTEGER DEFAULT 1,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ══════════════════════════════════════════════════════
-- 球员（生涯固定信息）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS players (
    player_id       INTEGER PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    birthdate       TEXT,
    country         TEXT,
    height_inches   REAL,
    weight_lbs      REAL,
    position        TEXT,
    jersey_number   TEXT,
    draft_year      INTEGER,
    draft_round     INTEGER,
    draft_pick      INTEGER,
    school          TEXT,
    from_year       INTEGER,
    to_year         INTEGER,
    is_active       INTEGER DEFAULT 1,
    current_team_id INTEGER REFERENCES teams(team_id),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_players_team   ON players(current_team_id);
CREATE INDEX IF NOT EXISTS idx_players_active ON players(is_active);
CREATE INDEX IF NOT EXISTS idx_players_name   ON players(full_name);

-- ══════════════════════════════════════════════════════
-- 球员属性（1-99 评分，每赛季一行，模拟中动态变化）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS player_attributes (
    attr_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL REFERENCES players(player_id),
    season_year     INTEGER NOT NULL,
    -- 身体
    speed           INTEGER DEFAULT 50,
    strength        INTEGER DEFAULT 50,
    vertical        INTEGER DEFAULT 50,
    endurance       INTEGER DEFAULT 50,
    -- 进攻技术
    ball_handling   INTEGER DEFAULT 50,
    shooting_2pt    INTEGER DEFAULT 50,
    shooting_3pt    INTEGER DEFAULT 50,
    free_throw      INTEGER DEFAULT 50,
    passing         INTEGER DEFAULT 50,
    post_moves      INTEGER DEFAULT 50,
    -- 防守技术
    perimeter_def   INTEGER DEFAULT 50,
    interior_def    INTEGER DEFAULT 50,
    steal_tendency  INTEGER DEFAULT 50,
    block_tendency  INTEGER DEFAULT 50,
    -- 心理/智商
    basketball_iq   INTEGER DEFAULT 50,
    clutch_factor   INTEGER DEFAULT 50,
    leadership      INTEGER DEFAULT 50,
    work_ethic      INTEGER DEFAULT 50,
    media_handling  INTEGER DEFAULT 50,
    -- 综合
    overall_rating  INTEGER DEFAULT 50,
    -- 状态（实时变化）
    health          INTEGER DEFAULT 100,
    morale          INTEGER DEFAULT 75,
    fatigue         INTEGER DEFAULT 0,
    UNIQUE(player_id, season_year)
);

-- ══════════════════════════════════════════════════════
-- 球员赛季统计（每人每赛季一行）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS player_season_stats (
    stat_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id           INTEGER NOT NULL REFERENCES players(player_id),
    team_id             INTEGER REFERENCES teams(team_id),
    season_year         INTEGER NOT NULL,
    season_type         TEXT DEFAULT 'Regular',
    games_played        INTEGER DEFAULT 0,
    games_started       INTEGER DEFAULT 0,
    minutes_pg          REAL DEFAULT 0,
    points_pg           REAL DEFAULT 0,
    rebounds_pg         REAL DEFAULT 0,
    assists_pg          REAL DEFAULT 0,
    steals_pg           REAL DEFAULT 0,
    blocks_pg           REAL DEFAULT 0,
    turnovers_pg        REAL DEFAULT 0,
    fg_pct              REAL DEFAULT 0,
    fg3_pct             REAL DEFAULT 0,
    ft_pct              REAL DEFAULT 0,
    per                 REAL DEFAULT 0,
    true_shooting       REAL DEFAULT 0,
    usage_rate          REAL DEFAULT 0,
    win_shares          REAL DEFAULT 0,
    games_missed_injury INTEGER DEFAULT 0,
    UNIQUE(player_id, season_year, season_type)
);

CREATE INDEX IF NOT EXISTS idx_pss_player ON player_season_stats(player_id, season_year);

-- ══════════════════════════════════════════════════════
-- 球员单场比赛记录（模拟时生成）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS player_game_log (
    log_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id        INTEGER NOT NULL REFERENCES players(player_id),
    team_id          INTEGER REFERENCES teams(team_id),
    opponent_team_id INTEGER REFERENCES teams(team_id),
    season_year      INTEGER NOT NULL,
    game_week        INTEGER NOT NULL,
    game_number      INTEGER NOT NULL,
    is_home          INTEGER DEFAULT 1,
    minutes          REAL,
    points           INTEGER,
    rebounds         INTEGER,
    assists          INTEGER,
    steals           INTEGER,
    blocks           INTEGER,
    turnovers        INTEGER,
    fg_made          INTEGER,
    fg_attempted     INTEGER,
    fg3_made         INTEGER,
    fg3_attempted    INTEGER,
    ft_made          INTEGER,
    ft_attempted     INTEGER,
    plus_minus       INTEGER,
    player_won       INTEGER,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_game_log_player ON player_game_log(player_id, season_year);

-- ══════════════════════════════════════════════════════
-- 球队赛季统计
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS team_season_stats (
    stat_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id            INTEGER NOT NULL REFERENCES teams(team_id),
    season_year        INTEGER NOT NULL,
    season_type        TEXT DEFAULT 'Regular',
    wins               INTEGER DEFAULT 0,
    losses             INTEGER DEFAULT 0,
    win_pct            REAL DEFAULT 0,
    points_pg          REAL DEFAULT 0,
    points_allowed_pg  REAL DEFAULT 0,
    offensive_rating   REAL DEFAULT 0,
    defensive_rating   REAL DEFAULT 0,
    net_rating         REAL DEFAULT 0,
    pace               REAL DEFAULT 0,
    conference_rank    INTEGER,
    playoff_seed       INTEGER,
    playoff_result     TEXT,
    UNIQUE(team_id, season_year, season_type)
);

-- ══════════════════════════════════════════════════════
-- 模拟存档
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS save_states (
    save_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    save_name       TEXT NOT NULL,
    player_id       INTEGER NOT NULL REFERENCES players(player_id),
    current_team_id INTEGER REFERENCES teams(team_id),
    current_season  INTEGER NOT NULL,
    current_week    INTEGER NOT NULL DEFAULT 1,
    current_age     INTEGER,
    career_year     INTEGER DEFAULT 1,
    total_salary    REAL DEFAULT 0,
    career_earnings REAL DEFAULT 0,
    game_mode       TEXT DEFAULT 'career',
    difficulty      TEXT DEFAULT 'normal',
    state_json      TEXT DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ══════════════════════════════════════════════════════
-- 事件叙事日志（模拟的故事历史）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS event_log (
    event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id         INTEGER NOT NULL REFERENCES save_states(save_id),
    player_id       INTEGER NOT NULL REFERENCES players(player_id),
    season_year     INTEGER NOT NULL,
    week_number     INTEGER NOT NULL,
    event_key       TEXT NOT NULL,
    category        TEXT NOT NULL,
    severity        TEXT DEFAULT 'normal',
    title           TEXT NOT NULL,
    narrative_text  TEXT NOT NULL,
    attribute_delta TEXT DEFAULT '{}',
    stat_delta      TEXT DEFAULT '{}',
    is_player_choice INTEGER DEFAULT 0,
    choice_made     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_event_log_save     ON event_log(save_id, season_year, week_number);
CREATE INDEX IF NOT EXISTS idx_event_log_category ON event_log(category);

-- ══════════════════════════════════════════════════════
-- 合同（Phase 3 启用）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS contracts (
    contract_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id      INTEGER NOT NULL REFERENCES players(player_id),
    team_id        INTEGER NOT NULL REFERENCES teams(team_id),
    save_id        INTEGER REFERENCES save_states(save_id),
    start_year     INTEGER NOT NULL,
    end_year       INTEGER NOT NULL,
    annual_salary  REAL NOT NULL,
    contract_type  TEXT,
    is_simulated   INTEGER DEFAULT 0,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ══════════════════════════════════════════════════════
-- 赛季荣誉（由 achievement_tracker 写入）
-- ══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS awards (
    award_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id     INTEGER NOT NULL REFERENCES save_states(save_id),
    player_id   INTEGER NOT NULL REFERENCES players(player_id),
    season_year INTEGER NOT NULL,
    award_type  TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_awards_save ON awards(save_id, season_year);
"""

# ── 迁移：为旧数据库补列/表 ──────────────────────────────────────────────────
_MIGRATIONS = [
    "ALTER TABLE players ADD COLUMN is_custom INTEGER DEFAULT 0",
]


def init_database():
    with db() as conn:
        conn.executescript(DDL)
        # 迁移：安全地补列（忽略已存在的列）
        for sql in _MIGRATIONS:
            try:
                conn.execute(sql)
            except Exception:
                pass
    print(f"[OK] 数据库初始化完成：{__import__('config').DB_PATH}")


if __name__ == "__main__":
    init_database()
