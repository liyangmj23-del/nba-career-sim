"""
从球员属性（1-99）生成每场比赛的数据（Box Score）。
核心设计：属性决定期望值，高斯噪音引入游戏间方差。
"""
import random
import math
from dataclasses import dataclass
from config import STAT_WEEKLY_VARIANCE


@dataclass
class GameBox:
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
    player_won: bool

    @property
    def fg_pct(self) -> float:
        return self.fg_made / self.fg_attempted if self.fg_attempted else 0.0

    @property
    def fg3_pct(self) -> float:
        return self.fg3_made / self.fg3_attempted if self.fg3_attempted else 0.0

    @property
    def ft_pct(self) -> float:
        return self.ft_made / self.ft_attempted if self.ft_attempted else 0.0

    def summary(self) -> str:
        result = "W" if self.player_won else "L"
        return (
            f"{self.points}分/{self.rebounds}篮/{self.assists}助"
            f" FG {self.fg_made}/{self.fg_attempted}"
            f" [{result}]"
        )


# ── 属性归一化到 [0,1] ────────────────────────────────────────────────────────
def _norm(val: int) -> float:
    return max(0.0, min(1.0, (val - 1) / 98.0))


# ── 期望出手数（按位置，单人首发场均，5人合计约60次，全队≈85）──────────────────
_POSITION_FGA = {"PG": 13, "SG": 14, "SF": 12, "PF": 11, "C": 10}
_POSITION_3PA = {"PG": 6,  "SG": 7,  "SF": 5,  "PF": 3,  "C": 1}
_POSITION_MIN = {"PG": 33, "SG": 32, "SF": 32, "PF": 30, "C": 29}


def _noise(scale: float = STAT_WEEKLY_VARIANCE) -> float:
    return random.gauss(1.0, scale)


def _clamp_int(val: float, lo: int, hi: int) -> int:
    return max(lo, min(hi, round(val)))


def generate_game(
    attrs: dict,
    position: str = "SF",
    role: float = 1.0,       # 1.0=首发, 0.65=替补
    win_prob: float = 0.5,   # 球队获胜概率
) -> GameBox:
    """
    attrs: player_attributes 行的字段字典
    role:  1.0 首发 / 0.65 替补
    """
    pos = position.upper() if position else "SF"
    if pos not in _POSITION_FGA:
        pos = "SF"

    # ── 状态修正 ─────────────────────────────────────────────────────────────
    health_mod  = (attrs.get("health", 100) / 100) ** 0.5
    fatigue_mod = 1.0 - attrs.get("fatigue", 0) * 0.003   # 最多 -30%
    morale_mod  = 0.85 + _norm(attrs.get("morale", 75)) * 0.3   # 0.85~1.15

    state_mod = health_mod * fatigue_mod * morale_mod

    # ── 上场时间 ──────────────────────────────────────────────────────────────
    base_min = _POSITION_MIN[pos] * role * state_mod
    minutes  = max(5.0, round(base_min * _noise(0.08), 1))

    # ── 出手分配 ──────────────────────────────────────────────────────────────
    n_fga = _POSITION_FGA[pos] * role * state_mod
    n_3pa = _POSITION_3PA[pos] * role * state_mod * _norm(attrs.get("shooting_3pt", 50))
    n_3pa = min(n_3pa, n_fga * 0.7)

    # 三分出手
    fg3_attempted = _clamp_int(n_3pa * _noise(), 0, 15)
    fg3_pct_exp   = 0.25 + _norm(attrs.get("shooting_3pt", 50)) * 0.22
    fg3_made      = _clamp_int(fg3_attempted * fg3_pct_exp * _noise(0.2), 0, fg3_attempted)

    # 两分出手
    n_2pa          = max(0, _clamp_int(n_fga * _noise() - fg3_attempted, 0, 25))
    fg2_pct_exp    = 0.38 + _norm(attrs.get("shooting_2pt", 50)) * 0.27
    fg2_made       = _clamp_int(n_2pa * fg2_pct_exp * _noise(0.18), 0, n_2pa)

    fg_attempted = n_2pa + fg3_attempted
    fg_made      = fg2_made + fg3_made

    # 罚球
    iq_foul_draw  = 0.02 + _norm(attrs.get("basketball_iq", 50)) * 0.06
    ft_attempted  = _clamp_int(fg_made * iq_foul_draw * 20 * _noise(0.3), 0, 12)
    ft_pct_exp    = 0.55 + _norm(attrs.get("free_throw", 50)) * 0.40
    ft_made       = _clamp_int(ft_attempted * ft_pct_exp * _noise(0.15), 0, ft_attempted)

    # 得分
    points = fg2_made * 2 + fg3_made * 3 + ft_made

    # ── 篮板 ──────────────────────────────────────────────────────────────────
    reb_base = (
        _norm(attrs.get("strength", 50)) * 4.5 +
        _norm(attrs.get("vertical", 50)) * 3.5 +
        _norm(attrs.get("basketball_iq", 50)) * 2.0
    )
    pos_bonus = {"PG": -2, "SG": -1.5, "SF": 0, "PF": 2, "C": 4}.get(pos, 0)
    rebounds = _clamp_int((reb_base + pos_bonus) * role * state_mod * _noise(), 0, 25)

    # ── 助攻 ──────────────────────────────────────────────────────────────────
    ast_base = (
        _norm(attrs.get("passing", 50)) * 6.0 +
        _norm(attrs.get("basketball_iq", 50)) * 4.0 +
        _norm(attrs.get("ball_handling", 50)) * 2.0
    )
    pos_ast  = {"PG": 3.5, "SG": 0.5, "SF": 0, "PF": -0.5, "C": -1}.get(pos, 0)
    assists  = _clamp_int((ast_base + pos_ast) * role * state_mod * _noise(), 0, 18)

    # ── 抢断 ──────────────────────────────────────────────────────────────────
    steals = _clamp_int(
        (_norm(attrs.get("steal_tendency", 50)) * 1.5 +
         _norm(attrs.get("speed", 50)) * 0.5) * role * state_mod * _noise(),
        0, 6
    )

    # ── 盖帽 ──────────────────────────────────────────────────────────────────
    blocks = _clamp_int(
        (_norm(attrs.get("block_tendency", 50)) * 2.0 +
         _norm(attrs.get("vertical", 50)) * 0.5) * role * state_mod * _noise(),
        0, 8
    )

    # ── 失误 ──────────────────────────────────────────────────────────────────
    to_risk  = 2.0 - _norm(attrs.get("ball_handling", 50)) * 1.2
    turnovers = _clamp_int(to_risk * role * state_mod * _noise(), 0, 8)

    # ── 比赛结果 ──────────────────────────────────────────────────────────────
    player_won = random.random() < win_prob
    iq_pm      = (_norm(attrs.get("basketball_iq", 50)) - 0.5) * 10
    plus_minus = _clamp_int(
        iq_pm * role * (1 if player_won else -0.5) * _noise(0.5),
        -30, 30
    )

    return GameBox(
        minutes=minutes,
        points=points,
        rebounds=rebounds,
        assists=assists,
        steals=steals,
        blocks=blocks,
        turnovers=turnovers,
        fg_made=fg_made,
        fg_attempted=fg_attempted,
        fg3_made=fg3_made,
        fg3_attempted=fg3_attempted,
        ft_made=ft_made,
        ft_attempted=ft_attempted,
        plus_minus=plus_minus,
        player_won=player_won,
    )


def generate_game_with_overrides(targets: dict, win_prob: float = 0.5) -> GameBox:
    """
    用指定的场均目标数据生成单场比赛。
    场均接近目标值，单场有自然波动（±15%高斯噪音），多场平均收敛到目标。
    targets 格式: {"pts": 10.0, "reb": 10.0, "ast": 10.0, "stl": 10.0, "blk": 10.0}
    """
    def t(key: str, default: float = 0.0) -> int:
        target = targets.get(key, default)
        # 单场波动 ±15%，多场平均收敛到目标值
        raw = target * random.gauss(1.0, 0.15)
        return max(0, round(raw))

    pts = t("pts")
    reb = t("reb")
    ast = t("ast")
    stl = t("stl")
    blk = t("blk")
    tov = max(0, round(random.gauss(2.5, 0.8)))

    # 从得分反推出手数据（假设 48% FG，38% 3P，85% FT）
    # 先估算罚球：约占总得分 15%
    ft_pts     = round(pts * 0.15)
    field_pts  = pts - ft_pts
    fg3_made   = max(0, round(field_pts * 0.30 / 3))      # 三分贡献约 30%
    fg2_made   = max(0, round((field_pts - fg3_made * 3) / 2))
    fg_made    = fg2_made + fg3_made
    fg_att     = max(fg_made, round(fg_made / 0.48))
    fg3_att    = max(fg3_made, round(fg3_made / 0.38))
    ft_made    = ft_pts
    ft_att     = max(ft_made, round(ft_made / 0.85))

    player_won = random.random() < win_prob
    plus_minus = random.randint(2, 20) if player_won else random.randint(-15, 5)

    return GameBox(
        minutes=random.uniform(34.0, 40.0),
        points=pts,
        rebounds=reb,
        assists=ast,
        steals=stl,
        blocks=blk,
        turnovers=tov,
        fg_made=fg_made,
        fg_attempted=fg_att,
        fg3_made=fg3_made,
        fg3_attempted=fg3_att,
        ft_made=ft_made,
        ft_attempted=ft_att,
        plus_minus=plus_minus,
        player_won=player_won,
    )


def aggregate_week(games: list[GameBox]) -> dict:
    """把本周所有比赛数据汇总成本周均值（用于更新赛季统计）。"""
    if not games:
        return {}
    n = len(games)

    def avg(field: str) -> float:
        return sum(getattr(g, field) for g in games) / n

    return {
        "games_this_week": n,
        "pts": round(avg("points"), 1),
        "reb": round(avg("rebounds"), 1),
        "ast": round(avg("assists"), 1),
        "stl": round(avg("steals"), 1),
        "blk": round(avg("blocks"), 1),
        "tov": round(avg("turnovers"), 1),
        "min": round(avg("minutes"), 1),
        "fg_made":       sum(g.fg_made for g in games),
        "fg_attempted":  sum(g.fg_attempted for g in games),
        "fg3_made":      sum(g.fg3_made for g in games),
        "fg3_attempted": sum(g.fg3_attempted for g in games),
        "ft_made":       sum(g.ft_made for g in games),
        "ft_attempted":  sum(g.ft_attempted for g in games),
        "wins":          sum(1 for g in games if g.player_won),
    }
