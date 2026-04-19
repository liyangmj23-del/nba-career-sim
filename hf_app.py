"""
Hugging Face Spaces 启动入口。
HF Spaces 要求端口 7860，自动初始化数据库。
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 确保数据目录存在
Path("data").mkdir(exist_ok=True)
Path("seeding/seed_cache").mkdir(parents=True, exist_ok=True)

# 如果数据库不存在，自动初始化（首次启动）
db_path = Path("data/nba_sim.db")
if not db_path.exists() or db_path.stat().st_size < 10000:
    print("首次启动，初始化数据库...")
    from database.schema import init_database
    init_database()
    print("正在导入球员数据（约2分钟）...")
    try:
        from seeding.seed_runner import run
        run(force=False, quick=True)
        print("数据初始化完成！")
    except Exception as e:
        print(f"种子数据导入失败（{e}），使用基础数据库")
        from database.schema import init_database
        init_database()
else:
    print("数据库已存在，直接启动...")
    from database.schema import init_database
    init_database()

# 启动 Flask，端口 7860
from web.flask_app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"NBA 假如模拟器启动：http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
