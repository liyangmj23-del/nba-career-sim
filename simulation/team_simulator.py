"""
球队实力评估与对手生成。
简化版：用球队名单的头八名球员综合评分估算球队整体实力，
再用 Sigmoid 函数将实力差距转化为获胜概率。
"""
import math
import random
from database.connection import db


def _team_rating(team_id: int, season_year: int) -> float:
    """取球队前8名球员的 overall_rating 平均值作为球队评级。"""
    with db() as conn:
        rows = conn.execute(
            """
            SELECT pa.overall_rating
            FROM player_attributes pa
            JOIN players p ON pa.player_id = p.player_id
            WHERE p.current_team_id = ? AND pa.season_year = ?
              AND p.is_active = 1 AND pa.health > 20
            ORDER BY pa.overall_rating DESC
            LIMIT 8
            """,
            (team_id, season_year),
        ).fetchall()
    if not rows:
        return 55.0   # 默认中等队伍
    return sum(r[0] for r in rows) / len(rows)


def win_probability(my_rating: float, opp_rating: float) -> float:
    """Sigmoid: 评级差距 -> 获胜概率 [0.2, 0.8]"""
    diff = (my_rating - opp_rating) / 10.0
    raw  = 1.0 / (1.0 + math.exp(-diff))
    # 限制在 0.20~0.80 之间，保留爆冷可能
    return 0.20 + raw * 0.60


# 30支球队 id（nba_api 标准 id）
_ALL_TEAM_IDS = [
    1610612737, 1610612738, 1610612739, 1610612740, 1610612741,
    1610612742, 1610612743, 1610612744, 1610612745, 1610612746,
    1610612747, 1610612748, 1610612749, 1610612750, 1610612751,
    1610612752, 1610612753, 1610612754, 1610612755, 1610612756,
    1610612757, 1610612758, 1610612759, 1610612760, 1610612761,
    1610612762, 1610612763, 1610612764, 1610612765, 1610612766,
]


def get_opponent(my_team_id: int | None) -> int:
    """随机返回一个对手 team_id（排除自己）。my_team_id 为 None 时从全部球队中选。"""
    others = [t for t in _ALL_TEAM_IDS if t != my_team_id]
    return random.choice(others)


def games_this_week() -> int:
    """本周比赛场数：2-4 场，用加权随机模拟 NBA 赛历。"""
    return random.choices([2, 3, 4], weights=[2, 5, 3])[0]
