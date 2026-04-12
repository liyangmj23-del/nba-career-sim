"""
生涯仪表盘：游戏核心屏幕。
左侧=球员卡，中间=事件叙事，右侧=操作按钮，底部=赛季统计。
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Footer
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding

from database.repositories.player_repo import PlayerRepository
from database.repositories.save_repo import SaveRepository
from ui.widgets.player_card import PlayerCard
from ui.widgets.event_feed import EventFeed
from simulation.engine import run_season, WeekResult
from config import CURRENT_SEASON_YEAR


class CareerDashboard(Screen):
    """主游戏界面。"""

    BINDINGS = [
        Binding("space", "advance_week", "推进一周", show=True),
        Binding("s", "view_stats", "数据", show=True),
        Binding("e", "edit_attrs", "编辑属性", show=True),
        Binding("d", "set_override", "指定数据", show=True),
        Binding("n", "new_player", "新建球员", show=True),
        Binding("h", "open_html", "HTML报告", show=True),
        Binding("q", "quit_game", "退出", show=True),
    ]

    DEFAULT_CSS = """
    CareerDashboard {
        layout: vertical;
        background: #0a0a12;
    }
    #dash-header {
        dock: top;
        height: 1;
        background: #06060f;
        border-bottom: solid #1a1a30;
        padding: 0 2;
        layout: horizontal;
        color: #506080;
    }
    #dash-header-name {
        color: #4dc3ff;
        text-style: bold;
        width: 32;
    }
    #dash-header-week {
        color: #8090b0;
        width: 30;
    }
    #dash-header-status {
        color: #505070;
        text-align: right;
    }
    #dash-body {
        height: 1fr;
        layout: horizontal;
    }
    #dash-left {
        width: 26;
        border-right: solid #1a1a30;
        background: #09090f;
        overflow-y: auto;
    }
    #dash-center {
        width: 1fr;
        border-right: solid #1a1a30;
        background: #080810;
    }
    #dash-right {
        width: 18;
        background: #09090f;
        padding: 1 1;
        align: center top;
    }
    #dash-footer {
        dock: bottom;
        height: 3;
        background: #06060f;
        border-top: solid #1a1a30;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
    }
    #season-stats-text {
        color: #506080;
        content-align: left middle;
    }
    .action-btn {
        width: 16;
        margin: 0 0 1 0;
        background: #0a1830;
        border: solid #1e4080;
        color: #7ab0e0;
    }
    .action-btn:hover {
        background: #0d2248;
        border: solid #3070c0;
        color: #ffffff;
    }
    .action-btn--advance {
        background: #0a2810;
        border: solid #1e6030;
        color: #44dd88;
        text-style: bold;
    }
    .action-btn--advance:hover {
        background: #0d3818;
        border: solid #2e8048;
    }
    .action-btn--warn {
        background: #281008;
        border: solid #603010;
        color: #dd8844;
    }
    #week-hint {
        color: #202840;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self, save_id: int, player, **kwargs):
        super().__init__(**kwargs)
        self.save_id  = save_id
        self.player   = player
        self._engine  = None
        self._current_wr: WeekResult | None = None
        self._season_done = False
        self._week = 1
        self._pending_choices_queue: list = []

    def compose(self) -> ComposeResult:
        # 顶部信息栏
        with Horizontal(id="dash-header"):
            yield Static(self.player.full_name, id="dash-header-name")
            yield Static("第 1 周  ·  赛季准备中", id="dash-header-week")
            yield Static("按 Space 推进", id="dash-header-status")

        with Horizontal(id="dash-body"):
            # 左侧：球员卡
            with Vertical(id="dash-left"):
                yield PlayerCard(
                    player=self.player,
                    attrs=self._load_attrs(),
                    id="player-card",
                )

            # 中间：事件流
            yield EventFeed(id="event-feed", max_lines=2000, markup=True)

            # 右侧：操作按钮
            with Vertical(id="dash-right"):
                yield Button("推进一周\n[Space]", id="btn-advance", classes="action-btn action-btn--advance")
                yield Button("查看数据\n[S]", id="btn-stats", classes="action-btn")
                yield Button("编辑属性\n[E]", id="btn-edit", classes="action-btn")
                yield Button("指定数据\n[D]", id="btn-override", classes="action-btn")
                yield Button("新建球员\n[N]", id="btn-new-player", classes="action-btn")
                yield Button("HTML报告\n[H]", id="btn-html", classes="action-btn")
                yield Button("退出存档\n[Q]", id="btn-quit", classes="action-btn action-btn--warn")
                yield Static("[dim]─────────────[/]", id="week-hint")

        # 底部赛季统计
        with Horizontal(id="dash-footer"):
            yield Static("", id="season-stats-text")

    def on_mount(self) -> None:
        # 初始化引擎生成器
        self._engine = run_season(self.save_id, CURRENT_SEASON_YEAR)
        feed = self.query_one("#event-feed", EventFeed)
        feed.write(
            f"[dim cyan]生涯开始  ·  {self.player.full_name}[/]\n"
            f"[dim]{CURRENT_SEASON_YEAR-1}-{str(CURRENT_SEASON_YEAR)[2:]} 赛季[/]\n"
            "[dim]按 Space 或点击「推进一周」开始模拟。[/]\n"
        )

    def _load_attrs(self) -> dict:
        repo = PlayerRepository()
        attr = repo.get_attributes(self.player.player_id, CURRENT_SEASON_YEAR)
        if not attr:
            return {}
        return {
            k: getattr(attr, k)
            for k in attr.__dataclass_fields__
            if k not in ("attr_id", "player_id", "season_year")
        }

    # ── 推进一周 ──────────────────────────────────────────────────────────────

    def action_advance_week(self) -> None:
        self._advance()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-advance":
            self._advance()
        elif btn_id == "btn-stats":
            self.action_view_stats()
        elif btn_id == "btn-edit":
            self.action_edit_attrs()
        elif btn_id == "btn-override":
            self.action_set_override()
        elif btn_id == "btn-new-player":
            self.action_new_player()
        elif btn_id == "btn-html":
            self.action_open_html()
        elif btn_id == "btn-quit":
            self.action_quit_game()

    def _advance(self) -> None:
        if self._season_done or self._engine is None:
            return

        try:
            wr = next(self._engine)
        except StopIteration:
            self._season_done = True
            self._show_season_end()
            return

        self._current_wr = wr
        self._week       = wr.week
        self._update_display(wr)

        # 若有待决策事件，逐个弹出选择框
        if wr.pending_choices:
            self._pending_choices_queue = list(wr.pending_choices)
            self._process_next_choice()

    def _update_display(self, wr: WeekResult) -> None:
        # 更新顶部信息栏
        self.query_one("#dash-header-week", Static).update(
            f"第 {wr.week} 周  ·  {wr.season_year-1}-{str(wr.season_year)[2:]} 赛季"
        )

        # 更新事件流
        feed = self.query_one("#event-feed", EventFeed)
        feed.push_week_divider(wr.week, wr.season_year)
        feed.push_games(wr.week_summary)
        if wr.events:
            for fe in wr.events:
                feed.push_event(fe)
        else:
            feed.push_no_event()

        # 更新球员卡（从DB重新读取属性，因为engine已写回）
        card = self.query_one("#player-card", PlayerCard)
        card.refresh_attrs(wr.attrs_after, wr.week_summary)

        # 更新底部赛季统计
        s = wr.season_stats
        gp = s.get("games_played", 0)
        if gp:
            self.query_one("#season-stats-text", Static).update(
                f"赛季  [dim]G[/][bold]{gp}[/]  "
                f"[dim]得分[/][bold cyan]{s.get('pts',0):.1f}[/]  "
                f"[dim]篮板[/][bold]{s.get('reb',0):.1f}[/]  "
                f"[dim]助攻[/][bold]{s.get('ast',0):.1f}[/]  "
                f"[dim]抢断[/][bold green]{s.get('stl',0):.1f}[/]  "
                f"[dim]盖帽[/][bold yellow]{s.get('blk',0):.1f}[/]  "
                f"[dim]FG%[/][bold]{s.get('fg_pct',0)*100:.1f}%[/]  "
                f"[dim]3P%[/][bold]{s.get('fg3_pct',0)*100:.1f}%[/]  "
                f"[dim]FT%[/][bold]{s.get('ft_pct',0)*100:.1f}%[/]  "
                f"[dim]胜负[/][bold]{s.get('wins',0)}W[/]"
            )

    def _show_season_end(self) -> None:
        feed = self.query_one("#event-feed", EventFeed)
        feed.write(
            "\n[bold gold1]══ 赛季结束 ══[/]\n"
            "[dim]本赛季所有比赛已完成。\n"
            "按 S 查看完整赛季数据，或按 Q 返回主菜单。[/]\n"
        )
        self.query_one("#dash-header-week", Static).update(
            "[bold gold1]赛季已结束[/]"
        )
        self.query_one("#btn-advance", Button).label = "赛季结束"
        self.query_one("#btn-advance", Button).disabled = True

    # ── 选择事件处理 ──────────────────────────────────────────────────────────

    def _process_next_choice(self) -> None:
        if not self._pending_choices_queue:
            return
        choice_data = self._pending_choices_queue.pop(0)
        from ui.screens.choice_modal import ChoiceModal
        self.app.push_screen(
            ChoiceModal(choice_data),
            callback=lambda key: self._on_choice_made(choice_data, key),
        )

    def _on_choice_made(self, choice_data: dict, chosen_key: str) -> None:
        """玩家选择后：应用效果 + 在事件流追加后续叙事 + 记录日志。"""
        if not chosen_key:
            self._process_next_choice()
            return

        # 找到选中的选项
        options = {opt["key"]: opt for opt in choice_data["options"]}
        opt = options.get(chosen_key)
        if not opt:
            self._process_next_choice()
            return

        # 应用属性效果
        from database.repositories.player_repo import PlayerRepository
        from events.event_registry import AttrEffect
        from config import CURRENT_SEASON_YEAR
        repo  = PlayerRepository()
        attrs = self._load_attrs()
        delta = {}
        for attr_name, d in opt["effects"]:
            import random
            resolved = random.randint(d[0], d[1]) if isinstance(d, tuple) else d
            new_val  = max(0, min(100 if attr_name in ("health","morale","fatigue") else 99,
                                  attrs.get(attr_name, 50) + resolved))
            delta[attr_name] = resolved
            attrs[attr_name] = new_val
        if delta:
            repo.update_attributes(self.player.player_id, CURRENT_SEASON_YEAR, attrs)

        # 在事件流追加选择结果
        feed = self.query_one("#event-feed", EventFeed)
        impact_labels = {
            "week": "[dim]影响：几场比赛[/]",
            "month": "[cyan]影响：约一个月[/]",
            "season": "[yellow]影响：本赛季[/]",
            "career": "[bold gold1]影响：整个职业生涯[/]",
        }
        scope_label = impact_labels.get(opt.get("impact_scope", "week"), "")
        feed.write(f"\n  [bold cyan]▶ 你选择了：{opt['label']}[/]  {scope_label}")
        if opt.get("narrative"):
            for line in opt["narrative"].strip().split("\n"):
                if line.strip():
                    feed.write(f"  [dim]{line.strip()}[/]")
                else:
                    feed.write("")

        # 属性变化摘要
        if delta:
            ATTR_LABELS = {
                "morale":"士气","health":"体力","speed":"速度","strength":"力量",
                "vertical":"弹跳","endurance":"耐力","shooting_2pt":"两分",
                "shooting_3pt":"三分","free_throw":"罚球","passing":"传球",
                "ball_handling":"控球","perimeter_def":"外防","interior_def":"内防",
                "basketball_iq":"IQ","clutch_factor":"关键","leadership":"领袖",
                "work_ethic":"勤奋","media_handling":"媒体","fatigue":"疲劳",
                "steal_tendency":"抢断","block_tendency":"盖帽",
            }
            parts = []
            for k, v in delta.items():
                sign = "+" if v > 0 else ""
                col  = "green" if v > 0 else "red"
                parts.append(f"[{col}]{sign}{v} {ATTR_LABELS.get(k,k)}[/]")
            if parts:
                feed.write("  " + "  ".join(parts) + "\n")

        # 记录到 event_log
        try:
            from database.repositories.event_log_repo import EventLogRepository
            from database.repositories.save_repo import SaveRepository
            save = SaveRepository().get_by_id(self.save_id)
            EventLogRepository().append({
                "save_id":         self.save_id,
                "player_id":       self.player.player_id,
                "season_year":     save.current_season if save else CURRENT_SEASON_YEAR,
                "week_number":     self._week,
                "event_key":       f"choice.{choice_data['event_key']}.{chosen_key}",
                "category":        "career_milestones",
                "severity":        "major",
                "title":           f"{choice_data['title']} → {opt['label']}",
                "narrative_text":  opt.get("narrative", ""),
                "attribute_delta": delta,
                "stat_delta":      {},
                "is_player_choice": 1,
                "choice_made":     chosen_key,
            })
        except Exception:
            pass

        # 刷新球员卡
        card = self.query_one("#player-card", PlayerCard)
        card.refresh_attrs(attrs, self._current_wr.week_summary if self._current_wr else None)

        # 继续处理下一个待选事件
        self._process_next_choice()

    # ── 导航 ─────────────────────────────────────────────────────────────────

    def action_view_stats(self) -> None:
        from ui.screens.stats_viewer import StatsViewer
        self.app.push_screen(
            StatsViewer(player=self.player, save_id=self.save_id)
        )

    def action_edit_attrs(self) -> None:
        from ui.screens.crud_editor import CrudEditor
        self.app.push_screen(
            CrudEditor(player=self.player, save_id=self.save_id,
                       on_save=self._on_attr_saved)
        )

    def action_set_override(self) -> None:
        """快捷键 D：直接打开编辑器的「指定数据」tab。"""
        from ui.screens.crud_editor import CrudEditor
        self.app.push_screen(
            CrudEditor(player=self.player, save_id=self.save_id,
                       on_save=self._on_attr_saved)
        )

    def action_new_player(self) -> None:
        from ui.screens.create_player import CreatePlayer
        self.app.push_screen(CreatePlayer())

    def action_open_html(self) -> None:
        from web.html_report import generate_and_open
        generate_and_open(self.player.player_id, self.save_id)

    def _on_attr_saved(self) -> None:
        """CRUD 保存后刷新球员卡。"""
        attrs = self._load_attrs()
        card  = self.query_one("#player-card", PlayerCard)
        ws    = self._current_wr.week_summary if self._current_wr else None
        card.refresh_attrs(attrs, ws)

    def action_quit_game(self) -> None:
        # 弹出所有屏幕回到主菜单
        self.app.pop_screen()   # 回到 player_select
        self.app.pop_screen()   # 回到 main_menu
