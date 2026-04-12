"""
将 nba_api 返回的原始字段转换为数据库 Schema 所需格式，
并从真实历史数据推算球员的初始属性（1-99 评分）。
"""
from config import CURRENT_SEASON_YEAR, ATTR_MIN, ATTR_MAX


# ── 身高字符串 "6-8" → 英寸 80.0 ─────────────────────────────────────────────
def _height_to_inches(h: str | None) -> float | None:
    if not h:
        return None
    try:
        feet, inches = h.split("-")
        return float(feet) * 12 + float(inches)
    except Exception:
        return None


# ── 将百分比/比率归一化到 1-99 ────────────────────────────────────────────────
def _normalize(value: float, lo: float, hi: float) -> int:
    if value is None or hi == lo:
        return 50
    clipped = max(lo, min(hi, value))
    normalized = (clipped - lo) / (hi - lo) * 98 + 1
    return max(ATTR_MIN, min(ATTR_MAX, round(normalized)))


# ── 按位置预设身体属性基准 ────────────────────────────────────────────────────
_POSITION_PHYSICAL = {
    "PG": {"speed": 70, "strength": 45, "vertical": 60, "endurance": 65},
    "SG": {"speed": 65, "strength": 50, "vertical": 62, "endurance": 62},
    "SF": {"speed": 60, "strength": 55, "vertical": 60, "endurance": 60},
    "PF": {"speed": 50, "strength": 65, "vertical": 58, "endurance": 58},
    "C":  {"speed": 40, "strength": 75, "vertical": 55, "endurance": 55},
}

_POSITION_DEFAULTS = {
    "PG": {"ball_handling": 70, "passing": 70, "shooting_3pt": 55,
           "perimeter_def": 55, "interior_def": 35, "post_moves": 30,
           "steal_tendency": 55, "block_tendency": 30},
    "SG": {"ball_handling": 60, "passing": 55, "shooting_3pt": 65,
           "perimeter_def": 58, "interior_def": 38, "post_moves": 35,
           "steal_tendency": 50, "block_tendency": 30},
    "SF": {"ball_handling": 55, "passing": 52, "shooting_3pt": 55,
           "perimeter_def": 58, "interior_def": 48, "post_moves": 45,
           "steal_tendency": 50, "block_tendency": 40},
    "PF": {"ball_handling": 45, "passing": 45, "shooting_3pt": 42,
           "perimeter_def": 50, "interior_def": 62, "post_moves": 58,
           "steal_tendency": 42, "block_tendency": 55},
    "C":  {"ball_handling": 35, "passing": 38, "shooting_3pt": 30,
           "perimeter_def": 42, "interior_def": 72, "post_moves": 65,
           "steal_tendency": 35, "block_tendency": 65},
}


def transform_team(raw: dict) -> dict:
    """nba_api teams.get_teams() 的单条记录 → teams 表字段。"""
    return {
        "team_id":      raw["id"],
        "full_name":    raw["full_name"],
        "abbreviation": raw["abbreviation"],
        "nickname":     raw["nickname"],
        "city":         raw["city"],
        "state":        raw.get("state"),
        "year_founded": raw.get("year_founded"),
        "conference":   None,   # 静态数据中没有，roster 阶段补充
        "division":     None,
        "arena":        None,
        "is_active":    1,
    }


def transform_player_basic(raw: dict) -> dict:
    """nba_api players.get_active_players() 单条 → players 表字段（部分）。"""
    return {
        "player_id":  raw["id"],
        "first_name": raw["first_name"],
        "last_name":  raw["last_name"],
        "full_name":  raw["full_name"],
        "is_active":  1,
    }


def transform_player_detail(basic: dict, info: dict | None) -> dict:
    """合并 common_player_info 字段，返回完整的 players 行。"""
    result = dict(basic)
    if not info:
        return result

    # 日期：去掉 T00:00:00 部分
    bd = info.get("BIRTHDATE", "")
    result["birthdate"] = bd[:10] if bd else None

    result["country"]       = info.get("COUNTRY") or None
    result["height_inches"] = _height_to_inches(info.get("HEIGHT"))
    result["weight_lbs"]    = float(info["WEIGHT"]) if info.get("WEIGHT") else None
    result["position"]      = (info.get("POSITION") or "").split("-")[0].strip() or None
    result["jersey_number"] = info.get("JERSEY") or None
    result["draft_year"]    = int(info["DRAFT_YEAR"]) if str(info.get("DRAFT_YEAR","")).isdigit() else None
    result["draft_round"]   = int(info["DRAFT_ROUND"]) if str(info.get("DRAFT_ROUND","")).isdigit() else None
    result["draft_pick"]    = int(info["DRAFT_NUMBER"]) if str(info.get("DRAFT_NUMBER","")).isdigit() else None
    result["school"]        = info.get("SCHOOL") or None
    result["from_year"]     = int(info["FROM_YEAR"]) if str(info.get("FROM_YEAR","")).isdigit() else None
    result["to_year"]       = int(info["TO_YEAR"]) if str(info.get("TO_YEAR","")).isdigit() else None
    result["current_team_id"] = int(info["TEAM_ID"]) if str(info.get("TEAM_ID","0")).isdigit() and info.get("TEAM_ID") else None

    return result


def derive_attributes(
    player_id: int,
    position: str | None,
    career_stats: dict | None,
    season_year: int = CURRENT_SEASON_YEAR,
) -> dict:
    """
    从历史赛季统计推算初始属性（1-99）。
    若没有真实数据，按位置给出合理默认值。
    """
    pos = (position or "SF").upper()
    if pos not in _POSITION_PHYSICAL:
        pos = "SF"

    # 基础物理属性（按位置）
    attrs = dict(_POSITION_PHYSICAL[pos])
    # 基础技术属性（按位置）
    attrs.update(_POSITION_DEFAULTS[pos])
    # 固定心理属性默认
    attrs.update({
        "shooting_2pt": 50,
        "free_throw":   50,
        "basketball_iq": 55,
        "clutch_factor": 50,
        "leadership":    50,
        "work_ethic":    60,
        "media_handling": 55,
    })

    if career_stats:
        # 取最近3个赛季的均值进行推算
        rows = career_stats.get("regular", {}).get("data", [])
        headers = career_stats.get("regular", {}).get("headers", [])
        if rows and headers:
            recent = rows[-3:]  # 最近3赛季

            def avg(col: str) -> float | None:
                idx = headers.index(col) if col in headers else -1
                if idx == -1:
                    return None
                vals = [r[idx] for r in recent if r[idx] is not None]
                return sum(vals) / len(vals) if vals else None

            fg3_pct = avg("FG3_PCT")
            ft_pct  = avg("FT_PCT")
            fg_pct  = avg("FG_PCT")
            ast     = avg("AST")
            to_val  = avg("TOV")
            pts     = avg("PTS")
            reb     = avg("REB")
            per_val = avg("EFF")  # 效率值（简易版）

            # 投篮属性
            if fg3_pct is not None:
                attrs["shooting_3pt"] = _normalize(fg3_pct, 0.25, 0.46)
            if ft_pct is not None:
                attrs["free_throw"] = _normalize(ft_pct, 0.55, 0.95)
            if fg_pct is not None:
                attrs["shooting_2pt"] = _normalize(fg_pct, 0.38, 0.65)

            # 传球
            if ast is not None and to_val is not None and to_val > 0:
                ast_to = ast / to_val
                attrs["passing"] = _normalize(ast_to, 0.5, 5.0)
            elif ast is not None:
                attrs["passing"] = _normalize(ast, 0.5, 10.0)

            # 综合评级（用得分+效率简单估算）
            if pts is not None:
                attrs["basketball_iq"] = _normalize(pts, 4.0, 30.0)

    # 综合评分（各属性均值）
    skill_attrs = [
        "speed", "strength", "vertical", "endurance",
        "ball_handling", "shooting_2pt", "shooting_3pt", "free_throw",
        "passing", "post_moves", "perimeter_def", "interior_def",
        "steal_tendency", "block_tendency", "basketball_iq",
        "clutch_factor", "leadership", "work_ethic", "media_handling",
    ]
    overall = round(sum(attrs.get(k, 50) for k in skill_attrs) / len(skill_attrs))

    return {
        "player_id":      player_id,
        "season_year":    season_year,
        **{k: max(ATTR_MIN, min(ATTR_MAX, int(v))) for k, v in attrs.items()},
        "overall_rating": max(ATTR_MIN, min(ATTR_MAX, overall)),
        "health":         100,
        "morale":         75,
        "fatigue":        0,
    }
