"""
种子数据导入脚本。
运行方式：python -m seeding.seed_runner [--force] [--quick]

--force  : 忽略本地缓存，重新从 nba_api 拉取
--quick  : 只导入球队+球员基础信息，跳过详细info和职业生涯统计（快速测试用）
"""
import sys
import argparse

from database.schema import init_database
from database.repositories.team_repo import TeamRepository
from database.repositories.player_repo import PlayerRepository
from seeding.nba_api_fetcher import (
    fetch_all_teams,
    fetch_all_active_players,
    fetch_player_info,
    fetch_player_career_stats,
    fetch_team_roster,
)
from seeding.data_transformer import (
    transform_team,
    transform_player_basic,
    transform_player_detail,
    derive_attributes,
)
from config import CURRENT_SEASON_YEAR


# ── 球队数据映射（补充 conference/division，静态 API 不含） ──────────────────
TEAM_CONFERENCE = {
    1610612737: ("East", "Southeast"), 1610612738: ("East", "Atlantic"),
    1610612739: ("East", "Central"),   1610612740: ("West", "Southwest"),
    1610612741: ("East", "Central"),   1610612742: ("West", "Southwest"),
    1610612743: ("West", "Northwest"), 1610612744: ("West", "Pacific"),
    1610612745: ("West", "Southwest"), 1610612746: ("West", "Pacific"),
    1610612747: ("West", "Pacific"),   1610612748: ("East", "Southeast"),
    1610612749: ("East", "Central"),   1610612750: ("West", "Northwest"),
    1610612751: ("East", "Atlantic"),  1610612752: ("East", "Atlantic"),
    1610612753: ("East", "Southeast"), 1610612754: ("East", "Central"),
    1610612755: ("East", "Atlantic"),  1610612756: ("West", "Pacific"),
    1610612757: ("West", "Northwest"), 1610612758: ("West", "Pacific"),
    1610612759: ("West", "Southwest"), 1610612760: ("West", "Northwest"),
    1610612761: ("East", "Atlantic"),  1610612762: ("West", "Northwest"),
    1610612763: ("West", "Southwest"), 1610612764: ("East", "Southeast"),
    1610612765: ("East", "Central"),   1610612766: ("East", "Southeast"),
}

TEAM_ARENA = {
    1610612737: "State Farm Arena",      1610612738: "TD Garden",
    1610612739: "Rocket Mortgage FieldHouse", 1610612740: "Smoothie King Center",
    1610612741: "United Center",         1610612742: "American Airlines Center",
    1610612743: "Ball Arena",            1610612744: "Chase Center",
    1610612745: "Toyota Center",         1610612746: "Crypto.com Arena",
    1610612747: "Crypto.com Arena",      1610612748: "Kaseya Center",
    1610612749: "Fiserv Forum",          1610612750: "Target Center",
    1610612751: "Barclays Center",       1610612752: "Madison Square Garden",
    1610612753: "Kia Center",            1610612754: "Gainbridge Fieldhouse",
    1610612755: "Wells Fargo Center",    1610612756: "Footprint Center",
    1610612757: "Moda Center",           1610612758: "Golden 1 Center",
    1610612759: "Frost Bank Center",     1610612760: "Paycom Center",
    1610612761: "Scotiabank Arena",      1610612762: "Delta Center",
    1610612763: "FedExForum",            1610612764: "Capital One Arena",
    1610612765: "Little Caesars Arena",  1610612766: "Spectrum Center",
}


def seed_teams(repo: TeamRepository, force: bool) -> None:
    print("\n[1/3] 导入球队数据...")
    raw_teams = fetch_all_teams(force=force)
    for raw in raw_teams:
        team = transform_team(raw)
        tid = team["team_id"]
        if tid in TEAM_CONFERENCE:
            team["conference"], team["division"] = TEAM_CONFERENCE[tid]
        if tid in TEAM_ARENA:
            team["arena"] = TEAM_ARENA[tid]
        repo.upsert(team)
    print(f"  [OK] {len(raw_teams)} 支球队写入完成")


def seed_players(
    player_repo: PlayerRepository,
    force: bool,
    quick: bool,
) -> None:
    print("\n[2/3] 导入球员基础信息...")
    raw_players = fetch_all_active_players(force=force)
    total = len(raw_players)

    for i, raw in enumerate(raw_players, 1):
        basic = transform_player_basic(raw)
        pid = basic["player_id"]

        if not quick:
            info = fetch_player_info(pid)
            player_data = transform_player_detail(basic, info)
        else:
            player_data = basic

        player_repo.upsert(player_data)

        if i % 50 == 0 or i == total:
            print(f"  进度：{i}/{total} 球员")

    print(f"  [OK] {total} 名球员写入完成")


def seed_attributes(
    player_repo: PlayerRepository,
    force: bool,
    quick: bool,
) -> None:
    print("\n[3/3] 推算球员初始属性...")
    players = player_repo.get_all(active_only=True)
    total = len(players)

    for i, p in enumerate(players, 1):
        # 已有该赛季属性则跳过（除非 force）
        if not force and player_repo.get_attributes(p.player_id, CURRENT_SEASON_YEAR):
            continue

        career = None
        if not quick:
            career = fetch_player_career_stats(p.player_id)

        attrs = derive_attributes(
            player_id=p.player_id,
            position=p.position,
            career_stats=career,
            season_year=CURRENT_SEASON_YEAR,
        )
        player_repo.upsert_attributes(attrs)

        if i % 50 == 0 or i == total:
            print(f"  进度：{i}/{total} 属性")

    print(f"  [OK] 属性推算完成")


def run(force: bool = False, quick: bool = False) -> None:
    print("=" * 50)
    print("  NBA 模拟器 — 数据初始化")
    print("=" * 50)

    # 确保数据库和表存在
    init_database()

    team_repo   = TeamRepository()
    player_repo = PlayerRepository()

    seed_teams(team_repo, force)
    seed_players(player_repo, force, quick)
    seed_attributes(player_repo, force, quick)

    p_count = player_repo.count()
    t_count = len(team_repo.get_all())
    print(f"\n{'='*50}")
    print(f"  完成！球队：{t_count} 支 | 现役球员：{p_count} 人")
    print(f"  数据库：{__import__('config').DB_PATH}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NBA 模拟器数据导入")
    parser.add_argument("--force", action="store_true", help="忽略缓存，重新拉取")
    parser.add_argument("--quick", action="store_true", help="跳过详细info，快速导入")
    args = parser.parse_args()
    run(force=args.force, quick=args.quick)
