"""
事件叙事滚动面板。
把 FiredEvent 渲染成带颜色、带标题的叙事块。
"""
from textual.widgets import RichLog
from textual.widget import Widget
from rich.text import Text

SEVERITY_COLOR = {
    "minor":     "dim white",
    "normal":    "white",
    "major":     "bold yellow",
    "legendary": "bold gold1",
}

SEVERITY_BORDER = {
    "minor":     "dim",
    "normal":    "blue",
    "major":     "yellow",
    "legendary": "gold1",
}

CATEGORY_LABEL = {
    "game_performance":  "比赛",
    "injury":            "伤病",
    "personal_life":     "个人",
    "team_chemistry":    "球队",
    "career_milestones": "里程碑",
    "off_court":         "场外",
}

CATEGORY_COLOR = {
    "game_performance":  "cyan",
    "injury":            "red",
    "personal_life":     "magenta",
    "team_chemistry":    "blue",
    "career_milestones": "gold1",
    "off_court":         "green",
}


class EventFeed(RichLog):
    """可滚动事件叙事面板，继承自 RichLog。"""

    DEFAULT_CSS = """
    EventFeed {
        background: #080810;
        padding: 0 1;
        border: none;
        scrollbar-color: #1e2040 #080810;
    }
    """

    def push_week_divider(self, week: int, season_year: int) -> None:
        self.write(
            f"\n[dim]{'─'*60}[/]\n"
            f"[bold dim]  第 {week} 周  ·  "
            f"{season_year-1}-{str(season_year)[2:]} 赛季[/]\n"
        )

    def push_games(self, week_summary: dict) -> None:
        wins  = week_summary.get("wins", 0)
        total = week_summary.get("games_this_week", 0)
        pts   = week_summary.get("pts", 0)
        reb   = week_summary.get("reb", 0)
        ast   = week_summary.get("ast", 0)
        stl   = week_summary.get("stl", 0)
        blk   = week_summary.get("blk", 0)
        tov   = week_summary.get("tov", 0)
        # 命中率从本周投篮总数计算（不从 pct 字段，因为 week_summary 没有）
        fg_m  = week_summary.get("fg_made", 0)
        fg_a  = week_summary.get("fg_attempted", 0)
        fg3_m = week_summary.get("fg3_made", 0)
        fg3_a = week_summary.get("fg3_attempted", 0)
        ft_m  = week_summary.get("ft_made", 0)
        ft_a  = week_summary.get("ft_attempted", 0)
        fg_pct  = fg_m  / fg_a  * 100 if fg_a  else 0
        fg3_pct = fg3_m / fg3_a * 100 if fg3_a else 0
        ft_pct  = ft_m  / ft_a  * 100 if ft_a  else 0

        wcol = "green" if wins == total else ("yellow" if wins > 0 else "red")
        # 第一行：胜负 + 核心数据
        self.write(
            f"  [{wcol}]{wins}胜{total-wins}负[/]  "
            f"[cyan]{pts:.1f}[/]分  "
            f"[white]{reb:.1f}[/]篮  "
            f"[white]{ast:.1f}[/]助  "
            f"[green]{stl:.1f}[/]断  "
            f"[yellow]{blk:.1f}[/]帽  "
            f"[dim]{tov:.1f}失[/]"
        )
        # 第二行：命中率
        self.write(
            f"  [dim]FG [/][bold]{fg_pct:.1f}%[/][dim]({fg_m}/{fg_a})  "
            f"3P [/][bold]{fg3_pct:.1f}%[/][dim]({fg3_m}/{fg3_a})  "
            f"FT [/][bold]{ft_pct:.1f}%[/][dim]({ft_m}/{ft_a})[/]\n"
        )

    def push_no_event(self) -> None:
        self.write("[dim]  本周平静，无特殊事件。[/]\n")

    def push_event(self, fe) -> None:
        ev    = fe.event_def
        scol  = SEVERITY_COLOR.get(ev.severity, "white")
        ccol  = CATEGORY_COLOR.get(ev.category, "white")
        clabel = CATEGORY_LABEL.get(ev.category, ev.category)

        # 标题行
        self.write(
            f"\n  [{ccol}]【{clabel}】[/] [{scol}]{ev.title}[/]"
        )

        # 叙事正文
        for line in fe.narrative.strip().split("\n"):
            stripped = line.strip()
            if stripped:
                self.write(f"  [dim]{stripped}[/]")
            else:
                self.write("")

        # 属性变化摘要
        delta_parts = []
        ATTR_LABELS = {
            "morale": "士气", "health": "体力", "fatigue": "疲劳",
            "speed": "速度", "strength": "力量", "vertical": "弹跳",
            "endurance": "耐力", "shooting_2pt": "两分", "shooting_3pt": "三分",
            "free_throw": "罚球", "passing": "传球", "ball_handling": "控球",
            "perimeter_def": "外防", "interior_def": "内防",
            "basketball_iq": "IQ", "clutch_factor": "关键",
            "leadership": "领袖", "work_ethic": "勤奋",
            "media_handling": "媒体", "block_tendency": "盖帽",
            "steal_tendency": "抢断", "post_moves": "背打",
        }
        for attr, d in fe.attribute_delta.items():
            sign = "+" if d > 0 else ""
            dcol = "green" if d > 0 else "red"
            label = ATTR_LABELS.get(attr, attr)
            delta_parts.append(f"[{dcol}]{sign}{d} {label}[/]")

        if delta_parts:
            self.write("  " + "  ".join(delta_parts))
        self.write("")
