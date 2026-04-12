"""
NBA 模拟器 Web 应用 —— Flask 后端。
所有游戏逻辑来自 simulation/ 和 database/，这里只做路由和 JSON 序列化。
"""
import sys, json, datetime, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, jsonify, session

from database.schema import init_database
from database.repositories.player_repo import PlayerRepository
from database.repositories.team_repo import TeamRepository
from database.repositories.save_repo import SaveRepository
from database.repositories.event_log_repo import EventLogRepository
from database.connection import db as getdb
from simulation.week_runner import run_one_week, week_result_to_dict
from simulation.achievement_tracker import evaluate_season
from simulation.historical_standing import build_historical_report
from seeding.data_transformer import derive_attributes
from config import CURRENT_SEASON_YEAR

app = Flask(__name__)
app.secret_key = "nba-sim-secret-2025"

# ── 初始化 ────────────────────────────────────────────────────────────────────
init_database()

# 后台检查更新（不阻塞启动）
from web.updater import check_update_async, get_update_info
check_update_async()
player_repo = PlayerRepository()
team_repo   = TeamRepository()
save_repo   = SaveRepository()
event_repo  = EventLogRepository()


# ══════════════════════════════════════════════════════════════════════════════
# 主菜单
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def menu():
    saves = save_repo.get_all()
    return render_template("main_menu.html", saves=saves)


# ══════════════════════════════════════════════════════════════════════════════
# 选择现有球员
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/select")
def player_select():
    q = request.args.get("q", "").strip()
    if q:
        players = player_repo.search(q)[:30]
    else:
        players = player_repo.get_all(active_only=True)[:40]

    # 附加 overall rating
    result = []
    for p in players:
        attr = player_repo.get_attributes(p.player_id, CURRENT_SEASON_YEAR)
        overall = attr.overall_rating if attr else "-"
        result.append({
            "id": p.player_id, "name": p.full_name,
            "pos": p.position or "-", "overall": overall,
            "team_id": p.current_team_id,
        })
    return render_template("player_select.html", players=result, q=q)


@app.route("/new/<int:player_id>", methods=["POST"])
def new_game(player_id):
    player = player_repo.get_by_id(player_id)
    if not player:
        return redirect(url_for("player_select"))

    attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
    if not attr:
        attrs_data = derive_attributes(player.player_id, player.position, None)
        player_repo.upsert_attributes(attrs_data)

    age = None
    if player.birthdate:
        try:
            bd  = datetime.date.fromisoformat(player.birthdate[:10])
            now = datetime.date.today()
            age = now.year - bd.year - ((now.month, now.day) < (bd.month, bd.day))
        except Exception:
            pass

    career_year = max(1, CURRENT_SEASON_YEAR - (player.from_year or CURRENT_SEASON_YEAR - 1))
    save_name   = f"{player.full_name}  {CURRENT_SEASON_YEAR-1}-{str(CURRENT_SEASON_YEAR)[2:]}"
    save_id = save_repo.create({
        "save_name": save_name, "player_id": player.player_id,
        "current_team_id": player.current_team_id,
        "current_season": CURRENT_SEASON_YEAR, "current_week": 1,
        "current_age": age, "career_year": career_year, "state_json": {},
    })
    return redirect(url_for("game", save_id=save_id))


# ══════════════════════════════════════════════════════════════════════════════
# 新建自定义球员
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/create-player", methods=["GET", "POST"])
def create_player():
    teams = team_repo.get_all()
    if request.method == "GET":
        return render_template("create_player.html", teams=teams)

    name     = request.form.get("name", "").strip()
    position = request.form.get("position", "PG")
    age      = int(request.form.get("age", 22))
    career_year = int(request.form.get("career_year", 1))
    team_id_raw = request.form.get("team_id", "").strip()
    overall_raw = request.form.get("overall", "").strip()

    if not name:
        return render_template("create_player.html", teams=teams, error="请输入球员姓名")

    team_id = int(team_id_raw) if team_id_raw.isdigit() else None

    with getdb() as conn:
        row = conn.execute("SELECT MIN(player_id) FROM players WHERE player_id < 0").fetchone()
        cid = (row[0] or 0) - 1

    parts = name.split(maxsplit=1)
    player_repo.upsert({
        "player_id": cid, "first_name": parts[0],
        "last_name": parts[1] if len(parts) > 1 else "",
        "full_name": name, "position": position,
        "is_active": 1, "is_custom": 1, "current_team_id": team_id,
        "from_year": CURRENT_SEASON_YEAR - career_year,
    })

    attrs_data = derive_attributes(cid, position, None)
    if overall_raw.isdigit():
        ov = max(1, min(99, int(overall_raw)))
        diff = ov - attrs_data.get("overall_rating", 50)
        for k in list(attrs_data.keys()):
            if k not in ("player_id","season_year","overall_rating","health","morale","fatigue"):
                attrs_data[k] = max(1, min(99, attrs_data[k] + diff))
        attrs_data["overall_rating"] = ov
    player_repo.upsert_attributes(attrs_data)

    save_id = save_repo.create({
        "save_name": f"[自定义] {name}",
        "player_id": cid, "current_team_id": team_id,
        "current_season": CURRENT_SEASON_YEAR, "current_week": 1,
        "current_age": age, "career_year": career_year, "state_json": {},
    })
    return redirect(url_for("game", save_id=save_id))


# ══════════════════════════════════════════════════════════════════════════════
# 加载存档
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/load/<int:save_id>")
def load_game(save_id):
    return redirect(url_for("game", save_id=save_id))


# ══════════════════════════════════════════════════════════════════════════════
# 游戏主界面
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>")
def game(save_id):
    save = save_repo.get_by_id(save_id)
    if not save:
        return redirect(url_for("menu"))

    player = player_repo.get_by_id(save.player_id)
    if not player:
        return redirect(url_for("menu"))

    attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
    attrs = {}
    if attr:
        skip = {"attr_id","player_id","season_year"}
        attrs = {k: getattr(attr, k) for k in attr.__dataclass_fields__ if k not in skip}

    # 赛季累计统计
    season_stats = _get_season_stats(player.player_id, CURRENT_SEASON_YEAR)

    # 已有事件（最近30条）
    events = event_repo.get_by_save(save_id, limit=50)

    # 球队名
    team_name = "-"
    if save.current_team_id:
        t = team_repo.get_by_id(save.current_team_id)
        if t:
            team_name = f"{t.full_name} ({t.abbreviation})"

    # 当前 stat_overrides
    overrides = save.state_json.get("stat_overrides", {})
    season_done = save.current_week > 30

    return render_template("game.html",
        save=save, player=player, attrs=attrs,
        season_stats=season_stats, events=events,
        team_name=team_name, overrides=overrides,
        season_done=season_done,
        CURRENT_SEASON_YEAR=CURRENT_SEASON_YEAR,
    )


# ══════════════════════════════════════════════════════════════════════════════
# AJAX: 推进一周
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>/advance", methods=["POST"])
def advance_week(save_id):
    try:
        save = save_repo.get_by_id(save_id)
        if not save or save.current_week > 30:
            return jsonify({"season_done": True, "week": save.current_week if save else 31})

        wr = run_one_week(save_id, CURRENT_SEASON_YEAR)
        if wr is None:
            return jsonify({"season_done": True, "week": 31})

        result = week_result_to_dict(wr)
        result["season_done"] = (wr.week >= 30)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "season_done": False}), 500


# ══════════════════════════════════════════════════════════════════════════════
# AJAX: 应用玩家选择
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>/choice", methods=["POST"])
def apply_choice(save_id):
    data = request.get_json()
    chosen_key = data.get("chosen_key", "")
    options    = data.get("options", [])
    opt = next((o for o in options if o["key"] == chosen_key), None)
    if not opt:
        return jsonify({"ok": False})

    # 应用属性效果
    save = save_repo.get_by_id(save_id)
    if not save:
        return jsonify({"ok": False})
    player = player_repo.get_by_id(save.player_id)
    attr   = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
    if not attr:
        return jsonify({"ok": False})

    skip = {"attr_id","player_id","season_year"}
    attrs = {k: getattr(attr, k) for k in attr.__dataclass_fields__ if k not in skip}
    delta = {}
    for a_name, d in opt.get("effects", []):
        resolved = random.randint(d[0], d[1]) if isinstance(d, list) else d
        lo, hi   = (0, 100) if a_name in ("health","morale","fatigue") else (1, 99)
        new_val  = max(lo, min(hi, attrs.get(a_name, 50) + resolved))
        delta[a_name] = resolved
        attrs[a_name]  = new_val
    if delta:
        player_repo.update_attributes(player.player_id, CURRENT_SEASON_YEAR, attrs)

    # 记录选择
    event_repo.append({
        "save_id": save_id, "player_id": player.player_id,
        "season_year": CURRENT_SEASON_YEAR,
        "week_number": save.current_week - 1,
        "event_key": f"choice.{chosen_key}",
        "category": "career_milestones", "severity": "major",
        "title": opt.get("label",""),
        "narrative_text": opt.get("narrative",""),
        "attribute_delta": delta, "stat_delta": {},
        "is_player_choice": 1, "choice_made": chosen_key,
    })

    return jsonify({"ok": True, "attrs": attrs, "delta": delta,
                    "narrative": opt.get("narrative",""),
                    "impact_scope": opt.get("impact_scope","week")})


# ══════════════════════════════════════════════════════════════════════════════
# 设置数据覆盖（神模式）
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>/override", methods=["POST"])
def set_override(save_id):
    data  = request.get_json()
    save  = save_repo.get_by_id(save_id)
    if not save:
        return jsonify({"ok": False})
    state = dict(save.state_json)
    overrides = {}
    for key in ("pts","reb","ast","stl","blk"):
        val = data.get(key)
        if val is not None and str(val).replace(".","").isdigit():
            overrides[key] = float(val)
    if overrides:
        state["stat_overrides"] = overrides
    else:
        state.pop("stat_overrides", None)
    save_repo.update(save_id, {"state_json": state})
    return jsonify({"ok": True, "overrides": overrides})


# ══════════════════════════════════════════════════════════════════════════════
# 修改球员属性（CRUD）
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>/update-attrs", methods=["POST"])
def update_attrs(save_id):
    data   = request.get_json()
    save   = save_repo.get_by_id(save_id)
    player = player_repo.get_by_id(save.player_id) if save else None
    if not player:
        return jsonify({"ok": False})

    updates = {}
    for k, v in data.items():
        try:
            val = int(v)
            lo, hi = (0,100) if k in ("health","morale","fatigue") else (1,99)
            updates[k] = max(lo, min(hi, val))
        except (ValueError, TypeError):
            pass

    if updates:
        # 重算综合评分
        attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
        if attr:
            skip = {"attr_id","player_id","season_year"}
            merged = {k: getattr(attr, k) for k in attr.__dataclass_fields__ if k not in skip}
            merged.update(updates)
            skill_keys = [
                "speed","strength","vertical","endurance","ball_handling",
                "shooting_2pt","shooting_3pt","free_throw","passing","post_moves",
                "perimeter_def","interior_def","steal_tendency","block_tendency",
                "basketball_iq","clutch_factor","leadership","work_ethic","media_handling",
            ]
            updates["overall_rating"] = max(1, min(99, round(
                sum(merged.get(k,50) for k in skill_keys) / len(skill_keys)
            )))
        player_repo.update_attributes(player.player_id, CURRENT_SEASON_YEAR, updates)

    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════════════
# 数据查看页
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>/stats")
def game_stats(save_id):
    save = save_repo.get_by_id(save_id)
    if not save:
        return redirect(url_for("menu"))
    player = player_repo.get_by_id(save.player_id)

    # 逐场数据
    with getdb() as conn:
        game_log = conn.execute(
            """SELECT gl.game_week, gl.game_number, gl.is_home,
                      t.abbreviation, gl.player_won,
                      gl.points, gl.rebounds, gl.assists,
                      gl.steals, gl.blocks, gl.turnovers,
                      gl.fg_made, gl.fg_attempted,
                      gl.fg3_made, gl.fg3_attempted,
                      gl.ft_made, gl.ft_attempted, gl.plus_minus
               FROM player_game_log gl
               LEFT JOIN teams t ON gl.opponent_team_id = t.team_id
               WHERE gl.player_id=? ORDER BY gl.game_number""",
            (player.player_id,),
        ).fetchall()

    games = []
    for r in game_log:
        fga=r[12]; fg3a=r[14]; fta=r[16]
        games.append({
            "week":r[0],"gnum":r[1],"home":r[2],
            "opp":r[3] or "?","won":r[4],
            "pts":r[5],"reb":r[6],"ast":r[7],
            "stl":r[8],"blk":r[9],"tov":r[10],
            "fgm":r[11],"fga":fga,
            "fg3m":r[13],"fg3a":fg3a,
            "ftm":r[15],"fta":fta,"pm":r[17],
            "fg_pct": round(r[11]/fga*100,1) if fga else 0,
            "fg3_pct": round(r[13]/fg3a*100,1) if fg3a else 0,
            "ft_pct": round(r[15]/fta*100,1) if fta else 0,
        })

    # 赛季统计
    season_rows = _get_all_season_stats(player.player_id)

    # 荣誉
    with getdb() as conn:
        award_rows = conn.execute(
            "SELECT season_year, award_type, description FROM awards WHERE save_id=? ORDER BY season_year, award_id",
            (save_id,)
        ).fetchall()
    awards = [{"year":r[0],"type":r[1],"desc":r[2]} for r in award_rows]

    # 历史地位
    history = build_historical_report(save_id, player.player_id, player.full_name)

    # 事件
    events = event_repo.get_by_save(save_id, limit=200)

    return render_template("game_stats.html",
        save=save, player=player, games=games,
        season_rows=season_rows, awards=awards,
        history=history, events=events,
        CURRENT_SEASON_YEAR=CURRENT_SEASON_YEAR,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Box Score（某场比赛）
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/game/<int:save_id>/box/<int:game_num>")
def box_score(save_id, game_num):
    save = save_repo.get_by_id(save_id)
    if not save:
        return jsonify({"error": "save not found"})
    player = player_repo.get_by_id(save.player_id)

    # 从 game_log 取当场数据
    with getdb() as conn:
        row = conn.execute(
            """SELECT gl.game_week, gl.opponent_team_id, gl.player_won,
                      gl.points, gl.rebounds, gl.assists,
                      gl.steals, gl.blocks, gl.turnovers,
                      gl.fg_made, gl.fg_attempted,
                      gl.fg3_made, gl.fg3_attempted,
                      gl.ft_made, gl.ft_attempted, gl.plus_minus
               FROM player_game_log gl
               WHERE gl.player_id=? AND gl.game_number=?""",
            (player.player_id, game_num)
        ).fetchone()

    if not row:
        return jsonify({"error": "game not found"})

    game_week, opp_id, won = row[0], row[1], row[2]

    class _FakeBox:
        def __init__(self, r):
            self.minutes=36.0; self.points=r[3]; self.rebounds=r[4]
            self.assists=r[5]; self.steals=r[6]; self.blocks=r[7]
            self.turnovers=r[8]; self.fg_made=r[9]; self.fg_attempted=r[10]
            self.fg3_made=r[11]; self.fg3_attempted=r[12]
            self.ft_made=r[13]; self.ft_attempted=r[14]
            self.plus_minus=r[15]; self.player_won=won

    from simulation.game_simulator import generate_full_box_score
    from simulation.team_simulator import get_opponent, _ALL_TEAM_IDS
    import random as _rnd

    # my_team_id / opp_id 可能为 None（自由球员）→ 随机取真实球队
    my_tid  = save.current_team_id or _rnd.choice(_ALL_TEAM_IDS)
    opp_tid = opp_id or get_opponent(my_tid)

    box = generate_full_box_score(
        my_team_id   = my_tid,
        opp_team_id  = opp_tid,
        season_year  = CURRENT_SEASON_YEAR,
        game_week    = game_week,
        game_number  = game_num,
        player_id    = player.player_id,
        hero_box     = _FakeBox(row),
        my_team_won  = bool(won),
    )

    def team_dict(t):
        return {
            "name": t.team_name, "abbr": t.abbreviation,
            "pts": t.total_points, "won": t.won,
            "players": [{
                "name": p.name, "pos": p.position,
                "is_hero": p.is_hero, "is_starter": p.is_starter,
                "pts": p.points, "reb": p.rebounds, "ast": p.assists,
                "stl": p.steals, "blk": p.blocks, "tov": p.turnovers,
                "fgm": p.fg_made, "fga": p.fg_attempted,
                "fg3m": p.fg3_made, "fg3a": p.fg3_attempted,
                "ftm": p.ft_made, "fta": p.ft_attempted,
                "pm": p.plus_minus,
                "fg_pct": round(p.fg_made/p.fg_attempted*100,1) if p.fg_attempted else 0,
            } for p in t.players],
        }
    return jsonify({"home": team_dict(box.home), "away": team_dict(box.away),
                    "week": game_week, "gnum": game_num})


# ══════════════════════════════════════════════════════════════════════════════
# 版本检查
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/update-info")
def update_info():
    return jsonify(get_update_info())


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _get_season_stats(player_id: int, season_year: int) -> dict:
    with getdb() as conn:
        row = conn.execute(
            """SELECT games_played, points_pg, rebounds_pg, assists_pg,
                      steals_pg, blocks_pg, turnovers_pg,
                      fg_pct, fg3_pct, ft_pct
               FROM player_season_stats
               WHERE player_id=? AND season_year=? AND season_type='Regular'""",
            (player_id, season_year)
        ).fetchone()
    if not row:
        return {}
    return {
        "gp": row[0], "pts": round(row[1],1), "reb": round(row[2],1),
        "ast": round(row[3],1), "stl": round(row[4],1), "blk": round(row[5],1),
        "tov": round(row[6],1),
        "fg": round((row[7] or 0)*100,1), "fg3": round((row[8] or 0)*100,1),
        "ft": round((row[9] or 0)*100,1),
    }


def _get_all_season_stats(player_id: int) -> list[dict]:
    with getdb() as conn:
        rows = conn.execute(
            """SELECT season_year, games_played, points_pg, rebounds_pg,
                      assists_pg, steals_pg, blocks_pg, turnovers_pg,
                      fg_pct, fg3_pct, ft_pct
               FROM player_season_stats WHERE player_id=? ORDER BY season_year DESC""",
            (player_id,)
        ).fetchall()
    return [{"year": r[0], "gp": r[1],
             "pts": round(r[2],1), "reb": round(r[3],1), "ast": round(r[4],1),
             "stl": round(r[5],1), "blk": round(r[6],1), "tov": round(r[7],1),
             "fg": round((r[8] or 0)*100,1), "fg3": round((r[9] or 0)*100,1),
             "ft": round((r[10] or 0)*100,1)} for r in rows]
