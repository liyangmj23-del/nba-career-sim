"""
赛季管理器：
- 赛季结束处理（总结/荣誉/年龄/属性衰退）
- 下一赛季准备
- 退役判断
"""
import random
from database.connection import db as getdb
from database.repositories.player_repo import PlayerRepository
from database.repositories.save_repo import SaveRepository
from database.repositories.event_log_repo import EventLogRepository
from simulation.achievement_tracker import evaluate_season, get_awards, count_awards
from simulation.historical_standing import build_historical_report
from simulation.attribute_calculator import year_end_delta, apply_delta, compute_overall
from config import CURRENT_SEASON_YEAR

# ── NBA 历史单赛季记录 ────────────────────────────────────────────────────────
NBA_SEASON_RECORDS = {
    "pts": (36.1, "Wilt Chamberlain", "1961-62"),
    "reb": (27.2, "Wilt Chamberlain", "1960-61"),
    "ast": (14.5, "John Stockton",    "1989-90"),
    "stl": (3.67, "Alvin Robertson",  "1985-86"),
    "blk": (5.56, "Mark Eaton",       "1984-85"),
}


def get_season_summary(save_id: int, player_id: int, season_year: int) -> dict:
    """构建完整的赛季总结数据，供 season_summary.html 使用。"""
    player_repo = PlayerRepository()
    save_repo   = SaveRepository()
    event_repo  = EventLogRepository()

    save   = save_repo.get_by_id(save_id)
    player = player_repo.get_by_id(player_id)

    # ── 本赛季统计 ────────────────────────────────────────────────────────────
    with getdb() as conn:
        stat_row = conn.execute(
            """SELECT games_played, points_pg, rebounds_pg, assists_pg,
                      steals_pg, blocks_pg, turnovers_pg, fg_pct, fg3_pct, ft_pct
               FROM player_season_stats
               WHERE player_id=? AND season_year=? AND season_type='Regular'""",
            (player_id, season_year)
        ).fetchone()

    season_stats = {}
    if stat_row:
        season_stats = {
            "gp": stat_row[0] or 0,
            "pts": round(stat_row[1] or 0, 1),
            "reb": round(stat_row[2] or 0, 1),
            "ast": round(stat_row[3] or 0, 1),
            "stl": round(stat_row[4] or 0, 1),
            "blk": round(stat_row[5] or 0, 1),
            "tov": round(stat_row[6] or 0, 1),
            "fg":  round((stat_row[7] or 0) * 100, 1),
            "fg3": round((stat_row[8] or 0) * 100, 1),
            "ft":  round((stat_row[9] or 0) * 100, 1),
        }

    # ── 假如设定 vs 实际均值 ──────────────────────────────────────────────────
    overrides = save.state_json.get("stat_overrides", {})

    # ── 本赛季荣誉 ────────────────────────────────────────────────────────────
    awards_this_season = get_awards(save_id, season_year)

    # ── 打破历史记录检测 ──────────────────────────────────────────────────────
    records_broken = []
    for key, (record_val, holder, year) in NBA_SEASON_RECORDS.items():
        player_val = season_stats.get(key, 0)
        if player_val > record_val:
            ratio = round(player_val / record_val, 2)
            records_broken.append({
                "stat":       key.upper(),
                "player_val": player_val,
                "record_val": record_val,
                "holder":     holder,
                "year":       year,
                "ratio":      ratio,
            })

    # ── 超历史叙事等级 ────────────────────────────────────────────────────────
    record_tier = None
    if len(records_broken) >= 5:
        record_tier = "unprecedented"   # 前无古人
    elif len(records_broken) >= 3:
        record_tier = "legendary"       # 史诗
    elif len(records_broken) >= 1:
        record_tier = "historic"        # 历史级

    # ── 球队投影胜场 ──────────────────────────────────────────────────────────
    from simulation.player_impact import compute_impact, LEAGUE_AVG_STARTER
    impact = compute_impact(
        season_stats.get("pts", 0), season_stats.get("reb", 0),
        season_stats.get("ast", 0), season_stats.get("stl", 0),
        season_stats.get("blk", 0), season_stats.get("tov", 2.5),
    )
    from simulation.team_simulator import _team_rating
    my_team_id = save.current_team_id
    try:
        team_rating = _team_rating(my_team_id, season_year) if my_team_id else 55.0
    except Exception:
        team_rating = 55.0
    base_wins = max(0, min(82, round((team_rating - 40) / 60 * 82)))
    player_win_bonus = round(impact["wp_bonus"] * 82)
    proj_team_wins   = max(0, min(82, base_wins + player_win_bonus))

    # ── 季后赛资格 ────────────────────────────────────────────────────────────
    playoff_qualified = proj_team_wins >= 41  # NBA实际约50%胜率（41胜）才能进季后赛

    # ── 本赛季关键事件 ────────────────────────────────────────────────────────
    events = event_repo.get_by_save(save_id, season_year=season_year, limit=50)
    key_events = [e for e in events if e.severity in ("major", "legendary")][:5]

    # ── 生涯数据 ──────────────────────────────────────────────────────────────
    career = _get_career_totals(player_id)

    # ── 历史地位 ──────────────────────────────────────────────────────────────
    history = build_historical_report(save_id, player_id, player.full_name)

    return {
        "player":             player,
        "save":               save,
        "season_year":        season_year,
        "season_stats":       season_stats,
        "overrides":          overrides,
        "awards":             awards_this_season,
        "records_broken":     records_broken,
        "record_tier":        record_tier,
        "proj_team_wins":     proj_team_wins,
        "player_win_bonus":   player_win_bonus,
        "playoff_qualified":  playoff_qualified,
        "key_events":         key_events,
        "career":             career,
        "history":            history,
        "career_year":        save.career_year,
        "age":                save.current_age or 0,
    }


def apply_year_end(player_id: int, save_id: int, season_year: int) -> dict:
    """
    赛季结束时：
    1. 应用年龄衰退到属性
    2. career_year + 1，年龄 + 1
    3. 假如数据按衰退系数调整（不修改设定，修改实际乘数存入state_json）
    返回 {attr_delta, new_age, new_career_year}
    """
    player_repo = PlayerRepository()
    save_repo   = SaveRepository()
    save        = save_repo.get_by_id(save_id)
    player      = player_repo.get_by_id(player_id)

    attr_record = player_repo.get_attributes(player_id, season_year)
    if not attr_record:
        return {}

    skip = {"attr_id", "player_id", "season_year"}
    attrs = {k: getattr(attr_record, k)
             for k in attr_record.__dataclass_fields__ if k not in skip}

    current_age = save.current_age or 22
    career_year = save.career_year or 1

    # 属性年末变化
    delta = year_end_delta(attrs, current_age, career_year)
    new_attrs = apply_delta(attrs, delta)
    new_attrs["overall_rating"] = compute_overall(new_attrs)
    new_attrs["health"]  = min(100, new_attrs.get("health", 100))
    new_attrs["fatigue"] = 0       # 休赛期完全恢复
    new_attrs["morale"]  = min(100, new_attrs.get("morale", 75) + 10)

    # 写入下一赛季属性
    next_year = season_year + 1
    new_attrs["player_id"]   = player_id
    new_attrs["season_year"] = next_year
    player_repo.upsert_attributes(new_attrs)

    # 更新存档
    new_age        = current_age + 1
    new_career_year= career_year + 1

    # 假如数据衰退系数
    state = dict(save.state_json or {})
    if state.get("stat_overrides"):
        decay = _compute_override_decay(new_age, state["stat_overrides"])
        state["override_decay"] = decay
    state.pop("season_ended", None)   # 新赛季开始，清除上赛季结束标记
    state["total_games_played"] = 0   # 重置出场数计数

    save_repo.update(save_id, {
        "current_age":     new_age,
        "career_year":     new_career_year,
        "current_season":  next_year,
        "current_week":    1,
        "state_json":      state,
    })

    return {
        "attr_delta":      delta,
        "new_age":         new_age,
        "new_career_year": new_career_year,
    }


def _compute_override_decay(age: int, overrides: dict) -> float:
    """计算假如数据的衰退乘数（基于年龄）。"""
    physical_peak = 26
    skill_peak    = 29
    if age <= skill_peak:
        return 1.0
    years_past = age - skill_peak
    decay = max(0.50, 1.0 - years_past * 0.025)
    return round(decay, 3)


def _get_career_totals(player_id: int) -> dict:
    """汇总生涯数据。"""
    with getdb() as conn:
        rows = conn.execute(
            """SELECT season_year, games_played, points_pg, rebounds_pg,
                      assists_pg, steals_pg, blocks_pg
               FROM player_season_stats WHERE player_id=? AND season_type='Regular'
               ORDER BY season_year""",
            (player_id,)
        ).fetchall()
    if not rows:
        return {"seasons": 0, "games": 0, "pts": 0, "reb": 0, "ast": 0, "stl": 0, "blk": 0}
    totals = {"seasons": len(rows), "games": 0,
              "pts": 0.0, "reb": 0.0, "ast": 0.0, "stl": 0.0, "blk": 0.0}
    for r in rows:
        gp = r[1] or 0
        totals["games"] += gp
        totals["pts"]   += (r[2] or 0) * gp
        totals["reb"]   += (r[3] or 0) * gp
        totals["ast"]   += (r[4] or 0) * gp
        totals["stl"]   += (r[5] or 0) * gp
        totals["blk"]   += (r[6] or 0) * gp
    for k in ("pts","reb","ast","stl","blk"):
        totals[k] = round(totals[k])
    return totals


def check_retirement(save_id: int, player_id: int) -> dict:
    """检查是否应该退役，返回 {should_suggest, force, reason}。"""
    save_repo   = SaveRepository()
    player_repo = PlayerRepository()
    save        = save_repo.get_by_id(save_id)
    attr        = player_repo.get_attributes(player_id, save.current_season - 1)

    age         = save.current_age or 22
    career_year = save.career_year or 1
    overall     = attr.overall_rating if attr else 50
    health      = attr.health if attr else 100

    # 强制退役
    if age >= 45 or (age >= 38 and health < 15):
        return {"should_suggest": True, "force": True,
                "reason": f"年龄已达 {age} 岁，身体无法继续支撑职业比赛"}

    # 建议退役
    if age >= 40:
        return {"should_suggest": True, "force": False,
                "reason": f"你已经 {age} 岁了，这个年龄继续打球是一种奇迹"}
    if age >= 36 and overall < 55:
        return {"should_suggest": True, "force": False,
                "reason": "体能大幅下滑，或许是时候考虑谢幕了"}
    if overall < 40 and career_year >= 12:
        return {"should_suggest": True, "force": False,
                "reason": "竞技状态已经很难维持职业水准"}

    return {"should_suggest": False, "force": False, "reason": ""}


def get_career_end_summary(save_id: int, player_id: int) -> dict:
    """构建完整的生涯总结数据，供 career_end.html 使用。"""
    player_repo = PlayerRepository()
    save_repo   = SaveRepository()
    event_repo  = EventLogRepository()

    save   = save_repo.get_by_id(save_id)
    player = player_repo.get_by_id(player_id)

    career  = _get_career_totals(player_id)
    awards  = count_awards(save_id)
    history = build_historical_report(save_id, player_id, player.full_name)

    # 关键抉择
    choice_events = event_repo.get_by_save(save_id, category="career_milestones", limit=200)
    choice_events = [e for e in choice_events if e.is_player_choice][:10]

    # 生涯高光事件
    all_events = event_repo.get_by_save(save_id, limit=300)
    legendary = [e for e in all_events if e.severity == "legendary"][:6]

    # 生涯时间跨度
    from_season = save.current_season - (save.career_year or 1)
    to_season   = save.current_season - 1

    return {
        "player":         player,
        "save":           save,
        "career":         career,
        "awards":         awards,
        "history":        history,
        "choice_events":  choice_events,
        "legendary":      legendary,
        "from_season":    from_season,
        "to_season":      to_season,
        "career_years":   save.career_year or 1,
        "final_age":      save.current_age or 0,
        "overrides":      save.state_json.get("stat_overrides", {}),
    }
