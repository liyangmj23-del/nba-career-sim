"""
CRUD 编辑器：修改球员属性、基本信息、球队信息。
按 Escape 返回，按 S 保存当前修改。
"""
from typing import Callable
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, Static, DataTable, TabbedContent, TabPane, Label
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding

from database.repositories.player_repo import PlayerRepository
from database.repositories.team_repo import TeamRepository
from config import CURRENT_SEASON_YEAR


ATTR_GROUPS = {
    "身体素质": ["speed", "strength", "vertical", "endurance"],
    "进攻技术": ["ball_handling", "shooting_2pt", "shooting_3pt", "free_throw", "passing", "post_moves"],
    "防守技术": ["perimeter_def", "interior_def", "steal_tendency", "block_tendency"],
    "心理/智商": ["basketball_iq", "clutch_factor", "leadership", "work_ethic", "media_handling"],
    "状  态": ["health", "morale", "fatigue"],
}

ATTR_LABELS = {
    "speed": "速度", "strength": "力量", "vertical": "弹跳", "endurance": "耐力",
    "ball_handling": "控球", "shooting_2pt": "两分", "shooting_3pt": "三分",
    "free_throw": "罚球", "passing": "传球", "post_moves": "背打",
    "perimeter_def": "外防", "interior_def": "内防",
    "steal_tendency": "抢断", "block_tendency": "盖帽",
    "basketball_iq": "篮球IQ", "clutch_factor": "关键时刻",
    "leadership": "领导力", "work_ethic": "勤奋",
    "media_handling": "媒体应对",
    "health": "体力", "morale": "士气", "fatigue": "疲劳",
}


class CrudEditor(Screen):
    """属性/球员/球队编辑器。"""

    BINDINGS = [
        Binding("escape", "go_back", "返回", show=True),
        Binding("ctrl+s", "save_all", "保存", show=True),
    ]

    DEFAULT_CSS = """
    CrudEditor {
        layout: vertical;
        background: #0a0a12;
    }
    #crud-header {
        dock: top;
        height: 2;
        background: #06060f;
        border-bottom: solid #1a1a30;
        padding: 0 2;
        color: #ffaa44;
        text-style: bold;
        content-align: left middle;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        background: #0a0a12;
        padding: 1 2;
        overflow-y: auto;
    }
    .group-title {
        color: #4080c0;
        text-style: bold;
        margin: 1 0 0 0;
    }
    .attr-edit-row {
        height: 3;
        layout: horizontal;
        align: left middle;
    }
    .attr-edit-label {
        width: 12;
        color: #506080;
        content-align: right middle;
        padding-right: 1;
    }
    .attr-edit-input {
        width: 8;
        background: #12122a;
        border: solid #2a3060;
        color: #ffffff;
    }
    .attr-edit-hint {
        color: #303050;
        content-align: left middle;
        padding-left: 1;
        width: 20;
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
    .save-btn {
        background: #0a2050;
        border: solid #1e6eb5;
        color: #4dc3ff;
        margin-right: 1;
    }
    .save-btn:hover {
        background: #0d3070;
    }
    .cancel-btn {
        background: #12122a;
        border: solid #1e3060;
        color: #9ab0d0;
    }
    #save-feedback {
        color: #44dd88;
        content-align: left middle;
        padding-left: 2;
    }
    """

    def __init__(self, player, save_id: int | None = None,
                 on_save: Callable | None = None, **kwargs):
        super().__init__(**kwargs)
        self.player   = player
        self.save_id  = save_id
        self.on_save  = on_save
        self._repo    = PlayerRepository()
        self._attrs   = {}
        self._inputs: dict[str, Input] = {}
        self._override_inputs: dict[str, Input] = {}

    def compose(self) -> ComposeResult:
        yield Static(
            f"  编辑器  ·  {self.player.full_name}  |  Ctrl+S 保存  Esc 返回",
            id="crud-header",
        )

        with TabbedContent():
            with TabPane("球员属性", id="tab-attrs"):
                yield ScrollableContainer(id="attrs-scroll")

            with TabPane("指定数据 [神模式]", id="tab-override"):
                yield self._make_override_form()

            with TabPane("基本信息", id="tab-basic"):
                yield self._make_basic_form()

        with Horizontal(id="bottom-bar"):
            yield Button("保存  [Ctrl+S]", id="btn-save", classes="save-btn")
            yield Button("取消  [Esc]", id="btn-cancel", classes="cancel-btn")
            yield Static("", id="save-feedback")

    def on_mount(self) -> None:
        self._load_attrs()
        self._build_attr_form()
        self._build_override_form()

    def _load_attrs(self) -> None:
        attr = self._repo.get_attributes(self.player.player_id, CURRENT_SEASON_YEAR)
        if attr:
            skip = {"attr_id", "player_id", "season_year"}
            self._attrs = {
                k: getattr(attr, k)
                for k in attr.__dataclass_fields__
                if k not in skip
            }

    def _build_attr_form(self) -> None:
        scroll = self.query_one("#attrs-scroll", ScrollableContainer)
        for group_name, fields in ATTR_GROUPS.items():
            scroll.mount(Static(f"── {group_name} ────────────────────", classes="group-title"))
            for field_key in fields:
                if field_key not in self._attrs:
                    continue
                val   = self._attrs[field_key]
                label = ATTR_LABELS.get(field_key, field_key)
                inp   = Input(
                    value=str(val),
                    id=f"input-{field_key}",
                    classes="attr-edit-input",
                )
                self._inputs[field_key] = inp
                # 评级提示
                if val >= 85: hint = "精英"
                elif val >= 75: hint = "优秀"
                elif val >= 65: hint = "良好"
                elif val >= 50: hint = "普通"
                else: hint = "较弱"

                row = Horizontal(classes="attr-edit-row")
                scroll.mount(row)
                row.mount(Static(label, classes="attr-edit-label"))
                row.mount(inp)
                row.mount(Static(f"[dim]{hint}  (1-99)[/]", classes="attr-edit-hint"))

    def _make_override_form(self) -> ScrollableContainer:
        """「指定数据」Tab：直接设置每场目标数据，绕过属性计算。"""
        scroll = ScrollableContainer()
        return scroll

    def _build_override_form(self) -> None:
        scroll = self.query_one("#tab-override ScrollableContainer", ScrollableContainer)

        # 读取当前存档的 stat_overrides（若有）
        current_overrides = {}
        if self.save_id:
            from database.repositories.save_repo import SaveRepository
            save = SaveRepository().get_by_id(self.save_id)
            if save:
                current_overrides = save.state_json.get("stat_overrides", {})

        OVERRIDE_FIELDS = [
            ("pts", "得分/场", "PPG", "0~100"),
            ("reb", "篮板/场", "RPG", "0~50"),
            ("ast", "助攻/场", "APG", "0~30"),
            ("stl", "抢断/场", "SPG", "0~20"),
            ("blk", "盖帽/场", "BPG", "0~20"),
        ]

        scroll.mount(Static(
            "[bold yellow]神模式：指定场均数据[/]\n"
            "[dim]填写后模拟将忽略属性，直接按指定数据生成比赛（±10%噪音）。\n"
            "留空=关闭覆盖，恢复属性驱动模式。[/]\n",
            id="override-desc",
        ))

        for key, label, abbr, hint in OVERRIDE_FIELDS:
            current_val = current_overrides.get(key, "")
            val_str = str(current_val) if current_val else ""
            inp = Input(
                value=val_str,
                placeholder=f"留空=关闭  例：10",
                id=f"ov-{key}",
                classes="attr-edit-input",
            )
            self._override_inputs[key] = inp
            row = Horizontal(classes="attr-edit-row")
            scroll.mount(row)
            row.mount(Static(f"{label} ({abbr})", classes="attr-edit-label"))
            row.mount(inp)
            row.mount(Static(f"[dim]{hint}[/]", classes="attr-edit-hint"))

        # 清除按钮
        clear_btn = Button("清除所有覆盖（回到属性模式）", id="btn-clear-override",
                           classes="cancel-btn")
        scroll.mount(clear_btn)

    def _make_basic_form(self) -> Vertical:
        v = Vertical()
        return v

    def _save_attrs(self) -> bool:
        """读取所有 Input，验证并写入 DB。返回是否成功。"""
        updates = {}
        for field_key, inp in self._inputs.items():
            raw = inp.value.strip()
            if not raw:
                continue
            try:
                val = int(raw)
                if field_key in ("health", "morale"):
                    val = max(0, min(100, val))
                elif field_key == "fatigue":
                    val = max(0, min(100, val))
                else:
                    val = max(1, min(99, val))
                updates[field_key] = val
            except ValueError:
                # 非法输入：恢复原值
                inp.value = str(self._attrs.get(field_key, 50))

        if not updates:
            return False

        # 重算综合评分
        merged = {**self._attrs, **updates}
        skill_keys = [
            "speed", "strength", "vertical", "endurance",
            "ball_handling", "shooting_2pt", "shooting_3pt", "free_throw",
            "passing", "post_moves", "perimeter_def", "interior_def",
            "steal_tendency", "block_tendency", "basketball_iq",
            "clutch_factor", "leadership", "work_ethic", "media_handling",
        ]
        overall = max(1, min(99, round(
            sum(merged.get(k, 50) for k in skill_keys) / len(skill_keys)
        )))
        updates["overall_rating"] = overall

        self._repo.update_attributes(
            self.player.player_id, CURRENT_SEASON_YEAR, updates
        )
        self._attrs.update(updates)
        return True

    # ── 按钮 / 快捷键 ─────────────────────────────────────────────────────────

    def _save_overrides(self) -> bool:
        """读取指定数据表单，写入 save_states.state_json。"""
        if not self.save_id:
            return False
        overrides = {}
        for key, inp in self._override_inputs.items():
            raw = inp.value.strip()
            if raw:
                try:
                    overrides[key] = float(raw)
                except ValueError:
                    pass
        from database.repositories.save_repo import SaveRepository
        save_repo = SaveRepository()
        save      = save_repo.get_by_id(self.save_id)
        if not save:
            return False
        new_state = dict(save.state_json)
        if overrides:
            new_state["stat_overrides"] = overrides
        else:
            new_state.pop("stat_overrides", None)
        save_repo.update(self.save_id, {"state_json": new_state})
        return True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save_all()
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()
        elif event.button.id == "btn-clear-override":
            for inp in self._override_inputs.values():
                inp.value = ""
            self._save_overrides()
            self.query_one("#save-feedback", Static).update("[green]已清除数据覆盖[/]")

    def action_save_all(self) -> None:
        ok_attrs     = self._save_attrs()
        ok_overrides = self._save_overrides()
        fb = self.query_one("#save-feedback", Static)
        if ok_attrs or ok_overrides:
            parts = []
            if ok_attrs:     parts.append("属性")
            if ok_overrides: parts.append("数据覆盖")
            fb.update(f"[bold green]已保存：{'、'.join(parts)}[/]")
            if self.on_save:
                self.on_save()
        else:
            fb.update("[dim]没有变化[/]")

    def action_go_back(self) -> None:
        self.app.pop_screen()
