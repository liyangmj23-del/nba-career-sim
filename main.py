"""
[已废弃] Textual UI 启动入口。
v0.2.0 起已切换为 Web 版，请使用：python run_web.py
保留此文件仅供参考，不再维护。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import NBASimApp


def main():
    app = NBASimApp()
    app.run()


if __name__ == "__main__":
    main()
