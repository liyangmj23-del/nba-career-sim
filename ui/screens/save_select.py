"""存档选择屏幕（继续游戏时使用）。"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static
from textual.containers import Horizontal
from textual.binding import Binding

from database.repositories.save_repo import SaveRepository
from database.repositories.player_repo import PlayerRepository


class SaveSelect(Screen):
    BINDINGS = [Binding("escape", "go_back", "返回", show=True)]

    DEFAULT_CSS = """
    SaveSelect {
        layout: vertical;
        background: #0a0a12;
    }
    #save-header {
        dock: top;
        height: 2;
        background: #06060f;
        border-bottom: solid #1a1a30;
        padding: 0 2;
        color: #4dc3ff;
        text-style: bold;
        content-align: left middle;
    }
    DataTable {
        background: #08080f;
        height: 1fr;
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
    .nav-btn {
        background: #0a1830;
        border: solid #1e4080;
        color: #7ab0e0;
        margin-right: 1;
    }
    .load-btn {
        background: #0a2050;
        border: solid #1e6eb5;
        color: #4dc3ff;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._saves = []
        self._selected_save_id = None

    def compose(self) -> ComposeResult:
        yield Static("  选择存档", id="save-header")
        yield DataTable(id="save-table", cursor_type="row")
        with Horizontal(id="bottom-bar"):
            yield Button("返回", id="btn-back", classes="nav-btn")
            yield Button("加载此存档", id="btn-load", classes="load-btn")

    def on_mount(self) -> None:
        table = self.query_one("#save-table", DataTable)
        table.add_columns("#", "存档名", "球员", "赛季", "第N周", "保存时间")
        self._saves = SaveRepository().get_all()
        player_repo = PlayerRepository()
        for i, s in enumerate(self._saves, 1):
            p = player_repo.get_by_id(s.player_id)
            name = p.full_name if p else "未知"
            table.add_row(
                str(i),
                s.save_name,
                name,
                f"{s.current_season-1}-{str(s.current_season)[2:]}",
                f"第{s.current_week}周",
                (s.updated_at or "")[:16],
                key=str(s.save_id),
            )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key:
            self._selected_save_id = int(event.row_key.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-load":
            self._load_save()

    def _load_save(self) -> None:
        if not self._selected_save_id and self._saves:
            self._selected_save_id = self._saves[0].save_id
        if not self._selected_save_id:
            return
        save = SaveRepository().get_by_id(self._selected_save_id)
        if not save:
            return
        player = PlayerRepository().get_by_id(save.player_id)
        if not player:
            return
        from ui.screens.career_dashboard import CareerDashboard
        self.app.push_screen(
            CareerDashboard(save_id=save.save_id, player=player)
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()
