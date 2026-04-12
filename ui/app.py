"""
NBASimApp：Textual 应用程序主类。
注册所有屏幕，管理屏幕导航。
"""
import sys
from pathlib import Path

# 确保项目根目录在 PATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.widgets import Footer

from ui.screens.main_menu import MainMenu
from ui.screens.player_select import PlayerSelect
from ui.screens.save_select import SaveSelect
from ui.screens.create_player import CreatePlayer
from database.schema import init_database


class NBASimApp(App):
    """NBA 生涯模拟器主应用。"""

    CSS_PATH   = Path(__file__).parent / "styles" / "nba_sim.tcss"
    TITLE      = "NBA 生涯模拟器"
    SUB_TITLE  = "你的选择，你的故事"

    SCREENS = {
        "main_menu":     MainMenu,
        "player_select": PlayerSelect,
        "save_select":   SaveSelect,
        "create_player": CreatePlayer,
    }

    def on_mount(self) -> None:
        init_database()
        self.push_screen("main_menu")
