"""
快速修复：从 nba_api 拉取各队名单，补全 players.current_team_id。
只请求 30 支球队的名单接口，不逐个请求球员详情，速度快。
运行方式：python -m seeding.fix_team_assignments
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db
from config import API_REQUEST_DELAY


TEAMS = [
    1610612737,1610612738,1610612739,1610612740,1610612741,
    1610612742,1610612743,1610612744,1610612745,1610612746,
    1610612747,1610612748,1610612749,1610612750,1610612751,
    1610612752,1610612753,1610612754,1610612755,1610612756,
    1610612757,1610612758,1610612759,1610612760,1610612761,
    1610612762,1610612763,1610612764,1610612765,1610612766,
]


def fix_assignments(season: str = "2024-25") -> None:
    print("=" * 55)
    print("  补全球员球队归属（current_team_id）")
    print("=" * 55)

    total_updated = 0

    for i, team_id in enumerate(TEAMS, 1):
        try:
            from nba_api.stats.endpoints import commonteamroster
            time.sleep(API_REQUEST_DELAY)
            roster = commonteamroster.CommonTeamRoster(
                team_id=team_id, season=season
            )
            data    = roster.common_team_roster.get_dict()
            headers = data["headers"]
            rows    = data["data"]

            pid_idx  = headers.index("PLAYER_ID")
            name_idx = headers.index("PLAYER") if "PLAYER" in headers else -1

            updated = 0
            with db() as conn:
                for row in rows:
                    player_id = row[pid_idx]
                    conn.execute(
                        "UPDATE players SET current_team_id=? WHERE player_id=?",
                        (team_id, player_id),
                    )
                    updated += 1

            total_updated += updated
            print(f"  [{i:2}/30] team={team_id}  更新 {updated} 名球员")

        except Exception as e:
            print(f"  [{i:2}/30] team={team_id}  失败: {e}")

    print(f"\n[OK] 完成，共更新 {total_updated} 条球员球队归属")
    print("  重启 run_web.py 后 Box Score 将显示真实球队名单\n")


if __name__ == "__main__":
    fix_assignments()
