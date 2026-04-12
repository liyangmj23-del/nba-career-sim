"""
球员卡片 Widget：属性条 + 本周数据 + 状态数值。
"""
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive


def _bar(val: int, width: int = 10, color: str = "cyan") -> str:
    """生成文本进度条，val=1-99。"""
    filled = max(0, min(width, round(val / 99 * width)))
    bar    = "\u2588" * filled + "\u2591" * (width - filled)
    return f"[{color}]{bar}[/]"


class PlayerCard(Widget):
    """显示球员属性和当前状态。通过 refresh_attrs() 更新。"""

    DEFAULT_CSS = """
    PlayerCard {
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def __init__(self, player, attrs: dict, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.attrs  = dict(attrs)

    def compose(self) -> ComposeResult:
        yield Static(id="pc-name")
        yield Static(id="pc-status")
        yield Static(id="pc-physical")
        yield Static(id="pc-offense")
        yield Static(id="pc-defense")
        yield Static(id="pc-mental")
        yield Static(id="pc-week")

    def on_mount(self) -> None:
        self._render_all()

    def refresh_attrs(self, attrs: dict, week_summary: dict | None = None) -> None:
        self.attrs = dict(attrs)
        self._render_all(week_summary)

    def _render_all(self, week_summary: dict | None = None) -> None:
        p = self.player
        a = self.attrs

        overall = a.get("overall_rating", 50)
        pos     = p.position or "?"

        # ── 标题 ──────────────────────────────────────────────────────────────
        self.query_one("#pc-name", Static).update(
            f"[bold cyan]{p.full_name}[/]  [dim]{pos}[/]  "
            f"综合 [bold white]{overall}[/]"
        )

        # ── 状态 ──────────────────────────────────────────────────────────────
        health  = a.get("health", 100)
        fatigue = a.get("fatigue", 0)
        morale  = a.get("morale", 75)

        hcol = "green" if health >= 70 else ("yellow" if health >= 40 else "red")
        fcol = "red" if fatigue >= 70 else ("yellow" if fatigue >= 40 else "green")
        mcol = "magenta" if morale >= 70 else ("yellow" if morale >= 40 else "red")

        self.query_one("#pc-status", Static).update(
            f"\n[dim]── 状态 ──────────────────[/]\n"
            f"[dim]体  力[/] {_bar(health, 10, hcol)} [{hcol}]{health:>3}[/]\n"
            f"[dim]疲  劳[/] {_bar(fatigue, 10, fcol)} [{fcol}]{fatigue:>3}[/]\n"
            f"[dim]士  气[/] {_bar(morale, 10, mcol)} [{mcol}]{morale:>3}[/]"
        )

        # ── 身体 ──────────────────────────────────────────────────────────────
        self.query_one("#pc-physical", Static).update(
            f"\n[dim]── 身体 ──────────────────[/]\n"
            f"[dim]速  度[/] {_bar(a.get('speed',50))} {a.get('speed',50):>3}\n"
            f"[dim]力  量[/] {_bar(a.get('strength',50))} {a.get('strength',50):>3}\n"
            f"[dim]弹  跳[/] {_bar(a.get('vertical',50))} {a.get('vertical',50):>3}\n"
            f"[dim]耐  力[/] {_bar(a.get('endurance',50))} {a.get('endurance',50):>3}"
        )

        # ── 进攻 ──────────────────────────────────────────────────────────────
        self.query_one("#pc-offense", Static).update(
            f"\n[dim]── 进攻 ──────────────────[/]\n"
            f"[dim]控  球[/] {_bar(a.get('ball_handling',50))} {a.get('ball_handling',50):>3}\n"
            f"[dim]两分球[/] {_bar(a.get('shooting_2pt',50))} {a.get('shooting_2pt',50):>3}\n"
            f"[dim]三分球[/] {_bar(a.get('shooting_3pt',50))} {a.get('shooting_3pt',50):>3}\n"
            f"[dim]罚  球[/] {_bar(a.get('free_throw',50))} {a.get('free_throw',50):>3}\n"
            f"[dim]传  球[/] {_bar(a.get('passing',50))} {a.get('passing',50):>3}"
        )

        # ── 防守 ──────────────────────────────────────────────────────────────
        self.query_one("#pc-defense", Static).update(
            f"\n[dim]── 防守 ──────────────────[/]\n"
            f"[dim]外线防[/] {_bar(a.get('perimeter_def',50))} {a.get('perimeter_def',50):>3}\n"
            f"[dim]内线防[/] {_bar(a.get('interior_def',50))} {a.get('interior_def',50):>3}\n"
            f"[dim]抢  断[/] {_bar(a.get('steal_tendency',50))} {a.get('steal_tendency',50):>3}\n"
            f"[dim]盖  帽[/] {_bar(a.get('block_tendency',50))} {a.get('block_tendency',50):>3}"
        )

        # ── 心理 ──────────────────────────────────────────────────────────────
        self.query_one("#pc-mental", Static).update(
            f"\n[dim]── 心理/智商 ─────────────[/]\n"
            f"[dim]篮球IQ[/] {_bar(a.get('basketball_iq',50))} {a.get('basketball_iq',50):>3}\n"
            f"[dim]关键时[/] {_bar(a.get('clutch_factor',50))} {a.get('clutch_factor',50):>3}\n"
            f"[dim]领导力[/] {_bar(a.get('leadership',50))} {a.get('leadership',50):>3}\n"
            f"[dim]勤  奋[/] {_bar(a.get('work_ethic',50))} {a.get('work_ethic',50):>3}"
        )

        # ── 本周数据 ──────────────────────────────────────────────────────────
        if week_summary:
            pts = week_summary.get("pts", 0)
            reb = week_summary.get("reb", 0)
            ast = week_summary.get("ast", 0)
            fg  = week_summary.get("fg_pct", 0)
            wins  = week_summary.get("wins", 0)
            total = week_summary.get("games_this_week", 0)
            wcol  = "green" if wins == total else ("yellow" if wins > 0 else "red")
            self.query_one("#pc-week", Static).update(
                f"\n[dim]── 本周数据 ─────────────[/]\n"
                f"[{wcol}]{wins}胜{total-wins}负[/]  "
                f"[cyan]{pts:.1f}[/]分  [white]{reb:.1f}[/]篮  [white]{ast:.1f}[/]助\n"
                f"[dim]FG[/] [bold]{fg*100:.0f}%[/]"
            )
        else:
            self.query_one("#pc-week", Static).update("")
