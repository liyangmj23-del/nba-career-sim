/* NBA 模拟器 — 游戏交互脚本 */

// ══════════════════════════════════════════════════════════════════════════════
// 推进一周
// ══════════════════════════════════════════════════════════════════════════════
async function advanceWeek() {
  if (typeof SAVE_ID === 'undefined') return;

  const btn = document.getElementById('btn-advance');
  if (!btn || btn.disabled) return;
  btn.disabled = true;
  btn.textContent = '模拟中...';

  try {
    const resp = await fetch(`/game/${SAVE_ID}/advance`, { method: 'POST' });
    const data = await resp.json();

    // 服务器报错时 data.error 有值
    if (!resp.ok || data.error) {
      showToast('服务器错误：' + (data.error || resp.status), true);
      return;
    }

    if (data.season_done && data.week >= 30) {
      // 最后一周也要显示内容
      if (data.week <= 30 && data.events !== undefined) {
        appendWeekToFeed(data);
        updatePlayerCard(data.attrs, data.week_summary);
        updateSeasonStats(data.season_stats);
        updateWeekNum(data.week);
      }
      showSeasonEnd();
      return;
    }

    appendWeekToFeed(data);
    updatePlayerCard(data.attrs, data.week_summary);
    updateSeasonStats(data.season_stats);
    updateWeekNum(data.week);
    showToast(`第 ${data.week} 周模拟完成`);

    if (data.pending_choices && data.pending_choices.length > 0) {
      await handleChoices(data.pending_choices);
    }
  } catch (e) {
    console.error('advance error', e);
    showToast('模拟出错：' + e.message, true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = '推进一周';
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 渲染事件流
// ══════════════════════════════════════════════════════════════════════════════
const CAT_LABELS = {
  game_performance:'比赛', injury:'伤病', personal_life:'个人',
  team_chemistry:'球队', career_milestones:'里程碑', off_court:'场外'
};

const ATTR_LABELS = {
  morale:'士气', health:'体力', speed:'速度', strength:'力量',
  vertical:'弹跳', endurance:'耐力', shooting_2pt:'两分', shooting_3pt:'三分',
  free_throw:'罚球', passing:'传球', ball_handling:'控球',
  perimeter_def:'外防', interior_def:'内防', basketball_iq:'IQ',
  clutch_factor:'关键', leadership:'领袖', work_ethic:'勤奋',
  media_handling:'媒体', fatigue:'疲劳', steal_tendency:'抢断',
  block_tendency:'盖帽',
};

function appendWeekToFeed(data) {
  const feed = document.getElementById('event-feed');
  if (!feed) { console.error('event-feed not found'); return; }

  // 清除欢迎提示
  const welcome = feed.querySelector('.feed-welcome');
  if (welcome) welcome.remove();

  const yr = data.season_year;
  const seasonLabel = `${yr-1}-${String(yr).slice(2)}`;

  // 周分隔线
  const divider = document.createElement('div');
  divider.className = 'feed-divider';
  divider.textContent = `── 第 ${data.week} 周 · ${seasonLabel} 赛季 ──`;
  feed.appendChild(divider);

  // 本周数据
  const ws = data.week_summary;
  if (ws && ws.games_this_week) {
    const wins  = ws.wins || 0;
    const total = ws.games_this_week || 0;
    const fga   = ws.fg_attempted || 0;
    const fgm   = ws.fg_made || 0;
    const fg3a  = ws.fg3_attempted || 0;
    const fg3m  = ws.fg3_made || 0;
    const fta   = ws.ft_attempted || 0;
    const ftm   = ws.ft_made || 0;
    const fgPct  = fga  ? (fgm/fga*100).toFixed(1)+'%'   : '-';
    const fg3Pct = fg3a ? (fg3m/fg3a*100).toFixed(1)+'%' : '-';
    const ftPct  = fta  ? (ftm/fta*100).toFixed(1)+'%'   : '-';
    const wCol   = wins===total ? '#22c55e' : wins>0 ? '#eab308' : '#ef4444';
    const statsDiv = document.createElement('div');
    statsDiv.className = 'feed-week-stats';
    statsDiv.innerHTML = `
      <span style="color:${wCol};font-weight:700">${wins}胜${total-wins}负</span>
      <span style="color:#4dc3ff;font-weight:700">${(ws.pts||0).toFixed(1)}分</span>
      ${(ws.reb||0).toFixed(1)}篮　${(ws.ast||0).toFixed(1)}助
      <span style="color:#22c55e">${(ws.stl||0).toFixed(1)}断</span>
      <span style="color:#f97316">${(ws.blk||0).toFixed(1)}帽</span>
      <span style="color:#64748b">${(ws.tov||0).toFixed(1)}失</span><br>
      <span style="color:#64748b;font-size:12px">
        FG ${fgm}/${fga} (${fgPct})　3P ${fg3m}/${fg3a} (${fg3Pct})　FT ${ftm}/${fta} (${ftPct})
      </span>`;
    feed.appendChild(statsDiv);
  }

  // 影响力报告
  if (data.impact && Math.abs(data.impact.wp_bonus) >= 0.02) {
    const imp = data.impact;
    const bonus = imp.wp_bonus;
    const sign  = bonus >= 0 ? '+' : '';
    const col   = bonus >= 0.10 ? '#22c55e' : bonus >= 0 ? '#eab308' : '#ef4444';
    const impDiv = document.createElement('div');
    impDiv.style.cssText = `padding:8px 14px;margin-bottom:8px;background:rgba(0,0,0,.3);
      border-radius:6px;border-left:3px solid ${col};font-size:12px;color:#94a3b8`;
    let html = `<span style="color:${col};font-weight:700">本周影响力：${imp.label}　胜率调整：${sign}${(bonus*100).toFixed(1)}%</span>`;
    if (imp.combos && imp.combos.length > 0)
      html += `<br><span style="color:#ffc107">★ ${imp.combos[0]}</span>`;
    if (imp.superhuman && imp.superhuman.length > 0)
      html += `<br><span style="color:#a855f7">⚡ ${imp.superhuman.join(' · ')}</span>`;
    const oe = imp.opp_effects || {};
    const oeParts = [];
    if (oe.opp_pts_reduction >= 1) oeParts.push(`对手得分压制 -${oe.opp_pts_reduction.toFixed(1)}`);
    if (oe.opp_tov_increase >= 0.5) oeParts.push(`对手失误增加 +${oe.opp_tov_increase.toFixed(1)}`);
    if (oe.team_pts_boost >= 0.5)   oeParts.push(`队友得分提升 +${oe.team_pts_boost.toFixed(1)}`);
    if (oeParts.length > 0) html += `<br><span style="color:#64748b">${oeParts.join('　')}</span>`;
    impDiv.innerHTML = html;
    feed.appendChild(impDiv);
  }

  // 事件
  if (!data.events || data.events.length === 0) {
    const noEvent = document.createElement('div');
    noEvent.className = 'feed-item minor';
    noEvent.innerHTML = `<div class="feed-meta">${CAT_LABELS['game_performance']||''}</div>
      <div class="feed-text" style="color:#475569">本周平静，无特殊事件。</div>`;
    feed.appendChild(noEvent);
  } else {
    data.events.forEach(ev => {
      const el = document.createElement('div');
      el.className = `feed-item ${ev.severity}`;
      const catLabel = CAT_LABELS[ev.category] || ev.category;
      let deltaHtml = '';
      if (ev.delta && Object.keys(ev.delta).length > 0) {
        const parts = Object.entries(ev.delta).map(([k,v]) => {
          const col = v>0 ? '#22c55e' : '#ef4444';
          const sign = v>0 ? '+' : '';
          const lbl = ATTR_LABELS[k] || k;
          return `<span style="color:${col}">${sign}${v} ${lbl}</span>`;
        });
        deltaHtml = `<div class="feed-delta">${parts.join('　')}</div>`;
      }
      el.innerHTML = `
        <div class="feed-meta">第${data.week}周 · ${catLabel}</div>
        <div class="feed-title">${ev.title}</div>
        <div class="feed-text">${(ev.narrative||'').trim().slice(0,400)}</div>
        ${deltaHtml}`;
      feed.appendChild(el);

      // 选择事件标记（由 handleChoices 处理）
      if (ev.choice_prompt) {
        el.dataset.hasChoice = '1';
      }
    });
  }

  // 强制滚到底（等 DOM 渲染完再滚）
  requestAnimationFrame(() => {
    feed.scrollTop = feed.scrollHeight;
    // 第二帧再滚一次，确保内容已经撑开
    requestAnimationFrame(() => { feed.scrollTop = feed.scrollHeight; });
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// 更新球员卡属性
// ══════════════════════════════════════════════════════════════════════════════
function updatePlayerCard(attrs, ws) {
  if (!attrs) return;
  const overall = attrs.overall_rating || 0;
  const overallEl = document.getElementById('overall-val');
  if (overallEl) overallEl.textContent = overall;

  const statusFields = {
    health:  {bar:'bar-health',  val:'val-health'},
    fatigue: {bar:'bar-fatigue', val:'val-fatigue'},
    morale:  {bar:'bar-morale',  val:'val-morale'},
  };
  for (const [key, ids] of Object.entries(statusFields)) {
    const v = attrs[key] ?? 0;
    const barEl = document.getElementById(ids.bar);
    const valEl = document.getElementById(ids.val);
    if (barEl) barEl.style.width = v + '%';
    if (valEl) valEl.textContent = v;
  }

  // 技术属性
  const techKeys = [
    'speed','strength','vertical','endurance','ball_handling',
    'shooting_2pt','shooting_3pt','free_throw','passing',
    'perimeter_def','interior_def','steal_tendency','block_tendency',
    'basketball_iq','clutch_factor','leadership','work_ethic',
  ];
  techKeys.forEach(k => {
    const v = attrs[k] ?? 50;
    const bar = document.getElementById('abar-' + k);
    const val = document.getElementById('aval-' + k);
    if (bar) { bar.style.width = v + '%'; }
    if (val) { val.textContent = v; }
    // 更新编辑框
    const inp = document.querySelector(`.edit-input[data-key="${k}"]`);
    if (inp) inp.value = v;
  });

  // 更新赛季数据块（如果有本周汇总）
  if (ws) updateWeekStatBlocks(ws);
}

function updateWeekStatBlocks(ws) {
  // 简单：把本周数据也写到 mini stats 里（如果没有赛季累计）
}

// ══════════════════════════════════════════════════════════════════════════════
// 更新赛季统计块
// ══════════════════════════════════════════════════════════════════════════════
function updateSeasonStats(s) {
  if (!s || !s.games_played) return;
  const mini = document.querySelector('.stats-mini-grid');
  if (!mini) return;
  const vals = [
    {v: (s.pts||0).toFixed(1), lbl:'得分', cls:'cyan'},
    {v: (s.reb||0).toFixed(1), lbl:'篮板', cls:'green'},
    {v: (s.ast||0).toFixed(1), lbl:'助攻', cls:'yellow'},
    {v: (s.stl||0).toFixed(1), lbl:'抢断', cls:'purple'},
    {v: (s.blk||0).toFixed(1), lbl:'盖帽', cls:'orange'},
    {v: ((s.fg_pct||0)*100).toFixed(1)+'%', lbl:'FG%', cls:''},
    {v: ((s.fg3_pct||0)*100).toFixed(1)+'%', lbl:'3P%', cls:''},
    {v: ((s.ft_pct||0)*100).toFixed(1)+'%', lbl:'FT%', cls:''},
  ];
  mini.innerHTML = vals.map(x =>
    `<div class="smc"><span class="smc-val ${x.cls}">${x.v}</span><span class="smc-lbl">${x.lbl}</span></div>`
  ).join('');
}

// ══════════════════════════════════════════════════════════════════════════════
// 更新周数进度
// ══════════════════════════════════════════════════════════════════════════════
function updateWeekNum(week) {
  const el = document.getElementById('week-num');
  if (el) el.textContent = week;
  const navEl = document.getElementById('nav-week');
  if (navEl) navEl.textContent = `第 ${week} 周`;
  const bar = document.getElementById('wp-bar');
  if (bar) bar.style.width = Math.min(100, week/30*100) + '%';
}

// ══════════════════════════════════════════════════════════════════════════════
// 处理选择事件（弹窗）
// ══════════════════════════════════════════════════════════════════════════════
const SCOPE_LABELS = {
  week: {text:'影响：几场比赛', cls:'scope-week'},
  month: {text:'影响：约一个月', cls:'scope-month'},
  season: {text:'影响：本赛季', cls:'scope-season'},
  career: {text:'影响：整个职业生涯', cls:'scope-career'},
};

async function handleChoices(choices) {
  for (const choiceData of choices) {
    const chosen = await showChoiceModal(choiceData);
    if (chosen) {
      await applyChoice(choiceData, chosen);
    }
  }
}

function showChoiceModal(choiceData) {
  return new Promise((resolve) => {
    const overlay = document.getElementById('choice-overlay');
    document.getElementById('choice-title').textContent = choiceData.title;
    const narrative = (choiceData.narrative || '').trim().slice(0, 300);
    document.getElementById('choice-narrative').textContent = narrative;
    document.getElementById('choice-prompt').textContent = choiceData.prompt;

    const optsEl = document.getElementById('choice-options');
    optsEl.innerHTML = '';
    choiceData.options.forEach(opt => {
      const scope = SCOPE_LABELS[opt.impact_scope] || SCOPE_LABELS.week;
      const div = document.createElement('div');
      div.className = 'choice-option';
      div.innerHTML = `
        <div class="opt-label">${opt.label}</div>
        <div class="opt-desc">${opt.description}</div>
        <div class="opt-scope ${scope.cls}">${scope.text}</div>`;
      div.onclick = () => {
        overlay.style.display = 'none';
        resolve(opt.key);
      };
      optsEl.appendChild(div);
    });

    overlay.style.display = 'flex';
  });
}

async function applyChoice(choiceData, chosenKey) {
  if (typeof SAVE_ID === 'undefined') return;

  const opt = choiceData.options.find(o => o.key === chosenKey);
  if (!opt) return;

  try {
    const resp = await fetch(`/game/${SAVE_ID}/choice`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ chosen_key: chosenKey, options: choiceData.options }),
    });
    const data = await resp.json();
    if (data.ok) {
      // 在事件流追加选择结果
      const feed = document.getElementById('event-feed');
      if (feed) {
        const el = document.createElement('div');
        el.className = 'feed-item major';
        const scope = SCOPE_LABELS[opt.impact_scope] || SCOPE_LABELS.week;
        let deltaHtml = '';
        if (data.delta && Object.keys(data.delta).length) {
          const parts = Object.entries(data.delta).map(([k,v]) => {
            const col = v>0 ? '#22c55e' : '#ef4444';
            return `<span style="color:${col}">${v>0?'+':''}${v} ${ATTR_LABELS[k]||k}</span>`;
          });
          deltaHtml = `<div class="feed-delta">${parts.join('　')}</div>`;
        }
        el.innerHTML = `
          <div class="feed-meta" style="color:#a855f7">⚡ 你的选择</div>
          <div class="feed-title" style="color:#c084fc">▶ ${opt.label}</div>
          <div class="feed-text">${(opt.narrative||'').trim().slice(0,300)}</div>
          <div style="color:${scope.cls==='scope-career'?'#ffc107':scope.cls==='scope-season'?'#eab308':'#4dc3ff'};font-size:12px;margin-top:6px">${scope.text}</div>
          ${deltaHtml}`;
        feed.appendChild(el);
        feed.scrollTop = feed.scrollHeight;
      }

      // 更新属性卡
      if (data.attrs) updatePlayerCard(data.attrs, null);
    }
  } catch(e) {
    console.error('choice error', e);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 赛季结束
// ══════════════════════════════════════════════════════════════════════════════
function showSeasonEnd() {
  const btn = document.getElementById('btn-advance');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '赛季结束';
    btn.style.background = 'linear-gradient(135deg,#1a1000,#2a1800)';
    btn.style.borderColor = '#ffc107';
    btn.style.color = '#ffc107';
  }
  const navWeek = document.getElementById('nav-week');
  if (navWeek) navWeek.textContent = '赛季结束';

  const feed = document.getElementById('event-feed');
  if (feed) {
    const el = document.createElement('div');
    el.innerHTML = `<div style="text-align:center;padding:24px;color:#ffc107;font-size:18px;font-weight:800;
      border:1px solid #ffc107;border-radius:12px;background:rgba(255,193,7,.08);margin-top:12px">
      ══ 赛季结束 ══<br>
      <span style="font-size:13px;color:#94a3b8;font-weight:400;display:block;margin-top:8px">
        点击「查看完整数据」查看生涯统计和历史地位
      </span>
    </div>`;
    feed.appendChild(el);
    feed.scrollTop = feed.scrollHeight;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 保存属性（CRUD）
// ══════════════════════════════════════════════════════════════════════════════
async function saveAttrs() {
  if (typeof SAVE_ID === 'undefined') return;
  const inputs = document.querySelectorAll('.edit-input');
  const payload = {};
  inputs.forEach(inp => { payload[inp.dataset.key] = inp.value; });

  const resp = await fetch(`/game/${SAVE_ID}/update-attrs`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  const fb = document.getElementById('edit-feedback');
  if (fb) { fb.textContent = data.ok ? '已保存' : '失败'; }
}

// ══════════════════════════════════════════════════════════════════════════════
// 神模式 Override
// ══════════════════════════════════════════════════════════════════════════════
async function saveOverrides() {
  if (typeof SAVE_ID === 'undefined') return;
  const inputs = document.querySelectorAll('.override-input');
  const payload = {};
  inputs.forEach(inp => {
    if (inp.value.trim()) payload[inp.dataset.key] = inp.value;
  });
  const resp = await fetch(`/game/${SAVE_ID}/override`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  const fb = document.getElementById('override-feedback');
  if (fb) fb.textContent = data.ok ? `已开启：${Object.entries(data.overrides).map(([k,v])=>`${k}=${v}`).join(', ')}` : '失败';
}

async function clearOverrides() {
  if (typeof SAVE_ID === 'undefined') return;
  document.querySelectorAll('.override-input').forEach(inp => inp.value='');
  await fetch(`/game/${SAVE_ID}/override`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({}),
  });
  const fb = document.getElementById('override-feedback');
  if (fb) fb.textContent = '已关闭神模式';
}

// ══════════════════════════════════════════════════════════════════════════════
// Toast 提示
// ══════════════════════════════════════════════════════════════════════════════
function showToast(msg, isError = false) {
  const existing = document.getElementById('nba-toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.id = 'nba-toast';
  t.textContent = msg;
  t.style.cssText = `
    position:fixed; top:60px; left:50%; transform:translateX(-50%);
    background:${isError ? '#2a0a0a' : '#0a2810'};
    border:1px solid ${isError ? '#ef4444' : '#22c55e'};
    color:${isError ? '#ef4444' : '#22c55e'};
    padding:8px 20px; border-radius:20px; font-size:13px; font-weight:600;
    z-index:9999; pointer-events:none;
    animation: fadeInOut 2.5s ease forwards;
  `;
  document.body.appendChild(t);
  // CSS animation
  if (!document.getElementById('toast-style')) {
    const s = document.createElement('style');
    s.id = 'toast-style';
    s.textContent = `@keyframes fadeInOut {
      0%{opacity:0;transform:translateX(-50%) translateY(-8px)}
      15%{opacity:1;transform:translateX(-50%) translateY(0)}
      75%{opacity:1}
      100%{opacity:0;transform:translateX(-50%) translateY(-4px)}
    }`;
    document.head.appendChild(s);
  }
  setTimeout(() => t.remove(), 2600);
}

// ══════════════════════════════════════════════════════════════════════════════
// 键盘快捷键
// ══════════════════════════════════════════════════════════════════════════════
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.code === 'Space') { e.preventDefault(); advanceWeek(); }
});
