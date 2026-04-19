---
title: NBA 假如模拟器
emoji: 🏀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
short_description: 你说数据，我告诉你结局。NBA生涯假如模拟器
---

# 🏀 NBA 假如模拟器

> **你说数据，我告诉你结局。**
>
> 篮球史上第一款让你直接设定场均数据、验证任何"假如"场景的生涯模拟游戏。

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/liyangmj23-del/nba-career-sim/releases)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Stars](https://img.shields.io/github/stars/liyangmj23-del/nba-career-sim)](https://github.com/liyangmj23-del/nba-career-sim/stargazers)

---

## ⚡ 核心差异化

**其他所有篮球游戏：** 调属性 → 系统生成数据（你不知道最终数据是多少）

**NBA 假如模拟器：** 直接声明数据 → 系统模拟这个数据对生涯的完整影响

这个位置没有竞争者。

---

## 🔥 假如你能验证

| 你的假如 | 游戏告诉你 |
|---|---|
| 场均 10断/10帽 | 能拿几个 MVP？球队赢多少场？是否打破历史记录？ |
| Wilt 的 50分/30板 放在今天 | 历史地位排在哪里？现代球队能赢多少场？ |
| 场均 60分 | 生涯总得分能超越 LeBron 吗？ |
| 完美五双 10/10/10/10/10 | 这种球员真实存在，联盟会发生什么？ |
| 场均 20助攻 | 能成为史上最佳控卫吗？ |

---

## ✨ 功能特性

### 假如验证（核心）
- 🎯 **直接设定场均数据**（得分/篮板/助攻/抢断/盖帽），绕过属性系统
- 🔥 **8个预设假如场景**（Wilt 的统治、乔丹效率、完美五双、得分机器…）
- 💥 **超历史记录检测**：突破 NBA 历史单赛季记录时触发专属叙事
- 📸 **生成分享卡片**（可下载图片，发小红书/虎扑）
- 📊 **完整影响力分析**：数据如何影响球队胜率、历史地位

### 生涯模拟（底层）
- 🏀 **530+ 真实 NBA 球员**（via nba_api）
- 📅 **完整多赛季生涯**：从新秀到退役，属性随年龄自然衰退
- 🏆 **完整季后赛**：4轮系列赛，G7 特殊叙事，冠军庆典
- 🎲 **70+ 随机事件**：伤病/爆发/更衣室冲突/媒体风波…
- ⚡ **13个玩家主动抉择**：合同方向、被交易决定、职业生涯节点
- 🏅 **完整荣誉系统**：MVP/冠军/全明星/历史记录/HOF 积分
- ⭐ **历史地位评级**：从新秀到"前无古人"

### 产品体验
- 🌐 **Web 界面**：浏览器直接运行，零安装门槛
- 📱 **移动端适配**：手机也能玩
- 💾 **多存档管理**：保存/删除/重命名
- ⚙️ **游戏设置**：难度/叙事风格/事件频率

---

## 🚀 快速开始

### 1. 克隆并安装依赖

```bash
git clone https://github.com/liyangmj23-del/nba-career-sim.git
cd nba-career-sim
pip install -r requirements.txt
```

### 2. 初始化球员数据

```bash
# 快速模式（2分钟，基础数据）
python -m seeding.seed_runner --quick

# 完整模式（10分钟，含真实球员属性和球队归属）
python -m seeding.seed_runner
```

### 3. 启动游戏

```bash
python run_web.py
```

浏览器自动打开 `http://127.0.0.1:5000`

---

## 🎮 游戏玩法

### 方式一：验证假如场景（推荐新手）

```
主页 → 选一个假如场景（如"完美五双"）→ 选球员 → 开始验证
→ 每周推进，看数据、事件、选择
→ 赛季结束看"假如验证结果"
→ 生成分享图，发给朋友讨论
```

### 方式二：完整生涯体验

```
主页 → 选择现有球员（或新建） → 设定你的假如数据（可选）
→ 模拟整个生涯（多赛季，球员会老去）
→ 退役时看完整生涯总结和历史地位
```

| 操作 | 快捷键 |
|---|---|
| 推进一周 | Space |
| 选择事件弹出时选择 | 点击选项 |

---

## 🗺️ 游戏流程图

```
开始
  ↓
选假如场景/球员
  ↓
设定假如数据（可跳过）
  ↓
常规赛 30周
  ├── 每周：比赛 + 随机事件 + 玩家选择
  └── 数据接近你的设定值（±15%自然波动）
  ↓
赛季总结（假如验证结果 + 荣誉 + 超历史记录）
  ↓
季后赛（如果球队晋级）
  ↓
休赛期（训练方向选择）
  ↓
下一赛季（球员变老，数据自然衰退）
  ↓
... 循环直到退役 ...
  ↓
生涯终章（完整生涯数据 + 历史地位 + 分享图）
```

---

## 📁 项目结构

```
nba_sim/
├── run_web.py          # 启动入口
├── config.py           # 全局配置
├── web/                # Flask 后端 + 前端
│   ├── flask_app.py    # 所有路由
│   ├── templates/      # 12个HTML页面
│   └── static/         # CSS + JS
├── simulation/         # 模拟引擎
│   ├── engine.py       # 赛季主循环
│   ├── season_manager.py   # 多赛季管理
│   ├── playoff_simulator.py # 季后赛
│   ├── stat_generator.py   # 数据生成
│   ├── player_impact.py    # 影响力系统
│   ├── achievement_tracker.py  # 荣誉评估
│   └── historical_standing.py  # 历史地位
├── events/             # 事件系统（70+事件）
│   ├── event_engine.py
│   └── categories/     # 7类事件文件
└── database/           # SQLite 数据层
    ├── schema.py        # 10张表 DDL
    └── repositories/   # 4个 Repository
```

---

## 🗺️ 路线图

- [x] v0.1.0 — Web界面 + 单赛季模拟 + 70+随机事件
- [x] v0.5.0 — 多赛季 + 季后赛 + 假如场景库 + 赛季总结 + 退役
- [x] **v1.0.0 — 完整生涯闭环 + 分享卡片 + 移动端 + 历史地位**
- [ ] v1.1.0 — 历史球员（Jordan/Kobe/Shaq）+ 真实属性差异化
- [ ] v1.2.0 — 在线版本（Hugging Face Spaces，无需安装）
- [ ] v2.0.0 — 多人对比 / 球队管理视角

---

## 🤝 贡献

欢迎 PR！特别需要：
- **更多假如场景**（经典历史讨论话题）
- **更多叙事事件文本**（中文，沉浸叙事风格）
- **UI/UX 改进**
- **英文翻译**

---

## ⚠️ 声明

本项目仅供学习和娱乐，球员数据来自 [nba_api](https://github.com/swar/nba_api)（非官方接口）。与 NBA 官方无关。

---

<div align="center">
  <strong>你说数据，我告诉你结局。 🏀</strong><br>
  <sub>如果这个项目让你觉得有趣，给个 ⭐ 吧</sub>
</div>
