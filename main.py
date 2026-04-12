"""
NBA 生涯模拟器启动入口。
运行方式：python main.py
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
