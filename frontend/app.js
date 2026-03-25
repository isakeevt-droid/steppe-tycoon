const API = '/api';

const goldEl = document.getElementById('gold');
const tapDamageEl = document.getElementById('tap-damage');
const dpsEl = document.getElementById('dps');
const waveEl = document.getElementById('wave');
const trophiesEl = document.getElementById('trophies');
const scoreEl = document.getElementById('score');
const stageEl = document.getElementById('stage');
const enemyTypeEl = document.getElementById('enemy-type');
const enemyNameEl = document.getElementById('enemy-name');
const enemyFlavorEl = document.getElementById('enemy-flavor');
const enemyImageEl = document.getElementById('enemy-image');
const enemyGlyphEl = document.getElementById('enemy-glyph');
const enemyWrapEl = document.getElementById('enemy-wrap');
const enemyHpEl = document.getElementById('enemy-hp');
const enemyHpFillEl = document.getElementById('enemy-hp-fill');
const enemyRewardEl = document.getElementById('enemy-reward');
const bossKillsEl = document.getElementById('boss-kills');
const tapUpgradeBtnEl = document.getElementById('tap-upgrade-btn');
const tapUpgradeCostEl = document.getElementById('tap-upgrade-cost');
const critChanceEl = document.getElementById('crit-chance');
const critMultiplierEl = document.getElementById('crit-multiplier');
const goldBonusEl = document.getElementById('gold-bonus');
const killsEl = document.getElementById('kills');

const metaTrophiesEl = document.getElementById('meta-trophies');
const metaPowerBonusEl = document.getElementById('meta-power-bonus');
const metaGoldBonusEl = document.getElementById('meta-gold-bonus');
const metaCritMultiplierEl = document.getElementById('meta-crit-multiplier');

const activeHeroesListEl = document.getElementById('active-heroes-list');
const heroesListEl = document.getElementById('heroes-list');
const ritualsListEl = document.getElementById('rituals-list');
const rebirthBtnEl = document.getElementById('rebirth-btn');
const rebirthGainEl = document.getElementById('rebirth-gain');
const rebirthCountEl = document.getElementById('rebirth-count');
const achievementsSummaryEl = document.getElementById('achievements-summary');
const achievementsListEl = document.getElementById('achievements-list');
const topBestScoreEl = document.getElementById('top-best-score');
const topMyRankEl = document.getElementById('top-my-rank');
const leaderboardListEl = document.getElementById('leaderboard-list');
const playerNameEl = document.getElementById('player-name');
const playerAuthStatusEl = document.getElementById('player-auth-status');
const toastEl = document.getElementById('toast');
const hitFloatEl = document.getElementById('hit-float');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-section');

let state = null;
let loading = false;
let pollTimer = null;
let toastTimer = null;
let telegramUser = null;
let telegramInitData = '';
let guestId = localStorage.getItem('steppe_shaman_guest_id') || `guest-${Math.random().toString(36).slice(2, 10)}`;
localStorage.setItem('steppe_shaman_guest_id', guestId);

function fmt(value) {
  const n = Number(value || 0);
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  if (Math.abs(n) >= 100) return String(Math.round(n));
  if (Number.isInteger(n)) return String(n);
  return n.toFixed(2);
}

function showToast(text) {
  toastEl.textContent = text;
  toastEl.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.add('hidden'), 1800);
}

function initTelegram() {
  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  if (!tg) return;
  try {
    tg.ready();
    tg.expand();
  } catch (_) {}
  telegramInitData = tg.initData || '';
  telegramUser = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user : null;
}

function buildAuthHeaders() {
  const headers = {};
  if (telegramUser) {
    headers['X-Telegram-User'] = JSON.stringify(telegramUser);
  }
  if (telegramInitData) {
    headers['X-Telegram-Init-Data'] = telegramInitData;
  }
  headers['X-Player-Id'] = guestId;
  return headers;
}


async function request(path, method = 'GET', body = null) {
  const options = { method, headers: buildAuthHeaders() };
  if (body) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  const res = await fetch(`${API}${path}`, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'request_failed');
  return data;
}


function enemyTypeLabel(type) {
  if (type === 'boss') return 'Босс';
  if (type === 'elite') return 'Элитка';
  return 'Обычный замес';
}

function activateTab(tab) {
  tabButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.tab === tab));
  tabPanels.forEach((panel) => panel.classList.toggle('active', panel.dataset.panel === tab));
}

tabButtons.forEach((btn) => btn.addEventListener('click', () => activateTab(btn.dataset.tab)));

function renderHit(lastHit) {
  if (!lastHit) return;
  hitFloatEl.textContent = `${lastHit.crit ? 'Крит ' : '-'}${fmt(lastHit.damage)}`;
  hitFloatEl.className = `hit-float ${lastHit.crit ? 'crit' : ''}`;
  void hitFloatEl.offsetWidth;
  hitFloatEl.classList.remove('hidden');
  setTimeout(() => hitFloatEl.classList.add('hidden'), 420);
}

function playHitEffect(event) {
  if (!event) return;

  const rect = enemyWrapEl.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  enemyWrapEl.classList.remove('hit');
  void enemyWrapEl.offsetWidth;
  enemyWrapEl.classList.add('hit');

  const spark = document.createElement('div');
  spark.className = 'hit-spark';
  spark.style.left = `${x}px`;
  spark.style.top = `${y}px`;

  const ring = document.createElement('div');
  ring.className = 'hit-ring';
  ring.style.left = `${x}px`;
  ring.style.top = `${y}px`;

  enemyWrapEl.appendChild(spark);
  enemyWrapEl.appendChild(ring);

  setTimeout(() => spark.remove(), 300);
  setTimeout(() => ring.remove(), 400);
  setTimeout(() => enemyWrapEl.classList.remove('hit'), 150);
}

function renderActiveHeroes(activeHeroes) {
  if (!activeHeroesListEl) return;

  if (!activeHeroes || activeHeroes.length === 0) {
    activeHeroesListEl.innerHTML = `
      <div class="ritual-row">
        <div>
          <div class="card-title">Пока пусто</div>
          <div class="card-desc">Как только наймёшь первого шамана, он появится здесь.</div>
        </div>
      </div>
    `;
    return;
  }

  activeHeroesListEl.innerHTML = activeHeroes.map((hero) => `
    <div class="card-row">
      <img src="${hero.asset}" alt="${hero.name}">
      <div class="card-info">
        <div class="card-title">${hero.name}</div>
        <div class="card-sub">${hero.title}</div>
        <div class="card-stats">
          <span class="chip">Уровень ${hero.level}</span>
          <span class="chip">Личный DPS ${fmt(hero.dps)}</span>
        </div>
        <div class="card-stats card-stats-secondary">
          <span class="chip">${hero.passive}</span>
        </div>
      </div>
    </div>
  `).join('');
}

function renderHeroes(heroes) {
  heroesListEl.innerHTML = heroes.map((hero) => `
    <div class="card-row">
      <img src="${hero.asset}" alt="${hero.name}">
      <div class="card-info">
        <div class="card-title">${hero.name}</div>
        <div class="card-sub">${hero.title}</div>
        <div class="card-desc">${hero.desc}</div>
        <div class="card-stats">
          <span class="chip">Уровень ${hero.level}</span>
          <span class="chip">Личный DPS ${fmt(hero.dps)}</span>
          <span class="chip">Порогов взято x${hero.breakpoints + 1}</span>
        </div>
        <div class="card-stats card-stats-secondary">
          <span class="chip">${hero.passive}</span>
        </div>
        <div class="card-next">${hero.next_bonus}</div>
      </div>
      <div class="card-actions">
        <div class="cost">${fmt(hero.cost)} золота</div>
        <button class="action-btn" data-hero-id="${hero.id}">Забрать в круг</button>
      </div>
    </div>
  `).join('');

  heroesListEl.querySelectorAll('[data-hero-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        const next = await request('/buy-hero', 'POST', { id: btn.dataset.heroId });
        setState(next);
      } catch (error) {
        showToast(error.message === 'not_enough_gold' ? 'Золота маловато' : 'Не вышло подтянуть шамана');
      } finally {
        loading = false;
      }
    });
  });
}

function renderRituals(rituals) {
  ritualsListEl.innerHTML = rituals.map((ritual) => `
    <div class="ritual-row">
      <div>
        <div class="card-title">${ritual.name}</div>
        <div class="card-desc">${ritual.desc}</div>
        <div class="card-stats"><span class="chip">Уровень ${ritual.level}</span></div>
      </div>
      <div class="card-actions">
        <div class="cost">${fmt(ritual.cost)} золота</div>
        <button class="action-btn" data-ritual-id="${ritual.id}">Провести</button>
      </div>
    </div>
  `).join('');

  ritualsListEl.querySelectorAll('[data-ritual-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        const next = await request('/buy-ritual', 'POST', { id: btn.dataset.ritualId });
        setState(next);
      } catch (error) {
        showToast(error.message === 'not_enough_gold' ? 'Золота маловато' : 'Ритуал не прокнулся');
      } finally {
        loading = false;
      }
    });
  });
}

function renderTop(top) {
  topBestScoreEl.textContent = fmt(top.best_score);
  topMyRankEl.textContent = top.my_rank ? `#${top.my_rank}` : '—';

  if (!leaderboardListEl) return;

  if (!top.leaderboard || top.leaderboard.length === 0) {
    leaderboardListEl.innerHTML = '<div class="empty-note">Пока топ пустой. Кто первый нафармит — тот и хан.</div>';
    return;
  }

  leaderboardListEl.innerHTML = top.leaderboard.map((item) => `
    <div class="leaderboard-row ${item.is_me ? 'is-me' : ''}">
      <div class="leaderboard-rank">#${item.rank}</div>
      <div class="leaderboard-main">
        <div class="leaderboard-name">${item.name}</div>
        <div class="leaderboard-sub">Этап ${item.best_stage} · Трофеи ${fmt(item.trophies)}</div>
      </div>
      <div class="leaderboard-score">${fmt(item.best_score)}</div>
    </div>
  `).join('');
}


function renderAchievements(achievements) {
  achievementsSummaryEl.textContent = `${achievements.unlocked} / ${achievements.total}`;
  achievementsListEl.innerHTML = achievements.items.map((item) => {
    const progress = Math.max(0, Math.min(100, (Number(item.value) / Number(item.target)) * 100));
    return `
      <div class="achievement ${item.done ? 'done' : ''}">
        <div class="achievement-head">
          <strong>${item.name}</strong>
          <span>${fmt(item.value)} / ${fmt(item.target)}</span>
        </div>
        <div class="card-desc">${item.desc}</div>
        <div class="achievement-bar"><div style="width:${progress}%"></div></div>
      </div>
    `;
  }).join('');
}

function setState(next) {
  state = next;

  if (playerNameEl && state.player) {
    playerNameEl.textContent = state.player.name || 'Гость степи';
    playerAuthStatusEl.textContent = state.player.is_telegram ? 'Автовход через Telegram' : 'Локальный вход';
  }

  goldEl.textContent = fmt(state.gold);
  tapDamageEl.textContent = fmt(state.tap_damage);
  dpsEl.textContent = fmt(state.dps);
  waveEl.textContent = state.wave;
  trophiesEl.textContent = fmt(state.trophies);
  scoreEl.textContent = fmt(state.score);

  stageEl.textContent = state.stage;
  enemyTypeEl.textContent = enemyTypeLabel(state.enemy.type);
  enemyNameEl.textContent = state.enemy.name;
  enemyFlavorEl.textContent = state.enemy.flavor || '';
  enemyWrapEl.className = `enemy-wrap ${state.enemy.type} ${state.enemy.id || ''}`;

  if (state.enemy.type === 'normal') {
    enemyImageEl.removeAttribute('src');
    enemyImageEl.classList.add('hidden');
    enemyGlyphEl.innerHTML = state.enemy.glyph
      ? `<img src="${state.enemy.glyph}" alt="${state.enemy.name}" class="enemy-icon">`
      : '✦';
    enemyGlyphEl.classList.remove('hidden');
  } else {
    enemyImageEl.src = state.enemy.asset;
    enemyImageEl.classList.remove('hidden');
    enemyGlyphEl.classList.add('hidden');
    enemyGlyphEl.innerHTML = '';
  }

  enemyHpEl.textContent = `${fmt(state.enemy.hp)} / ${fmt(state.enemy.max_hp)}`;
  const hpPercent = state.enemy.max_hp > 0 ? (state.enemy.hp / state.enemy.max_hp) * 100 : 0;
  enemyHpFillEl.style.width = `${Math.max(0, Math.min(100, hpPercent))}%`;
  enemyRewardEl.textContent = fmt(state.enemy.reward);
  bossKillsEl.textContent = state.boss_kills;

  tapUpgradeCostEl.textContent = fmt(state.tap_cost);
  critChanceEl.textContent = `${state.crit_chance}%`;
  critMultiplierEl.textContent = `x${state.crit_multiplier}`;
  goldBonusEl.textContent = `${state.gold_bonus}%`;
  killsEl.textContent = state.kills;

  metaTrophiesEl.textContent = fmt(state.trophies);
  metaPowerBonusEl.textContent = `${state.power_bonus}%`;
  metaGoldBonusEl.textContent = `${state.gold_bonus}%`;
  metaCritMultiplierEl.textContent = `x${state.crit_multiplier}`;

  rebirthGainEl.textContent = state.rebirth_gain;
  rebirthCountEl.textContent = state.rebirths;

  renderActiveHeroes(state.active_heroes);
  renderHeroes(state.heroes);
  renderRituals(state.rituals);
  renderTop(state.top);
  renderAchievements(state.achievements);
  renderHit(state.last_hit);
}

async function refreshState(silent = false) {
  try {
    const next = await request('/state');
    setState(next);
  } catch (error) {
    if (!silent) showToast('Сервер степи молчит');
  }
}

async function tapEnemy(event) {
  if (event) {
    playHitEffect(event);
  }

  if (loading) return;

  try {
    loading = true;
    const next = await request('/tap', 'POST');
    setState(next);
  } catch {
    showToast('Удар не прошёл');
  } finally {
    loading = false;
  }
}

async function upgradeTap() {
  if (loading) return;
  try {
    loading = true;
    const next = await request('/upgrade-tap', 'POST');
    setState(next);
  } catch (error) {
    showToast(error.message === 'not_enough_gold' ? 'Золота маловато' : 'Апыч не прошёл');
  } finally {
    loading = false;
  }
}

async function rebirth() {
  if (!window.confirm('Уйти в перерод и обменять текущий забег на трофеи?')) return;
  try {
    loading = true;
    const next = await request('/rebirth', 'POST');
    setState(next);
    showToast('Перерод удался');
  } catch (error) {
    showToast(error.message === 'rebirth_locked' ? 'Сначала дожми хотя бы первого босса или этап 10' : 'Перерод не сработал');
  } finally {
    loading = false;
  }
}

enemyWrapEl.addEventListener('click', tapEnemy);
tapUpgradeBtnEl.addEventListener('click', upgradeTap);
rebirthBtnEl.addEventListener('click', rebirth);

document.addEventListener('keydown', (event) => {
  if (event.code === 'Space') {
    event.preventDefault();
    tapEnemy();
  }
});

async function boot() {
  await refreshState();
  clearInterval(pollTimer);
  pollTimer = setInterval(() => refreshState(true), 800);
}

boot();