"""
版本检查模块。
游戏启动时请求 GitHub Releases API，有新版本则在界面显示提示条。
"""
import threading
from pathlib import Path

# 修改为你的 GitHub 仓库地址
GITHUB_REPO = "liyangmj23-del/nba-career-sim"
GITHUB_API  = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
VERSION_FILE = Path(__file__).parent.parent / "VERSION"

_latest_info: dict = {}   # {"version": "0.2.0", "url": "...", "notes": "..."}
_checked = False


def _get_current_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "0.0.0"


def _parse_version(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def _fetch_latest():
    global _latest_info, _checked
    try:
        import urllib.request, json
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "nba-career-sim-updater/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        tag     = data.get("tag_name", "").lstrip("v")
        url     = data.get("html_url", "")
        body    = data.get("body", "")
        current = _get_current_version()
        if _parse_version(tag) > _parse_version(current):
            _latest_info = {
                "version":  tag,
                "current":  current,
                "url":      url,
                "notes":    body[:300] if body else "",
                "has_update": True,
            }
        else:
            _latest_info = {"has_update": False, "current": current}
    except Exception:
        _latest_info = {"has_update": False, "current": _get_current_version()}
    finally:
        _checked = True


def check_update_async():
    """在后台线程检查更新，不阻塞启动。"""
    if GITHUB_REPO.startswith("YOUR_"):
        return   # 未配置仓库地址，跳过
    t = threading.Thread(target=_fetch_latest, daemon=True)
    t.start()


def get_update_info() -> dict:
    """获取更新信息（供 Flask 路由返回给前端）。"""
    return dict(_latest_info)
