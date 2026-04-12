"""
赛季末荣誉评估。
在每个赛季结束时调用 evaluate_season()，写荣誉到 awards 表，
同时返回荣誉列表供 engine 写入 event_log。
"""
from database.connection import db


# ── 荣誉类型中文说明 ──────────────────────────────────────────────────────────
AWARD_LABELS = {
    "allstar":              "全明星",
    "allnba_1":             "年度最佳阵容一队",
    "allnba_2":             "年度最佳阵容二队",
    "scoring_title":        "得分王",
    "rebounding_title":     "篮板王",
    "assist_title":         "助攻王",
    "steals_title":         "抢断王",
    "blocks_title":         "盖帽王",
    "mvp":                  "常规赛 MVP",
    "dpoy":                 "最佳防守球员",
    "champion":             "NBA 总冠军",
    "triple_double_avg":    "赛季场均三双",
    "quadruple_double_avg": "赛季场均四双",
    "quintuple_double_avg": "史诗级赛季场均五双",
    "efficiency_title":     "效率王（PER 最高）",
}

# 各单项历史记录（用于"史无前例"检测）
SEASON_AVG_RECORDS = {
    "pts": (36.1, "Wilt Chamberlain 1961-62"),
    "reb": (27.2, "Wilt Chamberlain 1960-61"),
    "ast": (14.5, "John Stockton 1989-90"),
    "stl": (3.67, "Alvin Robertson 1985-86"),
    "blk": (5.56, "Mark Eaton 1984-85"),
}


def evaluate_season(
    save_id: int,
    player_id: int,
    season_year: int,
    season_stats: dict,
) -> list[dict]:
    """
    根据赛季数据评估荣誉，写入 awards 表，返回荣誉列表。
    每个荣誉为 {"award_type": str, "description": str}。
    """
    pts = season_stats.get("pts", 0)
    reb = season_stats.get("reb", 0)
    ast = season_stats.get("ast", 0)
    stl = season_stats.get("stl", 0)
    blk = season_stats.get("blk", 0)
    gp  = season_stats.get("games_played", 0)
    wins = season_stats.get("wins", 0)

    # 用胜场推算球队赛季胜率（每周平均 3 场，30 周 = 90 场机会）
    win_rate = wins / max(gp, 1)
    proj_team_wins = round(win_rate * 82)

    earned: list[tuple[str, str]] = []

    # ── 个人数据项奖 ─────────────────────────────────────────────────────────
    if pts >= 25:
        earned.append(("scoring_title", f"得分王 {pts:.1f} 分/场"))
    if reb >= 13:
        earned.append(("rebounding_title", f"篮板王 {reb:.1f} 板/场"))
    if ast >= 11:
        earned.append(("assist_title", f"助攻王 {ast:.1f} 助/场"))
    if stl >= 2.5:
        earned.append(("steals_title", f"抢断王 {stl:.1f} 断/场"))
    if blk >= 3.0:
        earned.append(("blocks_title", f"盖帽王 {blk:.1f} 帽/场"))

    # ── 全明星 ───────────────────────────────────────────────────────────────
    star_score = pts * 0.5 + reb * 0.3 + ast * 0.4 + stl * 1.5 + blk * 1.5
    if star_score >= 14 or pts >= 18:
        earned.append(("allstar", "全明星"))

    # ── 最佳阵容 ─────────────────────────────────────────────────────────────
    if star_score >= 30:
        earned.append(("allnba_1", "年度最佳阵容一队"))
    elif star_score >= 22:
        earned.append(("allnba_2", "年度最佳阵容二队"))

    # ── MVP ──────────────────────────────────────────────────────────────────
    if pts >= 28 and proj_team_wins >= 52:
        earned.append(("mvp", f"常规赛 MVP ({pts:.1f}分 {proj_team_wins}胜)"))
    elif pts >= 32 and proj_team_wins >= 45:
        earned.append(("mvp", f"常规赛 MVP ({pts:.1f}分 超强个人表现)"))

    # ── 最佳防守 ─────────────────────────────────────────────────────────────
    def_score = blk * 2.5 + stl * 3.0
    if def_score >= 12:
        earned.append(("dpoy", f"最佳防守球员 ({blk:.1f}帽 {stl:.1f}断/场)"))

    # ── 冠军（基于球队胜率推算）─────────────────────────────────────────────
    if proj_team_wins >= 62:
        earned.append(("champion", f"NBA 总冠军 (球队预计 {proj_team_wins} 胜)"))
    elif proj_team_wins >= 55:
        # 季后赛夺冠概率较高，50% 概率给冠军
        import random
        if random.random() < 0.50:
            earned.append(("champion", f"NBA 总冠军 (季后赛逆境夺冠)"))

    # ── 场均多双 ─────────────────────────────────────────────────────────────
    double_fields = sum(1 for v in [pts, reb, ast, stl, blk] if v >= 10)
    if double_fields >= 5:
        earned.append(("quintuple_double_avg",
                        f"史诗级场均五双 {pts:.0f}/{reb:.0f}/{ast:.0f}/{stl:.0f}/{blk:.0f}"))
    elif double_fields >= 4:
        earned.append(("quadruple_double_avg",
                        f"场均四双 {pts:.0f}/{reb:.0f}/{ast:.0f}/{stl:.0f}/{blk:.0f}"))
    elif double_fields >= 3:
        earned.append(("triple_double_avg",
                        f"场均三双 {pts:.0f}/{reb:.0f}/{ast:.0f}"))

    # ── 史无前例检测 ─────────────────────────────────────────────────────────
    unprecedented = []
    for field_key, (record_val, holder) in SEASON_AVG_RECORDS.items():
        player_val = {"pts": pts, "reb": reb, "ast": ast, "stl": stl, "blk": blk}.get(field_key, 0)
        if player_val > record_val:
            unprecedented.append(
                f"{field_key.upper()} {player_val:.1f} 超越历史记录 {record_val}（{holder}）"
            )
    if unprecedented:
        for rec_desc in unprecedented:
            earned.append(("unprecedented_record", f"打破历史记录：{rec_desc}"))

    # ── 写入 awards 表 ───────────────────────────────────────────────────────
    result = []
    with db() as conn:
        for award_type, description in earned:
            # 同一存档同一赛季同一奖项不重复写入
            exists = conn.execute(
                "SELECT 1 FROM awards WHERE save_id=? AND season_year=? AND award_type=?",
                (save_id, season_year, award_type),
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO awards (save_id, player_id, season_year, award_type, description)"
                    " VALUES (?,?,?,?,?)",
                    (save_id, player_id, season_year, award_type, description),
                )
            result.append({"award_type": award_type, "description": description})

    return result


def get_awards(save_id: int, season_year: int | None = None) -> list[dict]:
    """取得本存档所有荣誉（或指定赛季）。"""
    sql = "SELECT season_year, award_type, description FROM awards WHERE save_id=?"
    params: list = [save_id]
    if season_year:
        sql += " AND season_year=?"
        params.append(season_year)
    sql += " ORDER BY season_year DESC, award_id"
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [{"season_year": r[0], "award_type": r[1], "description": r[2]} for r in rows]


def count_awards(save_id: int) -> dict:
    """统计各类荣誉数量，用于历史地位计算。"""
    with db() as conn:
        rows = conn.execute(
            "SELECT award_type, COUNT(*) FROM awards WHERE save_id=? GROUP BY award_type",
            (save_id,),
        ).fetchall()
    return {r[0]: r[1] for r in rows}
