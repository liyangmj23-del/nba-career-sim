"""
NBA 模拟器 — Rich CLI 游戏入口
运行方式：python play.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from rich.rule import Rule
from rich import box

from database.schema import init_database
from database.repositories.player_repo import PlayerRepository
from database.repositories.team_repo import TeamRepository
from database.repositories.save_repo import SaveRepository, SaveState
from database.repositories.event_log_repo import EventLogRepository
from simulation.engine import run_season, WeekResult
from config import CURRENT_SEASON_YEAR

console = Console(width=90)

# ── 颜色映射 ─────────────────────────────────────────────────────────────────
SEVERITY_COLOR = {
    "minor":     "dim white",
    "normal":    "white",
    "major":     "bold yellow",
    "legendary": "bold gold1",
}

CATEGORY_ICON = {
    "game_performance":  "[cyan]比赛[/]",
    "injury":            "[red]伤病[/]",
    "personal_life":     "[magenta]个人[/]",
    "team_chemistry":    "[blue]球队[/]",
    "career_milestones": "[gold1]里程碑[/]",
    "off_court":         "[green]场外[/]",
}


# ── 显示函数 ──────────────────────────────────────────────────────────────────

def show_player_card(player, attrs: dict) -> None:
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column("label", style="dim", width=14)
    t.add_column("val",   style="bold white")
    t.add_column("label", style="dim", width=14)
    t.add_column("val",   style="bold white")

    t.add_row("综合评级", f"[bold cyan]{attrs.get('overall_rating',50)}[/]",
              "位置", player.position or "-")
    t.add_row("得分能力",
              f"2P:{attrs.get('shooting_2pt',50)} 3P:{attrs.get('shooting_3pt',50)} FT:{attrs.get('free_throw',50)}",
              "传球/控球",
              f"{attrs.get('passing',50)} / {attrs.get('ball_handling',50)}")
    t.add_row("身体素质",
              f"速:{attrs.get('speed',50)} 力:{attrs.get('strength',50)} 弹:{attrs.get('vertical',50)}",
              "防守",
              f"外:{attrs.get('perimeter_def',50)} 内:{attrs.get('interior_def',50)}")
    t.add_row("状态",
              f"体力[green]{attrs.get('health',100)}[/] 疲劳[yellow]{attrs.get('fatigue',0)}[/] 士气[magenta]{attrs.get('morale',75)}[/]",
              "心理IQ",
              f"{attrs.get('basketball_iq',50)} / 关键{attrs.get('clutch_factor',50)}")

    console.print(Panel(t, title=f"[bold white]{player.full_name}[/]", border_style="cyan"))


def show_week_header(week: int, season_year: int) -> None:
    console.print(Rule(
        f"[bold]第 {week} 周  ·  {season_year-1}-{str(season_year)[2:]} 赛季[/]",
        style="dim blue"
    ))


def show_games(wr: WeekResult) -> None:
    s = wr.week_summary
    wins  = s.get("wins", 0)
    total = s.get("games_this_week", 0)
    result_color = "green" if wins == total else ("yellow" if wins > 0 else "red")

    console.print(
        f"  本周战绩  [{result_color}]{wins}胜{total-wins}负[/]  "
        f"[cyan]{s.get('pts',0):.1f}分[/] "
        f"[white]{s.get('reb',0):.1f}篮 {s.get('ast',0):.1f}助[/] "
        f"FG [dim]{int(s.get('fg_made_total',0))}/{int(s.get('fg_att_total',0))}[/] "
        f"({s.get('fg_pct',0)*100:.0f}%)"
    )


def show_event(fe) -> None:
    ev    = fe.event_def
    color = SEVERITY_COLOR.get(ev.severity, "white")
    icon  = CATEGORY_ICON.get(ev.category, "")

    # 属性变化摘要
    delta_parts = []
    for attr, d in fe.attribute_delta.items():
        sign   = "+" if d > 0 else ""
        dcol   = "green" if d > 0 else "red"
        labels = {
            "morale": "士气", "health": "体力", "fatigue": "疲劳",
            "speed": "速度", "strength": "力量", "vertical": "弹跳",
            "endurance": "耐力", "shooting_2pt": "2分", "shooting_3pt": "3分",
            "free_throw": "罚球", "passing": "传球", "ball_handling": "控球",
            "perimeter_def": "外防", "interior_def": "内防",
            "basketball_iq": "IQ", "clutch_factor": "关键",
            "leadership": "领袖", "work_ethic": "勤奋", "media_handling": "媒体",
            "block_tendency": "盖帽", "steal_tendency": "抢断",
            "post_moves": "背打",
        }
        label = labels.get(attr, attr)
        delta_parts.append(f"[{dcol}]{sign}{d} {label}[/]")

    delta_str = "  ".join(delta_parts) if delta_parts else ""

    # 标题行
    console.print(f"\n  {icon} [{color}]{ev.title}[/]")

    # 叙事正文（每段缩进）
    for line in fe.narrative.strip().split("\n"):
        if line.strip():
            console.print(f"  [dim]{line}[/]")
        else:
            console.print()

    if delta_str:
        console.print(f"\n  {delta_str}\n")


def show_season_stats(stats: dict) -> None:
    gp = stats.get("games_played", 0)
    if gp == 0:
        return
    console.print(
        f"  [dim]赛季累计  G[/][bold]{gp}[/]  "
        f"[dim]得分[/][bold cyan]{stats.get('pts',0):.1f}[/]  "
        f"[dim]篮板[/][bold]{stats.get('reb',0):.1f}[/]  "
        f"[dim]助攻[/][bold]{stats.get('ast',0):.1f}[/]  "
        f"[dim]FG%[/][bold]{stats.get('fg_pct',0)*100:.1f}%[/]  "
        f"[dim]3P%[/][bold]{stats.get('fg3_pct',0)*100:.1f}%[/]"
    )


# ── 搜索并选择球员 ────────────────────────────────────────────────────────────

def pick_player():
    repo = PlayerRepository()
    while True:
        query = Prompt.ask("\n[bold]输入球员姓名搜索[/] (例: LeBron, Curry, Durant)")
        results = repo.search(query)
        if not results:
            console.print("[red]未找到，请重试[/]")
            continue
        t = Table(box=box.SIMPLE_HEAVY, show_header=True)
        t.add_column("#",       style="dim", width=4)
        t.add_column("姓名",   style="bold white", width=24)
        t.add_column("位置",   width=6)
        t.add_column("综合",   width=6)
        t.add_column("球队ID", width=10)
        for i, p in enumerate(results[:10], 1):
            # 尝试拿属性
            attr = repo.get_attributes(p.player_id, CURRENT_SEASON_YEAR)
            overall = str(attr.overall_rating) if attr else "-"
            t.add_row(str(i), p.full_name, p.position or "-",
                      overall, str(p.current_team_id or "-"))
        console.print(t)
        choice = IntPrompt.ask(f"选择 1-{min(len(results),10)}", default=1)
        idx = max(1, min(choice, len(results[:10]))) - 1
        return results[idx]


# ── 创建新存档 ────────────────────────────────────────────────────────────────

def new_game():
    console.print(Panel("[bold cyan]开始新的生涯[/]", border_style="cyan"))
    player = pick_player()

    save_repo  = SaveRepository()
    player_repo = PlayerRepository()

    # 确保属性存在
    attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
    if not attr:
        console.print("[yellow]该球员暂无属性数据，将使用默认值[/]")
        from simulation.attribute_calculator import compute_overall
        from seeding.data_transformer import derive_attributes
        attrs_data = derive_attributes(player.player_id, player.position, None)
        player_repo.upsert_attributes(attrs_data)
        attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)

    import datetime
    save_name = f"{player.full_name} · {datetime.date.today()}"
    save_id = save_repo.create({
        "save_name":       save_name,
        "player_id":       player.player_id,
        "current_team_id": player.current_team_id,
        "current_season":  CURRENT_SEASON_YEAR,
        "current_week":    1,
        "current_age":     _calc_age(player.birthdate),
        "career_year":     1,
        "state_json":      {},
    })
    console.print(f"\n[green]存档创建成功[/]  ID={save_id}  球员：{player.full_name}\n")
    return save_id, player


def _calc_age(birthdate: str | None) -> int | None:
    if not birthdate:
        return None
    try:
        import datetime
        bd = datetime.date.fromisoformat(birthdate[:10])
        today = datetime.date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        return None


# ── 加载存档 ──────────────────────────────────────────────────────────────────

def load_game():
    save_repo   = SaveRepository()
    player_repo = PlayerRepository()
    saves       = save_repo.get_all()
    if not saves:
        console.print("[yellow]没有存档，请先开始新游戏[/]")
        return None, None

    t = Table(box=box.SIMPLE_HEAVY)
    t.add_column("#",    style="dim", width=4)
    t.add_column("存档名", width=30)
    t.add_column("赛季",  width=8)
    t.add_column("第N周", width=8)
    for i, s in enumerate(saves[:8], 1):
        t.add_row(str(i), s.save_name, str(s.current_season), str(s.current_week))
    console.print(t)
    choice = IntPrompt.ask(f"选择 1-{min(len(saves),8)}", default=1)
    idx  = max(1, min(choice, len(saves[:8]))) - 1
    save = saves[idx]
    player = player_repo.get_by_id(save.player_id)
    return save.save_id, player


# ── 主游戏循环 ────────────────────────────────────────────────────────────────

def play_season(save_id: int, player):
    player_repo = PlayerRepository()
    console.print(Panel(
        f"[bold]赛季模拟开始[/]\n{player.full_name}  ·  {CURRENT_SEASON_YEAR-1}-{str(CURRENT_SEASON_YEAR)[2:]} 赛季",
        border_style="blue",
    ))
    console.print("[dim]按 Enter 推进一周  |  输入 q 存档退出  |  输入 s 查看赛季数据[/]\n")

    try:
        for wr in run_season(save_id, CURRENT_SEASON_YEAR):
            show_week_header(wr.week, wr.season_year)
            show_games(wr)

            # 显示事件
            if wr.events:
                for fe in wr.events:
                    show_event(fe)
            else:
                console.print("  [dim]本周平静，无特殊事件。[/]")

            show_season_stats(wr.season_stats)

            # 每隔5周显示属性卡片
            if wr.week % 5 == 0:
                console.print()
                show_player_card(player, wr.attrs_after)

            # 用户输入
            user_input = Prompt.ask("\n[dim]>[/]", default="").strip().lower()
            if user_input == "q":
                console.print("[yellow]已存档，下次继续。[/]")
                break
            elif user_input == "s":
                show_player_card(player, wr.attrs_after)

    except KeyboardInterrupt:
        console.print("\n[yellow]模拟中断，进度已自动保存。[/]")

    # 赛季结束
    console.print(Rule("[bold gold1]赛季结束[/]", style="gold1"))
    save_repo = SaveRepository()
    save = save_repo.get_by_id(save_id)
    if save:
        attr = player_repo.get_attributes(player.player_id, CURRENT_SEASON_YEAR)
        attrs_dict = {k: getattr(attr, k) for k in attr.__dataclass_fields__ if k not in ("attr_id","player_id","season_year")} if attr else {}
        show_player_card(player, attrs_dict)
        # 展示本赛季历史事件
        event_repo = EventLogRepository()
        events = event_repo.get_by_save(save_id, season_year=CURRENT_SEASON_YEAR, limit=30)
        if events:
            console.print("\n[bold]本赛季事件回顾[/]")
            for e in events:
                icon = CATEGORY_ICON.get(e.category, "")
                col  = SEVERITY_COLOR.get(e.severity, "white")
                console.print(f"  第{e.week_number}周 {icon} [{col}]{e.title}[/]")


# ── 主菜单 ────────────────────────────────────────────────────────────────────

def main():
    init_database()
    console.print(Panel(
        "[bold cyan]NBA 生涯模拟器[/]\n"
        "[dim]你的选择，你的故事[/]",
        border_style="cyan",
        padding=(1, 4),
    ))

    while True:
        console.print("\n  [bold]1[/] 开始新生涯")
        console.print("  [bold]2[/] 继续存档")
        console.print("  [bold]q[/] 退出\n")
        choice = Prompt.ask("[dim]>[/]", default="1").strip()

        if choice == "1":
            save_id, player = new_game()
            if player:
                attr_rec = PlayerRepository().get_attributes(player.player_id, CURRENT_SEASON_YEAR)
                if attr_rec:
                    attrs = {k: getattr(attr_rec, k) for k in attr_rec.__dataclass_fields__ if k not in ("attr_id","player_id","season_year")}
                    show_player_card(player, attrs)
                play_season(save_id, player)

        elif choice == "2":
            save_id, player = load_game()
            if save_id and player:
                play_season(save_id, player)

        elif choice in ("q", "quit", "exit"):
            console.print("[dim]再见！[/]")
            break


if __name__ == "__main__":
    main()
