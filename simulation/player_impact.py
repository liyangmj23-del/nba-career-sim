"""
球员影响力系统（完整版）
涵盖：数据影响、属性影响、位置权重、连锁效应、对手调整

影响维度：
  1. 进攻端：得分、助攻、出手质量
  2. 防守端：抢断、盖帽、防守评级
  3. 控场端：篮板、失误控制、节奏把控
  4. 无形端：领导力、篮球IQ、关键时刻
  5. 状态端：体力、疲劳、士气
  6. 对手端：根据防守数据压制对手相应数据
"""

# ── 联盟均值（首发级别）───────────────────────────────────────────────────────
LEAGUE_AVG_STARTER = {
    "pts": 15.0, "reb": 5.0, "ast": 4.0,
    "stl": 1.2,  "blk": 0.8, "tov": 2.2,
    "fg_pct": 0.465, "fg3_pct": 0.360, "ft_pct": 0.780,
}

# ── 各项数据每超出均值 1 单位的胜率影响（按位置有差异，此为通用基准）─────────
BASE_IMPACT_PER_UNIT = {
    "pts":   0.007,   # 得分
    "reb":   0.006,   # 篮板（进攻+防守混合）
    "ast":   0.010,   # 助攻（拉高队友效率）
    "stl":   0.018,   # 抢断（直接转换+心理震慑）
    "blk":   0.015,   # 盖帽（改变对方出手习惯）
    "tov":  -0.012,   # 失误（负向）
    "fg_bonus": 0.06, # FG%每高1%（0.01）的影响
}

# ── 位置权重乘数（不同位置同一数据影响力不同）───────────────────────────────
POSITION_WEIGHT = {
    "PG": {"pts":0.9, "reb":0.7, "ast":1.3, "stl":1.2, "blk":0.7, "tov":1.1},
    "SG": {"pts":1.1, "reb":0.8, "ast":1.0, "stl":1.1, "blk":0.8, "tov":1.0},
    "SF": {"pts":1.0, "reb":1.0, "ast":0.9, "stl":1.0, "blk":1.0, "tov":1.0},
    "PF": {"pts":1.0, "reb":1.2, "ast":0.8, "stl":0.9, "blk":1.2, "tov":1.0},
    "C":  {"pts":0.9, "reb":1.4, "ast":0.7, "stl":0.8, "blk":1.4, "tov":0.9},
}

# ── 超人级别加成（远超历史记录时额外奖励）──────────────────────────────────────
SUPERHUMAN = [
    # (stat, threshold, bonus, 描述)
    ("stl", 3.67, 0.05, "超历史抢断纪录"),
    ("stl", 5.0,  0.08, "超自然级抢断"),
    ("stl", 8.0,  0.12, "物理定律之外"),
    ("blk", 5.56, 0.05, "超历史盖帽纪录"),
    ("blk", 8.0,  0.10, "禁区统治者"),
    ("pts", 36.1, 0.05, "超历史场均得分"),
    ("pts", 50.0, 0.10, "半个世纪只此一次"),
    ("ast", 14.5, 0.05, "超历史助攻纪录"),
    ("reb", 27.2, 0.08, "超历史篮板纪录"),
]

# ── 组合效应（多项数据同时超标的协同加成）──────────────────────────────────────
COMBO_BONUSES = [
    # (条件列表, 加成, 描述)
    ([("pts",">=",10),("reb",">=",10),("ast",">=",10)],
     0.06, "场均三双——联盟视角的全能控场"),
    ([("pts",">=",10),("reb",">=",10),("ast",">=",10),("stl",">=",10)],
     0.12, "场均四双——已无历史先例"),
    ([("pts",">=",10),("reb",">=",10),("ast",">=",10),("stl",">=",10),("blk",">=",10)],
     0.20, "场均五双——超越篮球认知边界"),
    ([("stl",">=",5),("blk",">=",5)],
     0.08, "双向防守怪兽——对手攻无可攻"),
    ([("ast",">=",8),("tov","<=",2)],
     0.05, "零失误高效组织——完美球权管理"),
    ([("reb",">=",12),("blk",">=",4)],
     0.07, "内线统治——禁区不可撼动"),
    ([("pts",">=",25),("fg_pct",">=",0.55)],
     0.05, "高效得分——既多又准"),
]

# ── 属性对无形影响（球场外看不见的影响力）──────────────────────────────────────
ATTR_INVISIBLE_IMPACT = [
    # (属性, 每超过50分的加成系数, 说明)
    ("basketball_iq",  0.001, "阅读比赛能力影响整体决策质量"),
    ("clutch_factor",  0.0008,"关键时刻表现稳定性"),
    ("leadership",     0.0006,"领袖气质带动全队"),
    ("work_ethic",     0.0003,"训练态度影响长期稳定性"),
]

# ── 对手数据压制系数（防守数据对对方相应数据的影响）────────────────────────────
OPP_SUPPRESSION = {
    # 我方数据 -> 对方哪些数据被压制，压制系数（per unit above avg）
    "stl": {"opp_ast": -0.06, "opp_tov": +0.08},    # 抢断多→对方助攻减少、失误增加
    "blk": {"opp_pts": -0.04, "opp_fg_pct": -0.003}, # 盖帽多→对方得分、命中率下降
    "reb": {"opp_pts": -0.02},                        # 篮板多→对方二次进攻机会减少
    "ast": {"team_pts": +0.03},                        # 助攻多→队友得分提升
}


def compute_impact(
    pts: float, reb: float, ast: float,
    stl: float, blk: float, tov: float = 2.5,
    fg_pct: float = 0.465, position: str = "SF",
    attrs: dict | None = None,
) -> dict:
    """
    完整版球员影响力计算。
    返回影响力报告字典。
    """
    pos = position.upper() if position in POSITION_WEIGHT else "SF"
    pw  = POSITION_WEIGHT[pos]
    avg = LEAGUE_AVG_STARTER

    stats = {"pts":pts, "reb":reb, "ast":ast, "stl":stl, "blk":blk, "tov":tov, "fg_pct":fg_pct}
    breakdown = {}
    total = 0.0

    # ── 1. 数据影响（位置权重修正）────────────────────────────────────────────
    for key in ("pts","reb","ast","stl","blk","tov"):
        diff  = stats[key] - avg.get(key, 0)
        base  = BASE_IMPACT_PER_UNIT[key]
        w     = pw.get(key, 1.0)
        bonus = diff * base * w
        breakdown[f"stats_{key}"] = round(bonus, 4)
        total += bonus

    # 命中率影响
    fg_diff = fg_pct - avg["fg_pct"]
    fg_bonus = fg_diff * 100 * 0.004   # 每超出1% → +0.4%
    breakdown["stats_fg_pct"] = round(fg_bonus, 4)
    total += fg_bonus

    # ── 2. 超人级加成 ─────────────────────────────────────────────────────────
    superhuman_flags = []
    for key, threshold, extra, desc in SUPERHUMAN:
        if stats.get(key, 0) >= threshold:
            breakdown[f"super_{key}_{int(threshold)}"] = extra
            total += extra
            superhuman_flags.append(desc)

    # ── 3. 组合效应 ───────────────────────────────────────────────────────────
    combo_flags = []
    for conditions, bonus, desc in COMBO_BONUSES:
        if all(_check_cond(stats, k, op, v) for k, op, v in conditions):
            breakdown[f"combo"] = bonus
            total += bonus
            combo_flags.append(desc)
            break  # 只取最高档

    # ── 4. 属性无形影响 ───────────────────────────────────────────────────────
    if attrs:
        for attr_key, coef, _ in ATTR_INVISIBLE_IMPACT:
            val = attrs.get(attr_key, 50)
            bonus = (val - 50) * coef
            if abs(bonus) > 0.001:
                breakdown[f"attr_{attr_key}"] = round(bonus, 4)
                total += bonus

    # ── 5. 状态修正 ───────────────────────────────────────────────────────────
    if attrs:
        health  = attrs.get("health", 100)
        fatigue = attrs.get("fatigue", 0)
        morale  = attrs.get("morale", 75)
        state_mod = (health/100 * 0.5) + ((100-fatigue)/100 * 0.3) + (morale/100 * 0.2)
        state_bonus = (state_mod - 0.75) * 0.08  # 理想状态 +4%，糟糕状态 -6%
        breakdown["state_modifier"] = round(state_bonus, 4)
        total += state_bonus

    # ── 6. 最终 ───────────────────────────────────────────────────────────────
    wp_bonus = max(-0.30, min(0.30, total))

    return {
        "wp_bonus":    round(wp_bonus, 4),
        "raw_total":   round(total, 4),
        "breakdown":   breakdown,
        "label":       _label(wp_bonus),
        "superhuman":  superhuman_flags,
        "combos":      combo_flags,
        "opp_effects": compute_opp_effects(stl, blk, reb, ast, avg),
    }


def compute_opp_effects(stl: float, blk: float, reb: float, ast: float, avg: dict) -> dict:
    """
    计算对手受到的数据压制。
    返回 {对手数据字段: 变化量} 字典。
    """
    effects = {}
    stl_excess = max(0, stl - avg["stl"])
    blk_excess = max(0, blk - avg["blk"])
    reb_excess = max(0, reb - avg["reb"])
    ast_excess = max(0, ast - avg["ast"])

    effects["opp_pts_reduction"]  = round(blk_excess * 0.4 + stl_excess * 0.3, 2)
    effects["opp_fg_pct_penalty"] = round(blk_excess * 0.003, 4)
    effects["opp_tov_increase"]   = round(stl_excess * 0.5, 2)
    effects["opp_ast_reduction"]  = round(stl_excess * 0.4, 2)
    effects["team_pts_boost"]     = round(ast_excess * 0.5, 2)  # 队友得分提升
    effects["opp_2nd_chance_loss"]= round(reb_excess * 0.2, 2)  # 对方二次进攻机会减少
    return effects


def expected_stats_from_override(overrides: dict) -> dict:
    avg = LEAGUE_AVG_STARTER
    return {
        "pts":    overrides.get("pts",  avg["pts"]),
        "reb":    overrides.get("reb",  avg["reb"]),
        "ast":    overrides.get("ast",  avg["ast"]),
        "stl":    overrides.get("stl",  avg["stl"]),
        "blk":    overrides.get("blk",  avg["blk"]),
        "tov":    overrides.get("tov",  avg["tov"]),
        "fg_pct": overrides.get("fg_pct", avg["fg_pct"]),
    }


def expected_stats_from_attrs(attrs: dict, position: str = "SF") -> dict:
    """从属性推算期望数据（综合多因素）。"""
    def n(k): return max(0.0, min(1.0, (attrs.get(k, 50) - 1) / 98.0))

    health_m  = attrs.get("health", 100)  / 100
    fatigue_m = max(0.3, 1.0 - attrs.get("fatigue", 0) * 0.004)
    morale_m  = 0.85 + n("morale") * 0.3

    state = health_m * fatigue_m * morale_m

    pts = (4 + n("shooting_2pt")*16 + n("shooting_3pt")*6 +
           n("basketball_iq")*4 + n("clutch_factor")*2) * state
    reb = (1 + n("strength")*4.5 + n("vertical")*3.5 + n("basketball_iq")*1) * state
    ast = (0.5 + n("passing")*7 + n("ball_handling")*2 + n("basketball_iq")*2) * state
    stl = (0.2 + n("steal_tendency")*2.5 + n("speed")*0.5) * state
    blk = (0.1 + n("block_tendency")*3.0 + n("vertical")*0.5) * state
    tov = max(0.5, (1.5 + (1-n("ball_handling"))*2.0 + (1-n("basketball_iq"))*0.5) / state)
    fg  = 0.36 + n("shooting_2pt")*0.22 + n("basketball_iq")*0.05

    return {"pts":pts, "reb":reb, "ast":ast, "stl":stl, "blk":blk, "tov":tov, "fg_pct":fg}


def adjusted_win_prob(base_wp: float, impact: dict) -> float:
    return max(0.05, min(0.95, base_wp + impact["wp_bonus"]))


def impact_report_html(impact: dict, stats: dict) -> str:
    """生成影响力报告的 HTML 片段，用于游戏事件流。"""
    bonus = impact["wp_bonus"]
    sign  = "+" if bonus >= 0 else ""
    color = "#22c55e" if bonus >= 0.1 else ("#eab308" if bonus >= 0 else "#ef4444")
    label = impact["label"]

    lines = [f'<b style="color:{color}">影响力：{label}　胜率调整：{sign}{bonus*100:.1f}%</b>']

    # 各项数据对胜率的贡献
    key_contribs = []
    for k, v in sorted(impact["breakdown"].items(), key=lambda x: -abs(x[1])):
        if abs(v) < 0.005: continue
        s = "+" if v >= 0 else ""
        if k.startswith("stats_"):
            stat_name = {"pts":"得分","reb":"篮板","ast":"助攻","stl":"抢断",
                         "blk":"盖帽","tov":"失误","fg_pct":"命中率"}.get(k[6:], k[6:])
            key_contribs.append(f'<span style="color:{"#22c55e" if v>=0 else "#ef4444"}">{s}{v*100:.1f}% ({stat_name})</span>')

    if key_contribs:
        lines.append("  " + "　".join(key_contribs[:5]))

    if impact["combos"]:
        lines.append(f'<span style="color:#ffc107">★ {impact["combos"][0]}</span>')

    if impact["superhuman"]:
        lines.append(f'<span style="color:#a855f7">⚡ {" · ".join(impact["superhuman"])}</span>')

    # 对手受影响
    oe = impact.get("opp_effects", {})
    opp_parts = []
    if oe.get("opp_pts_reduction", 0) >= 1:
        opp_parts.append(f'对手得分 -{oe["opp_pts_reduction"]:.1f}')
    if oe.get("opp_tov_increase", 0) >= 0.5:
        opp_parts.append(f'对手失误 +{oe["opp_tov_increase"]:.1f}')
    if oe.get("team_pts_boost", 0) >= 0.5:
        opp_parts.append(f'队友得分 +{oe["team_pts_boost"]:.1f}')
    if opp_parts:
        lines.append(f'<span style="color:#94a3b8">战场影响：{"　".join(opp_parts)}</span>')

    return "<br>".join(lines)


# ── 内部工具 ──────────────────────────────────────────────────────────────────

def _check_cond(stats: dict, key: str, op: str, val: float) -> bool:
    v = stats.get(key, 0)
    if op == ">=": return v >= val
    if op == "<=": return v <= val
    if op == "==": return v == val
    return False


def _label(wp_bonus: float) -> str:
    if wp_bonus >= 0.25: return "史诗级统治"
    if wp_bonus >= 0.18: return "决定性影响"
    if wp_bonus >= 0.12: return "强烈正面影响"
    if wp_bonus >= 0.06: return "明显正面影响"
    if wp_bonus >= 0.02: return "小幅正面影响"
    if wp_bonus >= -0.02: return "影响中性"
    if wp_bonus >= -0.08: return "轻微负面影响"
    if wp_bonus >= -0.15: return "明显拖累"
    return "严重负面影响"
