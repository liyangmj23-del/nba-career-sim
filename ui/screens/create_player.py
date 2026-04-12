"""
自定义球员创建屏幕。
支持任意姓名、位置、球队、年龄。创建后直接进入生涯仪表盘。
"""
import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, Static, Select
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding

from database.repositories.player_repo import PlayerRepository
from database.repositories.team_repo import TeamRepository
from database.repositories.save_repo import SaveRepository
from seeding.data_transformer import derive_attributes
from config import CURRENT_SEASON_YEAR


# 正整数 player_id 给 nba_api，自定义球员用负数（从 -1 开始递减）
def _next_custom_id() -> int:
    from database.connection import db
    with db() as conn:
        row = conn.execute("SELECT MIN(player_id) FROM players WHERE player_id < 0").fetchone()
        min_id = row[0] if row and row[0] is not None else 0
    return min_id - 1


POSITIONS = ["PG", "SG", "SF", "PF", "C"]


class CreatePlayer(Screen):
    """自定义球员创建表单。"""

    BINDINGS = [
        Binding("escape", "go_back", "返回", show=True),
    ]

    DEFAULT_CSS = """
    CreatePlayer {
        layout: vertical;
        background: #0a0a12;
        align: center top;
    }
    #create-header {
        dock: top;
        height: 2;
        background: #06060f;
        border-bottom: solid #1a1a30;
        padding: 0 2;
        color: #ffaa44;
        text-style: bold;
        content-align: left middle;
    }
    #form-box {
        width: 60;
        margin: 2 0;
        border: solid #2a3060;
        background: #0d0d1a;
        padding: 2 3;
    }
    .form-row {
        height: 3;
        layout: horizontal;
        align: left middle;
        margin-bottom: 1;
    }
    .form-label {
        width: 12;
        color: #506080;
        content-align: right middle;
        padding-right: 1;
    }
    .form-input {
        width: 30;
        background: #12122a;
        border: solid #2a3060;
        color: #ffffff;
    }
    .form-select {
        width: 18;
        background: #12122a;
        border: solid #2a3060;
        color: #ffffff;
    }
    .form-hint {
        color: #303050;
        content-align: left middle;
        padding-left: 1;
    }
    .section-title {
        color: #4080c0;
        text-style: bold;
        margin: 1 0;
    }
    #bottom-bar {
        dock: bottom;
        height: 3;
        background: #06060f;
        border-top: solid #1a1a30;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
    }
    .create-btn {
        background: #0a2050;
        border: solid #1e6eb5;
        color: #4dc3ff;
        text-style: bold;
        margin-right: 1;
    }
    .cancel-btn {
        background: #12122a;
        border: solid #1e3060;
        color: #9ab0d0;
    }
    #feedback {
        color: #44dd88;
        content-align: left middle;
        padding-left: 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._teams: list = []

    def compose(self) -> ComposeResult:
        yield Static("  新建自定义球员", id="create-header")

        with Vertical(id="form-box"):
            yield Static("── 基本信息 ─────────────────────────────", classes="section-title")

            with Horizontal(classes="form-row"):
                yield Static("球员姓名", classes="form-label")
                yield Input(placeholder="例：张伟 / LeBron Clone", id="inp-name", classes="form-input")

            with Horizontal(classes="form-row"):
                yield Static("位  置", classes="form-label")
                yield Select(
                    [(p, p) for p in POSITIONS],
                    value="PG",
                    id="sel-position",
                    classes="form-select",
                )

            with Horizontal(classes="form-row"):
                yield Static("年  龄", classes="form-label")
                yield Input(placeholder="例：22", value="22", id="inp-age", classes="form-input")

            with Horizontal(classes="form-row"):
                yield Static("生涯年", classes="form-label")
                yield Input(placeholder="例：1", value="1", id="inp-career", classes="form-input")

            yield Static("── 加入球队 ─────────────────────────────", classes="section-title")

            with Horizontal(classes="form-row"):
                yield Static("球队 ID", classes="form-label")
                yield Input(
                    placeholder="例：1610612747（LAL）留空=自由球员",
                    id="inp-team",
                    classes="form-input",
                )
                yield Static("[dim]留空=自由球员[/]", classes="form-hint")

            yield Static("── 初始属性（可留空使用位置默认值）────", classes="section-title")

            with Horizontal(classes="form-row"):
                yield Static("综合评级", classes="form-label")
                yield Input(placeholder="1-99，留空=按位置默认", id="inp-overall", classes="form-input")

        with Horizontal(id="bottom-bar"):
            yield Button("创建并开始生涯", id="btn-create", classes="create-btn")
            yield Button("返回  [Esc]", id="btn-cancel", classes="cancel-btn")
            yield Static("", id="feedback")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            self._create_player()
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def _create_player(self) -> None:
        # ── 读取表单 ──────────────────────────────────────────────────────────
        name = self.query_one("#inp-name", Input).value.strip()
        if not name:
            self.query_one("#feedback", Static).update("[red]请输入球员姓名[/]")
            return

        pos_widget = self.query_one("#sel-position", Select)
        position   = str(pos_widget.value) if pos_widget.value else "PG"

        try:
            age = int(self.query_one("#inp-age", Input).value.strip() or "22")
        except ValueError:
            age = 22

        try:
            career_year = int(self.query_one("#inp-career", Input).value.strip() or "1")
        except ValueError:
            career_year = 1

        team_raw = self.query_one("#inp-team", Input).value.strip()
        try:
            team_id = int(team_raw) if team_raw else None
        except ValueError:
            team_id = None

        overall_raw = self.query_one("#inp-overall", Input).value.strip()
        try:
            custom_overall = int(overall_raw) if overall_raw else None
        except ValueError:
            custom_overall = None

        # ── 创建 Player 记录 ──────────────────────────────────────────────────
        player_id  = _next_custom_id()
        parts      = name.split(maxsplit=1)
        first_name = parts[0]
        last_name  = parts[1] if len(parts) > 1 else ""

        player_repo = PlayerRepository()
        player_repo.upsert({
            "player_id":       player_id,
            "first_name":      first_name,
            "last_name":       last_name,
            "full_name":       name,
            "position":        position,
            "is_active":       1,
            "is_custom":       1,
            "current_team_id": team_id,
            "from_year":       CURRENT_SEASON_YEAR - career_year,
        })

        # ── 生成默认属性 ──────────────────────────────────────────────────────
        attrs_data = derive_attributes(player_id, position, None)
        if custom_overall:
            # 把所有技术属性缩放到目标综合评级附近
            diff = custom_overall - attrs_data.get("overall_rating", 50)
            for k in attrs_data:
                if k not in ("player_id", "season_year", "overall_rating",
                             "health", "morale", "fatigue"):
                    attrs_data[k] = max(1, min(99, attrs_data[k] + diff))
            attrs_data["overall_rating"] = max(1, min(99, custom_overall))

        player_repo.upsert_attributes(attrs_data)

        # ── 创建存档 ──────────────────────────────────────────────────────────
        save_repo = SaveRepository()
        today     = datetime.date.today().isoformat()
        save_id   = save_repo.create({
            "save_name":       f"[自定义] {name}  {CURRENT_SEASON_YEAR-1}-{str(CURRENT_SEASON_YEAR)[2:]}",
            "player_id":       player_id,
            "current_team_id": team_id,
            "current_season":  CURRENT_SEASON_YEAR,
            "current_week":    1,
            "current_age":     age,
            "career_year":     career_year,
            "state_json":      {},
        })

        self.query_one("#feedback", Static).update(f"[green]创建成功！进入生涯...[/]")

        # ── 推入游戏主界面 ────────────────────────────────────────────────────
        player = player_repo.get_by_id(player_id)
        from ui.screens.career_dashboard import CareerDashboard
        self.app.push_screen(CareerDashboard(save_id=save_id, player=player))
