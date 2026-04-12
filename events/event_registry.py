"""
事件定义数据结构 + 全局注册表。
所有 EventDefinition 实例由各 categories/*.py 注册进来。
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Condition:
    """单条触发条件。所有条件必须同时满足事件才有资格触发。"""
    attr: str          # 检查的字段名，见 EventEngine.build_context()
    op: str            # "<" ">" "<=" ">=" "==" "!=" "in" "not_in" "between"
    value: Any         # 比较值；between 时为 (lo, hi) 元组；in 时为 list


@dataclass
class AttrEffect:
    """属性变化效果。delta 可以是 int（固定）或 (min, max) 元组（随机范围）。"""
    attr: str
    delta: int | tuple          # int 或 (min, max)
    duration_weeks: int = 0     # 0 = 永久（本赛季）；> 0 = 临时 buff/debuff


@dataclass
class ChoiceOption:
    """玩家可以选择的一个选项。"""
    key: str                        # 选项标识，如 "A" "B" "C"
    label: str                      # 按钮文字（简短）
    description: str                # 选项说明（后果预告）
    attr_effects: list[AttrEffect] = field(default_factory=list)
    narrative: str = ""             # 选择后追加的叙事文字
    chains_to: str = ""             # 选择后触发的连锁事件 key
    impact_scope: str = "week"      # "week" / "month" / "season" / "career"


@dataclass
class EventDefinition:
    key: str                                   # 唯一标识，如 "injury.ankle.mild"
    category: str                              # 大类
    title: str                                 # 短标题（UI 显示）
    narratives: list[str]                      # 叙事文本变体（随机选一条）
    base_prob: float                           # 每周基础触发概率 [0, 1]
    severity: str = "normal"                   # minor / normal / major / legendary
    conditions: list[Condition] = field(default_factory=list)
    attr_effects: list[AttrEffect] = field(default_factory=list)
    chains_to: list[str] = field(default_factory=list)   # 触发后接的事件 key 列表
    chain_delay: int = 0                       # 连锁事件几周后触发
    cooldown_weeks: int = 0                    # 触发后冷却周数
    one_time: bool = False                     # True = 本次存档只触发一次
    career_year_min: int = 1
    career_year_max: int = 25
    monthly_only: bool = False                 # True = 只在第 4/8/12/… 周触发
    # ── 玩家选择 ──────────────────────────────────────────────────────────────
    choice_prompt: str = ""                    # 非空 = 需要玩家做选择
    choices: list[ChoiceOption] = field(default_factory=list)  # 选项列表


# ── 全局注册表 ────────────────────────────────────────────────────────────────
_REGISTRY: dict[str, EventDefinition] = {}


def register(ev: EventDefinition) -> EventDefinition:
    _REGISTRY[ev.key] = ev
    return ev


def get_event(key: str) -> EventDefinition | None:
    return _REGISTRY.get(key)


def all_events() -> list[EventDefinition]:
    return list(_REGISTRY.values())


def events_by_category(cat: str) -> list[EventDefinition]:
    return [e for e in _REGISTRY.values() if e.category == cat]
