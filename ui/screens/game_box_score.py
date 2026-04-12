"""
比赛数据看板：展示一场比赛双方所有球员的完整 Box Score。
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, DataTable
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from simulation.game_simulator import FullGameBoxScore, TeamBoxScore


class GameBoxScore(Screen):
    """完整比赛 Box Score 屏幕。"""

    BINDINGS = [Binding("escape", "go_back", "返回", show=True)]

    DEFAULT_CSS = """
    GameBoxScore {
        layout: vertical;
        background: #0a0a12;
    }
    #box-header {
        dock: top;
        height: 3;
        background: #06060f;
        border-bottom: solid #1a1a30;
        padding: 0 2;
        layout: horizontal;
        align: center middle;
    }
    #score-display {
        color: #4dc3ff;
        text-style: bold;
        text-align: center;
        width: 1fr;
    }
    #box-body {
        height: 1fr;
        layout: horizontal;
    }
    #home-panel {
        width: 1fr;
        border-right: solid #1e2040;
    }
    #away-panel {
        width: 1fr;
    }
    .team-header {
        height: 2;
        background: #0d0d20;
        border-bottom: solid #1e2040;
        padding: 0 1;
        color: #8090b0;
        text-style: bold;
        content-align: left middle;
    }
    .team-table {
        background: #08080f;
        border: none;
    }
    #back-bar {
        dock: bottom;
        height: 3;
        background: #06060f;
        border-top: solid #1a1a30;
        padding: 0 2;
        align: left middle;
    }
    .back-btn {
        background: #0a1830;
        border: solid #1e4080;
        color: #7ab0e0;
    }
    """

    def __init__(self, box_score: FullGameBoxScore, **kwargs):
        super().__init__(**kwargs)
        self._box = box_score

    def compose(self) -> ComposeResult:
        home = self._box.home
        away = self._box.away
        result_str = (
            f"[bold cyan]{away.abbreviation}[/]  "
            f"{'[green]' if not away.won else '[red]'}{away.total_points}[/]"
            f"  :  "
            f"{'[green]' if home.won else '[red]'}{home.total_points}[/]"
            f"  [bold cyan]{home.abbreviation}[/]"
            f"  [dim]第{self._box.game_week}周  第{self._box.game_number}场[/]"
        )

        with Horizontal(id="box-header"):
            yield Static(result_str, id="score-display")

        with Horizontal(id="box-body"):
            with Vertical(id="home-panel"):
                yield Static(
                    f"  {'[green]主队 WIN' if home.won else '[red]主队'}"
                    f"  {home.team_name}",
                    classes="team-header",
                )
                yield DataTable(id="home-table", classes="team-table", cursor_type="row")

            with Vertical(id="away-panel"):
                yield Static(
                    f"  {'[green]客队 WIN' if away.won else '[red]客队'}"
                    f"  {away.team_name}",
                    classes="team-header",
                )
                yield DataTable(id="away-table", classes="team-table", cursor_type="row")

        with Horizontal(id="back-bar"):
            yield Button("返回  [Esc]", id="btn-back", classes="back-btn")

    def on_mount(self) -> None:
        self._fill_table("home-table", self._box.home)
        self._fill_table("away-table", self._box.away)

    def _fill_table(self, table_id: str, team: TeamBoxScore) -> None:
        table = self.query_one(f"#{table_id}", DataTable)
        table.add_columns(
            "球员", "位", "分", "篮", "助", "断", "帽", "失",
            "FG", "FG%", "3P", "3P%", "FT", "+/-",
        )
        for p in team.players:
            name_disp = p.name
            if p.is_hero:
                name_disp = f"★ {p.name}"

            # 首发/替补分隔
            if not p.is_starter and table.row_count > 0:
                # 检查上一行是否已是替补
                pass  # DataTable 不支持分隔行，用样式区分

            fg_str  = f"{p.fg_made}/{p.fg_attempted}"
            fg3_str = f"{p.fg3_made}/{p.fg3_attempted}"
            ft_str  = f"{p.ft_made}/{p.ft_attempted}"
            pm_str  = f"+{p.plus_minus}" if p.plus_minus > 0 else str(p.plus_minus)

            table.add_row(
                name_disp,
                p.position,
                str(p.points),
                str(p.rebounds),
                str(p.assists),
                str(p.steals),
                str(p.blocks),
                str(p.turnovers),
                fg_str,
                p.fg_pct,
                fg3_str,
                p.fg3_pct,
                ft_str,
                pm_str,
                key=p.name,
            )

        # 添加合计行
        table.add_row(
            "[bold]合计[/]", "-",
            str(sum(p.points for p in team.players)),
            str(sum(p.rebounds for p in team.players)),
            str(sum(p.assists for p in team.players)),
            str(sum(p.steals for p in team.players)),
            str(sum(p.blocks for p in team.players)),
            str(sum(p.turnovers for p in team.players)),
            f"{sum(p.fg_made for p in team.players)}/{sum(p.fg_attempted for p in team.players)}",
            "-",
            f"{sum(p.fg3_made for p in team.players)}/{sum(p.fg3_attempted for p in team.players)}",
            "-",
            f"{sum(p.ft_made for p in team.players)}/{sum(p.ft_attempted for p in team.players)}",
            "-",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
