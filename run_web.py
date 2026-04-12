"""
NBA 生涯模拟器 —— Web 版启动脚本。
运行方式：python run_web.py
"""
import sys, webbrowser, threading, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from web.flask_app import app

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("=" * 50)
    print("  NBA 生涯模拟器  —  Web 版")
    print("  http://127.0.0.1:5000")
    print("  按 Ctrl+C 退出")
    print("=" * 50)
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
