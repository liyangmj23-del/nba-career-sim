"""
连锁事件管理器：读写 save_state.state_json 中的 pending_chains 和 cooldowns。
"""


def get_forced_chains(state_json: dict, current_week: int) -> list[str]:
    """返回本周应当强制触发的连锁事件 key 列表，并从 pending 中移除它们。"""
    pending = state_json.get("pending_chains", [])
    due     = [p["key"] for p in pending if p["fire_week"] <= current_week]
    state_json["pending_chains"] = [p for p in pending if p["fire_week"] > current_week]
    return due


def enqueue_chains(
    state_json: dict,
    fired_events,          # list[FiredEvent]
    current_week: int,
) -> None:
    """把本周触发事件的连锁事件放入 pending_chains。"""
    pending = state_json.setdefault("pending_chains", [])
    for fe in fired_events:
        ev = fe.event_def
        if ev.chains_to:
            # 若只有一个连锁目标，直接入队；多个取第一个（后续可扩展为随机）
            next_key = ev.chains_to[0]
            fire_week = current_week + max(1, ev.chain_delay)
            pending.append({"key": next_key, "fire_week": fire_week})


def update_cooldowns(
    state_json: dict,
    fired_events,
) -> None:
    """为本周触发的事件写入冷却期。"""
    cooldowns = state_json.setdefault("cooldowns", {})
    for fe in fired_events:
        ev = fe.event_def
        if ev.cooldown_weeks > 0:
            cooldowns[ev.key] = ev.cooldown_weeks


def tick_cooldowns(state_json: dict) -> dict:
    """每周开始时把所有冷却值 -1，返回当前冷却字典。"""
    cooldowns = state_json.get("cooldowns", {})
    cooldowns = {k: max(0, v - 1) for k, v in cooldowns.items()}
    state_json["cooldowns"] = cooldowns
    return cooldowns


def update_one_time_flags(state_json: dict, fired_events) -> set:
    """记录已触发过的 one_time 事件 key。"""
    flags = set(state_json.get("milestone_flags", []))
    for fe in fired_events:
        if fe.event_def.one_time:
            flags.add(fe.event_def.key)
    state_json["milestone_flags"] = list(flags)
    return flags


def update_streak(state_json: dict, recent_games: list[dict]) -> int:
    """
    根据本周比赛结果更新连胜/连败计数。
    正数 = 连胜，负数 = 连败。
    """
    streak = state_json.get("streak", 0)
    for g in recent_games:
        if g.get("won"):
            streak = max(0, streak) + 1
        else:
            streak = min(0, streak) - 1
    state_json["streak"] = streak
    return streak


def update_recent_games(state_json: dict, week_summary: dict) -> list[dict]:
    """
    把本周比赛汇总追加进 recent_games 滑窗（保留最近 3 周）。
    """
    recent = state_json.get("recent_games", [])
    recent.append({
        "pts":  week_summary.get("pts", 0),
        "reb":  week_summary.get("reb", 0),
        "ast":  week_summary.get("ast", 0),
        "won":  week_summary.get("wins", 0) > 0,
    })
    state_json["recent_games"] = recent[-3:]
    return state_json["recent_games"]
