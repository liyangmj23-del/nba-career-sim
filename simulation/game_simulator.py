"""
全队 Box Score 生成器。
给定主队/客队 team_id，生成一场完整比赛的双方所有球员数据。
用于「比赛数据看板」的展示，不写入 DB。
"""
import random
from dataclasses import dataclass
from database.connection import db
from simulation.stat_generator import generate_game


@dataclass
class PlayerBoxRow:
    name: str
    position: str
    is_starter: bool
    is_hero: bool       # 是否是我们的主控球员
    minutes: float
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fg_made: int
    fg_attempted: int
    fg3_made: int
    fg3_attempted: int
    ft_made: int
    ft_attempted: int
    plus_minus: int

    @property
    def fg_pct(self) -> str:
        return f"{self.fg_made/self.fg_attempted*100:.0f}%" if self.fg_attempted else "-"

    @property
    def fg3_pct(self) -> str:
        return f"{self.fg3_made/self.fg3_attempted*100:.0f}%" if self.fg3_attempted else "-"

    @property
    def ft_pct(self) -> str:
        return f"{self.ft_made/self.ft_attempted*100:.0f}%" if self.ft_attempted else "-"


@dataclass
class TeamBoxScore:
    team_name: str
    abbreviation: str
    total_points: int
    won: bool
    players: list[PlayerBoxRow]


@dataclass
class FullGameBoxScore:
    home: TeamBoxScore
    away: TeamBoxScore
    season_year: int
    game_week: int
    game_number: int


_POS_NORMALIZE = {
    # nba_api 返回的全拼 → 缩写
    "GUARD": "G", "FORWARD": "F", "CENTER": "C",
    "POINT GUARD": "PG", "SHOOTING GUARD": "SG",
    "SMALL FORWARD": "SF", "POWER FORWARD": "PF",
    "G": "G", "F": "F", "FC": "PF", "GF": "SF",
    "PG": "PG", "SG": "SG", "SF": "SF", "PF": "PF",
}


def _normalize_pos(pos: str | None) -> str:
    if not pos:
        return "-"
    return _POS_NORMALIZE.get(pos.upper().strip(), pos[:3])


def _get_team_info(team_id: int) -> tuple[str, str]:
    """返回 (full_name, abbreviation)。team_id 为 None/0 时随机返回一支真实球队。"""
    if team_id:
        with db() as conn:
            row = conn.execute(
                "SELECT full_name, abbreviation FROM teams WHERE team_id=?",
                (team_id,)
            ).fetchone()
        if row:
            return row[0], row[1]
    # 找不到时随机一支真实球队
    with db() as conn:
        row = conn.execute(
            "SELECT full_name, abbreviation FROM teams WHERE is_active=1 ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
    return (row[0], row[1]) if row else ("Unknown Team", "UNK")


_ROSTER_COLS = [
    "player_id","full_name","position","overall_rating",
    "speed","strength","vertical","endurance",
    "ball_handling","shooting_2pt","shooting_3pt","free_throw",
    "passing","post_moves","perimeter_def","interior_def",
    "steal_tendency","block_tendency","basketball_iq",
    "clutch_factor","leadership","work_ethic","media_handling",
    "health","morale","fatigue",
]

_ROSTER_SELECT = """
    SELECT p.player_id, p.full_name, p.position,
           pa.overall_rating,
           pa.speed, pa.strength, pa.vertical, pa.endurance,
           pa.ball_handling, pa.shooting_2pt, pa.shooting_3pt,
           pa.free_throw, pa.passing, pa.post_moves,
           pa.perimeter_def, pa.interior_def,
           pa.steal_tendency, pa.block_tendency,
           pa.basketball_iq, pa.clutch_factor, pa.leadership,
           pa.work_ethic, pa.media_handling,
           pa.health, pa.morale, pa.fatigue
    FROM players p
    JOIN player_attributes pa
      ON p.player_id = pa.player_id AND pa.season_year = ?
    WHERE p.is_active = 1 AND p.player_id > 0
"""
# 自定义球员（player_id < 0）单独查询，只用于 hero 球员匹配
_CUSTOM_SELECT = """
    SELECT p.player_id, p.full_name, p.position,
           pa.overall_rating,
           pa.speed, pa.strength, pa.vertical, pa.endurance,
           pa.ball_handling, pa.shooting_2pt, pa.shooting_3pt,
           pa.free_throw, pa.passing, pa.post_moves,
           pa.perimeter_def, pa.interior_def,
           pa.steal_tendency, pa.block_tendency,
           pa.basketball_iq, pa.clutch_factor, pa.leadership,
           pa.work_ethic, pa.media_handling,
           pa.health, pa.morale, pa.fatigue
    FROM players p
    JOIN player_attributes pa
      ON p.player_id = pa.player_id AND pa.season_year = ?
    WHERE p.player_id < 0 AND p.is_active = 1
"""


def _get_team_roster(team_id: int, season_year: int,
                     hero_player_id: int | None = None) -> list[dict]:
    """
    取球队名单及属性。
    规则：
    1. 只取真实NBA球员（player_id > 0）
    2. 若不足8人（快速种子），从全联盟随机补充真实球员
    3. hero_player_id 如果是自定义球员（<0），单独处理，不混入常规名单
    """
    with db() as conn:
        # 1. 真实球员按球队查询
        rows = conn.execute(
            _ROSTER_SELECT + " AND p.current_team_id = ?"
            " ORDER BY pa.overall_rating DESC LIMIT 12",
            (season_year, team_id),
        ).fetchall()

        # 2. 若不足8人，从全联盟随机补充真实球员（不包括已在名单的）
        if len(rows) < 8:
            existing_ids = tuple(r[0] for r in rows) or (0,)
            placeholders = ",".join("?" * len(existing_ids))
            extra = conn.execute(
                _ROSTER_SELECT +
                f" AND p.player_id NOT IN ({placeholders})"
                " ORDER BY RANDOM() LIMIT ?",
                (season_year, *existing_ids, 12 - len(rows)),
            ).fetchall()
            rows = list(rows) + list(extra)

    result = [dict(zip(_ROSTER_COLS, r)) for r in rows]

    # 3. 如果 hero 是自定义球员（<0），单独查询并加到名单最前面
    if hero_player_id and hero_player_id < 0:
        with db() as conn:
            hr = conn.execute(
                _CUSTOM_SELECT + " AND p.player_id = ?",
                (season_year, hero_player_id)
            ).fetchone()
        if hr:
            hero_dict = dict(zip(_ROSTER_COLS, hr))
            # 移除名单中可能存在的同名旧记录，hero只出现一次
            result = [r for r in result if r["player_id"] != hero_player_id]
            result.insert(0, hero_dict)

    return result


def _generate_team_box(
    team_id: int,
    season_year: int,
    team_won: bool,
    target_pts: int,
    hero_player_id: int | None = None,
    hero_box: "GameBox | None" = None,
) -> TeamBoxScore:
    """生成一支球队的 Box Score。"""
    team_name, abbr = _get_team_info(team_id)
    # 传入 hero_player_id，让 _get_team_roster 单独处理自定义球员，不污染真实名单
    roster = _get_team_roster(team_id, season_year, hero_player_id)

    # 按位置顺序分配默认位置（球员 DB 中 position 可能为 None）
    _POS_ORDER = ["PG","SG","SF","PF","C","SG","SF","PF","C","PG","SF","SG","PF"]

    rows: list[PlayerBoxRow] = []
    generated_pts = 0

    # 如果有主控球员的实际数据，直接构建 hero 行
    # 先从 roster 里找名字，找不到再直接从 DB 查（自定义球员/自由球员均适用）
    if hero_box and hero_player_id:
        hero_name = None
        hero_pos  = None
        for r in roster:
            if r["player_id"] == hero_player_id:
                hero_name = r["full_name"]
                hero_pos  = _normalize_pos(r.get("position"))
                break
        if not hero_name:
            # roster 里没有（自由球员/随机球队）→ 直接查 DB
            with db() as conn:
                hr = conn.execute(
                    "SELECT full_name, position FROM players WHERE player_id=?",
                    (hero_player_id,)
                ).fetchone()
            if hr:
                hero_name = hr[0]
                hero_pos  = hr[1]
        if hero_name:
            rows.append(PlayerBoxRow(
                name         = f"★ {hero_name}",
                position     = hero_pos or "SF",
                is_starter   = True,
                is_hero      = True,
                minutes      = hero_box.minutes,
                points       = hero_box.points,
                rebounds     = hero_box.rebounds,
                assists      = hero_box.assists,
                steals       = hero_box.steals,
                blocks       = hero_box.blocks,
                turnovers    = hero_box.turnovers,
                fg_made      = hero_box.fg_made,
                fg_attempted = hero_box.fg_attempted,
                fg3_made     = hero_box.fg3_made,
                fg3_attempted= hero_box.fg3_attempted,
                ft_made      = hero_box.ft_made,
                ft_attempted = hero_box.ft_attempted,
                plus_minus   = hero_box.plus_minus,
            ))
            generated_pts += hero_box.points

    # 生成其他球员数据
    remaining_slots = min(12, len(roster))
    slot_counter = 0  # 用于分配默认位置
    for i, r in enumerate(roster[:remaining_slots]):
        if r["player_id"] == hero_player_id:
            continue   # 已处理
        is_starter = i < 5
        role = 1.0 if is_starter else 0.32  # 替补球员出手约为首发的1/3
        attrs = {k: r[k] for k in r if k not in ("player_id","full_name","position","overall_rating")}
        box = generate_game(
            attrs=attrs,
            position=r.get("position") or "SF",
            role=role,
            win_prob=0.7 if team_won else 0.3,
        )
        pos = _normalize_pos(r.get("position")) or _POS_ORDER[slot_counter % len(_POS_ORDER)]
        slot_counter += 1
        rows.append(PlayerBoxRow(
            name         = r["full_name"],
            position     = pos,
            is_starter   = is_starter,
            is_hero      = False,
            minutes      = box.minutes,
            points       = box.points,
            rebounds     = box.rebounds,
            assists      = box.assists,
            steals       = box.steals,
            blocks       = box.blocks,
            turnovers    = box.turnovers,
            fg_made      = box.fg_made,
            fg_attempted = box.fg_attempted,
            fg3_made     = box.fg3_made,
            fg3_attempted= box.fg3_attempted,
            ft_made      = box.ft_made,
            ft_attempted = box.ft_attempted,
            plus_minus   = box.plus_minus,
        ))
        generated_pts += box.points

    # 若球员数仍不足（极端情况），用符合NBA真实节奏的通用数据填充
    if len(rows) < 10:
        positions = ["PG","SG","SF","PF","C","SG","SF","PF","C","PG"]
        for slot in range(len(rows), 10):
            is_starter = slot < 5
            # 首发：15-26分，替补：6-16分（符合NBA均值）
            if is_starter:
                pts = random.randint(12, 26)
                fga = random.randint(10, 18)
                min_ = random.uniform(28, 36)
                reb  = random.randint(3, 11)
                ast  = random.randint(1, 8)
            else:
                pts = random.randint(6, 16)
                fga = random.randint(5, 11)
                min_ = random.uniform(12, 24)
                reb  = random.randint(1, 6)
                ast  = random.randint(0, 4)
            fg_made = round(fga * random.uniform(0.42, 0.54))
            fg3a    = random.randint(1, 5) if is_starter else random.randint(0, 3)
            fg3m    = round(fg3a * random.uniform(0.33, 0.42))
            # 从得分倒推罚球
            field_pts = fg_made * 2 + fg3m
            ft_pts    = max(0, pts - field_pts)
            fta       = max(ft_pts, round(ft_pts / 0.82))
            ftm       = ft_pts
            pm = random.randint(2, 12) if team_won else random.randint(-12, 3)
            rows.append(PlayerBoxRow(
                name=f"球员 {slot+1}", position=positions[slot % 5],
                is_starter=is_starter, is_hero=False,
                minutes=min_, points=pts,
                rebounds=reb, assists=ast,
                steals=random.randint(0, 2), blocks=random.randint(0, 2),
                turnovers=random.randint(0, 4),
                fg_made=fg_made, fg_attempted=fga,
                fg3_made=fg3m, fg3_attempted=fg3a,
                ft_made=ftm, ft_attempted=fta,
                plus_minus=pm,
            ))
            generated_pts += pts

    rows.sort(key=lambda r: (not r.is_starter, -r.points))

    # ── 缩放：确保全队得分在真实 NBA 范围内（100-122分）────────────────────────
    total = sum(r.points for r in rows)
    target = random.randint(100, 122)
    if total > 0 and abs(total - target) > 8:
        scale = target / total
        for p in rows:
            p.points       = max(0, round(p.points * scale))
            # 先缩放 attempted，再确保 made <= attempted
            p.fg_attempted = max(1, round(p.fg_attempted * scale))
            p.fg_made      = max(0, min(p.fg_attempted, round(p.fg_made * scale)))
            p.fg3_attempted= max(0, round(p.fg3_attempted * scale))
            p.fg3_made     = max(0, min(p.fg3_attempted, round(p.fg3_made * scale)))
            p.ft_attempted = max(0, round(p.ft_attempted * scale))
            p.ft_made      = max(0, min(p.ft_attempted, round(p.ft_made * scale)))

    return TeamBoxScore(
        team_name    = team_name,
        abbreviation = abbr,
        total_points = sum(r.points for r in rows),
        won          = team_won,
        players      = rows,
    )


def generate_full_box_score(
    my_team_id: int,
    opp_team_id: int,
    season_year: int,
    game_week: int,
    game_number: int,
    player_id: int,
    hero_box,        # GameBox from engine
    my_team_won: bool,
    opp_suppression: dict | None = None,  # 来自 player_impact 的对手压制效果
) -> FullGameBoxScore:
    """生成完整双方 Box Score，对手数据根据球员防守表现受到压制。"""
    home_is_mine = random.random() > 0.5
    sup = opp_suppression or {}

    my_team = _generate_team_box(
        team_id        = my_team_id,
        season_year    = season_year,
        team_won       = my_team_won,
        target_pts     = round(110 + sup.get("team_pts_boost", 0)),
        hero_player_id = player_id,
        hero_box       = hero_box,
    )
    opp_team = _generate_team_box(
        team_id     = opp_team_id,
        season_year = season_year,
        team_won    = not my_team_won,
        target_pts  = max(80, round(105 - sup.get("opp_pts_reduction", 0))),
    )

    # 把防守压制应用到对手每位球员的数据上
    _apply_suppression_to_team(opp_team, sup)

    return FullGameBoxScore(
        home        = my_team if home_is_mine else opp_team,
        away        = opp_team if home_is_mine else my_team,
        season_year = season_year,
        game_week   = game_week,
        game_number = game_number,
    )


def _apply_suppression_to_team(team: TeamBoxScore, sup: dict) -> None:
    """
    把防守压制效果分摊到对手每位球员数据上（近似模拟）。
    例：我方10盖帽 → 对方内线球员得分下降
    """
    if not sup or not team.players:
        return
    import math

    pts_cut    = sup.get("opp_pts_reduction", 0)    # 对方总得分减少
    tov_add    = sup.get("opp_tov_increase", 0)     # 对方总失误增加
    ast_cut    = sup.get("opp_ast_reduction", 0)    # 对方助攻减少
    fg_penalty = sup.get("opp_fg_pct_penalty", 0)  # 命中率下降

    starters = [p for p in team.players if p.is_starter]
    n = max(1, len(starters))

    for p in starters:
        # 得分压制
        cut = round(pts_cut / n)
        p.points    = max(0, p.points - cut)
        p.fg_made   = max(0, p.fg_made - cut // 2)

        # 失误增加（随机分配给控球手）
        if p.position in ("PG", "SG"):
            p.turnovers = min(10, p.turnovers + round(tov_add / max(1, len([x for x in starters if x.position in ("PG","SG")]))))

        # 助攻减少
        if p.assists > 0:
            p.assists = max(0, p.assists - round(ast_cut / n))

        # 命中率调整（通过增加出手数来反映）
        if fg_penalty > 0 and p.fg_attempted > 0:
            extra_misses = round(p.fg_attempted * fg_penalty * 100 / 10)
            p.fg_attempted = p.fg_attempted + extra_misses

    team.total_points = sum(p.points for p in team.players)
