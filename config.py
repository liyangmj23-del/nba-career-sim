from pathlib import Path

# ── 路径 ────────────────────────────────────────────────────────────────────
ROOT_DIR        = Path(__file__).parent
DATA_DIR        = ROOT_DIR / "data"
DB_PATH         = DATA_DIR / "nba_sim.db"
SEED_CACHE_DIR  = ROOT_DIR / "seeding" / "seed_cache"

DATA_DIR.mkdir(exist_ok=True)
SEED_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── 赛季 ────────────────────────────────────────────────────────────────────
CURRENT_SEASON_YEAR = 2025        # 2024-25 赛季用 2025 表示
SEASON_WEEKS        = 30          # 常规赛周数（82场，约3场/周）
GAMES_PER_WEEK_AVG  = 3
PLAYOFF_ROUNDS      = 4

# ── 事件系统 ────────────────────────────────────────────────────────────────
MAX_EVENTS_PER_WEEK       = 3   # 选择事件1 + 叙事事件2
MAX_MAJOR_EVENTS_PER_WEEK = 1
INJURY_FATIGUE_THRESHOLD  = 70    # 疲劳超过此值时伤病概率 ×1.5
OFFCOURT_PLAYOFF_FACTOR   = 0.3   # 季后赛期间场外事件概率系数

# ── 球员属性 ────────────────────────────────────────────────────────────────
ATTR_MIN = 1
ATTR_MAX = 99

# 年龄-属性巅峰期
AGE_PHYSICAL_PEAK = 26
AGE_SKILL_PEAK    = 29
AGE_MENTAL_PEAK   = 32

# 每年衰退速率（超过巅峰后，每岁减多少点）
DECAY_PHYSICAL = 0.8
DECAY_SKILL    = 0.4
DECAY_MENTAL   = 0.2

# ── 数据生成噪音 ────────────────────────────────────────────────────────────
STAT_WEEKLY_VARIANCE = 0.15       # ±15% 随机波动

# ── nba_api 请求限速（秒）────────────────────────────────────────────────────
API_REQUEST_DELAY = 0.6

# ── 叙事风格 ────────────────────────────────────────────────────────────────
NARRATIVE_STYLE = "immersive"     # "immersive" | "humorous"
