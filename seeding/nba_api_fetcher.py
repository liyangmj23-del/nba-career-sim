"""
从 nba_api 拉取数据并缓存到本地 JSON。
断网后使用缓存，不影响游戏运行。
"""
import json
import time
from pathlib import Path
from config import SEED_CACHE_DIR, API_REQUEST_DELAY


def _cache_path(name: str) -> Path:
    return SEED_CACHE_DIR / f"{name}.json"


def _load_cache(name: str):
    p = _cache_path(name)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def _save_cache(name: str, data) -> None:
    _cache_path(name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def fetch_all_teams(force: bool = False) -> list[dict]:
    """拉取全部 NBA 球队（30支）。"""
    if not force:
        cached = _load_cache("teams")
        if cached:
            print("  [缓存] 球队数据已存在，跳过请求")
            return cached

    from nba_api.stats.static import teams as nba_teams
    data = nba_teams.get_teams()
    _save_cache("teams", data)
    print(f"  [API] 获取球队：{len(data)} 支")
    return data


def fetch_all_active_players(force: bool = False) -> list[dict]:
    """拉取全部现役球员基础信息。"""
    if not force:
        cached = _load_cache("players_basic")
        if cached:
            print(f"  [缓存] 球员基础数据已存在：{len(cached)} 人")
            return cached

    from nba_api.stats.static import players as nba_players
    data = nba_players.get_active_players()
    _save_cache("players_basic", data)
    print(f"  [API] 获取现役球员：{len(data)} 人")
    return data


def fetch_player_info(player_id: int) -> dict | None:
    """
    拉取单个球员的详细信息（身高体重、出生日期、选秀信息等）。
    有本地缓存则跳过。
    """
    cache_name = f"player_info_{player_id}"
    cached = _load_cache(cache_name)
    if cached:
        return cached

    try:
        from nba_api.stats.endpoints import commonplayerinfo
        time.sleep(API_REQUEST_DELAY)
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        row = info.common_player_info.get_dict()["data"][0]
        headers = info.common_player_info.get_dict()["headers"]
        data = dict(zip(headers, row))
        _save_cache(cache_name, data)
        return data
    except Exception as e:
        print(f"  [警告] player_info {player_id} 失败：{e}")
        return None


def fetch_player_career_stats(player_id: int) -> dict | None:
    """
    拉取球员历史赛季统计（用于推算初始属性）。
    """
    cache_name = f"player_career_{player_id}"
    cached = _load_cache(cache_name)
    if cached:
        return cached

    try:
        from nba_api.stats.endpoints import playercareerstats
        time.sleep(API_REQUEST_DELAY)
        stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        data = {
            "regular": stats.season_totals_regular_season.get_dict(),
        }
        _save_cache(cache_name, data)
        return data
    except Exception as e:
        print(f"  [警告] career_stats {player_id} 失败：{e}")
        return None


def fetch_team_roster(team_id: int, season: str = "2024-25") -> list[dict] | None:
    """拉取某球队当前赛季名单，用于关联 current_team_id。"""
    cache_name = f"roster_{team_id}_{season.replace('-','_')}"
    cached = _load_cache(cache_name)
    if cached:
        return cached

    try:
        from nba_api.stats.endpoints import commonteamroster
        time.sleep(API_REQUEST_DELAY)
        roster = commonteamroster.CommonTeamRoster(
            team_id=team_id, season=season
        )
        data = roster.common_team_roster.get_dict()
        rows = [
            dict(zip(data["headers"], row))
            for row in data["data"]
        ]
        _save_cache(cache_name, rows)
        return rows
    except Exception as e:
        print(f"  [警告] roster {team_id} 失败：{e}")
        return None
