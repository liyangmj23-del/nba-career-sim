"""
球员搜索与选择屏幕。
选中球员后创建新存档，推入 CareerDashboard。
"""
import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, DataTable, Static, Footer
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from database.repositories.player_repo import PlayerRepository
from database.repositories.save_repo import SaveRepository
from seeding.data_transformer import derive_attributes
from config import CURRENT_SEASON_YEAR


class PlayerSelect(Screen):
    """球员搜索 & 选择界面。"""

    BINDINGS = [
        Binding("escape", "go_back", "返回"),
        Binding("enter", "select_player", "选择"),
    ]

    DEFAULT_CSS = """
    PlayerSelect {
        layout: vertical;
        background: #0a0a12;
    }
    #search-row {
        dock: top;
        height: 3;
        layout: horizontal;
        background: #060612;
        border-bottom: solid #1e2040;
        padding: 0 2;
        align: left middle;
    }
    #search-input {
        width: 40;
        background: #12122a;
        border: solid #2a3060;
        color: #ffffff;
        margin-right: 1;
    }
    #search-hint {
        color: #304060;
        content-align: left middle;
    }
    #player-table {
        border: none;
        background: #0a0a12;
    }
    #bottom-bar {
        dock: bottom;
        height: 3;
        layout: horizontal;
        background: #060612;
        border-top: solid #1e2040;
        padding: 0 2;
        align: left middle;
    }
    .nav-btn {
        background: #12122a;
        border: solid #1e3060;
        color: #9ab0d0;
        margin-right: 1;
    }
    .select-btn {
        background: #0a2050;
        border: solid #1e6eb5;
        color: #4dc3ff;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._player_repo = PlayerRepository()
        self._save_repo   = SaveRepository()
        self._results     = []
        self._selected_id = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-row"):
            yield Input(placeholder="输入球员姓名搜索...", id="search-input")
            yield Static("Enter 搜索  ↑↓ 选择  空格 确认", id="search-hint")

        yield DataTable(id="player-table", cursor_type="row")

        with Horizontal(id="bottom-bar"):
            yield Button("返回", id="btn-back", classes="nav-btn")
            yield Button("选择此球员开始生涯", id="btn-select", classes="select-btn")

    def on_mount(self) -> None:
        self._setup_table()
        self._do_search("")          # 显示所有球员

    def _setup_table(self) -> None:
        table = self.query_one("#player-table", DataTable)
        table.add_columns("#", "姓名", "位置", "综合", "球队", "出生年")

    def _do_search(self, query: str) -> None:
        self._player_repo = PlayerRepository()
        if query.strip():
            self._results = self._player_repo.search(query)[:50]
        else:
            self._results = self._player_repo.get_all(active_only=True)[:50]

        table = self.query_one("#player-table", DataTable)
        table.clear()
        for i, p in enumerate(self._results, 1):
            attr = self._player_repo.get_attributes(p.player_id, CURRENT_SEASON_YEAR)
            overall = str(attr.overall_rating) if attr else "-"
            birth_year = p.birthdate[:4] if p.birthdate else "-"
            team_id = str(p.current_team_id or "-")
            table.add_row(
                str(i),
                p.full_name,
                p.position or "-",
                overall,
                team_id,
                birth_year,
                key=str(p.player_id),
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self._do_search(event.value)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key:
            self._selected_id = int(event.row_key.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-select":
            self._start_career()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_select_player(self) -> None:
        self._start_career()

    def _start_career(self) -> None:
        if not self._selected_id:
            # 若没有高亮行，选第一个
            if self._results:
                self._selected_id = self._results[0].player_id
            else:
                return

        player_repo = PlayerRepository()
        player = player_repo.get_by_id(self._selected_id)
        if not player:
            return

        # 确保属性存在
        attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
        if not attr:
            attrs_data = derive_attributes(player.player_id, player.position, None)
            player_repo.upsert_attributes(attrs_data)

        # 计算年龄
        age = None
        if player.birthdate:
            try:
                bd  = datetime.date.fromisoformat(player.birthdate[:10])
                now = datetime.date.today()
                age = now.year - bd.year - ((now.month, now.day) < (bd.month, bd.day))
            except Exception:
                pass

        # 判断生涯年
        career_year = 1
        if player.from_year:
            career_year = max(1, CURRENT_SEASON_YEAR - player.from_year)

        save_name = f"{player.full_name}  {CURRENT_SEASON_YEAR-1}-{str(CURRENT_SEASON_YEAR)[2:]}"
        save_id = self._save_repo.create({
            "save_name":       save_name,
            "player_id":       player.player_id,
            "current_team_id": player.current_team_id,
            "current_season":  CURRENT_SEASON_YEAR,
            "current_week":    1,
            "current_age":     age,
            "career_year":     career_year,
            "state_json":      {},
        })

        # 推入游戏主界面
        from ui.screens.career_dashboard import CareerDashboard
        self.app.push_screen(CareerDashboard(save_id=save_id, player=player))
