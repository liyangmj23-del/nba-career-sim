from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Vertical


class MainMenu(Screen):
    """主菜单屏幕。"""

    CSS_ID = "main-menu"

    DEFAULT_CSS = """
    MainMenu {
        align: center middle;
        background: #0a0a12;
    }
    #main-menu-box {
        width: 52;
        height: 24;
        border: double #1e6eb5;
        background: #0a0a18;
        padding: 2 4;
        align: center top;
    }
    #menu-title {
        text-align: center;
        color: #4dc3ff;
        text-style: bold;
        height: 3;
    }
    #menu-subtitle {
        text-align: center;
        color: #304060;
        height: 2;
        margin-bottom: 1;
    }
    .menu-btn {
        width: 100%;
        margin: 0 0 1 0;
        background: #12122a;
        border: solid #1e3060;
        color: #9ab0d0;
    }
    .menu-btn:hover {
        background: #1a2040;
        border: solid #4080c0;
        color: #ffffff;
    }
    .menu-btn--primary {
        background: #0a2050;
        border: solid #1e6eb5;
        color: #4dc3ff;
        text-style: bold;
    }
    .menu-btn--primary:hover {
        background: #0d3070;
        border: solid #3090e0;
    }
    #menu-version {
        text-align: center;
        color: #1e2840;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="main-menu-box"):
            yield Static(
                "NBA  生涯模拟器\n"
                "─────────────────────────",
                id="menu-title",
            )
            yield Static("你的选择，你的故事", id="menu-subtitle")
            yield Button("选择现有球员开始", id="btn-new",    classes="menu-btn menu-btn--primary")
            yield Button("新建自定义球员",   id="btn-custom", classes="menu-btn menu-btn--primary")
            yield Button("继续存档",         id="btn-load",   classes="menu-btn")
            yield Button("退出",             id="btn-quit",   classes="menu-btn")
            yield Static("v0.3", id="menu-version")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-new":
            self.app.push_screen("player_select")
        elif btn_id == "btn-custom":
            self.app.push_screen("create_player")
        elif btn_id == "btn-load":
            self.app.push_screen("save_select")
        elif btn_id == "btn-quit":
            self.app.exit()
