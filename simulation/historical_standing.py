"""
历史地位系统：根据生涯累计数据+荣誉计算历史评级。
"""
from database.connection import db
from simulation.achievement_tracker import count_awards

# ── NBA 历史生涯记录（用于对比）────────────────────────────────────────────────
NBA_CAREER_RECORDS = {
    "pts":  {"record": 38652, "holder": "LeBron James",       "unit": "分"},
    "reb":  {"record": 23924, "holder": "Wilt Chamberlain",    "unit": "篮板"},
    "ast":  {"record": 15806, "holder": "John Stockton",       "unit": "助攻"},
    "stl":  {"record": 3265,  "holder": "John Stockton",       "unit": "抢断"},
    "blk":  {"record": 3830,  "holder": "Hakeem Olajuwon",     "unit": "盖帽"},
    "gp":   {"record": 1611,  "holder": "Robert Parish",       "unit": "场"},
}

# ── 历史地位等级（HOF 积分阈值）─────────────────────────────────────────────────
TIERS = [
    (250, "前无古人 — 超越人类极限"),
    (180, "历史 GOAT 级 — 篮球神话"),
    (120, "名人堂第一梯队"),
    (70,  "名人堂"),
    (35,  "全明星级生涯"),
    (15,  "联盟长期主力"),
    (5,   "NBA 老将"),
    (0,   "新秀/短暂生涯"),
]

# HOF 积分权重
HOF_WEIGHTS = {
    "mvp":                  20,
    "champion":             25,
    "allstar":              4,
    "allnba_1":             8,
    "allnba_2":             5,
    "dpoy":                 8,
    "scoring_title":        6,
    "rebounding_title":     6,
    "assist_title":         6,
    "triple_double_avg":    5,
    "quadruple_double_avg": 15,
    "quintuple_double_avg": 50,
    "unprecedented_record": 30,
}


def get_career_totals(player_id: int, save_id: int) -> dict:
    """从 player_season_stats 聚合生涯总计数据，只统计当前存档的赛季，防止跨存档数据混合。"""
    with db() as conn:
        # 取该存档出现过的赛季（通过 event_log 过滤）
        save_seasons = {r[0] for r in conn.execute(
            "SELECT DISTINCT season_year FROM event_log WHERE save_id=?",
            (save_id,)
        ).fetchall()}

        rows = conn.execute(
            """SELECT season_year, games_played, points_pg, rebounds_pg,
                      assists_pg, steals_pg, blocks_pg, turnovers_pg
               FROM player_season_stats
               WHERE player_id=? AND season_type='Regular'
               ORDER BY season_year""",
            (player_id,),
        ).fetchall()

    # 隔离：只计入该存档参与的赛季
    if save_seasons:
        rows = [r for r in rows if r[0] in save_seasons]

    totals = {
        "seasons": 0, "games": 0,
        "pts": 0.0, "reb": 0.0, "ast": 0.0, "stl": 0.0, "blk": 0.0, "tov": 0.0,
        "best_pts": 0.0, "best_reb": 0.0, "best_ast": 0.0,
        "best_stl": 0.0, "best_blk": 0.0,
        "season_data": [],
    }

    for r in rows:
        gp = r[1] or 0
        totals["seasons"] += 1
        totals["games"]   += gp
        totals["pts"]     += (r[2] or 0) * gp
        totals["reb"]     += (r[3] or 0) * gp
        totals["ast"]     += (r[4] or 0) * gp
        totals["stl"]     += (r[5] or 0) * gp
        totals["blk"]     += (r[6] or 0) * gp
        totals["tov"]     += (r[7] or 0) * gp
        totals["best_pts"] = max(totals["best_pts"], r[2] or 0)
        totals["best_reb"] = max(totals["best_reb"], r[3] or 0)
        totals["best_ast"] = max(totals["best_ast"], r[4] or 0)
        totals["best_stl"] = max(totals["best_stl"], r[5] or 0)
        totals["best_blk"] = max(totals["best_blk"], r[6] or 0)
        totals["season_data"].append({
            "year": r[0], "gp": gp,
            "pts": round(r[2] or 0, 1), "reb": round(r[3] or 0, 1),
            "ast": round(r[4] or 0, 1),
        })

    # 生涯场均
    g = totals["games"]
    totals["avg_pts"] = round(totals["pts"] / g, 1) if g else 0
    totals["avg_reb"] = round(totals["reb"] / g, 1) if g else 0
    totals["avg_ast"] = round(totals["ast"] / g, 1) if g else 0
    totals["avg_stl"] = round(totals["stl"] / g, 1) if g else 0
    totals["avg_blk"] = round(totals["blk"] / g, 1) if g else 0

    return totals


def compute_hof_score(save_id: int, player_id: int) -> tuple[float, dict]:
    """
    计算 HOF 积分。
    返回 (总分, 积分明细字典)。
    """
    awards    = count_awards(save_id)
    totals    = get_career_totals(player_id, save_id)
    breakdown = {}

    score = 0.0

    # ── 荣誉积分 ─────────────────────────────────────────────────────────────
    for award_type, weight in HOF_WEIGHTS.items():
        cnt = awards.get(award_type, 0)
        if cnt:
            pts = cnt * weight
            breakdown[award_type] = pts
            score += pts

    # ── 生涯总数积分 ─────────────────────────────────────────────────────────
    # 每 1000 分 +1 分
    scoring_pts = totals["pts"] / 1000
    if scoring_pts:
        breakdown["career_pts_bonus"] = round(scoring_pts, 1)
        score += scoring_pts

    # 每 1000 篮板 +0.8 分
    reb_pts = totals["reb"] / 1000 * 0.8
    if reb_pts:
        breakdown["career_reb_bonus"] = round(reb_pts, 1)
        score += reb_pts

    # 每 1000 助攻 +0.8 分
    ast_pts = totals["ast"] / 1000 * 0.8
    if ast_pts:
        breakdown["career_ast_bonus"] = round(ast_pts, 1)
        score += ast_pts

    # ── 历史记录比较 ─────────────────────────────────────────────────────────
    field_map = {
        "pts": totals["pts"], "reb": totals["reb"],
        "ast": totals["ast"], "stl": totals["stl"], "blk": totals["blk"],
    }
    for key, career_val in field_map.items():
        rec = NBA_CAREER_RECORDS[key]
        if career_val >= rec["record"]:
            extra = 40 * (career_val / rec["record"] - 1) + 30
            breakdown[f"breaks_{key}_record"] = round(extra, 1)
            score += extra
        elif career_val >= rec["record"] * 0.7:
            extra = (career_val / rec["record"]) * 10
            breakdown[f"top_{key}_career"] = round(extra, 1)
            score += extra

    return round(score, 1), breakdown


def get_historical_tier(score: float) -> str:
    for threshold, label in TIERS:
        if score >= threshold:
            return label
    return TIERS[-1][1]


def build_historical_report(save_id: int, player_id: int, player_name: str) -> dict:
    """
    构建完整的历史地位报告，供 StatsViewer 展示。
    """
    totals      = get_career_totals(player_id, save_id)
    hof_score, breakdown = compute_hof_score(save_id, player_id)
    tier        = get_historical_tier(hof_score)
    awards_cnt  = count_awards(save_id)

    # 与历史记录对比
    comparisons = []
    field_map = {
        "pts": ("得分", totals["pts"]),
        "reb": ("篮板", totals["reb"]),
        "ast": ("助攻", totals["ast"]),
        "stl": ("抢断", totals["stl"]),
        "blk": ("盖帽", totals["blk"]),
    }
    for key, (label, val) in field_map.items():
        rec = NBA_CAREER_RECORDS[key]
        pct = val / rec["record"] * 100 if rec["record"] else 0
        status = ""
        if val >= rec["record"]:
            status = f"超越历史记录！(x{val/rec['record']:.1f})"
        elif pct >= 90:
            status = f"历史前列 ({pct:.0f}%)"
        elif pct >= 50:
            status = f"历史中上 ({pct:.0f}%)"
        comparisons.append({
            "label":   label,
            "value":   round(val),
            "record":  rec["record"],
            "holder":  rec["holder"],
            "pct":     round(pct, 1),
            "status":  status,
        })

    # 生涯里程碑
    milestones = []
    for pts_milestone in [5000, 10000, 15000, 20000, 25000, 30000, 38652]:
        if totals["pts"] >= pts_milestone:
            milestones.append(f"生涯 {pts_milestone:,} 分")
    for reb_milestone in [5000, 10000, 15000, 20000]:
        if totals["reb"] >= reb_milestone:
            milestones.append(f"生涯 {reb_milestone:,} 篮板")
    for ast_milestone in [3000, 5000, 8000, 10000, 15000]:
        if totals["ast"] >= ast_milestone:
            milestones.append(f"生涯 {ast_milestone:,} 助攻")
    if totals["blk"] > NBA_CAREER_RECORDS["blk"]["record"]:
        milestones.append("盖帽历史记录保持者")
    if totals["stl"] > NBA_CAREER_RECORDS["stl"]["record"]:
        milestones.append("抢断历史记录保持者")

    return {
        "player_name":  player_name,
        "hof_score":    hof_score,
        "tier":         tier,
        "totals":       totals,
        "comparisons":  comparisons,
        "milestones":   milestones,
        "awards_count": awards_cnt,
        "breakdown":    breakdown,
    }
