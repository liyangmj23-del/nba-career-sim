"""
HTML 数据报告生成器。
生成自包含的 HTML 文件并在默认浏览器中打开。
"""
import webbrowser
import json
from pathlib import Path
from database.connection import db as getdb
from config import DATA_DIR, CURRENT_SEASON_YEAR


# ── 数据查询 ──────────────────────────────────────────────────────────────────

def _fetch_player(player_id: int) -> dict:
    with getdb() as conn:
        row = conn.execute(
            "SELECT full_name, position, current_team_id FROM players WHERE player_id=?",
            (player_id,)
        ).fetchone()
    if not row:
        return {"full_name": "未知球员", "position": "-", "team_id": None}
    return {"full_name": row[0], "position": row[1] or "-", "team_id": row[2]}


def _fetch_team_name(team_id) -> str:
    if not team_id:
        return "自由球员"
    with getdb() as conn:
        row = conn.execute(
            "SELECT full_name, abbreviation FROM teams WHERE team_id=?", (team_id,)
        ).fetchone()
    return f"{row[0]} ({row[1]})" if row else str(team_id)


def _fetch_attrs(player_id: int) -> dict:
    with getdb() as conn:
        row = conn.execute(
            "SELECT * FROM player_attributes WHERE player_id=? AND season_year=?",
            (player_id, CURRENT_SEASON_YEAR)
        ).fetchone()
    if not row:
        return {}
    return dict(row)


def _fetch_season_stats(player_id: int) -> list[dict]:
    with getdb() as conn:
        rows = conn.execute(
            """SELECT season_year, games_played, points_pg, rebounds_pg,
                      assists_pg, steals_pg, blocks_pg, turnovers_pg,
                      fg_pct, fg3_pct, ft_pct
               FROM player_season_stats WHERE player_id=?
               ORDER BY season_year DESC""",
            (player_id,)
        ).fetchall()
    return [
        {"year": r[0], "gp": r[1],
         "pts": r[2], "reb": r[3], "ast": r[4], "stl": r[5], "blk": r[6], "tov": r[7],
         "fg": r[8]*100, "fg3": r[9]*100, "ft": r[10]*100}
        for r in rows
    ]


def _fetch_game_log(player_id: int) -> list[dict]:
    with getdb() as conn:
        rows = conn.execute(
            """SELECT gl.game_week, gl.game_number, gl.is_home,
                      t.abbreviation, gl.player_won,
                      gl.points, gl.rebounds, gl.assists,
                      gl.steals, gl.blocks, gl.turnovers,
                      gl.fg_made, gl.fg_attempted,
                      gl.fg3_made, gl.fg3_attempted,
                      gl.ft_made, gl.ft_attempted, gl.plus_minus
               FROM player_game_log gl
               LEFT JOIN teams t ON gl.opponent_team_id = t.team_id
               WHERE gl.player_id=? ORDER BY gl.game_number""",
            (player_id,)
        ).fetchall()
    result = []
    for r in rows:
        fga = r[12]; fg3a = r[14]; fta = r[16]
        result.append({
            "week": r[0], "gnum": r[1], "home": r[2],
            "opp": r[3] or "?", "won": r[4],
            "pts": r[5], "reb": r[6], "ast": r[7],
            "stl": r[8], "blk": r[9], "tov": r[10],
            "fgm": r[11], "fga": fga,
            "fg3m": r[13], "fg3a": fg3a,
            "ftm": r[15], "fta": fta,
            "pm": r[17],
            "fg_pct": round(r[11]/fga*100, 1) if fga else 0,
            "fg3_pct": round(r[13]/fg3a*100, 1) if fg3a else 0,
            "ft_pct": round(r[15]/fta*100, 1) if fta else 0,
        })
    return result


def _fetch_events(save_id: int) -> list[dict]:
    with getdb() as conn:
        rows = conn.execute(
            """SELECT season_year, week_number, category, severity, title, narrative_text, choice_made
               FROM event_log WHERE save_id=?
               ORDER BY season_year, week_number, event_id
               LIMIT 200""",
            (save_id,)
        ).fetchall()
    return [
        {"year": r[0], "week": r[1], "cat": r[2], "sev": r[3],
         "title": r[4], "text": r[5], "choice": r[6]}
        for r in rows
    ]


def _fetch_awards(save_id: int) -> list[dict]:
    with getdb() as conn:
        rows = conn.execute(
            "SELECT season_year, award_type, description FROM awards WHERE save_id=? ORDER BY season_year, award_id",
            (save_id,)
        ).fetchall()
    return [{"year": r[0], "type": r[1], "desc": r[2]} for r in rows]


# ── HTML 模板 ─────────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{PLAYER_NAME}} · NBA 生涯数据报告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg:       #0a0a12;
    --bg2:      #0d0d1a;
    --bg3:      #12122a;
    --border:   #1e2040;
    --cyan:     #4dc3ff;
    --gold:     #ffc107;
    --green:    #22c55e;
    --red:      #ef4444;
    --yellow:   #eab308;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --hero-bg:  #0a2050;
    --hero-bd:  #1e6eb5;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }

  /* ── 导航栏 ── */
  nav { background: #060610; border-bottom: 1px solid var(--border);
        padding: 0 24px; display: flex; align-items: center; gap: 24px; height: 52px; position: sticky; top:0; z-index:100; }
  nav .logo { color: var(--cyan); font-weight: 700; font-size: 18px; letter-spacing: 1px; }
  nav a { color: var(--muted); text-decoration: none; font-size: 13px; padding: 6px 12px;
          border-radius: 6px; transition: all .2s; }
  nav a:hover, nav a.active { color: var(--cyan); background: rgba(77,195,255,.08); }

  /* ── 主容器 ── */
  .container { max-width: 1400px; margin: 0 auto; padding: 24px; }

  /* ── 卡片 ── */
  .card { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px;
          padding: 20px; margin-bottom: 20px; }
  .card-title { color: var(--cyan); font-size: 13px; font-weight: 600;
                letter-spacing: 1px; text-transform: uppercase; margin-bottom: 16px;
                padding-bottom: 8px; border-bottom: 1px solid var(--border); }

  /* ── 球员头部 ── */
  .player-header { display: grid; grid-template-columns: auto 1fr auto; gap: 24px;
                   align-items: center; }
  .player-number { font-size: 72px; font-weight: 900; color: var(--border);
                   line-height: 1; letter-spacing: -4px; }
  .player-name { font-size: 36px; font-weight: 800; color: var(--text); }
  .player-meta { font-size: 14px; color: var(--muted); margin-top: 6px; }
  .player-meta span { margin-right: 16px; }
  .overall-badge { background: linear-gradient(135deg,var(--hero-bg),#0d3070);
                   border: 1px solid var(--hero-bd); border-radius: 12px;
                   padding: 16px 24px; text-align: center; }
  .overall-num { font-size: 52px; font-weight: 900; color: var(--cyan); line-height: 1; }
  .overall-label { font-size: 12px; color: var(--muted); margin-top: 4px; }

  /* ── 属性条 ── */
  .attrs-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .attr-item { display: flex; align-items: center; gap: 8px; }
  .attr-label { width: 64px; color: var(--muted); font-size: 12px; flex-shrink: 0; }
  .attr-bar-wrap { flex: 1; background: var(--bg3); border-radius: 4px; height: 6px; overflow: hidden; }
  .attr-bar { height: 100%; border-radius: 4px; transition: width .4s; }
  .attr-val { width: 28px; text-align: right; font-weight: 600; font-size: 13px; }

  /* ── 统计块 ── */
  .stat-blocks { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; }
  .stat-block { background: var(--bg3); border-radius: 8px; padding: 14px; text-align: center; }
  .stat-block .val { font-size: 28px; font-weight: 800; color: var(--text); }
  .stat-block .lbl { font-size: 11px; color: var(--muted); margin-top: 4px; text-transform: uppercase; }

  /* ── 表格 ── */
  .tbl-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: var(--bg3); color: var(--muted); font-weight: 600; text-align: center;
       padding: 8px 6px; white-space: nowrap; border-bottom: 1px solid var(--border); font-size: 11px; }
  td { padding: 7px 6px; text-align: center; border-bottom: 1px solid rgba(30,32,64,.5); }
  tr:hover td { background: rgba(77,195,255,.04); }
  .hero-row td { background: rgba(10,32,80,.5) !important; color: var(--cyan); font-weight: 600; }
  .total-row td { background: var(--bg3) !important; font-weight: 700; border-top: 1px solid var(--border); }
  .win  { color: var(--green); font-weight: 600; }
  .loss { color: var(--red); font-weight: 600; }
  .home { color: var(--cyan); }
  .away { color: var(--muted); }
  .pts-high { color: var(--gold); font-weight: 700; }
  .pts-low  { color: var(--muted); }

  /* ── 比赛 Box Score ── */
  .boxscore-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .team-header-box { display: flex; justify-content: space-between; align-items: center;
                     margin-bottom: 12px; }
  .team-name { font-size: 18px; font-weight: 700; }
  .team-score { font-size: 32px; font-weight: 900; }
  .team-score.win  { color: var(--green); }
  .team-score.loss { color: var(--red); }

  /* ── 事件流 ── */
  .event-feed { max-height: 600px; overflow-y: auto; }
  .event-item { border-left: 3px solid var(--border); padding: 12px 16px;
                margin-bottom: 12px; border-radius: 0 8px 8px 0; background: var(--bg3); }
  .event-item.legendary { border-color: var(--gold); }
  .event-item.major { border-color: var(--yellow); }
  .event-item.normal { border-color: var(--cyan); }
  .event-item.minor { border-color: var(--muted); }
  .event-item.choice { border-color: #a855f7; }
  .event-meta { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
  .event-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
  .event-text { font-size: 13px; color: #94a3b8; line-height: 1.6; white-space: pre-line; }
  .choice-badge { display: inline-block; background: rgba(168,85,247,.2);
                  border: 1px solid #a855f7; border-radius: 4px;
                  padding: 2px 8px; font-size: 11px; color: #c084fc; margin-bottom: 6px; }

  /* ── 荣誉 ── */
  .awards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .award-item { background: var(--bg3); border-radius: 8px; padding: 14px;
                border-left: 3px solid var(--gold); }
  .award-year { font-size: 11px; color: var(--muted); }
  .award-desc { font-size: 13px; font-weight: 600; margin-top: 4px; color: var(--gold); }

  /* ── 图表 ── */
  .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .chart-box { background: var(--bg3); border-radius: 8px; padding: 16px; }
  .chart-title { font-size: 13px; color: var(--muted); margin-bottom: 12px; font-weight: 600; }

  /* ── Section 标题 ── */
  .section-title { font-size: 22px; font-weight: 700; color: var(--text);
                   margin-bottom: 20px; padding-bottom: 12px;
                   border-bottom: 2px solid var(--border); }
  .section-title span { color: var(--cyan); }

  /* ── 页脚 ── */
  footer { text-align: center; color: var(--muted); font-size: 12px;
           padding: 32px; border-top: 1px solid var(--border); margin-top: 40px; }

  /* ── Tab 切换 ── */
  .tab-bar { display: flex; gap: 4px; margin-bottom: 20px;
             border-bottom: 1px solid var(--border); }
  .tab-btn { padding: 10px 18px; background: none; border: none; border-bottom: 2px solid transparent;
             color: var(--muted); font-size: 13px; cursor: pointer; transition: all .2s; margin-bottom: -1px; }
  .tab-btn:hover { color: var(--text); }
  .tab-btn.active { color: var(--cyan); border-bottom-color: var(--cyan); }
  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* ── 响应式 ── */
  @media(max-width: 900px) {
    .attrs-grid { grid-template-columns: repeat(2,1fr); }
    .stat-blocks { grid-template-columns: repeat(4,1fr); }
    .boxscore-grid { grid-template-columns: 1fr; }
    .charts-grid { grid-template-columns: 1fr; }
    .awards-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<nav>
  <div class="logo">NBA SIM</div>
  <a href="#overview" class="active" onclick="scrollTo('#overview')">概览</a>
  <a href="#gamelog" onclick="scrollTo('#gamelog')">逐场数据</a>
  <a href="#boxscore" onclick="scrollTo('#boxscore')">比赛看板</a>
  <a href="#events" onclick="scrollTo('#events')">生涯事件</a>
  <a href="#awards" onclick="scrollTo('#awards')">荣誉</a>
  <a href="#history" onclick="scrollTo('#history')">历史地位</a>
</nav>

<div class="container">

<!-- ══ 概览 ══════════════════════════════════════════════════════════════ -->
<div id="overview" style="padding-top:24px">
  <div class="card player-header">
    <div class="player-number">{{JERSEY}}</div>
    <div>
      <div class="player-name">{{PLAYER_NAME}}</div>
      <div class="player-meta">
        <span>{{POSITION}}</span>
        <span>{{TEAM_NAME}}</span>
        <span>{{CURRENT_SEASON}} 赛季</span>
      </div>
      <div style="margin-top:16px">
        <div class="stat-blocks" id="season-blocks">{{SEASON_BLOCKS}}</div>
      </div>
    </div>
    <div class="overall-badge">
      <div class="overall-num">{{OVERALL}}</div>
      <div class="overall-label">综合评级</div>
    </div>
  </div>

  <!-- 属性 -->
  <div class="card">
    <div class="card-title">球员属性</div>
    <div class="attrs-grid" id="attrs-grid">{{ATTRS_HTML}}</div>
  </div>

  <!-- 赛季统计 -->
  <div class="card">
    <div class="card-title">历年赛季数据</div>
    <div class="tbl-wrap">
      <table id="season-table">
        <thead>
          <tr>
            <th>赛季</th><th>场次</th><th>得分</th><th>篮板</th><th>助攻</th>
            <th>抢断</th><th>盖帽</th><th>失误</th><th>FG%</th><th>3P%</th><th>FT%</th>
          </tr>
        </thead>
        <tbody>{{SEASON_ROWS}}</tbody>
      </table>
    </div>
  </div>
</div>

<!-- ══ 逐场数据 ══════════════════════════════════════════════════════════ -->
<div id="gamelog" style="padding-top:24px">
  <div class="section-title">逐场 <span>数据</span></div>
  <div class="card">
    <div class="tbl-wrap">
      <table id="gamelog-table">
        <thead>
          <tr>
            <th>周</th><th>场</th><th>主/客</th><th>对手</th><th>胜负</th>
            <th>分</th><th>篮</th><th>助</th><th>断</th><th>帽</th><th>失</th>
            <th>FG</th><th>FG%</th><th>3P</th><th>3P%</th><th>FT</th><th>FT%</th><th>+/-</th>
          </tr>
        </thead>
        <tbody>{{GAMELOG_ROWS}}</tbody>
      </table>
    </div>
  </div>

  <!-- 得分走势图 -->
  <div class="charts-grid">
    <div class="chart-box">
      <div class="chart-title">逐场得分趋势</div>
      <canvas id="pts-chart" height="200"></canvas>
    </div>
    <div class="chart-box">
      <div class="chart-title">篮板 / 助攻 趋势</div>
      <canvas id="reb-ast-chart" height="200"></canvas>
    </div>
  </div>
</div>

<!-- ══ 比赛看板 ══════════════════════════════════════════════════════════ -->
<div id="boxscore" style="padding-top:24px">
  <div class="section-title">比赛 <span>看板</span></div>
  <p style="color:var(--muted);margin-bottom:16px;font-size:13px">
    选择场次查看完整双方 Box Score（数据为该场模拟结果）
  </p>
  <div class="card">
    <select id="game-select" onchange="showBoxScore(this.value)"
      style="background:var(--bg3);color:var(--text);border:1px solid var(--border);
             border-radius:6px;padding:8px 12px;font-size:13px;width:300px;margin-bottom:16px;">
      <option value="">选择比赛场次...</option>
      {{GAME_OPTIONS}}
    </select>
    <div id="boxscore-display"></div>
  </div>
</div>

<!-- ══ 事件日志 ══════════════════════════════════════════════════════════ -->
<div id="events" style="padding-top:24px">
  <div class="section-title">生涯 <span>事件</span></div>
  <div class="card">
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('all')">全部</button>
      <button class="tab-btn" onclick="switchTab('game_performance')">比赛</button>
      <button class="tab-btn" onclick="switchTab('injury')">伤病</button>
      <button class="tab-btn" onclick="switchTab('choice')">抉择</button>
      <button class="tab-btn" onclick="switchTab('career_milestones')">里程碑</button>
    </div>
    <div class="event-feed" id="event-feed">{{EVENTS_HTML}}</div>
  </div>
</div>

<!-- ══ 荣誉 ══════════════════════════════════════════════════════════════ -->
<div id="awards" style="padding-top:24px">
  <div class="section-title">荣誉 <span>殿堂</span></div>
  {{AWARDS_HTML}}
</div>

<!-- ══ 历史地位 ══════════════════════════════════════════════════════════ -->
<div id="history" style="padding-top:24px">
  <div class="section-title">历史 <span>地位</span></div>
  {{HISTORY_HTML}}
</div>

</div><!-- /container -->

<footer>NBA 生涯模拟器 · 数据报告 · 生成时间：{{GEN_TIME}}</footer>

<script>
// ── 图表数据 ──────────────────────────────────────────────────────────────
const gameLogData = {{CHART_DATA}};

// ── 得分趋势 ──────────────────────────────────────────────────────────────
if (gameLogData.length > 0) {
  const labels = gameLogData.map(g => `G${g.gnum}`);
  new Chart(document.getElementById('pts-chart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '得分',
        data: gameLogData.map(g => g.pts),
        borderColor: '#4dc3ff', backgroundColor: 'rgba(77,195,255,.1)',
        borderWidth: 2, fill: true, tension: 0.3, pointRadius: 3,
      }]
    },
    options: {
      plugins: { legend: { labels: { color:'#94a3b8', font:{size:11} } } },
      scales: {
        x: { ticks: { color:'#64748b', font:{size:10} }, grid: { color:'rgba(30,32,64,.5)' } },
        y: { ticks: { color:'#64748b', font:{size:10} }, grid: { color:'rgba(30,32,64,.5)' } },
      }
    }
  });

  new Chart(document.getElementById('reb-ast-chart'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label:'篮板', data: gameLogData.map(g=>g.reb), borderColor:'#22c55e', backgroundColor:'rgba(34,197,94,.1)', borderWidth:2, fill:true, tension:0.3, pointRadius:3 },
        { label:'助攻', data: gameLogData.map(g=>g.ast), borderColor:'#eab308', backgroundColor:'rgba(234,179,8,.1)', borderWidth:2, fill:false, tension:0.3, pointRadius:3 },
      ]
    },
    options: {
      plugins: { legend: { labels: { color:'#94a3b8', font:{size:11} } } },
      scales: {
        x: { ticks: { color:'#64748b', font:{size:10} }, grid: { color:'rgba(30,32,64,.5)' } },
        y: { ticks: { color:'#64748b', font:{size:10} }, grid: { color:'rgba(30,32,64,.5)' } },
      }
    }
  });
}

// ── Box Score 数据 ────────────────────────────────────────────────────────
const boxScoreData = {{BOXSCORE_DATA}};

function showBoxScore(gameNum) {
  const container = document.getElementById('boxscore-display');
  if (!gameNum) { container.innerHTML = ''; return; }
  const data = boxScoreData[gameNum];
  if (!data) { container.innerHTML = '<p style="color:var(--muted)">该场数据不可用</p>'; return; }
  container.innerHTML = renderBoxScore(data);
}

function renderBoxScore(data) {
  const renderTeam = (team, side) => {
    const scoreClass = team.won ? 'win' : 'loss';
    const rows = team.players.map(p => {
      const heroClass = p.is_hero ? 'hero-row' : '';
      const fg = p.fg_attempted ? (p.fg_made/p.fg_attempted*100).toFixed(0)+'%' : '-';
      const fg3 = p.fg3_attempted ? (p.fg3_made/p.fg3_attempted*100).toFixed(0)+'%' : '-';
      const ft = p.ft_attempted ? (p.ft_made/p.ft_attempted*100).toFixed(0)+'%' : '-';
      const pm = p.plus_minus > 0 ? '+'+p.plus_minus : p.plus_minus;
      const ptsClass = p.points >= 25 ? 'pts-high' : (p.points <= 5 ? 'pts-low' : '');
      const name = p.is_hero ? '★ '+p.name : p.name;
      return `<tr class="${heroClass}">
        <td style="text-align:left;padding-left:8px">${name}</td>
        <td>${p.position}</td>
        <td class="${ptsClass}">${p.points}</td>
        <td>${p.rebounds}</td><td>${p.assists}</td>
        <td>${p.steals}</td><td>${p.blocks}</td><td>${p.turnovers}</td>
        <td>${p.fg_made}/${p.fg_attempted}</td><td>${fg}</td>
        <td>${p.fg3_made}/${p.fg3_attempted}</td><td>${fg3}</td>
        <td>${p.ft_made}/${p.ft_attempted}</td><td>${ft}</td>
        <td>${pm}</td>
      </tr>`;
    }).join('');
    const totPts = team.players.reduce((s,p)=>s+p.points,0);
    const totReb = team.players.reduce((s,p)=>s+p.rebounds,0);
    const totAst = team.players.reduce((s,p)=>s+p.assists,0);
    const totFgM = team.players.reduce((s,p)=>s+p.fg_made,0);
    const totFgA = team.players.reduce((s,p)=>s+p.fg_attempted,0);
    const totFg3M = team.players.reduce((s,p)=>s+p.fg3_made,0);
    const totFg3A = team.players.reduce((s,p)=>s+p.fg3_attempted,0);
    return `
      <div>
        <div class="team-header-box">
          <div class="team-name">${team.team_name}</div>
          <div class="team-score ${scoreClass}">${team.total_points}</div>
        </div>
        <div class="tbl-wrap">
          <table>
            <thead><tr>
              <th style="text-align:left">球员</th><th>位</th>
              <th>分</th><th>篮</th><th>助</th><th>断</th><th>帽</th><th>失</th>
              <th>FG</th><th>FG%</th><th>3P</th><th>3P%</th><th>FT</th><th>FT%</th><th>+/-</th>
            </tr></thead>
            <tbody>${rows}</tbody>
            <tfoot><tr class="total-row">
              <td style="text-align:left"><b>合计</b></td><td>-</td>
              <td><b>${totPts}</b></td><td>${totReb}</td><td>${totAst}</td>
              <td>-</td><td>-</td><td>-</td>
              <td>${totFgM}/${totFgA}</td>
              <td>${totFgA ? (totFgM/totFgA*100).toFixed(1)+'%' : '-'}</td>
              <td>${totFg3M}/${totFg3A}</td>
              <td>${totFg3A ? (totFg3M/totFg3A*100).toFixed(1)+'%' : '-'}</td>
              <td>-</td><td>-</td><td>-</td>
            </tr></tfoot>
          </table>
        </div>
      </div>`;
  };
  return `<div class="boxscore-grid">
    ${renderTeam(data.home,'home')}
    ${renderTeam(data.away,'away')}
  </div>`;
}

// ── 事件 Tab 筛选 ──────────────────────────────────────────────────────────
function switchTab(cat) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.event-item').forEach(el => {
    if (cat === 'all') { el.style.display=''; return; }
    const elCat = el.dataset.cat || '';
    const isChoice = el.dataset.choice === '1';
    if (cat === 'choice') { el.style.display = isChoice ? '' : 'none'; }
    else { el.style.display = (elCat === cat && !isChoice) ? '' : 'none'; }
  });
}

// ── 平滑滚动 ──────────────────────────────────────────────────────────────
function scrollTo(id) {
  document.querySelector(id)?.scrollIntoView({behavior:'smooth'});
}
</script>
</body>
</html>"""


# ── 渲染函数 ─────────────────────────────────────────────────────────────────

ATTR_LABELS = {
    "speed":"速度","strength":"力量","vertical":"弹跳","endurance":"耐力",
    "ball_handling":"控球","shooting_2pt":"两分","shooting_3pt":"三分",
    "free_throw":"罚球","passing":"传球","post_moves":"背打",
    "perimeter_def":"外防","interior_def":"内防",
    "steal_tendency":"抢断","block_tendency":"盖帽",
    "basketball_iq":"篮球IQ","clutch_factor":"关键时刻",
    "leadership":"领导力","work_ethic":"勤奋","media_handling":"媒体",
}


def _attr_color(val: int) -> str:
    if val >= 85: return "#ffc107"
    if val >= 75: return "#4dc3ff"
    if val >= 60: return "#22c55e"
    if val >= 45: return "#94a3b8"
    return "#64748b"


def _render_attrs(attrs: dict) -> str:
    skip = {"attr_id","player_id","season_year","overall_rating","health","morale","fatigue"}
    html = ""
    for k, label in ATTR_LABELS.items():
        val = attrs.get(k, 50)
        col = _attr_color(val)
        pct = round(val / 99 * 100)
        html += f"""<div class="attr-item">
          <div class="attr-label">{label}</div>
          <div class="attr-bar-wrap"><div class="attr-bar" style="width:{pct}%;background:{col}"></div></div>
          <div class="attr-val" style="color:{col}">{val}</div>
        </div>\n"""
    # 状态
    for k, label, lo, hi in [("health","体力",0,100),("morale","士气",0,100),("fatigue","疲劳",0,100)]:
        val = attrs.get(k, 50)
        col = "#22c55e" if k=="health" else ("#a855f7" if k=="morale" else "#f97316")
        pct = round(val / hi * 100)
        html += f"""<div class="attr-item">
          <div class="attr-label">{label}</div>
          <div class="attr-bar-wrap"><div class="attr-bar" style="width:{pct}%;background:{col}"></div></div>
          <div class="attr-val" style="color:{col}">{val}</div>
        </div>\n"""
    return html


def _render_season_rows(season_stats: list[dict]) -> str:
    if not season_stats:
        return '<tr><td colspan="11" style="color:var(--muted);text-align:center">暂无赛季数据</td></tr>'
    html = ""
    for s in season_stats:
        yr = s["year"]
        label = f"{yr-1}-{str(yr)[2:]}"
        html += f"""<tr>
          <td>{label}</td><td>{s['gp']}</td>
          <td><b>{s['pts']:.1f}</b></td><td>{s['reb']:.1f}</td><td>{s['ast']:.1f}</td>
          <td>{s['stl']:.1f}</td><td>{s['blk']:.1f}</td><td>{s['tov']:.1f}</td>
          <td>{s['fg']:.1f}%</td><td>{s['fg3']:.1f}%</td><td>{s['ft']:.1f}%</td>
        </tr>\n"""
    return html


def _render_season_blocks(season_stats: list[dict]) -> str:
    if not season_stats:
        return ""
    s = season_stats[0]
    blocks = [
        ("pts","得分","#4dc3ff",f"{s['pts']:.1f}"),
        ("reb","篮板","#22c55e",f"{s['reb']:.1f}"),
        ("ast","助攻","#eab308",f"{s['ast']:.1f}"),
        ("stl","抢断","#a855f7",f"{s['stl']:.1f}"),
        ("blk","盖帽","#f97316",f"{s['blk']:.1f}"),
        ("fg","FG%","#94a3b8",f"{s['fg']:.1f}%"),
        ("ft","FT%","#94a3b8",f"{s['ft']:.1f}%"),
    ]
    html = ""
    for _, label, color, val in blocks:
        html += f"""<div class="stat-block">
          <div class="val" style="color:{color}">{val}</div>
          <div class="lbl">{label}</div>
        </div>\n"""
    return html


def _render_gamelog_rows(games: list[dict]) -> str:
    if not games:
        return '<tr><td colspan="18" style="color:var(--muted);text-align:center">暂无比赛记录，请先推进赛季</td></tr>'
    html = ""
    for g in games:
        result_class = "win" if g["won"] else "loss"
        result_text  = "W" if g["won"] else "L"
        home_class   = "home" if g["home"] else "away"
        home_text    = "主" if g["home"] else "客"
        pm_str = f"+{g['pm']}" if g['pm'] > 0 else str(g['pm'])
        pts_class = "pts-high" if g["pts"] >= 30 else ("pts-low" if g["pts"] <= 8 else "")
        html += f"""<tr>
          <td>第{g['week']}周</td><td>G{g['gnum']}</td>
          <td class="{home_class}">{home_text}</td>
          <td><b>{g['opp']}</b></td>
          <td class="{result_class}">{result_text}</td>
          <td class="{pts_class}"><b>{g['pts']}</b></td>
          <td>{g['reb']}</td><td>{g['ast']}</td><td>{g['stl']}</td><td>{g['blk']}</td><td>{g['tov']}</td>
          <td>{g['fgm']}/{g['fga']}</td><td>{g['fg_pct']:.0f}%</td>
          <td>{g['fg3m']}/{g['fg3a']}</td><td>{g['fg3_pct']:.0f}%</td>
          <td>{g['ftm']}/{g['fta']}</td><td>{g['ft_pct']:.0f}%</td>
          <td>{pm_str}</td>
        </tr>\n"""
    return html


def _render_events(events: list[dict]) -> str:
    SEV_CLASS = {"legendary":"legendary","major":"major","normal":"normal","minor":"minor"}
    CAT_LABEL = {
        "game_performance":"比赛","injury":"伤病","personal_life":"个人",
        "team_chemistry":"球队","career_milestones":"里程碑","off_court":"场外",
    }
    html = ""
    for e in events:
        is_choice = bool(e.get("choice"))
        sev_class = "choice" if is_choice else SEV_CLASS.get(e["sev"], "normal")
        cat_label = CAT_LABEL.get(e["cat"], e["cat"])
        yr_label  = f"{e['year']-1}-{str(e['year'])[2:]}"
        choice_badge = f'<span class="choice-badge">你的选择：{e["choice"]}</span>' if is_choice else ""
        text = (e["text"] or "").replace("<","&lt;").replace(">","&gt;")
        html += f"""<div class="event-item {sev_class}" data-cat="{e['cat']}" data-choice="{'1' if is_choice else '0'}">
          <div class="event-meta">{yr_label} 赛季 · 第{e['week']}周 · {cat_label}</div>
          {choice_badge}
          <div class="event-title">{e['title']}</div>
          <div class="event-text">{text[:500]}</div>
        </div>\n"""
    return html or '<p style="color:var(--muted)">暂无事件记录</p>'


def _render_awards(awards: list[dict]) -> str:
    if not awards:
        return '<div class="card" style="color:var(--muted)">暂无荣誉记录，继续模拟赛季获取荣誉</div>'
    html = '<div class="card"><div class="awards-grid">'
    for a in awards:
        yr = a["year"]
        html += f"""<div class="award-item">
          <div class="award-year">{yr-1}-{str(yr)[2:]} 赛季</div>
          <div class="award-desc">{a['desc']}</div>
        </div>\n"""
    html += "</div></div>"
    return html


def _render_history(player_id: int, save_id: int, player_name: str) -> str:
    try:
        from simulation.historical_standing import build_historical_report
        report = build_historical_report(save_id, player_id, player_name)
    except Exception:
        return '<div class="card" style="color:var(--muted)">历史地位数据计算中...</div>'

    tier  = report["tier"]
    score = report["hof_score"]
    totals = report["totals"]

    html = f"""<div class="card">
      <div style="display:grid;grid-template-columns:1fr auto;gap:20px;align-items:start">
        <div>
          <div style="font-size:28px;font-weight:800;color:#ffc107">{tier}</div>
          <div style="color:var(--muted);margin-top:4px">HOF 积分：{score:.0f} 分</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:13px;color:var(--muted)">{totals['seasons']} 赛季 / {totals['games']} 场</div>
          <div style="font-size:13px;color:var(--muted)">生涯场均：{totals['avg_pts']}分 {totals['avg_reb']}篮 {totals['avg_ast']}助</div>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">生涯数据 vs NBA 历史记录</div>
      <div class="tbl-wrap"><table>
        <thead><tr><th>统计项</th><th>生涯总计</th><th>历史记录</th><th>记录保持者</th><th>占比</th><th>状态</th></tr></thead>
        <tbody>"""
    for comp in report["comparisons"]:
        pct = comp["pct"]
        bar_w = min(100, round(pct))
        col = "#ffc107" if pct>=100 else ("#4dc3ff" if pct>=70 else "#94a3b8")
        status = comp.get("status","")
        html += f"""<tr>
          <td><b>{comp['label']}</b></td>
          <td style="color:{col};font-weight:700">{comp['value']:,}</td>
          <td>{comp['record']:,}</td>
          <td style="color:var(--muted)">{comp['holder']}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px">
              <div style="flex:1;background:var(--bg3);border-radius:4px;height:6px">
                <div style="width:{bar_w}%;background:{col};height:100%;border-radius:4px"></div>
              </div>
              <span style="color:{col}">{pct:.1f}%</span>
            </div>
          </td>
          <td style="color:{col}">{status}</td>
        </tr>"""
    html += "</tbody></table></div></div>"

    if report["milestones"]:
        html += '<div class="card"><div class="card-title">生涯里程碑</div><ul style="list-style:none">'
        for m in report["milestones"]:
            html += f'<li style="padding:6px 0;color:#ffc107;border-bottom:1px solid var(--border)">★ {m}</li>'
        html += "</ul></div>"

    return html


def _generate_boxscore_data(player_id: int, team_id, save_id: int, games: list[dict]) -> dict:
    """为每场比赛生成 Box Score 数据（按需生成，不走 DB）。"""
    from simulation.game_simulator import generate_full_box_score, PlayerBoxRow
    from database.repositories.save_repo import SaveRepository
    from database.connection import db as getdb
    import random, dataclasses

    save = SaveRepository().get_by_id(save_id)
    season_year = save.current_season if save else CURRENT_SEASON_YEAR

    # 取上周各场比赛的对手（从 game_log 里读）
    with getdb() as conn:
        log_rows = conn.execute(
            "SELECT game_number, opponent_team_id, player_won FROM player_game_log WHERE player_id=? ORDER BY game_number",
            (player_id,)
        ).fetchall()

    result = {}
    for gnum, opp_id, won in log_rows:
        # 找到对应的 game log 行的数据
        matching = [g for g in games if g["gnum"] == gnum]
        if not matching:
            continue
        g = matching[0]

        # 构造一个临时 GameBox-like 对象
        class _FakeBox:
            def __init__(self, g):
                self.minutes   = 36.0
                self.points    = g["pts"]; self.rebounds = g["reb"]
                self.assists   = g["ast"]; self.steals   = g["stl"]
                self.blocks    = g["blk"]; self.turnovers= g["tov"]
                self.fg_made   = g["fgm"]; self.fg_attempted = g["fga"]
                self.fg3_made  = g["fg3m"]; self.fg3_attempted= g["fg3a"]
                self.ft_made   = g["ftm"]; self.ft_attempted = g["fta"]
                self.plus_minus= g["pm"]; self.player_won   = g["won"]

        box = generate_full_box_score(
            my_team_id   = team_id or 0,
            opp_team_id  = opp_id or 0,
            season_year  = season_year,
            game_week    = g["week"],
            game_number  = gnum,
            player_id    = player_id,
            hero_box     = _FakeBox(g),
            my_team_won  = bool(won),
        )
        # 序列化为可 JSON 的 dict
        def team_dict(t):
            return {
                "team_name": t.team_name,
                "abbreviation": t.abbreviation,
                "total_points": t.total_points,
                "won": t.won,
                "players": [{
                    "name": p.name, "position": p.position,
                    "is_hero": p.is_hero, "is_starter": p.is_starter,
                    "points": p.points, "rebounds": p.rebounds,
                    "assists": p.assists, "steals": p.steals,
                    "blocks": p.blocks, "turnovers": p.turnovers,
                    "fg_made": p.fg_made, "fg_attempted": p.fg_attempted,
                    "fg3_made": p.fg3_made, "fg3_attempted": p.fg3_attempted,
                    "ft_made": p.ft_made, "ft_attempted": p.ft_attempted,
                    "plus_minus": p.plus_minus,
                } for p in t.players],
            }
        result[str(gnum)] = {"home": team_dict(box.home), "away": team_dict(box.away)}
        if len(result) >= 30:  # 最多生成30场避免太慢
            break

    return result


def _game_options_html(games: list[dict]) -> str:
    html = ""
    for g in games:
        result = "W" if g["won"] else "L"
        html += f'<option value="{g["gnum"]}">G{g["gnum"]} 第{g["week"]}周 vs {g["opp"]} ({result} {g["pts"]}分)</option>\n'
    return html


# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate_report(player_id: int, save_id: int) -> Path:
    """生成 HTML 报告，返回文件路径。"""
    import datetime
    p    = _fetch_player(player_id)
    attrs = _fetch_attrs(player_id)
    season_stats = _fetch_season_stats(player_id)
    games = _fetch_game_log(player_id)
    events = _fetch_events(save_id)
    awards = _fetch_awards(save_id)
    team_name = _fetch_team_name(p["team_id"])

    # Box score 数据（最多30场，避免太慢）
    boxscore_data = {}
    try:
        boxscore_data = _generate_boxscore_data(player_id, p["team_id"], save_id, games)
    except Exception:
        pass

    html = HTML_TEMPLATE
    html = html.replace("{{PLAYER_NAME}}", p["full_name"])
    html = html.replace("{{JERSEY}}", "#")
    html = html.replace("{{POSITION}}", p["position"])
    html = html.replace("{{TEAM_NAME}}", team_name)
    html = html.replace("{{CURRENT_SEASON}}", f"{CURRENT_SEASON_YEAR-1}-{str(CURRENT_SEASON_YEAR)[2:]}")
    html = html.replace("{{OVERALL}}", str(attrs.get("overall_rating", "-")))
    html = html.replace("{{ATTRS_HTML}}", _render_attrs(attrs))
    html = html.replace("{{SEASON_BLOCKS}}", _render_season_blocks(season_stats))
    html = html.replace("{{SEASON_ROWS}}", _render_season_rows(season_stats))
    html = html.replace("{{GAMELOG_ROWS}}", _render_gamelog_rows(games))
    html = html.replace("{{CHART_DATA}}", json.dumps(games, ensure_ascii=False))
    html = html.replace("{{BOXSCORE_DATA}}", json.dumps(boxscore_data, ensure_ascii=False))
    html = html.replace("{{GAME_OPTIONS}}", _game_options_html(games))
    html = html.replace("{{EVENTS_HTML}}", _render_events(events))
    html = html.replace("{{AWARDS_HTML}}", _render_awards(awards))
    html = html.replace("{{HISTORY_HTML}}", _render_history(player_id, save_id, p["full_name"]))
    html = html.replace("{{GEN_TIME}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 保存文件
    out_path = DATA_DIR / f"report_{player_id}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def generate_and_open(player_id: int, save_id: int) -> None:
    """生成并在浏览器中打开报告。"""
    path = generate_report(player_id, save_id)
    webbrowser.open(path.as_uri())
