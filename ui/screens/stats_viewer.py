"""
数据查看器：当前赛季统计 / 生涯事件日志 / 属性快照。
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, DataTable, TabbedContent, TabPane
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from database.repositories.player_repo import PlayerRepository
from database.repositories.event_log_repo import EventLogRepository
from config import CURRENT_SEASON_YEAR

ATTR_LABELS = {
    "speed": "速度", "strength": "力量", "vertical": "弹跳", "endurance": "耐力",
    "ball_handling": "控球", "shooting_2pt": "两分", "shooting_3pt": "三分",
    "free_throw": "罚球", "passing": "传球", "post_moves": "背打",
    "perimeter_def": "外防", "interior_def": "内防",
    "steal_tendency": "抢断", "block_tendency": "盖帽",
    "basketball_iq": "IQ", "clutch_factor": "关键时刻",
    "leadership": "领导力", "work_ethic": "勤奋",
    "media_handling": "媒体应对", "overall_rating": "综合评级",
    "health": "体力", "morale": "士气", "fatigue": "疲劳",
}


class StatsViewer(Screen):
    """数据查看屏幕（Escape 返回）。"""

    BINDINGS = [
        Binding("escape", "go_back", "返回", show=True),
    ]

    DEFAULT_CSS = """
    StatsViewer {
        layout: vertical;
        background: #0a0a12;
    }
    #stats-header {
        dock: top;
        height: 2;
        background: #06060f;
        border-bottom: solid #1a1a30;
        padding: 0 2;
        color: #4dc3ff;
        text-style: bold;
        content-align: left middle;
    }
    TabbedContent {
        height: 1fr;
        background: #0a0a12;
    }
    TabPane {
        background: #0a0a12;
        padding: 1 2;
    }
    DataTable {
        background: #08080f;
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

    def __init__(self, player, save_id: int, **kwargs):
        super().__init__(**kwargs)
        self.player  = player
        self.save_id = save_id

    def compose(self) -> ComposeResult:
        yield Static(
            f"  数据中心  ·  {self.player.full_name}",
            id="stats-header",
        )

        with TabbedContent():
            with TabPane("赛季数据", id="tab-season"):
                yield DataTable(id="season-table", cursor_type="row")

            with TabPane("属性详情", id="tab-attrs"):
                yield DataTable(id="attrs-table", cursor_type="row")

            with TabPane("事件历史", id="tab-events"):
                yield DataTable(id="events-table", cursor_type="row")

            with TabPane("荣誉 & 里程碑", id="tab-milestones"):
                yield DataTable(id="milestones-table", cursor_type="row")

            with TabPane("逐场数据", id="tab-gamelog"):
                yield DataTable(id="gamelog-table", cursor_type="row")

            with TabPane("生涯总计", id="tab-career"):
                yield DataTable(id="career-table", cursor_type="row")

            with TabPane("历史地位", id="tab-history"):
                from textual.widgets import RichLog
                yield RichLog(id="history-log", markup=True, max_lines=500)

        with Horizontal(id="back-bar"):
            yield Button("返回游戏  [Esc]", id="btn-back", classes="back-btn")
            yield Button("导出 HTML 数据报告", id="btn-html", classes="back-btn")

    def on_mount(self) -> None:
        self._load_season_data()
        self._load_attrs_data()
        self._load_events_data()
        self._load_milestones_data()
        self._load_gamelog_data()
        self._load_career_data()
        self._load_history_data()

    # ── 赛季统计 ──────────────────────────────────────────────────────────────

    def _load_season_data(self) -> None:
        from database.connection import db
        table = self.query_one("#season-table", DataTable)
        table.add_columns("赛季", "场次", "得分", "篮板", "助攻", "抢断", "盖帽", "失误", "FG%", "3P%", "FT%")

        with db() as conn:
            rows = conn.execute(
                """SELECT season_year, games_played, points_pg, rebounds_pg,
                          assists_pg, steals_pg, blocks_pg, turnovers_pg,
                          fg_pct, fg3_pct, ft_pct
                   FROM player_season_stats
                   WHERE player_id=? ORDER BY season_year DESC""",
                (self.player.player_id,),
            ).fetchall()

        if not rows:
            table.add_row("暂无数据", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-")
            return

        for r in rows:
            table.add_row(
                f"{r[0]-1}-{str(r[0])[2:]}",
                str(r[1]),
                f"{r[2]:.1f}",
                f"{r[3]:.1f}",
                f"{r[4]:.1f}",
                f"{r[5]:.1f}",
                f"{r[6]:.1f}",
                f"{r[7]:.1f}",
                f"{r[8]*100:.1f}%",
                f"{r[9]*100:.1f}%",
                f"{r[10]*100:.1f}%",
            )

    # ── 属性详情 ──────────────────────────────────────────────────────────────

    def _load_attrs_data(self) -> None:
        repo  = PlayerRepository()
        table = self.query_one("#attrs-table", DataTable)
        table.add_columns("属性", "数值", "评级", "可视化")

        attr = repo.get_attributes(self.player.player_id, CURRENT_SEASON_YEAR)
        if not attr:
            table.add_row("暂无属性数据", "-", "-", "-")
            return

        skip = {"attr_id", "player_id", "season_year"}
        for field_name in attr.__dataclass_fields__:
            if field_name in skip:
                continue
            val = getattr(attr, field_name)
            label = ATTR_LABELS.get(field_name, field_name)
            # 评级
            if val >= 85:   rating = "精英"
            elif val >= 75: rating = "优秀"
            elif val >= 65: rating = "良好"
            elif val >= 50: rating = "普通"
            else:           rating = "较弱"
            # 进度条
            bar = "\u2588" * (val // 10) + "\u2591" * (10 - val // 10)
            table.add_row(label, str(val), rating, bar)

    # ── 事件历史 ──────────────────────────────────────────────────────────────

    def _load_events_data(self) -> None:
        repo  = EventLogRepository()
        table = self.query_one("#events-table", DataTable)
        table.add_columns("周", "类型", "等级", "标题")

        events = repo.get_by_save(self.save_id, limit=100)
        if not events:
            table.add_row("-", "-", "-", "暂无事件记录")
            return

        CAT_MAP = {
            "game_performance": "比赛", "injury": "伤病",
            "personal_life": "个人", "team_chemistry": "球队",
            "career_milestones": "里程碑", "off_court": "场外",
        }
        SEV_MAP = {
            "minor": "轻微", "normal": "普通",
            "major": "重大", "legendary": "传奇",
        }
        for e in events:
            table.add_row(
                f"第{e.week_number}周",
                CAT_MAP.get(e.category, e.category),
                SEV_MAP.get(e.severity, e.severity),
                e.title,
            )

    # ── 生涯里程碑 ────────────────────────────────────────────────────────────

    def _load_milestones_data(self) -> None:
        repo  = EventLogRepository()
        table = self.query_one("#milestones-table", DataTable)
        table.add_columns("赛季", "周", "里程碑")

        milestones = repo.get_milestones(self.save_id)
        if not milestones:
            table.add_row("-", "-", "暂无里程碑")
            return

        for m in milestones:
            table.add_row(
                f"{m.season_year-1}-{str(m.season_year)[2:]}",
                f"第{m.week_number}周",
                m.title,
            )

    # ── 逐场数据 ──────────────────────────────────────────────────────────────

    def _load_gamelog_data(self) -> None:
        from database.connection import db as getdb
        table = self.query_one("#gamelog-table", DataTable)
        table.add_columns(
            "周", "场", "主/客", "对手",
            "胜负", "分", "篮", "助", "断", "帽", "失",
            "FG", "FG%", "3P", "3P%", "FT", "FT%", "+/-",
        )

        with getdb() as conn:
            rows = conn.execute(
                """SELECT gl.game_week, gl.game_number, gl.is_home,
                          gl.opponent_team_id, gl.player_won,
                          gl.points, gl.rebounds, gl.assists,
                          gl.steals, gl.blocks, gl.turnovers,
                          gl.fg_made, gl.fg_attempted,
                          gl.fg3_made, gl.fg3_attempted,
                          gl.ft_made, gl.ft_attempted, gl.plus_minus,
                          t.abbreviation
                   FROM player_game_log gl
                   LEFT JOIN teams t ON gl.opponent_team_id = t.team_id
                   WHERE gl.player_id = ?
                   ORDER BY gl.game_number""",
                (self.player.player_id,),
            ).fetchall()

        if not rows:
            table.add_row("-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "暂无比赛记录")
            return

        for r in rows:
            (week, gnum, is_home, opp_id, won,
             pts, reb, ast, stl, blk, tov,
             fgm, fga, fg3m, fg3a, ftm, fta, pm,
             opp_abbr) = r

            home_away = "主" if is_home else "客"
            result    = "[green]W[/]" if won else "[red]L[/]"
            opp_name  = opp_abbr or str(opp_id)
            fg_pct    = f"{fgm/fga*100:.0f}%" if fga else "-"
            fg3_pct   = f"{fg3m/fg3a*100:.0f}%" if fg3a else "-"
            ft_pct    = f"{ftm/fta*100:.0f}%" if fta else "-"
            pm_str    = f"+{pm}" if pm > 0 else str(pm)

            table.add_row(
                f"第{week}周", f"G{gnum}", home_away, opp_name,
                result, str(pts), str(reb), str(ast), str(stl), str(blk), str(tov),
                f"{fgm}/{fga}", fg_pct, f"{fg3m}/{fg3a}", fg3_pct, f"{ftm}/{fta}", ft_pct,
                pm_str,
            )

    # ── HTML 导出 ────────────────────────────────────────────────────────────

    def _export_html(self) -> None:
        from web.html_report import generate_and_open
        generate_and_open(self.player.player_id, self.save_id)

    # ── 生涯总计 ──────────────────────────────────────────────────────────────

    def _load_career_data(self) -> None:
        from simulation.historical_standing import get_career_totals, NBA_CAREER_RECORDS
        table = self.query_one("#career-table", DataTable)
        table.add_columns("统计项", "生涯总计", "生涯场均", "历史记录", "记录保持者", "占比%")

        totals = get_career_totals(self.player.player_id, self.save_id)

        if totals["seasons"] == 0:
            table.add_row("暂无数据", "-", "-", "-", "-", "-")
            return

        # 汇总行
        table.add_row(
            "赛季数",
            str(totals["seasons"]),
            "-",
            "-",
            "-",
            "-",
        )
        table.add_row(
            "出场数",
            str(totals["games"]),
            "-",
            str(NBA_CAREER_RECORDS["gp"]["record"]),
            NBA_CAREER_RECORDS["gp"]["holder"],
            f"{totals['games']/NBA_CAREER_RECORDS['gp']['record']*100:.1f}%",
        )

        field_map = [
            ("pts", "总得分",   "avg_pts", "分"),
            ("reb", "总篮板",   "avg_reb", "板"),
            ("ast", "总助攻",   "avg_ast", "助"),
            ("stl", "总抢断",   "avg_stl", "断"),
            ("blk", "总盖帽",   "avg_blk", "帽"),
        ]
        for key, label, avg_key, unit in field_map:
            val  = totals[key]
            avg  = totals[avg_key]
            rec  = NBA_CAREER_RECORDS[key]
            pct  = val / rec["record"] * 100 if rec["record"] else 0
            flag = " ★历史记录！" if val >= rec["record"] else ""
            table.add_row(
                label,
                f"{round(val):,}{unit}{flag}",
                f"{avg:.1f}{unit}/场",
                f"{rec['record']:,}{unit}",
                rec["holder"],
                f"{pct:.1f}%",
            )

        # 生涯荣誉合计
        from simulation.achievement_tracker import count_awards, AWARD_LABELS
        awards = count_awards(self.save_id)
        if awards:
            table.add_row("─" * 6, "─" * 8, "─" * 6, "─" * 8, "─" * 14, "─" * 6)
            for award_type, cnt in sorted(awards.items(), key=lambda x: -x[1]):
                label = AWARD_LABELS.get(award_type, award_type)
                table.add_row(label, f"{cnt} 次", "-", "-", "-", "-")

    # ── 历史地位 ──────────────────────────────────────────────────────────────

    def _load_history_data(self) -> None:
        from textual.widgets import RichLog
        from simulation.historical_standing import build_historical_report, get_historical_tier

        log = self.query_one("#history-log", RichLog)
        report = build_historical_report(
            self.save_id, self.player.player_id, self.player.full_name
        )

        tier  = report["tier"]
        score = report["hof_score"]

        # 等级颜色
        tier_color = {
            "前无古人": "bold gold1",
            "历史 GOAT": "bold gold1",
            "名人堂第一": "bold yellow",
            "名人堂": "yellow",
            "全明星级": "cyan",
            "联盟长期": "white",
        }
        tcol = next((v for k, v in tier_color.items() if k in tier), "dim white")

        log.write(f"\n  [{tcol}]★ {tier}[/]  [dim]HOF积分：{score:.0f}[/]\n")
        log.write(f"  [dim]球员：[/][bold]{report['player_name']}[/]  "
                  f"[dim]生涯 {report['totals']['seasons']} 赛季 "
                  f"{report['totals']['games']} 场[/]\n")

        # 生涯数据与历史记录对比
        log.write("\n  [bold cyan]── 生涯数据 vs 历史记录 ──────────────────[/]\n")
        for comp in report["comparisons"]:
            pct    = comp["pct"]
            status = comp["status"]
            bar_w  = min(30, round(pct / 100 * 30))
            bar    = "\u2588" * bar_w + "\u2591" * (30 - bar_w)
            pcol   = "gold1" if pct >= 100 else ("yellow" if pct >= 70 else "cyan")
            log.write(
                f"  [dim]{comp['label']:4}[/] [{pcol}]{bar}[/] "
                f"[bold]{round(comp['value']):>8,}[/] / {comp['record']:,}  "
                f"[dim]{comp['holder']}[/]"
            )
            if status:
                log.write(f"       [{pcol}]{status}[/]")

        # 生涯里程碑
        if report["milestones"]:
            log.write("\n  [bold cyan]── 生涯里程碑 ─────────────────────────────[/]\n")
            for m in report["milestones"]:
                log.write(f"  [gold1]✦[/] {m}")

        # 荣誉列表
        awards_cnt = report["awards_count"]
        if awards_cnt:
            log.write("\n  [bold cyan]── 荣誉汇总 ────────────────────────────────[/]\n")
            from simulation.achievement_tracker import AWARD_LABELS
            for award_type, cnt in sorted(awards_cnt.items(), key=lambda x: -x[1]):
                label = AWARD_LABELS.get(award_type, award_type)
                col   = "gold1" if cnt >= 3 else ("yellow" if cnt >= 1 else "dim")
                log.write(f"  [{col}]{label}[/]  x{cnt}")

        # HOF 积分明细
        if report["breakdown"]:
            log.write("\n  [bold cyan]── HOF 积分明细 ─────────────────────────────[/]\n")
            for item, pts in sorted(report["breakdown"].items(), key=lambda x: -x[1]):
                from simulation.achievement_tracker import AWARD_LABELS
                label = AWARD_LABELS.get(item, item)
                log.write(f"  [dim]{label:<20}[/] +[bold]{pts:.1f}[/]")

    # ── 导航 ─────────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-html":
            self._export_html()

    def action_go_back(self) -> None:
        self.app.pop_screen()
