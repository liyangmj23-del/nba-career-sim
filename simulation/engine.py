"""
赛季主循环。
engine.run_season() 是一个生成器，每次 next() 推进一周，
返回 WeekResult 供 UI/CLI 消费。
"""
import json
import random
from dataclasses import dataclass, field

from config import SEASON_WEEKS, CURRENT_SEASON_YEAR
from database.repositories.player_repo import PlayerRepository, AttributeRecord
from database.repositories.save_repo import SaveRepository
from database.repositories.event_log_repo import EventLogRepository
from simulation.stat_generator import generate_game, generate_game_with_overrides, aggregate_week, GameBox
from simulation.team_simulator import (
    _team_rating, win_probability, get_opponent, games_this_week,
)
from events.event_engine import (
    roll_events, apply_effects, FiredEvent,
)
from events.event_chain import (
    get_forced_chains, enqueue_chains,
    update_cooldowns, tick_cooldowns,
    update_one_time_flags, update_streak, update_recent_games,
)


@dataclass
class WeekResult:
    week: int
    season_year: int
    games: list[GameBox]
    week_summary: dict        # 本周均值汇总
    events: list[FiredEvent]
    attrs_after: dict         # 事件应用后的属性快照
    season_stats: dict        # 累计赛季均值（滚动更新）
    pending_choices: list     # 需要玩家做决定的选择事件列表
    impact: dict | None = None  # 本周影响力数据


# ── 赛季统计滚动更新 ──────────────────────────────────────────────────────────

def _update_season_stats(accum: dict, week_summary: dict) -> dict:
    """用本周数据更新滚动均值。"""
    n = accum.get("games_played", 0) + week_summary.get("games_this_week", 0)
    if n == 0:
        return accum

    def weighted_avg(old_key: str, new_key: str) -> float:
        old_n   = accum.get("games_played", 0)
        old_val = accum.get(old_key, 0)
        new_val = week_summary.get(new_key, 0)
        new_n   = week_summary.get("games_this_week", 0)
        return round((old_val * old_n + new_val * new_n) / n, 1) if n else 0

    fg_m  = accum.get("fg_made_total", 0)  + week_summary.get("fg_made", 0)
    fg_a  = accum.get("fg_att_total", 0)   + week_summary.get("fg_attempted", 0)
    fg3_m = accum.get("fg3_made_total", 0) + week_summary.get("fg3_made", 0)
    fg3_a = accum.get("fg3_att_total", 0)  + week_summary.get("fg3_attempted", 0)
    ft_m  = accum.get("ft_made_total", 0)  + week_summary.get("ft_made", 0)
    ft_a  = accum.get("ft_att_total", 0)   + week_summary.get("ft_attempted", 0)

    accum.update({
        "games_played":    n,
        "wins":            accum.get("wins", 0) + week_summary.get("wins", 0),
        "pts":             weighted_avg("pts", "pts"),
        "reb":             weighted_avg("reb", "reb"),
        "ast":             weighted_avg("ast", "ast"),
        "stl":             weighted_avg("stl", "stl"),
        "blk":             weighted_avg("blk", "blk"),
        "tov":             weighted_avg("tov", "tov"),
        "min":             weighted_avg("min", "min"),
        "fg_made_total":   fg_m,
        "fg_att_total":    fg_a,
        "fg3_made_total":  fg3_m,
        "fg3_att_total":   fg3_a,
        "ft_made_total":   ft_m,
        "ft_att_total":    ft_a,
        "fg_pct":          round(fg_m / fg_a, 3) if fg_a else 0,
        "fg3_pct":         round(fg3_m / fg3_a, 3) if fg3_a else 0,
        "ft_pct":          round(ft_m / ft_a, 3) if ft_a else 0,
    })
    return accum


# ── 主生成器 ─────────────────────────────────────────────────────────────────

def run_season(save_id: int, season_year: int = CURRENT_SEASON_YEAR):
    """
    赛季模拟生成器。
    调用方循环 next() 即可获得每周结果。

    用法：
        for week_result in run_season(save_id=1):
            render(week_result)
    """
    player_repo  = PlayerRepository()
    save_repo    = SaveRepository()
    event_repo   = EventLogRepository()

    save = save_repo.get_by_id(save_id)
    if not save:
        raise ValueError(f"save_id={save_id} 不存在")

    player = player_repo.get_by_id(save.player_id)
    if not player:
        raise ValueError(f"player_id={save.player_id} 不存在")

    attrs_record = player_repo.get_attributes(player.player_id, season_year)
    if not attrs_record:
        raise ValueError(f"球员 {player.full_name} 没有 {season_year} 赛季属性数据")

    attrs = {
        k: getattr(attrs_record, k)
        for k in attrs_record.__dataclass_fields__
        if k not in ("attr_id", "player_id", "season_year")
    }

    state_json = dict(save.state_json or {})

    # 从DB读已有赛季统计（断点续玩时不会重置）
    season_stats: dict = _load_season_stats(player.player_id, season_year)

    # import 放循环外，避免每周重复import
    from simulation.player_impact import (
        compute_impact, expected_stats_from_override,
        expected_stats_from_attrs, adjusted_win_prob,
    )

    # 获取球队实力评级（用于计算获胜概率）
    my_team_id = save.current_team_id or player.current_team_id
    try:
        my_rating = _team_rating(my_team_id, season_year) if my_team_id else 55.0
    except Exception:
        my_rating = 55.0

    # 起始周
    start_week = save.current_week

    for week in range(start_week, SEASON_WEEKS + 1):
        # ── 1. 每周开始：冷却 -1 ─────────────────────────────────────────────
        cooldowns = tick_cooldowns(state_json)

        # ── 2. 获取强制连锁事件 ──────────────────────────────────────────────
        forced_chains = get_forced_chains(state_json, week)

        # ── 2b. 触发选择后果延迟叙事 ─────────────────────────────────────────
        pending_cons = state_json.get("pending_consequences", [])
        due_cons     = [c for c in pending_cons if c.get("fire_week", 9999) <= week]
        if due_cons:
            state_json["pending_consequences"] = [c for c in pending_cons if c.get("fire_week", 9999) > week]
            for cons in due_cons:
                event_repo.append({
                    "save_id":         save_id,
                    "player_id":       player.player_id,
                    "season_year":     season_year,
                    "week_number":     week,
                    "event_key":       f"consequence.{cons.get('choice_key','unknown')}",
                    "category":        "career_milestones",
                    "severity":        "normal",
                    "title":           cons.get("title", "选择的影响"),
                    "narrative_text":  cons.get("narrative", ""),
                    "attribute_delta": {},
                    "stat_delta":      {},
                    "is_player_choice": 0,
                })

        # ── 3. 疲劳自然恢复（每周 -8，但比赛会加回来）────────────────────────
        attrs["fatigue"] = max(0, attrs["fatigue"] - 8)

        # ── 4. 模拟本周比赛 ──────────────────────────────────────────────────
        stat_overrides_raw = state_json.get("stat_overrides")
        # 应用年龄衰退系数（多赛季后假如数据自然下降）
        override_decay = state_json.get("override_decay", 1.0)
        stat_overrides = None
        if stat_overrides_raw:
            stat_overrides = {k: v * override_decay for k, v in stat_overrides_raw.items()}
        n_games = games_this_week()
        games: list[GameBox] = []
        game_opponents: list[int] = []
        game_number_base = state_json.get("total_games_played", 0)
        week_impact_labels = []   # 本周影响力摘要，加入事件流

        # 预计算球员期望数据（用于影响力计算）
        if stat_overrides:
            expected = expected_stats_from_override(stat_overrides)
        else:
            expected = expected_stats_from_attrs(attrs, player.position or "SF")

        # 预计算本场影响加成（每场相同，基于期望值）
        pre_impact = compute_impact(
            expected["pts"], expected["reb"], expected["ast"],
            expected["stl"], expected["blk"], expected.get("tov", 2.5),
        )

        for g_idx in range(n_games):
            # 无论 my_team_id 是否为 None，都从真实球队中取对手
            opp_id = get_opponent(my_team_id)
            try:
                opp_rating = _team_rating(opp_id, season_year)
            except Exception:
                opp_rating = 55.0
            base_wp = win_probability(my_rating, opp_rating)
            # ★ 关键：球员影响力调整胜率
            wp = adjusted_win_prob(base_wp, pre_impact)

            if stat_overrides:
                box = generate_game_with_overrides(stat_overrides, win_prob=wp)
            else:
                box = generate_game(
                    attrs=attrs, position=player.position or "SF",
                    role=1.0, win_prob=wp,
                )
            games.append(box)
            game_opponents.append(opp_id)
            _persist_game_log(
                player_id=player.player_id, team_id=my_team_id,
                opponent_team_id=opp_id, season_year=season_year,
                game_week=week, game_number=game_number_base + g_idx + 1,
                is_home=random.random() > 0.5, box=box,
            )
            attrs["fatigue"] = min(100, attrs["fatigue"] + random.randint(6, 12))

        state_json["last_impact"] = pre_impact
        state_json["total_games_played"] = game_number_base + n_games

        week_summary = aggregate_week(games)
        week_summary["games_this_week"] = n_games

        # ── 5. 更新最近比赛滑窗 & 连胜/连败 ─────────────────────────────────
        recent_games = update_recent_games(state_json, week_summary)
        update_streak(state_json, [{"won": g.player_won} for g in games])

        # ── 6. 触发事件 ──────────────────────────────────────────────────────
        milestone_flags = set(state_json.get("milestone_flags", []))
        fired_events = roll_events(
            attrs          = attrs,
            save_state_json= state_json,
            week_number    = week,
            season_year    = season_year,
            career_year    = save.career_year,
            is_playoff     = False,
            recent_games   = recent_games,
            milestone_flags= milestone_flags,
            cooldowns      = cooldowns,
            forced_chains  = forced_chains,
        )

        # ── 7. 应用事件效果 ──────────────────────────────────────────────────
        if fired_events:
            attrs = apply_effects(attrs, fired_events)
            enqueue_chains(state_json, fired_events, week)
            update_cooldowns(state_json, fired_events)
            update_one_time_flags(state_json, fired_events)

        # ── 8. 更新赛季累计统计 + 实时写入 DB（每周都写，供数据查看器使用）──
        season_stats = _update_season_stats(season_stats, week_summary)
        _persist_season_stats(player.player_id, my_team_id, season_year, season_stats)

        # ── 8b. 检查是否正在接近/超越历史记录（第15/25周触发实时叙事）─────────
        if week in (15, 25) and season_stats.get("games_played", 0) >= 10:
            _check_record_approach(save_id, player.player_id, season_year, week, season_stats, event_repo)

        # ── 9. 持久化：写回属性 + 存档 + 事件日志 ────────────────────────────
        player_repo.update_attributes(player.player_id, season_year, attrs)

        save_repo.update(save_id, {
            "current_week":  week + 1,
            "state_json":    state_json,
            "current_age":   save.current_age,
        })

        for fe in fired_events:
            event_repo.append({
                "save_id":        save_id,
                "player_id":      player.player_id,
                "season_year":    season_year,
                "week_number":    week,
                "event_key":      fe.event_def.key,
                "category":       fe.event_def.category,
                "severity":       fe.event_def.severity,
                "title":          fe.event_def.title,
                "narrative_text": fe.narrative,
                "attribute_delta": fe.attribute_delta,
                "stat_delta":     {},
                "is_player_choice": 0,
            })

        # ── 10. 收集本周需要玩家做选择的事件 ────────────────────────────────
        pending_choices = []
        for fe in fired_events:
            ev = fe.event_def
            if ev.choice_prompt and ev.choices:
                pending_choices.append({
                    "event_key":    ev.key,
                    "title":        ev.title,
                    "prompt":       ev.choice_prompt,
                    "narrative":    fe.narrative,
                    "options": [
                        {
                            "key":         opt.key,
                            "label":       opt.label,
                            "description": opt.description,
                            "effects":     [(e.attr, e.delta) for e in opt.attr_effects],
                            "narrative":   opt.narrative,
                            "chains_to":   opt.chains_to,
                            "impact_scope": opt.impact_scope,
                        }
                        for opt in ev.choices
                    ],
                })

        # ── 11. yield 本周结果给调用方 ───────────────────────────────────────
        yield WeekResult(
            week            = week,
            season_year     = season_year,
            games           = games,
            week_summary    = week_summary,
            events          = fired_events,
            attrs_after     = dict(attrs),
            season_stats    = dict(season_stats),
            pending_choices = pending_choices,
            impact          = pre_impact,     # 本周影响力数据
        )

    # ── 赛季结束：标记已完成 + 评估荣誉 ───────────────────────────────────────
    state_json["season_ended"] = True   # 持久化标记，不依赖 current_week
    save_repo.update(save_id, {"state_json": state_json})
    _evaluate_achievements(save_id, player.player_id, season_year, season_stats, event_repo)


def _check_record_approach(save_id, player_id, season_year, week, season_stats, event_repo):
    """实时检测球员数据是否接近或超越 NBA 历史单赛季记录，触发专属事件叙事。"""
    from simulation.season_manager import NBA_SEASON_RECORDS
    APPROACH_RATIO = 0.90  # 接近90%就开始叙事
    state_key      = f"record_event_fired_{season_year}"

    for stat_key, (record_val, holder, record_year) in NBA_SEASON_RECORDS.items():
        player_val = season_stats.get(stat_key, 0)
        if player_val <= 0:
            continue
        ratio = player_val / record_val
        fired_key = f"{state_key}_{stat_key}"

        if ratio >= 1.0:
            # 已超越历史记录
            title     = f"超越历史记录：{stat_key.upper()} {player_val:.1f}（{holder} {record_val}）"
            narrative = (
                f"数据摆在那里：{stat_key.upper()} {player_val:.1f}。\n"
                f"\n"
                f"{holder} 在 {record_year} 创下的 {record_val} 单赛季记录，"
                f"现在有人超越了它。\n"
                f"\n"
                f"统计员在数据库里更新了那一栏，\n"
                f"但没有人知道该怎么评价这件事——\n"
                f"因为语言是为正常范围内的事情准备的。"
            )
            severity = "legendary"
        elif ratio >= APPROACH_RATIO and week == 15:
            # 接近历史记录（第15周预警）
            title     = f"接近历史记录：{stat_key.upper()} {player_val:.1f}（{holder} {record_val}）"
            narrative = (
                f"有人注意到了。\n"
                f"\n"
                f"当前 {stat_key.upper()} 场均 {player_val:.1f}，"
                f"而 {holder} 在 {record_year} 的历史记录是 {record_val}。\n"
                f"\n"
                f"没有人大声说出来，但那个数字被悄悄地传了出去。\n"
                f"记者们开始在采访中绕着弯子提问。"
            )
            severity = "major"
        else:
            continue

        # 避免重复触发同一赛季同一项记录事件
        event_repo.append({
            "save_id":         save_id,
            "player_id":       player_id,
            "season_year":     season_year,
            "week_number":     week,
            "event_key":       f"record.{stat_key}.{'break' if ratio>=1 else 'approach'}",
            "category":        "career_milestones",
            "severity":        severity,
            "title":           title,
            "narrative_text":  narrative,
            "attribute_delta": {},
            "stat_delta":      {},
            "is_player_choice": 0,
        })


def _load_season_stats(player_id: int, season_year: int) -> dict:
    """从DB读取已有赛季统计，用于断点续玩时恢复累计数据。"""
    from database.connection import db
    with db() as conn:
        row = conn.execute(
            """SELECT games_played, points_pg, rebounds_pg, assists_pg,
                      steals_pg, blocks_pg, turnovers_pg, minutes_pg,
                      fg_pct, fg3_pct, ft_pct
               FROM player_season_stats
               WHERE player_id=? AND season_year=? AND season_type='Regular'""",
            (player_id, season_year)
        ).fetchone()
    if not row:
        return {}
    gp = row[0] or 0
    return {
        "games_played": gp,
        "pts": round(row[1] or 0, 1),
        "reb": round(row[2] or 0, 1),
        "ast": round(row[3] or 0, 1),
        "stl": round(row[4] or 0, 1),
        "blk": round(row[5] or 0, 1),
        "tov": round(row[6] or 0, 1),
        "min": round(row[7] or 0, 1),
        "fg_pct":  round(row[8] or 0, 3),
        "fg3_pct": round(row[9] or 0, 3),
        "ft_pct":  round(row[10] or 0, 3),
        # 总计字段（用于加权均值计算）
        "fg_made_total":  round((row[8] or 0) * gp * 13),
        "fg_att_total":   gp * 13,
        "fg3_made_total": round((row[9] or 0) * gp * 5),
        "fg3_att_total":  gp * 5,
        "ft_made_total":  round((row[10] or 0) * gp * 4),
        "ft_att_total":   gp * 4,
        "wins": 0,  # 胜场从game_log重算更准，这里给默认值
    }


def _persist_season_stats(
    player_id: int,
    team_id: int | None,
    season_year: int,
    stats: dict,
) -> None:
    from database.connection import db
    gp = stats.get("games_played", 0)
    if gp == 0:
        return
    with db() as conn:
        conn.execute(
            """
            INSERT INTO player_season_stats
              (player_id, team_id, season_year, season_type,
               games_played, games_started, minutes_pg,
               points_pg, rebounds_pg, assists_pg, steals_pg, blocks_pg, turnovers_pg,
               fg_pct, fg3_pct, ft_pct)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(player_id, season_year, season_type)
            DO UPDATE SET
              games_played=excluded.games_played,
              games_started=excluded.games_started,
              minutes_pg=excluded.minutes_pg,
              points_pg=excluded.points_pg,
              rebounds_pg=excluded.rebounds_pg,
              assists_pg=excluded.assists_pg,
              steals_pg=excluded.steals_pg,
              blocks_pg=excluded.blocks_pg,
              turnovers_pg=excluded.turnovers_pg,
              fg_pct=excluded.fg_pct,
              fg3_pct=excluded.fg3_pct,
              ft_pct=excluded.ft_pct
            """,
            (
                player_id, team_id, season_year, "Regular",
                gp, gp, stats.get("min", 0),
                stats.get("pts", 0), stats.get("reb", 0), stats.get("ast", 0),
                stats.get("stl", 0), stats.get("blk", 0), stats.get("tov", 0),
                stats.get("fg_pct", 0), stats.get("fg3_pct", 0), stats.get("ft_pct", 0),
            ),
        )


def _persist_game_log(
    player_id: int,
    team_id: int | None,
    opponent_team_id: int,
    season_year: int,
    game_week: int,
    game_number: int,
    is_home: bool,
    box: "GameBox",
) -> None:
    from database.connection import db

    def _try_insert(conn, opp_id):
        conn.execute(
            """INSERT OR IGNORE INTO player_game_log
               (player_id, team_id, opponent_team_id, season_year, game_week,
                game_number, is_home, minutes, points, rebounds, assists,
                steals, blocks, turnovers, fg_made, fg_attempted,
                fg3_made, fg3_attempted, ft_made, ft_attempted,
                plus_minus, player_won)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (player_id, team_id, opp_id, season_year, game_week,
             game_number, int(is_home),
             round(box.minutes, 1), box.points, box.rebounds, box.assists,
             box.steals, box.blocks, box.turnovers,
             box.fg_made, box.fg_attempted,
             box.fg3_made, box.fg3_attempted,
             box.ft_made, box.ft_attempted,
             box.plus_minus, int(box.player_won)),
        )

    try:
        with db() as conn:
            _try_insert(conn, opponent_team_id)
    except Exception:
        # 外键约束失败（对手 team_id 不在 teams 表中），用 NULL 写入
        try:
            with db() as conn:
                _try_insert(conn, None)
        except Exception:
            pass


def _evaluate_achievements(
    save_id: int,
    player_id: int,
    season_year: int,
    season_stats: dict,
    event_repo,
) -> None:
    """赛季末：调用 achievement_tracker，把荣誉写入 event_log。"""
    try:
        from simulation.achievement_tracker import evaluate_season
        awards = evaluate_season(save_id, player_id, season_year, season_stats)
        for award in awards:
            event_repo.append({
                "save_id":         save_id,
                "player_id":       player_id,
                "season_year":     season_year,
                "week_number":     31,     # 赛季末特殊周号
                "event_key":       f"award.{award['award_type']}",
                "category":        "career_milestones",
                "severity":        "legendary" if award["award_type"] in
                                   ("mvp", "champion", "quintuple_double_avg",
                                    "unprecedented_record") else "major",
                "title":           award["description"],
                "narrative_text":  f"赛季结束。你获得了：{award['description']}",
                "attribute_delta": {},
                "stat_delta":      {},
                "is_player_choice": 0,
            })
    except Exception:
        pass   # 荣誉评估失败不影响主流程
