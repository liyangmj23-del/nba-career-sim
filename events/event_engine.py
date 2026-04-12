"""
事件引擎：每周根据球员状态、比赛结果、冷却期等
从注册表中筛选可用事件，加权抽取并应用效果。
"""
import random
from dataclasses import dataclass, field
from typing import Any

from events.event_registry import (
    EventDefinition, Condition, AttrEffect,
    all_events, get_event,
)
from config import MAX_EVENTS_PER_WEEK, MAX_MAJOR_EVENTS_PER_WEEK, OFFCOURT_PLAYOFF_FACTOR

# 确保所有事件分类都被注册
import events.categories.game_performance  # noqa
import events.categories.injury            # noqa
import events.categories.personal_life     # noqa
import events.categories.team_chemistry    # noqa
import events.categories.career_milestones # noqa
import events.categories.off_court         # noqa
import events.categories.player_choices    # noqa


@dataclass
class FiredEvent:
    event_def: EventDefinition
    narrative: str          # 选中的叙事变体（支持 {pts} 等简单替换）
    attribute_delta: dict   # 实际应用的属性变化
    choice_made: str | None = None


def _resolve_delta(delta: int | tuple) -> int:
    if isinstance(delta, tuple):
        return random.randint(delta[0], delta[1])
    return delta


def _check_condition(cond: Condition, ctx: dict) -> bool:
    val = ctx.get(cond.attr)
    if val is None:
        return False
    op = cond.op
    if op == "<":      return val < cond.value
    if op == ">":      return val > cond.value
    if op == "<=":     return val <= cond.value
    if op == ">=":     return val >= cond.value
    if op == "==":     return val == cond.value
    if op == "!=":     return val != cond.value
    if op == "in":     return val in cond.value
    if op == "not_in": return val not in cond.value
    if op == "between":
        lo, hi = cond.value
        return lo <= val <= hi
    return False


def _check_all_conditions(ev: EventDefinition, ctx: dict) -> bool:
    return all(_check_condition(c, ctx) for c in ev.conditions)


def _effective_prob(ev: EventDefinition, ctx: dict) -> float:
    prob = ev.base_prob

    # 季后赛期间场外事件压缩
    if ctx.get("is_playoff") and ev.category in ("off_court", "personal_life"):
        prob *= OFFCOURT_PLAYOFF_FACTOR

    # 疲劳加重伤病概率
    if ev.category == "injury":
        fatigue = ctx.get("fatigue", 0)
        if fatigue >= 70:
            prob *= 1.5
        elif fatigue >= 50:
            prob *= 1.2

    # 月度事件只在第 4/8/12/... 周触发
    if ev.monthly_only and ctx.get("week_number", 1) % 4 != 0:
        return 0.0

    return min(prob, 1.0)


def build_context(
    attrs: dict,
    save_state_json: dict,
    week_number: int,
    season_year: int,
    career_year: int,
    is_playoff: bool,
    recent_games: list[dict],   # [{pts, reb, ast, won}, ...]
) -> dict:
    """
    把所有触发条件需要的字段汇总成一个上下文字典。
    """
    wins   = sum(1 for g in recent_games if g.get("won"))
    losses = len(recent_games) - wins
    pts_list = [g.get("pts", 0) for g in recent_games]
    high_pts = max(pts_list) if pts_list else 0
    avg_pts  = sum(pts_list) / len(pts_list) if pts_list else 0

    reb_list = [g.get("reb", 0) for g in recent_games]
    avg_reb  = sum(reb_list) / len(reb_list) if reb_list else 0

    # 从 state_json 拿连胜/连败
    streak = save_state_json.get("streak", 0)  # 正=连胜，负=连败

    ctx = {
        # 属性
        **attrs,
        # 状态
        "week_number":      week_number,
        "season_year":      season_year,
        "career_year":      career_year,
        "is_playoff":       is_playoff,
        # 本周比赛结果
        "week_wins":        wins,
        "week_losses":      losses,
        "week_avg_pts":     avg_pts,
        "week_high_pts":    high_pts,
        "rebounds_context": avg_reb,
        # 球队连胜/连败（正负）
        "team_win_streak":  max(0, streak),
        "team_loss_streak": max(0, -streak),
        # usage_rate 占位（Phase 2 简化处理）
        "usage_rate":       50,
    }
    return ctx


def roll_events(
    attrs: dict,
    save_state_json: dict,
    week_number: int,
    season_year: int,
    career_year: int,
    is_playoff: bool,
    recent_games: list[dict],
    milestone_flags: set[str],   # 已触发过的 one_time 事件 key 集合
    cooldowns: dict[str, int],   # {event_key: weeks_remaining}
    forced_chains: list[str],    # 本周必须触发的连锁事件 key
) -> list[FiredEvent]:
    """
    返回本周触发的事件列表（最多 MAX_EVENTS_PER_WEEK 个）。
    """
    ctx = build_context(
        attrs, save_state_json, week_number, season_year,
        career_year, is_playoff, recent_games,
    )

    fired: list[FiredEvent] = []
    major_count = 0

    # ── 1. 先处理强制连锁事件 ────────────────────────────────────────────────
    for key in forced_chains:
        ev = get_event(key)
        if ev:
            fe = _fire_event(ev, ctx)
            if fe:
                fired.append(fe)
                if ev.severity in ("major", "legendary"):
                    major_count += 1

    # ── 2. 筛选候选事件 ──────────────────────────────────────────────────────
    candidates = []
    choice_candidates = []   # 选择事件单独列表，优先保证触发一个

    for ev in all_events():
        if ev.key in forced_chains:
            continue
        if ev.one_time and ev.key in milestone_flags:
            continue
        if cooldowns.get(ev.key, 0) > 0:
            continue
        if not (ev.career_year_min <= career_year <= ev.career_year_max):
            continue
        if not _check_all_conditions(ev, ctx):
            continue
        prob = _effective_prob(ev, ctx)
        if prob <= 0:
            continue
        if ev.choices:
            choice_candidates.append((ev, prob))
        else:
            candidates.append((ev, prob))

    # ── 3. 优先抽一个选择事件（每周保证至少尝试一次）────────────────────────────
    random.shuffle(choice_candidates)
    choice_fired = False
    for ev, prob in choice_candidates:
        if random.random() < prob:
            fe = _fire_event(ev, ctx)
            if fe:
                fired.append(fe)
                if ev.severity in ("major", "legendary"):
                    major_count += 1
                choice_fired = True
                break   # 每周最多一个选择事件

    # ── 4. 再抽普通事件 ──────────────────────────────────────────────────────
    random.shuffle(candidates)
    for ev, prob in candidates:
        if len(fired) >= MAX_EVENTS_PER_WEEK:
            break
        if ev.severity in ("major", "legendary") and major_count >= MAX_MAJOR_EVENTS_PER_WEEK:
            continue
        if random.random() < prob:
            fe = _fire_event(ev, ctx)
            if fe:
                fired.append(fe)
                if ev.severity in ("major", "legendary"):
                    major_count += 1

    return fired


def _fire_event(ev: EventDefinition, ctx: dict) -> FiredEvent | None:
    narrative = random.choice(ev.narratives)
    # 简单变量替换（{pts} → 上下文中的最高分）
    narrative = narrative.replace("{pts}", str(int(ctx.get("week_high_pts", 0))))

    attr_delta = {}
    for eff in ev.attr_effects:
        d = _resolve_delta(eff.delta)
        attr_delta[eff.attr] = d

    return FiredEvent(
        event_def=ev,
        narrative=narrative,
        attribute_delta=attr_delta,
    )


def apply_effects(attrs: dict, fired_events: list[FiredEvent]) -> dict:
    """
    把所有触发事件的属性变化应用到 attrs 副本，返回新 attrs。
    （临时效果 duration_weeks > 0 由引擎层管理，此处只处理永久变化。）
    """
    # health/morale/fatigue 是 0-100 的状态值，其余技术属性是 1-99
    _STATE_ATTRS = {"health", "morale", "fatigue"}

    new_attrs = dict(attrs)
    for fe in fired_events:
        for attr, delta in fe.attribute_delta.items():
            if attr in new_attrs:
                lo, hi = (0, 100) if attr in _STATE_ATTRS else (1, 99)
                new_attrs[attr] = max(lo, min(hi, new_attrs[attr] + delta))
            elif attr == "usage_rate":
                pass  # 忽略虚拟属性
    # 重算综合评分
    skill_keys = [
        "speed", "strength", "vertical", "endurance",
        "ball_handling", "shooting_2pt", "shooting_3pt", "free_throw",
        "passing", "post_moves", "perimeter_def", "interior_def",
        "steal_tendency", "block_tendency", "basketball_iq",
        "clutch_factor", "leadership", "work_ethic", "media_handling",
    ]
    new_attrs["overall_rating"] = max(1, min(99,
        round(sum(new_attrs.get(k, 50) for k in skill_keys) / len(skill_keys))
    ))
    return new_attrs
