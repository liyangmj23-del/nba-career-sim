"""
年龄曲线：每个赛季结束时计算属性的成长/衰退。
工作热情（work_ethic）影响衰退速率。
"""
import random
from config import (
    AGE_PHYSICAL_PEAK, AGE_SKILL_PEAK, AGE_MENTAL_PEAK,
    DECAY_PHYSICAL, DECAY_SKILL, DECAY_MENTAL,
    ATTR_MIN, ATTR_MAX,
)

# 属性分组
_PHYSICAL_ATTRS = ["speed", "strength", "vertical", "endurance"]
_SKILL_ATTRS    = [
    "ball_handling", "shooting_2pt", "shooting_3pt", "free_throw",
    "passing", "post_moves", "perimeter_def", "interior_def",
    "steal_tendency", "block_tendency",
]
_MENTAL_ATTRS   = [
    "basketball_iq", "clutch_factor", "leadership", "work_ethic", "media_handling",
]


def _clamp(val: int) -> int:
    return max(ATTR_MIN, min(ATTR_MAX, val))


def year_end_delta(attrs: dict, current_age: int, career_year: int) -> dict:
    """
    计算赛季结束后各属性的变化量（delta），返回 {attr: delta} 字典。
    调用方负责把 delta 加到当前属性并写入 DB。
    """
    work = attrs.get("work_ethic", 60)
    work_factor = 0.6 + (work - 1) / 98 * 0.8   # 0.6 ~ 1.4

    delta = {}

    # ── 身体属性 ──────────────────────────────────────────────────────────────
    for attr in _PHYSICAL_ATTRS:
        val = attrs.get(attr, 50)
        if current_age < AGE_PHYSICAL_PEAK:
            # 成长期：年轻球员每年 +0.5~2
            growth = random.uniform(0.5, 2.0) * work_factor
            delta[attr] = _clamp(round(val + growth)) - val
        else:
            years_past_peak = current_age - AGE_PHYSICAL_PEAK
            decay = DECAY_PHYSICAL * years_past_peak / work_factor
            # 随机性：±30%
            decay *= random.uniform(0.7, 1.3)
            delta[attr] = -_clamp(round(decay))

    # ── 技术属性 ──────────────────────────────────────────────────────────────
    for attr in _SKILL_ATTRS:
        val = attrs.get(attr, 50)
        if current_age < AGE_SKILL_PEAK:
            growth = random.uniform(0.3, 1.5) * work_factor
            delta[attr] = _clamp(round(val + growth)) - val
        else:
            years_past = current_age - AGE_SKILL_PEAK
            decay = DECAY_SKILL * years_past / work_factor
            decay *= random.uniform(0.7, 1.3)
            delta[attr] = -max(0, round(decay))

    # ── 心理属性 ──────────────────────────────────────────────────────────────
    for attr in _MENTAL_ATTRS:
        val = attrs.get(attr, 50)
        if career_year <= 8:
            # 前8年持续成长
            growth = random.uniform(0.2, 1.2) * work_factor
            delta[attr] = _clamp(round(val + growth)) - val
        elif current_age < AGE_MENTAL_PEAK:
            delta[attr] = 0
        else:
            years_past = current_age - AGE_MENTAL_PEAK
            decay = DECAY_MENTAL * years_past
            delta[attr] = -max(0, round(decay))

    return delta


def apply_delta(attrs: dict, delta: dict) -> dict:
    """把 delta 应用到 attrs，返回新的 attrs 字典。"""
    new_attrs = dict(attrs)
    for k, d in delta.items():
        if k in new_attrs:
            new_attrs[k] = _clamp(new_attrs[k] + d)
    # 重算综合评分
    skill_keys = _PHYSICAL_ATTRS + _SKILL_ATTRS + _MENTAL_ATTRS
    new_attrs["overall_rating"] = _clamp(
        round(sum(new_attrs.get(k, 50) for k in skill_keys) / len(skill_keys))
    )
    return new_attrs


def compute_overall(attrs: dict) -> int:
    skill_keys = _PHYSICAL_ATTRS + _SKILL_ATTRS + _MENTAL_ATTRS
    return _clamp(round(sum(attrs.get(k, 50) for k in skill_keys) / len(skill_keys)))
