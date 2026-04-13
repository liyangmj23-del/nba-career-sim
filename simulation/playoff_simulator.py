"""
季后赛模拟器（简化版）。
基于球队投影胜率 + 球员影响力，逐轮模拟季后赛结果。
每轮产生叙事和结果。
"""
import random
from database.connection import db as getdb

# 季后赛对阵名称
ROUND_NAMES = ["首轮", "次轮（分区半决赛）", "分区决赛", "NBA总决赛"]
ROUND_SHORT  = ["首轮", "次轮", "分区决", "总决赛"]

# 种子差对胜率的影响（种子越低越强）
SEED_ADVANTAGE = {
    (1, 8): 0.18, (2, 7): 0.15, (3, 6): 0.10, (4, 5): 0.05,
    (1, 4): 0.12, (2, 3): 0.06, (1, 2): 0.06,
    (1, 1): 0.0,  # 东西冠军相遇，均等
}


def get_seed_advantage(my_seed: int, opp_seed: int) -> float:
    key = (min(my_seed, opp_seed), max(my_seed, opp_seed))
    advantage = SEED_ADVANTAGE.get(key, 0.0)
    return advantage if my_seed < opp_seed else -advantage


def simulate_series(win_prob: float) -> tuple[int, int]:
    """模拟最多7场的系列赛，返回(我方胜场, 对方胜场)。"""
    my_wins = opp_wins = 0
    while my_wins < 4 and opp_wins < 4:
        if random.random() < win_prob:
            my_wins += 1
        else:
            opp_wins += 1
    return my_wins, opp_wins


def get_round_opponent_name(round_num: int, my_seed: int) -> str:
    """根据轮次和种子返回对手描述。"""
    opponents = {
        0: {1:"8号种子",2:"7号种子",3:"6号种子",4:"5号种子",
            5:"4号种子",6:"3号种子",7:"2号种子",8:"1号种子"},
        1: {1:"4号种子获胜方",2:"3号种子获胜方",
            3:"2号种子获胜方",4:"1号种子获胜方"},
        2: "分区另一侧的强队",
        3: "另一个联盟的冠军",
    }
    if round_num <= 1:
        opp_map = opponents[round_num]
        return opp_map.get(my_seed, "对手")
    return opponents.get(round_num, "强劲对手")


def simulate_playoffs(
    save_id: int,
    player_id: int,
    season_year: int,
    base_wp: float,
    player_impact: dict,
) -> dict:
    """
    模拟完整季后赛。
    base_wp: 常规赛推算的单场胜率
    player_impact: 球员影响力字典

    返回：{
        "reached_round": int (0=首轮出局前, 1=首轮, 2=次轮, 3=分区决, 4=总冠军)
        "champion": bool
        "rounds": list of round results
        "narrative": str
        "key_moment": str
    }
    """
    # 随机分配种子（1-8）
    my_seed  = random.randint(1, 5)  # 略偏向较好种子
    rounds   = []
    current_wp = min(0.92, max(0.08, base_wp + player_impact.get("wp_bonus", 0)))

    for round_num in range(4):
        opp_seed = _get_opponent_seed(round_num, my_seed)
        seed_adv = get_seed_advantage(my_seed, opp_seed)
        round_wp = min(0.92, max(0.08, current_wp + seed_adv))

        my_wins, opp_wins = simulate_series(round_wp)
        won = my_wins >= 4
        total_games = my_wins + opp_wins
        is_sweep   = won and total_games == 4
        is_seven   = total_games == 7

        round_result = {
            "round_num":   round_num,
            "round_name":  ROUND_NAMES[round_num],
            "my_seed":     my_seed,
            "opp_seed":    opp_seed,
            "opp_name":    get_round_opponent_name(round_num, my_seed),
            "my_wins":     my_wins,
            "opp_wins":    opp_wins,
            "won":         won,
            "is_sweep":    is_sweep,
            "is_seven":    is_seven,
            "round_wp":    round(round_wp, 3),
        }
        round_result["narrative"] = _make_round_narrative(round_result, round_num)
        rounds.append(round_result)

        if not won:
            # 出局
            return {
                "reached_round": round_num,
                "champion":      False,
                "rounds":        rounds,
                "narrative":     _make_elimination_narrative(round_num, my_wins, opp_wins),
                "key_moment":    _pick_key_moment(rounds, False),
            }

        # 晋级：下一轮胜率略微提升（球队磨合）
        current_wp = min(0.90, current_wp + 0.02)

    # 总冠军！
    return {
        "reached_round": 4,
        "champion":      True,
        "rounds":        rounds,
        "narrative":     _make_champion_narrative(rounds),
        "key_moment":    _pick_key_moment(rounds, True),
    }


def _get_opponent_seed(round_num: int, my_seed: int) -> int:
    """根据轮次和己方种子推算对手种子。"""
    if round_num == 0:
        return 9 - my_seed  # 1vs8, 2vs7...
    elif round_num == 1:
        return random.choice([seed for seed in range(1, 9) if seed != my_seed])
    elif round_num == 2:
        return random.randint(1, 4)
    else:
        return random.randint(1, 4)  # 另一联盟冠军


def _make_round_narrative(r: dict, round_num: int) -> str:
    rn = r["round_name"]
    if r["won"]:
        if r["is_sweep"]:
            return f"{rn}横扫对手（{r['my_wins']}-{r['opp_wins']}），以统治者的姿态晋级。没有人觉得这是意外。"
        elif r["is_seven"]:
            return f"{rn}打满7场（{r['my_wins']}-{r['opp_wins']}）。每一场都是悬念，每一场你都撑了下来。这种磨砺会成为你的一部分。"
        else:
            return f"{rn}以{r['my_wins']}-{r['opp_wins']}晋级。节奏控制得很好，没有让系列赛走向危险地带。"
    else:
        if r["is_seven"]:
            return f"{rn}打满7场后惜败（{r['my_wins']}-{r['opp_wins']}）。最后一场你给了所有能给的，但还不够。"
        else:
            return f"{rn}以{r['my_wins']}-{r['opp_wins']}落败出局。系列赛里有几场你本可以赢，但没有。"


def _make_elimination_narrative(round_num: int, my_wins: int, opp_wins: int) -> str:
    stage = ["首轮", "次轮", "分区决赛", "总决赛"][round_num]
    texts = [
        f"你们在{stage}（{my_wins}-{opp_wins}）止步。更衣室里很安静，没有人大声说话。你换衣服，最后看了一眼球馆的灯光，走出去了。赛季就这样结束了。",
        f"{stage}结束，{my_wins}-{opp_wins}出局。你在场上做到了你能做的一切，但对手也是。有时候这就够了，有时候这不够。今天属于后者。",
        f"最后的哨声响起，{my_wins}-{opp_wins}。你站在场上，感受着这种输掉的重量。没有话可以让它变轻，只能带着它走出去，等明年。",
    ]
    return random.choice(texts)


def _make_champion_narrative(rounds: list) -> str:
    g7_rounds = [r for r in rounds if r["is_seven"] and r["won"]]
    sweeps    = [r for r in rounds if r["is_sweep"]]

    if g7_rounds:
        return ("总决赛的最后一秒，哨声响起，你们赢了。你站在场上，脑子里一片空白。"
                "队友把你围起来，有人在哭，有人在喊，有人只是把手放在你肩上。"
                "你们打了很长的路才到这里，每一场G7，每一次危机，都在这一刻有了答案。"
                "这是你的冠军。它是真实的。")
    elif sweeps and sweeps[-1]["round_name"] == "NBA总决赛":
        return ("横扫对手，总冠军。数字是4-0，但这不只是数字。"
                "这是整个赛季积累的结果，是所有人看着你说'他不可能赢'之后你交出的答案。"
                "领奖台上，你举起冠军奖杯，灯光打下来，那一刻什么都够了。")
    else:
        return ("终场哨响的时候，你还站在场上。"
                "你们赢了。你们是冠军了。"
                "在那一刻，之前所有的问题都有了答案，所有的代价都变得值得了。"
                "你深呼了一口气，感觉到那个东西真实地落在了手里。")


def _pick_key_moment(rounds: list, champion: bool) -> str:
    if champion:
        g7 = next((r for r in rounds if r["is_seven"] and r["won"]), None)
        if g7:
            return f"在{g7['round_name']}G7中逆境求生，这是整个季后赛之路的转折点"
        return "以近乎完美的状态走完整个季后赛"
    else:
        lost = next((r for r in reversed(rounds) if not r["won"]), None)
        if lost and lost["is_seven"]:
            return f"在{lost['round_name']}G7中功亏一篑，差一点就走更远"
        return "季后赛积累了宝贵的经验"
