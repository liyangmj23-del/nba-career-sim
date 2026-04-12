"""
Phase 1 验证脚本。
运行方式：python verify.py
检查数据库、球队、球员、属性是否都正常。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.schema import init_database
from database.repositories.team_repo import TeamRepository
from database.repositories.player_repo import PlayerRepository
from config import DB_PATH, CURRENT_SEASON_YEAR


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[OK]" if condition else "[XX]"
    print(f"  {status} {label}", end="")
    if detail:
        print(f"  →  {detail}", end="")
    print()
    return condition


def main():
    print("\n" + "=" * 55)
    print("  NBA 模拟器 — Phase 1 验证")
    print("=" * 55)

    ok = True

    # 1. 数据库文件存在
    ok &= check("数据库文件", DB_PATH.exists(), str(DB_PATH))

    # 2. 建表不报错
    try:
        init_database()
        ok &= check("建表 DDL", True)
    except Exception as e:
        ok &= check("建表 DDL", False, str(e))

    team_repo   = TeamRepository()
    player_repo = PlayerRepository()

    # 3. 球队数量
    teams = team_repo.get_all()
    ok &= check("球队总数 >= 30", len(teams) >= 30, f"{len(teams)} 支")

    # 4. 球队有 conference
    with_conf = [t for t in teams if t.conference]
    ok &= check("球队有 conference 字段", len(with_conf) > 0, f"{len(with_conf)} 支有数据")

    # 5. 球员数量
    players = player_repo.get_all()
    ok &= check("现役球员 >= 400", len(players) >= 400, f"{len(players)} 人")

    # 6. 示例球员查询
    results = player_repo.search("LeBron")
    ok &= check("搜索 LeBron 有结果", len(results) > 0,
                results[0].full_name if results else "无")

    # 7. 属性数据
    if results:
        lebron = results[0]
        attr = player_repo.get_attributes(lebron.player_id, CURRENT_SEASON_YEAR)
        ok &= check(
            "LeBron 有属性数据",
            attr is not None,
            f"overall={attr.overall_rating}" if attr else "无"
        )
        if attr:
            ok &= check(
                "属性值在合理范围",
                1 <= attr.overall_rating <= 99,
                f"1 ≤ {attr.overall_rating} ≤ 99"
            )

    # 8. Repository CRUD 基础操作
    team = team_repo.get_by_abbreviation("LAL")
    ok &= check("按缩写查球队 LAL", team is not None,
                team.full_name if team else "无")

    print("=" * 55)
    if ok:
        print("  全部通过！可以进入 Phase 2 模拟引擎开发。")
    else:
        print("  部分检查未通过，请先运行：")
        print("    python -m seeding.seed_runner --quick")
    print("=" * 55 + "\n")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
