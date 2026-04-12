"""
选择弹窗：当事件需要玩家做决定时弹出。
用 push_screen_wait() 调用，dismiss() 返回选择的 option key。
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer

IMPACT_LABEL = {
    "week":   "影响范围：几场比赛",
    "month":  "影响范围：约一个月",
    "season": "影响范围：本赛季",
    "career": "影响范围：整个职业生涯",
}

IMPACT_COLOR = {
    "week":   "dim",
    "month":  "cyan",
    "season": "yellow",
    "career": "bold gold1",
}


class ChoiceModal(Screen):
    """
    选择模态界面。
    dismiss(option_key) 把玩家的选择传回 career_dashboard。
    """

    DEFAULT_CSS = """
    ChoiceModal {
        align: center middle;
        background: rgba(0,0,0,0.85);
    }
    #choice-box {
        width: 72;
        max-height: 40;
        border: double #4080c0;
        background: #080818;
        padding: 1 2;
    }
    #choice-title {
        color: #ffaa44;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    #choice-narrative {
        color: #8090a8;
        margin-bottom: 1;
        padding: 0 1;
    }
    #choice-prompt {
        color: #4dc3ff;
        text-style: bold;
        margin-bottom: 1;
        text-align: center;
    }
    #options-scroll {
        max-height: 24;
    }
    .option-block {
        border: solid #1e3060;
        background: #0a0a1a;
        margin-bottom: 1;
        padding: 1;
    }
    .option-block:hover {
        border: solid #4080c0;
        background: #0d0d20;
    }
    .option-btn {
        width: 100%;
        background: #0a2050;
        border: solid #1e4080;
        color: #4dc3ff;
        text-style: bold;
        margin-bottom: 1;
    }
    .option-btn:hover {
        background: #0d3070;
        border: solid #3090e0;
    }
    .option-desc {
        color: #506080;
        padding: 0 1;
    }
    .option-impact {
        padding: 0 1;
        margin-top: 0;
    }
    .option-narrative {
        color: #3a4a60;
        padding: 0 1;
        margin-top: 1;
    }
    """

    def __init__(self, choice_data: dict, **kwargs):
        super().__init__(**kwargs)
        self._data = choice_data

    def compose(self) -> ComposeResult:
        with Vertical(id="choice-box"):
            yield Static(f"【需要你做出选择】\n{self._data['title']}", id="choice-title")

            # 叙事（截取前200字，避免太长）
            narrative = self._data.get("narrative", "")
            if len(narrative) > 200:
                narrative = narrative[:200].rsplit("\n", 1)[0] + "\n……"
            yield Static(narrative, id="choice-narrative")

            yield Static(self._data["prompt"], id="choice-prompt")

            with ScrollableContainer(id="options-scroll"):
                for opt in self._data["options"]:
                    scope = opt.get("impact_scope", "week")
                    icol  = IMPACT_COLOR.get(scope, "dim")
                    ilabel = IMPACT_LABEL.get(scope, scope)

                    with Vertical(classes="option-block"):
                        yield Button(
                            opt["label"],
                            id=f"opt-{opt['key']}",
                            classes="option-btn",
                        )
                        yield Static(
                            f"[dim]{opt['description']}[/]",
                            classes="option-desc",
                        )
                        yield Static(
                            f"[{icol}]{ilabel}[/]",
                            classes="option-impact",
                        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("opt-"):
            chosen_key = btn_id[4:]
            self.dismiss(chosen_key)
