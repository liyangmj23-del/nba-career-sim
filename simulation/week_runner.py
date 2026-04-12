"""
run_one_week: 每次 HTTP 请求调用一次，从 DB 恢复状态推进一周。
Flask 是无状态的，无法保存 generator，所以每次重新创建 generator 并调用一次 next()。
engine 在 yield 之前已把新的 current_week 写入 DB，所以每次创建 generator
都会从上次保存的位置继续。
"""
from simulation.engine import run_season, WeekResult
from config import CURRENT_SEASON_YEAR


def run_one_week(save_id: int, season_year: int = CURRENT_SEASON_YEAR) -> WeekResult | None:
    """
    推进一周并返回 WeekResult。
    返回 None 表示赛季已结束。
    """
    gen = run_season(save_id, season_year)
    try:
        return next(gen)
    except StopIteration:
        return None


def week_result_to_dict(wr: WeekResult) -> dict:
    """WeekResult → JSON 序列化字典，供 Flask jsonify 使用。"""
    # 影响力报告
    impact_data = None
    if wr.impact:
        imp = wr.impact
        impact_data = {
            "wp_bonus":   imp["wp_bonus"],
            "label":      imp["label"],
            "combos":     imp.get("combos", []),
            "superhuman": imp.get("superhuman", []),
            "opp_effects": imp.get("opp_effects", {}),
        }

    return {
        "week":         wr.week,
        "season_year":  wr.season_year,
        "season_done":  False,
        "week_summary": wr.week_summary,
        "events": [
            {
                "key":        fe.event_def.key,
                "category":   fe.event_def.category,
                "severity":   fe.event_def.severity,
                "title":      fe.event_def.title,
                "narrative":  fe.narrative,
                "delta":      fe.attribute_delta,
                "choice_prompt": fe.event_def.choice_prompt,
            }
            for fe in wr.events
        ],
        "pending_choices": wr.pending_choices,
        "attrs":           wr.attrs_after,
        "season_stats":    wr.season_stats,
        "impact":          impact_data,
    }
