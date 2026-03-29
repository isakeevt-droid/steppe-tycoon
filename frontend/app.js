const API = '/api';

const $ = (id) => document.getElementById(id);
const bySelectorAll = (selector) => Array.from(document.querySelectorAll(selector));

const els = {
  gold: $('gold'),
  tapDamage: $('tap-damage'),
  dps: $('dps'),
  wave: $('wave'),
  trophies: $('trophies'),
  score: $('score'),
  stage: $('stage'),
  enemyType: $('enemy-type'),
  enemyName: $('enemy-name'),
  enemyFlavor: $('enemy-flavor'),
  highShamanIcon: $('high-shaman-icon'),
  highShamanHp: $('high-shaman-hp'),
  highShamanHpFill: $('high-shaman-hp-fill'),
  highShamanShield: $('high-shaman-shield'),
  highShamanShieldFill: $('high-shaman-shield-fill'),
  highShamanDefense: $('high-shaman-defense'),
  highShamanRegen: $('high-shaman-regen'),
  highShamanHealPower: $('high-shaman-heal-power'),
  playerHitFloat: $('player-hit-float'),
  playerHealFloat: $('player-heal-float'),
  tapDamageInline: $('tap-damage-inline'),
  dpsInline: $('dps-inline'),
  critInline: $('crit-inline'),
  enemyImage: $('enemy-image'),
  enemyGlyph: $('enemy-glyph'),
  enemyWrap: $('enemy-wrap'),
  enemyHp: $('enemy-hp'),
  enemyHpFill: $('enemy-hp-fill'),
  enemyShield: $('enemy-shield'),
  enemyShieldFill: $('enemy-shield-fill'),
  bossShieldBlock: $('boss-shield-block'),
  enemyReward: $('enemy-reward'),
  bossKills: $('boss-kills'),
  tapUpgradeBtn: $('tap-upgrade-btn'),
  tapUpgradeCost: $('tap-upgrade-cost'),
  critChance: $('crit-chance'),
  critMultiplier: $('crit-multiplier'),
  goldBonus: $('gold-bonus'),
  kills: $('kills'),
  metaTrophies: $('meta-trophies'),
  metaPowerBonus: $('meta-power-bonus'),
  metaGoldBonus: $('meta-gold-bonus'),
  metaCritMultiplier: $('meta-crit-multiplier'),
  activeHeroesList: $('active-heroes-list'),
  heroesList: $('heroes-list'),
  rebirthBtn: $('rebirth-btn'),
  rebirthGain: $('rebirth-gain'),
  rebirthCount: $('rebirth-count'),
  rebirthDepth: $('rebirth-depth'),
  rebirthBoss: $('rebirth-boss'),
  rebirthWaveBonus: $('rebirth-wave-bonus'),
  rebirthElite: $('rebirth-elite'),
  rebirthLockText: $('rebirth-lock-text'),
  blessingsList: $('blessings-list'),
  blessingSynergies: $('blessing-synergies'),
  rebirthOverlay: $('rebirth-overlay'),
  overlayRebirthGain: $('overlay-rebirth-gain'),
  rebirthChoiceList: $('rebirth-choice-list'),
  rebirthContinueBtn: $('rebirth-continue-btn'),
  rebirthResultText: $('rebirth-result-text'),
  rebirthStep1: $('rebirth-step-1'),
  rebirthStep2: $('rebirth-step-2'),
  rebirthRitualFx: $('rebirth-ritual-fx'),
  achievementsSummary: $('achievements-summary'),
  achievementsList: $('achievements-list'),
  topBestScore: $('top-best-score'),
  topMyRank: $('top-my-rank'),
  leaderboardList: $('leaderboard-list'),
  playerName: $('player-name'),
  playerAuthStatus: $('player-auth-status'),
  toast: $('toast'),
  hitFloat: $('hit-float'),
  killFloat: $('kill-float'),
  bossMechanicPanel: $('boss-mechanic-panel'),
  bossMechanicName: $('boss-mechanic-name'),
  bossMechanicDesc: $('boss-mechanic-desc'),
  bossMechanicStatus: $('boss-mechanic-status'),
  bossMechanicPhase: $('boss-mechanic-phase'),
  swipeMeterFill: $('swipe-meter-fill'),
  swipeComboName: $('swipe-combo-name'),
  swipeComboText: $('swipe-combo-text'),
  swipeHistory: $('swipe-history'),
  swipeHint: $('swipe-hint'),
  holdMeterFill: $('hold-meter-fill'),
  holdName: $('hold-name'),
  holdText: $('hold-text'),
  holdLastMs: $('hold-last-ms'),
  holdWaterState: $('hold-water-state'),
  holdEarthState: $('hold-earth-state'),
  holdHint: $('hold-hint'),
  swipeTrailLayer: $('swipe-trail-layer'),
  waveLocation: $('wave-location'),
  waveHint: $('wave-hint'),
  waveRecommended: $('wave-recommended'),
  waveProgressPill: $('wave-progress-pill'),
  startWaveBtn: $('start-wave-btn'),
  stopExpeditionBtn: $('stop-expedition-btn'),
  waveTransitionOverlay: $('wave-transition-overlay'),
  waveTransitionWave: $('wave-transition-wave'),
  waveTransitionTitle: $('wave-transition-title'),
  waveTransitionCopy: $('wave-transition-copy'),
  waveTransitionReward: $('wave-transition-reward'),
  waveTransitionContinueBtn: $('wave-transition-continue-btn'),
  waveTransitionStopBtn: $('wave-transition-stop-btn'),
};

const tabButtons = bySelectorAll('.tab-btn');
const tabPanels = bySelectorAll('.tab-section');
const ELEMENTAL_FX_CLASSES = ['fx-fire-wind', 'fx-storm', 'fx-lava', 'fx-sand', 'fx-mud', 'fx-steam', 'fx-fire', 'fx-water', 'fx-wind', 'fx-earth', 'fx-arcane', 'fx-shadow'];
const SWIPE_MIN_DISTANCE = 42;
const HOLD_TRIGGER_MS = 240;
const HOLD_MAX_MS = 2200;
const POLL_INTERVAL_MS = 800;

let state = null;
let loading = false;
let pollTimer = null;
let toastTimer = null;
let swipeFxTimer = null;
let holdChargeTimer = null;
let telegramUser = null;
let telegramInitData = '';
let localSwipeHistory = [];
let guestId = localStorage.getItem('steppe_shaman_guest_id') || `guest-${Math.random().toString(36).slice(2, 10)}`;

localStorage.setItem('steppe_shaman_guest_id', guestId);

let pendingWaveAutoStart = false;

let pointerState = {
  active: false,
  pointerId: null,
  startX: 0,
  startY: 0,
  lastX: 0,
  lastY: 0,
  startedAt: 0,
  moved: false,
  path: [],
};

let holdVisual = {
  marker: null,
  ring: null,
  label: null,
};

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function fmt(value) {
  const n = Number(value || 0);
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  if (Number.isInteger(n)) return String(n);
  if (Math.abs(n) >= 100) return String(Math.round(n));
  return n.toFixed(2);
}

function setText(el, value) {
  if (el) el.textContent = value;
}

function setHtml(el, value) {
  if (el) el.innerHTML = value;
}

function showToast(text) {
  if (!els.toast) return;
  els.toast.textContent = text;
  els.toast.classList.remove('hidden');
  void els.toast.offsetWidth;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    els.toast?.classList.add('hidden');
  }, 1900);
}

function enemyTypeLabel(type) {
  if (type === 'boss') return 'Босс';
  if (type === 'elite') return 'Элитка';
  if (type === 'group') return 'Пачка';
  return 'Обычный замес';
}

function directionLabel(direction) {
  return ({ up: '↑', down: '↓', left: '←', right: '→' }[direction] || '↔');
}

function pairLabel(pairKey) {
  const map = {
    solo: 'Базовые жесты',
    fire_air: 'Огонь + Воздух',
    fire_water: 'Огонь + Вода',
    fire_earth: 'Огонь + Земля',
    air_water: 'Воздух + Вода',
    air_earth: 'Воздух + Земля',
    water_earth: 'Вода + Земля',
  };
  return map[pairKey] || 'Комбо жестов';
}

function recommendedPairsText(items) {
  const list = safeArray(items).map((item) => String(item || '').trim()).filter(Boolean);
  return list.length ? `Следы: ${list.join(' · ')}` : 'Следы: степь молчит';
}

function renderGroupGlyph(enemy) {
  const count = Math.max(3, Math.min(6, Number(enemy.count || 4)));
  const icons = Array.from({ length: count }, (_, index) => `
    <div class="enemy-pack-icon slot-${index + 1}">
      <img src="${enemy.glyph}" alt="${enemy.name}" class="enemy-icon">
    </div>`).join('');
  return `<div class="enemy-pack">${icons}<div class="enemy-pack-badge">x${count}</div></div>`;
}

function activateTab(tab) {
  tabButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.tab === tab));
  tabPanels.forEach((panel) => panel.classList.toggle('active', panel.dataset.panel === tab));
}

tabButtons.forEach((btn) => btn.addEventListener('click', () => activateTab(btn.dataset.tab)));

function initTelegram() {
  const tg = window.Telegram?.WebApp || null;
  if (!tg) return;
  try {
    tg.ready();
    tg.expand();
  } catch (_) {}
  telegramInitData = tg.initData || '';
  telegramUser = tg.initDataUnsafe?.user || null;
}

function buildAuthHeaders() {
  const headers = { 'X-Player-Id': guestId };
  if (telegramUser) headers['X-Telegram-User'] = JSON.stringify(telegramUser);
  if (telegramInitData) headers['X-Telegram-Init-Data'] = telegramInitData;
  return headers;
}

async function request(path, method = 'GET', body = null) {
  const options = { method, headers: buildAuthHeaders() };
  if (body) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  const res = await fetch(`${API}${path}`, options);
  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : null;

  if (!res.ok) {
    throw new Error(data?.error || 'request_failed');
  }
  return data;
}

function setButtonsDisabled(disabled) {
  if (els.tapUpgradeBtn) els.tapUpgradeBtn.disabled = disabled;
  if (els.startWaveBtn) els.startWaveBtn.disabled = disabled || Boolean(state?.wave_state?.in_progress);
  if (els.stopExpeditionBtn) els.stopExpeditionBtn.disabled = disabled || !Boolean(state?.wave_state?.in_progress);
  if (els.rebirthBtn) els.rebirthBtn.disabled = disabled || !(state?.can_rebirth);
  document.querySelectorAll('[data-hero-buy-id], [data-hero-toggle-id], [data-active-hero-id]').forEach((node) => {
    node.disabled = disabled;
  });
}

function clearElementalFx() {
  if (!els.enemyWrap) return;
  els.enemyWrap.classList.remove('swipe-up', 'swipe-down', 'swipe-left', 'swipe-right', 'combo-active', 'tap-pulse', 'hold-pulse', ...ELEMENTAL_FX_CLASSES);
}

function pulseEnemy(effectClass = '', source = 'tap') {
  if (!els.enemyWrap) return;
  clearElementalFx();
  void els.enemyWrap.offsetWidth;
  els.enemyWrap.classList.add(source === 'hold' ? 'hold-pulse' : 'tap-pulse');
  if (effectClass) els.enemyWrap.classList.add(effectClass);
  clearTimeout(swipeFxTimer);
  swipeFxTimer = setTimeout(clearElementalFx, source === 'hold' ? 560 : 360);
}

function pointFromClient(clientX, clientY) {
  const rect = els.enemyWrap?.getBoundingClientRect();
  if (!rect) return { x: 0, y: 0 };
  return { x: clientX - rect.left, y: clientY - rect.top };
}

function playPointBurst(clientX, clientY, className = '') {
  if (!els.enemyWrap) return;
  const { x, y } = pointFromClient(clientX, clientY);

  els.enemyWrap.classList.remove('hit');
  void els.enemyWrap.offsetWidth;
  els.enemyWrap.classList.add('hit');

  const spark = document.createElement('div');
  spark.className = `hit-spark ${className}`.trim();
  spark.style.left = `${x}px`;
  spark.style.top = `${y}px`;

  const ring = document.createElement('div');
  ring.className = `hit-ring ${className}`.trim();
  ring.style.left = `${x}px`;
  ring.style.top = `${y}px`;

  els.enemyWrap.appendChild(spark);
  els.enemyWrap.appendChild(ring);

  setTimeout(() => spark.remove(), 340);
  setTimeout(() => ring.remove(), 430);
  setTimeout(() => els.enemyWrap?.classList.remove('hit'), 160);
}

function visualStyle(effectClass) {
  const map = {
    'fx-basic': { color: 'rgba(232,238,255,0.95)', glow: 'rgba(255,255,255,0.65)' },
    'fx-fire': { color: 'rgba(255,132,51,0.98)', glow: 'rgba(255,91,0,0.72)' },
    'fx-water': { color: 'rgba(102,194,255,0.98)', glow: 'rgba(67,142,255,0.7)' },
    'fx-earth': { color: 'rgba(189,152,106,0.98)', glow: 'rgba(124,93,57,0.7)' },
    'fx-wind': { color: 'rgba(205,238,255,0.98)', glow: 'rgba(122,213,255,0.68)' },
    'fx-fire-wind': { color: 'rgba(255,170,91,0.98)', glow: 'rgba(255,120,36,0.78)' },
    'fx-storm': { color: 'rgba(135,214,255,0.98)', glow: 'rgba(103,146,255,0.78)' },
    'fx-lava': { color: 'rgba(255,101,54,0.98)', glow: 'rgba(255,51,0,0.8)' },
    'fx-sand': { color: 'rgba(232,198,132,0.98)', glow: 'rgba(179,131,45,0.72)' },
    'fx-mud': { color: 'rgba(153,123,94,0.98)', glow: 'rgba(98,71,44,0.76)' },
    'fx-steam': { color: 'rgba(221,233,255,0.98)', glow: 'rgba(172,196,255,0.74)' },
    'fx-arcane': { color: 'rgba(180,150,255,0.98)', glow: 'rgba(117,85,255,0.76)' },
    'fx-shadow': { color: 'rgba(155,167,208,0.96)', glow: 'rgba(79,90,131,0.74)' },
  };
  return map[effectClass || 'fx-basic'] || map['fx-basic'];
}

function normalizedSwipePath(path, direction) {
  const rect = els.enemyWrap?.getBoundingClientRect();
  if (!rect) return [];
  if (Array.isArray(path) && path.length >= 2) {
    return path.map((point) => ({ x: point.x - rect.left, y: point.y - rect.top }));
  }
  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const offset = Math.min(rect.width, rect.height) * 0.24;
  if (direction === 'up') return [{ x: cx, y: cy + offset }, { x: cx, y: cy - offset }];
  if (direction === 'down') return [{ x: cx, y: cy - offset }, { x: cx, y: cy + offset }];
  if (direction === 'left') return [{ x: cx + offset, y: cy }, { x: cx - offset, y: cy }];
  return [{ x: cx - offset, y: cy }, { x: cx + offset, y: cy }];
}

function clearSwipeTrailLayer() {
  if (els.swipeTrailLayer) {
    els.swipeTrailLayer.innerHTML = '';
  }
}

function createTrailSegment(from, to, style, effectClass, isCombo) {
  if (!els.swipeTrailLayer) return;
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.max(12, Math.hypot(dx, dy));
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);

  const seg = document.createElement('div');
  seg.className = `swipe-trail-line ${effectClass || 'fx-basic'} ${isCombo ? 'combo-line' : ''}`.trim();
  seg.style.position = 'absolute';
  seg.style.left = `${from.x}px`;
  seg.style.top = `${from.y}px`;
  seg.style.width = `${length}px`;
  seg.style.height = isCombo ? '7px' : '5px';
  seg.style.transformOrigin = '0 50%';
  seg.style.transform = `translateY(-50%) rotate(${angle}deg)`;
  seg.style.borderRadius = '999px';
  seg.style.pointerEvents = 'none';
  seg.style.background = `linear-gradient(90deg, rgba(255,255,255,0.02) 0%, ${style.color} 20%, ${style.color} 80%, rgba(255,255,255,0.02) 100%)`;
  seg.style.boxShadow = `0 0 12px ${style.glow}, 0 0 24px ${style.glow}`;
  seg.style.opacity = '0.98';
  seg.style.animation = 'none';
  els.swipeTrailLayer.appendChild(seg);
  setTimeout(() => {
    seg.style.transition = 'opacity 220ms ease';
    seg.style.opacity = '0';
    setTimeout(() => seg.remove(), 240);
  }, 260);
}

function createTrailSpark(x, y, style, effectClass) {
  if (!els.swipeTrailLayer) return;
  const spark = document.createElement('div');
  spark.className = `swipe-trail-spark ${effectClass || 'fx-basic'}`.trim();
  spark.style.position = 'absolute';
  spark.style.left = `${x}px`;
  spark.style.top = `${y}px`;
  spark.style.width = `${6 + Math.random() * 8}px`;
  spark.style.height = spark.style.width;
  spark.style.marginLeft = '-4px';
  spark.style.marginTop = '-4px';
  spark.style.borderRadius = '50%';
  spark.style.pointerEvents = 'none';
  spark.style.background = style.color;
  spark.style.boxShadow = `0 0 10px ${style.glow}, 0 0 22px ${style.glow}`;
  spark.style.opacity = '1';
  els.swipeTrailLayer.appendChild(spark);
  const driftX = Math.random() * 24 - 12;
  const driftY = Math.random() * 24 - 12;
  requestAnimationFrame(() => {
    spark.style.transition = 'transform 320ms ease-out, opacity 320ms ease-out';
    spark.style.transform = `translate(${driftX}px, ${driftY}px) scale(0.4)`;
    spark.style.opacity = '0';
  });
  setTimeout(() => spark.remove(), 340);
}

function drawSwipeTrail(direction, effectClass = 'fx-basic', comboName = '', gesture = null) {
  if (!els.enemyWrap || !els.swipeTrailLayer) return;
  clearElementalFx();
  void els.enemyWrap.offsetWidth;
  els.enemyWrap.classList.add(`swipe-${direction}`);
  if (effectClass) els.enemyWrap.classList.add(effectClass);
  if (comboName) els.enemyWrap.classList.add('combo-active');

  const style = visualStyle(effectClass || 'fx-basic');
  const points = normalizedSwipePath(gesture?.path, direction);
  clearSwipeTrailLayer();

  for (let i = 1; i < points.length; i += 1) {
    createTrailSegment(points[i - 1], points[i], style, effectClass || 'fx-basic', Boolean(comboName));
  }

  const end = points[points.length - 1] || { x: 0, y: 0 };
  for (let i = 0; i < 6; i += 1) {
    createTrailSpark(end.x, end.y, style, effectClass || 'fx-basic');
  }

  clearTimeout(swipeFxTimer);
  swipeFxTimer = setTimeout(() => {
    clearElementalFx();
    clearSwipeTrailLayer();
  }, 520);
}

function triggerEnemyEnter() {
  if (!els.enemyWrap) return;
  els.enemyWrap.classList.remove('enemy-enter');
  void els.enemyWrap.offsetWidth;
  els.enemyWrap.classList.add('enemy-enter');
  setTimeout(() => els.enemyWrap?.classList.remove('enemy-enter'), 280);
}

function hpFillState(percent) {
  if (percent <= 28) return 'hp-low';
  if (percent <= 62) return 'hp-mid';
  return '';
}

function hitLabel(lastHit) {
  if (!lastHit) return '';
  if (lastHit.blocked && lastHit.blocked_reason === 'shield') return 'Щит';
  if (lastHit.blocked && lastHit.blocked_reason === 'earth_shield') return 'Нужна Земля';
  if (lastHit.blocked && lastHit.blocked_reason === 'shadow') return 'Тень';
  if (lastHit.blocked && lastHit.blocked_reason === 'combo_gate') return 'Печать';
  if (lastHit.blocked && lastHit.blocked_reason === 'swipe_gate') return 'Нужен свайп';
  if (lastHit.blocked && lastHit.blocked_reason === 'hold_gate') return 'Нужен hold';
  if (lastHit.blocked && lastHit.blocked_reason === 'pair_mismatch') return 'Не та связка';
  if (lastHit.blocked && lastHit.blocked_reason === 'pair_action_mismatch') return 'Не тот стиль';
  if (lastHit.blocked && lastHit.blocked_reason === 'pair_combo_mismatch') return 'Нужен комбо-свайп';
  if (lastHit.source === 'swipe') {
    if (lastHit.combo_name) return `${lastHit.combo_name} ${fmt(lastHit.damage)}`;
    return `${directionLabel(lastHit.swipe_direction)} ${fmt(lastHit.damage)}`;
  }
  if (lastHit.source === 'hold') return `Hold ${fmt(lastHit.damage)}`;
  return `${lastHit.crit ? 'Крит ' : ''}${fmt(lastHit.damage || 0)}`;
}

function renderHit(lastHit) {
  if (!els.hitFloat || !lastHit || typeof lastHit.damage === 'undefined') return;
  els.hitFloat.textContent = hitLabel(lastHit);
  els.hitFloat.className = `hit-float ${lastHit.crit ? 'crit' : ''} ${lastHit.source === 'swipe' ? 'swipe' : ''}`.trim();
  void els.hitFloat.offsetWidth;
  els.hitFloat.classList.remove('hidden');
  setTimeout(() => els.hitFloat?.classList.add('hidden'), 520);
}

function renderKill(lastHit) {
  if (!els.killFloat || !lastHit || !lastHit.kills) return;
  const reward = lastHit.gold_gained ? ` +${fmt(lastHit.gold_gained)} золота` : '';
  els.killFloat.textContent = lastHit.boss_kill ? `БОСС ПАЛ${reward}` : `Разнос${reward}`;
  els.killFloat.className = `kill-float ${lastHit.boss_kill ? 'boss' : ''}`;
  void els.killFloat.offsetWidth;
  els.killFloat.classList.remove('hidden');
  els.enemyWrap?.classList.add('boss-hit');
  setTimeout(() => els.killFloat?.classList.add('hidden'), 760);
  setTimeout(() => els.enemyWrap?.classList.remove('boss-hit'), 360);
}

function mechanicAction(enemy, lastHit) {
  if (!enemy) return '';
  if (lastHit?.blocked_reason === 'shadow') return 'Бей тапом';
  if (lastHit?.blocked_reason === 'shield' || enemy.mechanic === 'shield_hits') return enemy.shield_hp > 0 ? 'Свайп + Земля по щиту' : 'Щит лопнул';
  if (lastHit?.blocked_reason === 'combo_gate') return 'Тяжёлый свайп вниз';
  if (lastHit?.blocked_reason === 'swipe_gate') return 'Нужен свайп';
  if (lastHit?.blocked_reason === 'hold_gate') return 'Нужен hold';
  if (lastHit?.blocked_reason === 'pair_mismatch') return 'Читай следы локации';
  if (lastHit?.blocked_reason === 'pair_action_mismatch') return 'Эта связка бьёт иначе';
  if (lastHit?.blocked_reason === 'pair_combo_mismatch') return 'Открой тяжёлый комбо-свайп';
  const map = { shadow: 'Тап в окно', shield_hits: 'Свайпни с Землёй', combo_gate: 'DD или RRUU через Землю', rage_phase: 'Дожимай фазу комбо', swipe_gate: 'Режь свайпами', hold_gate: 'Зажимай hold' };
  return map[enemy.mechanic] || (enemy.status || '');
}


function waveVictoryFlavor(waveNumber, enemyType = 'normal') {
  const boss = [
    'Хана прижал. Даже ветер стих.',
    'Большой зверь лёг. Теперь степь дышит ровнее.',
    'Босса осадил жёстко. Круг шаманов не зря ел хлеб.',
  ];
  const elite = [
    'Жирного снял чисто. Без суеты, по делу.',
    'Элитку уложил ровно. След в степи остался.',
    'Крепыша дожал как надо. Пыль только осела.',
  ];
  const regular = [
    'Волна сыпанулась, как сухая трава под ветром.',
    'Разобрал их тихо, по-степному, без лишнего шума.',
    'Тропа чистая. Можно гнать дальше.',
    'Стаю осадил ровно. Степь кивнула.',
  ];
  const pool = enemyType === 'boss' ? boss : enemyType === 'elite' ? elite : regular;
  return pool[(Math.max(1, Number(waveNumber || 1)) - 1) % pool.length];
}

function openWaveTransitionOverlay(summary) {
  if (!els.waveTransitionOverlay || !summary) return;
  setText(els.waveTransitionWave, `Волна ${summary.wave || 1} пройдена`);
  setText(els.waveTransitionTitle, waveVictoryFlavor(summary.wave, summary.enemyType));
  setText(els.waveTransitionCopy, summary.copy || 'Добычу собрал. Дальше решай сам: идти глубже или сворачивать поход.');
  setText(els.waveTransitionReward, `+${fmt(summary.reward || 0)} золота`);
  els.waveTransitionOverlay.classList.remove('hidden');
  document.body.classList.add('wave-transition-open');
}

function closeWaveTransitionOverlay() {
  els.waveTransitionOverlay?.classList.add('hidden');
  document.body.classList.remove('wave-transition-open');
}

function maybeShowWaveTransition(lastHit) {
  if (!lastHit?.wave_completed) return;
  const completedWave = Math.max(1, Number(state?.wave_state?.index || 1) - 1);
  const enemyType = lastHit.enemy_type || lastHit.defeated_enemy_type || 'normal';
  let copy = 'Добычу собрал. Дальше решай сам: идти глубже или сворачивать поход.';
  if (enemyType === 'boss') copy = 'Большого уложил. Добыча тяжёлая, путь дальше ещё злее.';
  else if (enemyType === 'elite') copy = 'Крепкий замес закрыт. Можно брать паузу или жать дальше.';
  openWaveTransitionOverlay({
    wave: completedWave,
    reward: Number(lastHit.gold_gained || lastHit.reward || 0),
    enemyType,
    copy,
  });
}

function renderWavePanel(waveState) {
  if (!waveState) return;
  setText(els.waveLocation, waveState.location || 'Степь');
  setText(els.waveHint, waveState.hint || 'Степь шепчет что-то мутное.');
  setText(els.waveRecommended, recommendedPairsText(waveState.recommended_pairs));
  const progressText = waveState.in_progress
    ? `Бой ${Math.min(Number(waveState.progress || 0) + 1, Math.max(1, Number(waveState.size || 1)))}/${Math.max(1, Number(waveState.size || 1))}`
    : 'Пауза между волнами';
  setText(els.waveProgressPill, progressText);
  if (els.startWaveBtn) {
    els.startWaveBtn.textContent = waveState.in_progress ? 'Волна идёт' : (Number(waveState.index || 1) <= 1 && !Number(waveState.progress || 0) ? 'Начать волну' : 'Следующая волна');
    els.startWaveBtn.disabled = loading || Boolean(waveState.in_progress);
  }
  if (els.stopExpeditionBtn) {
    els.stopExpeditionBtn.disabled = loading || !Boolean(waveState.in_progress);
  }
}

function renderBossMechanic(enemy, lastHit) {
  if (!els.bossMechanicPanel || !enemy || enemy.type !== 'boss' || !enemy.mechanic_name) {
    els.bossMechanicPanel?.classList.add('hidden');
    return;
  }

  els.bossMechanicPanel.classList.remove('hidden');
  setText(els.bossMechanicName, enemy.mechanic_name || '—');
  setText(els.bossMechanicDesc, mechanicAction(enemy, lastHit));
  setText(els.bossMechanicPhase, enemy.phase || 'Босс');
  setText(els.bossMechanicStatus, enemy.status || '');
}

function renderSwipeHud(swipeState, lastHit = null) {
  const history = (lastHit && Array.isArray(lastHit.swipe_history) ? lastHit.swipe_history : swipeState?.history) || [];
  localSwipeHistory = history.slice(-4);

  if (els.swipeHistory) {
    if (localSwipeHistory.length) {
      els.swipeHistory.innerHTML = localSwipeHistory.map((item) => `<span class="swipe-history-chip">${directionLabel(item)}</span>`).join('');
    } else {
      els.swipeHistory.innerHTML = '<span class="swipe-history-chip muted">Жестов пока нет</span>';
    }
  }

  if (lastHit?.source === 'swipe') {
    setText(els.swipeComboName, lastHit.combo_name || directionLabel(lastHit.swipe_direction));
    setText(els.swipeComboText, lastHit.combo_effect || 'Одиночный направленный свайп.');
    if (els.swipeMeterFill) els.swipeMeterFill.style.width = `${lastHit.combo_name ? 100 : 42}%`;
  } else {
    setText(els.swipeComboName, pairLabel(swipeState?.pair_key || 'solo'));
    setText(els.swipeComboText, 'Собери рисунок и вскрой цель.');
    if (els.swipeMeterFill) els.swipeMeterFill.style.width = `${Math.min(100, localSwipeHistory.length * 24)}%`;
  }

  setText(els.swipeHint, `${pairLabel(swipeState?.pair_key || 'solo')}`);
}

function renderHoldHud(holdState, lastHit = null) {
  const lastMs = lastHit?.source === 'hold' ? Number(lastHit.hold_ms || 0) : Number(holdState?.last_hold_ms || 0);
  const pairKey = lastHit?.pair_key || holdState?.pair_key || 'solo';
  const waterActive = Boolean(holdState?.water_active);
  const earthActive = Boolean(holdState?.earth_active);

  let textValue = waterActive ? 'С водой hold бьёт заметно злее.' : 'Без воды hold — ситуативный добор.';
  if (earthActive) textValue += ' Земля сверху даёт щит верховному шаману.';
  if (lastHit?.source === 'hold') {
    textValue = lastHit.combo_effect || 'Заряд выпущен.';
    if (Number(lastHit.player_healed || 0) > 0) textValue += ` · хил ${fmt(lastHit.player_healed)}`;
    if (Number(lastHit.player_shielded || 0) > 0) textValue += ` · щит ${fmt(lastHit.player_shielded)}`;
  }

  setText(els.holdName, lastHit?.source === 'hold' ? `Канал ${Math.round(lastMs)} мс` : pairLabel(pairKey));
  setText(els.holdText, textValue);
  setText(els.holdLastMs, `${Math.round(lastMs)} мс`);
  setText(els.holdWaterState, waterActive ? 'Вкл' : 'Выкл');
  setText(els.holdEarthState, earthActive ? 'Вкл' : 'Выкл');
  setText(els.holdHint, waterActive || earthActive ? 'Копи и отпускай' : 'Вода и Земля усиливают');

  if (els.holdMeterFill) {
    const width = lastHit?.source === 'hold'
      ? Math.max(8, Math.min(100, Number(lastHit.hold_charge || 0) * 100))
      : Math.max(0, Math.min(100, (lastMs / HOLD_MAX_MS) * 100));
    els.holdMeterFill.style.width = `${width}%`;
  }
}

function renderActiveHeroes(activeHeroes) {
  if (!els.activeHeroesList) return;
  const source = safeArray(activeHeroes);
  const slots = source.length ? source : [{ slot: 1, empty: true }, { slot: 2, empty: true }];
  const filled = slots.filter((item) => !item.empty);
  const totalDps = filled.reduce((sum, hero) => sum + Number(hero.dps || 0), 0);

  els.activeHeroesList.innerHTML = `
    <div class="active-squad">
      <div class="core-slot">
        <span>Связка</span>
        <strong>${filled.length}/2</strong>
        <span>${fmt(totalDps)} DPS</span>
      </div>
      ${slots.map((hero, index) => {
        if (hero.empty) {
          return `
            <div class="active-slot empty">
              <div class="slot-avatar">+</div>
              <div class="slot-copy">
                <span class="slot-label">Слот ${index + 1}</span>
                <strong class="slot-name">Пусто</strong>
                <span class="card-subtext">Найми шамана и кинь в связку.</span>
              </div>
              <button class="slot-btn" type="button" disabled>Пусто</button>
            </div>
          `;
        }
        return `
          <div class="active-slot">
            <div class="slot-avatar"><img src="${hero.asset}" alt="${hero.name}"></div>
            <div class="slot-copy">
              <span class="slot-label">Слот ${index + 1}</span>
              <strong class="slot-name">${hero.name}</strong>
              <span class="card-subtext">${hero.passive || hero.title || ''}</span>
            </div>
            <button class="slot-btn" type="button" data-active-hero-id="${hero.id}">Снять</button>
          </div>
        `;
      }).join('')}
    </div>
  `;

  els.activeHeroesList.querySelectorAll('[data-active-hero-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        setButtonsDisabled(true);
        const next = await request('/toggle-active-hero', 'POST', { id: btn.dataset.activeHeroId });
        setState(next);
        showToast('Снял из связки');
      } catch (error) {
        if (error.message === 'hero_not_owned') showToast('Сначала найми шамана'); else if (error.message === 'wave_locked') showToast('Связку меняем только между волнами'); else showToast('Не удалось снять шамана');
      } finally {
        loading = false;
        setButtonsDisabled(false);
      }
    });
  });
}

function renderHeroes(heroes) {
  if (!els.heroesList) return;
  const source = safeArray(heroes);

  if (!source.length) {
    els.heroesList.innerHTML = '<div class="empty-note">Герои не загрузились. Обнови страницу один раз.</div>';
    return;
  }

  els.heroesList.innerHTML = source.map((hero) => {
    const buyLabel = hero.owned ? 'Улучшить' : 'Нанять';
    const toggleLabel = hero.selected ? 'Снять' : 'В связку';
    const heroLevel = Number(hero.level || 0);
    const heroDps = Number(hero.dps || 0);
    return `
      <div class="hero-card ${hero.selected ? 'is-selected' : ''}">
        <div class="hero-avatar"><img src="${hero.asset}" alt="${hero.name}"></div>
        <div class="hero-copy">
          <div class="hero-overline">${hero.title || 'Шаман стихии'}</div>
          <div class="hero-title-row">
            <strong class="hero-title">${hero.name}</strong>
            ${hero.selected ? '<span class="tag active">В связке</span>' : ''}
          </div>
          <div class="card-subtext">${hero.passive || hero.desc || ''}</div>
          <div class="hero-tags">
            <span class="tag">Lvl ${heroLevel}</span>
            <span class="tag">DPS ${fmt(heroDps)}</span>
            <span class="tag">Цена ${fmt(hero.cost)}</span>
            <span class="tag muted">x${Number(hero.breakpoints || 0) + 1} пороги</span>
          </div>
        </div>
        <div class="hero-actions">
          <button class="hero-main-btn" data-hero-buy-id="${hero.id}" data-owned="${hero.owned ? '1' : '0'}">${buyLabel}</button>
          ${hero.owned ? `<button class="hero-ghost-btn" data-hero-toggle-id="${hero.id}" data-selected="${hero.selected ? '1' : '0'}">${toggleLabel}</button>` : ''}
        </div>
      </div>
    `;
  }).join('');

  els.heroesList.querySelectorAll('[data-hero-buy-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        setButtonsDisabled(true);
        const next = await request('/buy-hero', 'POST', { id: btn.dataset.heroBuyId });
        setState(next);
        showToast(btn.dataset.owned === '1' ? 'Шаман усилен' : 'Шаман нанят');
      } catch (error) {
        if (error.message === 'not_enough_gold') showToast('Золота маловато'); else if (error.message === 'wave_locked') showToast('Апгрейды между волнами'); else showToast('Не вышло усилить шамана');
      } finally {
        loading = false;
        setButtonsDisabled(false);
      }
    });
  });

  els.heroesList.querySelectorAll('[data-hero-toggle-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        setButtonsDisabled(true);
        const next = await request('/toggle-active-hero', 'POST', { id: btn.dataset.heroToggleId });
        setState(next);
        showToast(btn.dataset.selected === '1' ? 'Шаман снят' : 'Шаман в связке');
      } catch (error) {
        if (error.message === 'circle_full') showToast('В связке только 2 шамана. Сними одного.');
        else if (error.message === 'hero_not_owned') showToast('Сначала найми шамана');
        else if (error.message === 'wave_locked') showToast('Связку меняем только между волнами');
        else showToast('Не вышло обновить связку');
      } finally {
        loading = false;
        setButtonsDisabled(false);
      }
    });
  });
}

function renderTop(top) {
  if (!top) return;
  setText(els.topBestScore, fmt(top.best_score || 0));
  setText(els.topMyRank, top.my_rank ? `#${top.my_rank}` : '—');

  if (!els.leaderboardList) return;
  const list = safeArray(top.leaderboard);
  if (!list.length) {
    els.leaderboardList.innerHTML = '<div class="empty-note">Пока топ пустой. Кто первый нафармит — тот и хан.</div>';
    return;
  }

  els.leaderboardList.innerHTML = list.map((item) => `
    <div class="leaderboard-row ${item.is_me ? 'is-me' : ''}">
      <div class="leaderboard-rank">#${item.rank}</div>
      <div class="leaderboard-main">
        <div class="leaderboard-name">${item.name}</div>
        <em>${item.is_me ? 'Это ты' : 'Степной ранг'}</em>
      </div>
      <div class="leaderboard-score">${fmt(item.best_score)}</div>
    </div>
  `).join('');
}

function renderAchievements(achievements) {
  if (!achievements) return;
  setText(els.achievementsSummary, `${achievements.unlocked} / ${achievements.total}`);
  if (!els.achievementsList) return;
  els.achievementsList.innerHTML = safeArray(achievements.items).map((item) => {
    const progress = Math.max(0, Math.min(100, (Number(item.value || 0) / Math.max(1, Number(item.target || 1))) * 100));
    return `
      <div class="achievement-card ${item.done ? 'done' : ''}">
        <div class="achievement-top">
          <strong>${item.name}</strong>
          <span>${fmt(item.value)} / ${fmt(item.target)}</span>
        </div>
        <div class="achievement-sub">${item.desc}</div>
        <div class="achievement-bar"><div style="width:${progress}%"></div></div>
      </div>
    `;
  }).join('');
}

function renderHighShaman(highShaman) {
  if (!highShaman) return;
  setText(els.highShamanHp, `${fmt(highShaman.hp)} / ${fmt(highShaman.max_hp)}`);
  setText(els.highShamanShield, `${fmt(highShaman.shield)} / ${fmt(highShaman.max_shield)}`);
  setText(els.highShamanDefense, `${highShaman.defense}%`);
  setText(els.highShamanRegen, fmt(highShaman.regen));
  setText(els.highShamanHealPower, `${highShaman.heal_power}%`);
  if (els.highShamanHpFill) {
    const percent = Number(highShaman.hp_percent || 0);
    els.highShamanHpFill.className = `hp-fill ${hpFillState(percent)}`.trim();
    els.highShamanHpFill.style.width = `${Math.max(0, Math.min(100, percent))}%`;
  }
  if (els.highShamanShieldFill) {
    const shieldPercent = Number(highShaman.shield_percent || 0);
    els.highShamanShieldFill.style.width = `${Math.max(0, Math.min(100, shieldPercent))}%`;
    els.highShamanShieldFill.parentElement?.classList.toggle('hidden', Number(highShaman.max_shield || 0) <= 0);
  }
}

function renderPlayerCombat(lastHit) {
  if (!lastHit) return;
  if (lastHit.sustain_tick && !Number(lastHit.player_damage_taken || 0) && lastHit.source !== 'hold') return;
  if (els.playerHitFloat && Number(lastHit.player_damage_taken || 0) > 0) {
    els.playerHitFloat.textContent = `-${fmt(lastHit.player_damage_taken)} HP`;
    els.playerHitFloat.className = 'player-hit-float';
    if (Number(lastHit.player_damage_blocked || 0) > 0) els.playerHitFloat.classList.add('shielded');
    if (lastHit.player_defeated) els.playerHitFloat.classList.add('fatal');
    void els.playerHitFloat.offsetWidth;
    els.playerHitFloat.classList.remove('hidden');
    setTimeout(() => els.playerHitFloat?.classList.add('hidden'), 760);
  }
  if (els.playerHealFloat && (Number(lastHit.player_healed || 0) > 0 || Number(lastHit.player_shielded || 0) > 0)) {
    const chunks = [];
    if (Number(lastHit.player_healed || 0) > 0) chunks.push(`+${fmt(lastHit.player_healed)} HP`);
    if (Number(lastHit.player_shielded || 0) > 0) chunks.push(`+${fmt(lastHit.player_shielded)} щит`);
    els.playerHealFloat.textContent = chunks.join(' · ');
    els.playerHealFloat.className = 'player-heal-float';
    void els.playerHealFloat.offsetWidth;
    els.playerHealFloat.classList.remove('hidden');
    setTimeout(() => els.playerHealFloat?.classList.add('hidden'), 860);
  }
}

function renderEnemy(enemy) {
  if (!enemy) return;

  setText(els.stage, String(state?.stage || 1));
  setText(els.enemyType, enemy.type === 'group' ? `${enemyTypeLabel(enemy.type)} ×${enemy.count || 1}` : enemyTypeLabel(enemy.type));
  setText(els.enemyName, enemy.name || '...');
  setText(els.enemyFlavor, enemy.flavor || '');

  if (els.enemyWrap) {
    els.enemyWrap.className = `enemy-wrap ${enemy.type || 'normal'} ${enemy.id || ''}`;
  }

  if (enemy.type === 'normal' || enemy.type === 'group') {
    if (els.enemyImage) {
      els.enemyImage.removeAttribute('src');
      els.enemyImage.classList.add('hidden');
    }
    if (els.enemyGlyph) {
      els.enemyGlyph.innerHTML = enemy.glyph ? (enemy.type === 'group' ? renderGroupGlyph(enemy) : `<img src="${enemy.glyph}" alt="${enemy.name}" class="enemy-icon">`) : '✦';
      els.enemyGlyph.classList.remove('hidden');
    }
  } else {
    if (els.enemyImage) {
      els.enemyImage.src = enemy.asset || '';
      els.enemyImage.classList.remove('hidden');
    }
    if (els.enemyGlyph) {
      els.enemyGlyph.classList.add('hidden');
      els.enemyGlyph.innerHTML = '';
    }
  }

  setText(els.enemyHp, `${fmt(enemy.hp)} / ${fmt(enemy.max_hp)}`);
  const percent = enemy.max_hp > 0 ? (enemy.hp / enemy.max_hp) * 100 : 0;
  if (els.enemyHpFill) {
    els.enemyHpFill.className = `hp-fill ${hpFillState(percent)}`.trim();
    els.enemyHpFill.style.width = `${Math.max(0, Math.min(100, percent))}%`;
  }
  setText(els.enemyReward, fmt(enemy.reward));
  setText(els.bossKills, String(state?.boss_kills || 0));
  const shieldMax = Number(enemy.shield_max || 0);
  const shieldHp = Number(enemy.shield_hp || 0);
  if (els.bossShieldBlock) {
    const showShield = shieldMax > 0;
    els.bossShieldBlock.classList.toggle('hidden', !showShield);
    if (showShield) {
      setText(els.enemyShield, `${fmt(shieldHp)} / ${fmt(shieldMax)}`);
      if (els.enemyShieldFill) {
        els.enemyShieldFill.style.width = `${Math.max(0, Math.min(100, shieldHp / Math.max(1, shieldMax) * 100))}%`;
      }
    }
  }
}

function showHitToast(lastHit, previousEnemyId) {
  if (!lastHit) return;
  if (lastHit.blocked && lastHit.blocked_reason === 'wave_paused') showToast('Сначала жми «Начать волну»');
  else if (lastHit.blocked && lastHit.blocked_reason === 'shadow') showToast('Босс ушёл в тень — DPS сейчас не проходит');
  else if (lastHit.blocked && lastHit.blocked_reason === 'shield') showToast(state?.enemy?.shield_hp > 0 ? `Щит трещит: ${fmt(state.enemy.shield_hp)}` : 'Щит сломан');
  else if (lastHit.blocked && lastHit.blocked_reason === 'earth_shield') showToast('Каменный щит почти не пускает урон без земной связки');
  else if (lastHit.blocked && lastHit.blocked_reason === 'combo_gate') showToast('Нужен тяжёлый земной комбо-свайп вниз');
  else if (lastHit.blocked && lastHit.blocked_reason === 'swipe_gate') showToast('Нужен свайп');
  else if (lastHit.blocked && lastHit.blocked_reason === 'hold_gate') showToast('Нужен hold');
  else if (lastHit.blocked && lastHit.blocked_reason === 'burn_gate') showToast('Сначала раскочегарь поджог');
  else if (lastHit.blocked && lastHit.blocked_reason === 'mirror_repeat') showToast('Не долби один и тот же свайп подряд');
  else if (lastHit.blocked && lastHit.blocked_reason === 'chain_repeat') showToast('Меняй tap / swipe / hold, босс жрёт повторы');
  else if (lastHit.blocked && lastHit.blocked_reason === 'pair_mismatch') showToast('После 10-й волны нужна правильная связка шаманов');
  else if (lastHit.blocked && lastHit.blocked_reason === 'pair_action_mismatch') showToast('Связка выбрана верно, но нужен другой тип удара');
  else if (lastHit.blocked && lastHit.blocked_reason === 'pair_combo_mismatch') showToast('Эта цель раскрывается только через комбо-свайпы');
  else if (lastHit.combo_name) showToast(lastHit.combo_name);
  else if (lastHit.boss_kill) showToast(`Босс пал. Награда: ${fmt(lastHit.gold_gained)}`);
  else if (previousEnemyId && previousEnemyId !== state?.enemy?.id && lastHit.gold_gained) showToast(`Лут: +${fmt(lastHit.gold_gained)}`);
}

function blessingIcon(id) {
  return ({ fire: '🔥', water: '💧', earth: '🪨', air: '💨' }[id] || '✦');
}

function blessingTitle(id) {
  return ({ fire: 'Путь Огня', water: 'Путь Воды', earth: 'Путь Земли', air: 'Путь Ветра' }[id] || 'Дар');
}

function renderBlessings(blessings) {
  if (!els.blessingsList) return;
  const items = safeArray(blessings?.items);
  els.blessingsList.innerHTML = items.map((item) => `
    <div class="blessing-card">
      <div class="blessing-card-head">
        <strong>${blessingIcon(item.id)} ${item.name}</strong>
        <span>ур. ${item.level || 0}</span>
      </div>
      <div class="blessing-card-desc">${item.desc || ''}</div>
      <div class="blessing-card-foot">Следующий дар: ${fmt(item.cost || 0)} троф.</div>
    </div>
  `).join('');

  if (els.blessingSynergies) {
    const syn = blessings?.synergies || {};
    const rows = [
      { key: 'fire_air', name: '🔥 + 💨 Искровой разгон', value: syn.fire_air },
      { key: 'fire_earth', name: '🔥 + 🪨 Треск панциря', value: syn.fire_earth },
      { key: 'water_earth', name: '💧 + 🪨 Тяжёлая хватка', value: syn.water_earth },
    ];
    els.blessingSynergies.innerHTML = rows.map((row) => `
      <div class="synergy-row ${row.value > 0 ? 'is-active' : ''}">
        <span>${row.name}</span>
        <strong>${row.value > 0 ? `+${Math.round(row.value * 100)}%` : 'не открыт'}</strong>
      </div>
    `).join('');
  }
}

function openRebirthOverlay() {
  if (!state) return;
  const items = safeArray(state.blessings?.items);
  if (els.overlayRebirthGain) els.overlayRebirthGain.textContent = `+${state.rebirth_gain || 0}`;
  if (els.rebirthChoiceList) {
    els.rebirthChoiceList.innerHTML = items.map((item) => `
      <button class="rebirth-choice" data-path="${item.id}" type="button">
        <span>${blessingIcon(item.id)} ${item.name}</span>
        <small>ур. ${item.level || 0} · след. дар ${fmt(item.cost || 0)} троф.</small>
      </button>
    `).join('');
    els.rebirthChoiceList.querySelectorAll('[data-path]').forEach((btn) => {
      btn.addEventListener('click', () => confirmRebirth(btn.dataset.path));
    });
  }
  els.rebirthStep1?.classList.add('active');
  els.rebirthStep2?.classList.remove('active');
  els.rebirthOverlay?.classList.remove('hidden');
  document.body.classList.add('rebirth-open');
}

function closeRebirthOverlay() {
  els.rebirthOverlay?.classList.add('hidden');
  document.body.classList.remove('rebirth-open');
}

function showRebirthResult(summary) {
  const path = summary?.path || 'fire';
  const title = blessingTitle(path);
  const invested = !!summary?.invested;
  if (els.rebirthResultText) {
    els.rebirthResultText.innerHTML = invested
      ? `Дар принят.<br>Степь запомнила твой путь. Усилен: <strong>${title}</strong>.`
      : `Трофеи приняты духами.<br>До следующего дара <strong>${title}</strong> пока не хватило, но путь уже отмечен.`;
  }
  if (els.rebirthRitualFx) {
    els.rebirthRitualFx.className = `rebirth-ritual-fx is-${path}`;
  }
  els.rebirthStep1?.classList.remove('active');
  els.rebirthStep2?.classList.add('active');
}

async function confirmRebirth(path) {
  if (loading) return;
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/rebirth', 'POST', { path });
    setState(next);
    showRebirthResult(next.last_rebirth_summary || { path });
  } catch (error) {
    console.error('rebirth_confirm_failed', error);
    showToast(error.message === 'rebirth_locked' ? 'Перерождение ещё закрыто' : 'Ритуал сорвался');
    closeRebirthOverlay();
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

function applyViewportMode() {
  const isMobile = window.innerWidth <= 860;
  document.body.classList.toggle('mobile-ui', isMobile);
  document.body.classList.toggle('desktop-ui', !isMobile);
  ensureMobileNav();
  if (!isMobile) {
    setMobileScreen('fight');
    return;
  }
  setMobileScreen(mobileScreen || 'fight');
}

function setState(next) {
  if (!next || typeof next !== 'object') {
    console.error('bad_state', next);
    showToast('Состояние игры не загрузилось');
    return;
  }

  const previousEnemyId = state?.enemy?.id || null;
  state = next;

  try {
    setText(els.playerName, state.player?.name || 'Гость степи');
    setText(els.playerAuthStatus, state.player?.is_telegram ? 'Автовход через Telegram' : 'Локальный вход');

    setText(els.gold, fmt(state.gold));
    setText(els.tapDamage, fmt(state.tap_damage));
    setText(els.tapDamageInline, fmt(state.tap_damage));
    setText(els.dps, fmt(state.dps));
    setText(els.dpsInline, fmt(state.dps));
    setText(els.wave, String(state.wave || 1));
    setText($('wave-top-inline'), String(state.wave || 1));
    setText(els.trophies, fmt(state.trophies));
    setText(els.score, fmt(state.score));
    setText(els.tapUpgradeCost, fmt(state.tap_cost));
    setText(els.critChance, `${state.crit_chance}%`);
    setText(els.critInline, `${state.crit_chance}%`);
    setText(els.critMultiplier, `x${state.crit_multiplier}`);
    setText(els.goldBonus, `${state.gold_bonus}%`);
    setText(els.kills, String(state.kills || 0));
    setText(els.metaTrophies, fmt(state.trophies));
    setText(els.metaPowerBonus, `${state.power_bonus}%`);
    setText(els.metaGoldBonus, `${state.gold_bonus}%`);
    setText(els.metaCritMultiplier, `x${state.crit_multiplier}`);
    setText(els.rebirthGain, String(state.rebirth_gain || 0));
    setText(els.rebirthCount, String(state.rebirths || 0));
    setText(els.rebirthDepth, String(state.rebirth_breakdown?.depth || 0));
    setText(els.rebirthBoss, String(state.rebirth_breakdown?.boss || 0));
    setText(els.rebirthWaveBonus, String(state.rebirth_breakdown?.wave || 0));
    setText(els.rebirthElite, String(state.rebirth_breakdown?.elite || 0));
    if (els.rebirthLockText) {
      const needed = Number(state.rebirth_breakdown?.stage_needed || 0);
      els.rebirthLockText.textContent = needed > 0
        ? `Добеги ещё ${needed} этап., чтобы духи степи услышали зов.`
        : 'Чем глубже забег, тем жирнее трофеи. Ранний сброс режется по награде.';
    }
    setText($('high-shaman-hp-mobile-mirror'), `${fmt(state.high_shaman?.hp || 0)} / ${fmt(state.high_shaman?.max_hp || 0)}`);
    setText($('dps-mobile-mirror'), fmt(state.dps));
    setText($('def-mobile-mirror'), `${state.high_shaman?.defense || 0}%`);

    renderEnemy(state.enemy);
    renderWavePanel(state.wave_state);
    renderHighShaman(state.high_shaman);
    renderBossMechanic(state.enemy, state.last_hit);
    renderSwipeHud(state.swipe_state, state.last_hit);
    renderHoldHud(state.hold_state, state.last_hit);

    if (previousEnemyId && previousEnemyId !== state.enemy?.id) {
      triggerEnemyEnter();
    }

    renderActiveHeroes(state.active_heroes);
    renderHeroes(state.heroes);
    renderTop(state.top);
    renderAchievements(state.achievements);
    renderBlessings(state.blessings);
    renderHit(state.last_hit);
    renderKill(state.last_hit);
    renderPlayerCombat(state.last_hit);
    maybeShowWaveTransition(state.last_hit);

    if (state.last_hit?.source === 'swipe' && state.last_hit.swipe_direction) {
      drawSwipeTrail(
        state.last_hit.swipe_direction,
        state.last_hit.combo_visual || 'fx-basic',
        state.last_hit.combo_name || '',
        window.__lastSwipeGesture || null,
      );
      window.__lastSwipeGesture = null;
    } else if (state.last_hit?.source === 'tap') {
      if (els.highShamanIcon) { els.highShamanIcon.classList.remove('is-hit'); void els.highShamanIcon.offsetWidth; els.highShamanIcon.classList.add('is-hit'); }
      pulseEnemy(state.last_hit.visual || '', 'tap');
    } else if (state.last_hit?.source === 'hold') {
      pulseEnemy(state.last_hit.hold_visual || state.last_hit.visual || 'fx-water', 'hold');
    }

    showHitToast(state.last_hit, previousEnemyId);
    if (state.last_hit?.expedition_stopped) {
      closeWaveTransitionOverlay();
      showToast(state.last_hit.stopped_mid_wave ? 'Поход свернул. Вернулся к привалу.' : 'Поход завершён у привала.');
    }
    setButtonsDisabled(loading);
  } catch (error) {
    console.error('set_state_failed', error, next);
    showToast('Фронт словил ошибку при рендере');
  }
}

async function refreshState(silent = false) {
  try {
    const next = await request('/state');
    setState(next);
  } catch (error) {
    console.error('refresh_state_failed', error);
    if (!silent) showToast('Сервер степи молчит');
  }
}

async function tapEnemy(eventLike = null) {
  if (loading) return;
  if (state?.wave_state?.waiting || !state?.wave_state?.in_progress) { showToast('Сначала жми «Начать волну»'); return; }
  if (eventLike?.clientX != null && eventLike?.clientY != null) {
    playPointBurst(eventLike.clientX, eventLike.clientY);
  }
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/tap', 'POST');
    setState(next);
  } catch (error) {
    console.error('tap_failed', error);
    showToast('Удар не прошёл');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

async function swipeEnemy(direction, eventLike = null) {
  if (loading) return;
  if (state?.wave_state?.waiting || !state?.wave_state?.in_progress) { showToast('Сначала жми «Начать волну»'); return; }
  if (eventLike?.clientX != null && eventLike?.clientY != null) {
    playPointBurst(eventLike.clientX, eventLike.clientY, 'swipe-burst');
  }
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/swipe', 'POST', { direction });
    setState(next);
  } catch (error) {
    console.error('swipe_failed', error);
    showToast(error.message === 'invalid_direction' ? 'Жест не распознан' : 'Свайп не прошёл');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

async function holdEnemy(durationMs, eventLike = null) {
  if (loading) return;
  if (state?.wave_state?.waiting || !state?.wave_state?.in_progress) { showToast('Сначала жми «Начать волну»'); return; }
  if (eventLike?.clientX != null && eventLike?.clientY != null) {
    playPointBurst(eventLike.clientX, eventLike.clientY, 'hold-burst');
  }
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/hold', 'POST', { duration_ms: Math.round(durationMs) });
    setState(next);
  } catch (error) {
    console.error('hold_failed', error);
    showToast('Удержание не прошло');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}


async function startWaveAction() {
  if (loading || state?.wave_state?.in_progress) return;
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/start-wave', 'POST');
    setState(next);
    showToast('Волна пошла');
  } catch (error) {
    console.error('start_wave_failed', error);
    showToast('Не удалось запустить волну');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

async function stopExpeditionAction() {
  if (loading || !state?.wave_state?.in_progress) return;
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/stop-expedition', 'POST');
    setState(next);
  } catch (error) {
    console.error('stop_expedition_failed', error);
    showToast('Не удалось свернуть поход');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

async function upgradeTap() {
  if (loading) return;
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/upgrade-tap', 'POST');
    setState(next);
  } catch (error) {
    console.error('upgrade_tap_failed', error);
    showToast(error.message === 'not_enough_gold' ? 'Золота маловато' : 'Апыч не прошёл');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

async function rebirth() {
  if (!state?.can_rebirth) {
    showToast('Сначала добейся хотя бы этапа 10');
    return;
  }
  if (!window.confirm(`Уйти в перерод и забрать ${state.rebirth_gain} трофеев?`)) return;
  try {
    loading = true;
    setButtonsDisabled(true);
    const next = await request('/rebirth', 'POST');
    setState(next);
    showToast('Перерод удался');
  } catch (error) {
    console.error('rebirth_failed', error);
    showToast(error.message === 'rebirth_locked' ? 'Перерождение ещё закрыто' : 'Перерод не сработал');
  } finally {
    loading = false;
    setButtonsDisabled(false);
  }
}

function dominantDirection(dx, dy) {
  const absX = Math.abs(dx);
  const absY = Math.abs(dy);
  if (Math.max(absX, absY) < SWIPE_MIN_DISTANCE) return null;
  if (absX > absY) return dx >= 0 ? 'right' : 'left';
  return dy >= 0 ? 'down' : 'up';
}


function clearHoldVisual() {
  if (holdVisual.marker) holdVisual.marker.remove();
  holdVisual = { marker: null, ring: null, label: null };
}

function ensureHoldVisual(clientX, clientY) {
  if (!els.swipeTrailLayer || !els.enemyWrap) return null;
  const { x, y } = pointFromClient(clientX, clientY);

  if (!holdVisual.marker) {
    const marker = document.createElement('div');
    marker.className = 'hold-marker';

    const ring = document.createElement('div');
    ring.className = 'hold-marker-ring';

    const core = document.createElement('div');
    core.className = 'hold-marker-core';

    const label = document.createElement('div');
    label.className = 'hold-marker-label';
    label.textContent = 'HOLD';

    marker.appendChild(ring);
    marker.appendChild(core);
    marker.appendChild(label);
    els.swipeTrailLayer.appendChild(marker);
    holdVisual = { marker, ring, label };
  }

  holdVisual.marker.style.left = `${x}px`;
  holdVisual.marker.style.top = `${y}px`;
  return holdVisual;
}

function updateHoldVisual(clientX, clientY, progress = 0) {
  const visual = ensureHoldVisual(clientX, clientY);
  if (!visual) return;
  const safeProgress = Math.max(0, Math.min(1, progress));
  visual.marker.style.opacity = '1';
  visual.ring.style.setProperty('--hold-progress', `${safeProgress}`);
  visual.label.textContent = `${Math.round(safeProgress * HOLD_MAX_MS)} мс`;
  visual.marker.classList.toggle('is-ready', safeProgress >= 0.999);
}

function burstHoldVisual(clientX, clientY, effectClass = 'fx-water') {
  const visual = ensureHoldVisual(clientX, clientY);
  if (!visual) return;
  visual.marker.classList.add('is-burst');
  if (effectClass) visual.marker.classList.add(effectClass);
  setTimeout(() => clearHoldVisual(), 360);
}

function startHoldCharge() {
  clearInterval(holdChargeTimer);
  holdChargeTimer = setInterval(() => {
    if (!pointerState.active) return;
    const elapsed = Date.now() - pointerState.startedAt;
    const progress = Math.max(0, Math.min(1, elapsed / HOLD_MAX_MS));
    updateHoldVisual(pointerState.lastX, pointerState.lastY, progress);
  }, 40);
}

function resetPointer(event) {
  if (pointerState.active && event?.pointerId != null) {
    try {
      els.enemyWrap?.releasePointerCapture?.(event.pointerId);
    } catch (_) {}
  }
  pointerState = {
    active: false,
    pointerId: null,
    startX: 0,
    startY: 0,
    lastX: 0,
    lastY: 0,
    startedAt: 0,
    moved: false,
    path: [],
  };
  clearInterval(holdChargeTimer);
  clearHoldVisual();
}

function onPointerDown(event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return;
  pointerState = {
    active: true,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    lastX: event.clientX,
    lastY: event.clientY,
    startedAt: Date.now(),
    moved: false,
    path: [{ x: event.clientX, y: event.clientY }],
  };
  updateHoldVisual(event.clientX, event.clientY, 0);
  startHoldCharge();
  els.enemyWrap?.setPointerCapture?.(event.pointerId);
}

function onPointerMove(event) {
  if (!pointerState.active || pointerState.pointerId !== event.pointerId) return;
  pointerState.lastX = event.clientX;
  pointerState.lastY = event.clientY;
  const dx = event.clientX - pointerState.startX;
  const dy = event.clientY - pointerState.startY;
  if (Math.abs(dx) > 8 || Math.abs(dy) > 8) {
    pointerState.moved = true;
  }
  const elapsed = Date.now() - pointerState.startedAt;
  updateHoldVisual(event.clientX, event.clientY, Math.max(0, Math.min(1, elapsed / HOLD_MAX_MS)));
  const last = pointerState.path[pointerState.path.length - 1];
  if (!last || Math.abs(last.x - event.clientX) > 6 || Math.abs(last.y - event.clientY) > 6) {
    pointerState.path.push({ x: event.clientX, y: event.clientY });
  }
}

async function onPointerUp(event) {
  if (!pointerState.active || pointerState.pointerId !== event.pointerId) return;

  const snapshot = {
    startX: pointerState.startX,
    startY: pointerState.startY,
    endX: event.clientX,
    endY: event.clientY,
    path: [...pointerState.path, { x: event.clientX, y: event.clientY }],
    startedAt: pointerState.startedAt,
  };

  const dx = event.clientX - pointerState.startX;
  const dy = event.clientY - pointerState.startY;
  const elapsed = Date.now() - pointerState.startedAt;
  const direction = dominantDirection(dx, dy);
  const syntheticEvent = { clientX: event.clientX, clientY: event.clientY };

  resetPointer(event);

  if (direction && (Math.abs(dx) > SWIPE_MIN_DISTANCE || Math.abs(dy) > SWIPE_MIN_DISTANCE)) {
    window.__lastSwipeGesture = snapshot;
    await swipeEnemy(direction, syntheticEvent);
    return;
  }

  if (elapsed >= HOLD_TRIGGER_MS) {
    await holdEnemy(elapsed, syntheticEvent);
    return;
  }

  await tapEnemy(syntheticEvent);
}

function onPointerCancel(event) {
  resetPointer(event);
}

if (els.enemyWrap) {
  els.enemyWrap.addEventListener('pointerdown', onPointerDown);
  els.enemyWrap.addEventListener('pointermove', onPointerMove);
  els.enemyWrap.addEventListener('pointerup', onPointerUp);
  els.enemyWrap.addEventListener('pointercancel', onPointerCancel);
}

els.tapUpgradeBtn?.addEventListener('click', upgradeTap);
els.startWaveBtn?.addEventListener('click', startWaveAction);
els.stopExpeditionBtn?.addEventListener('click', stopExpeditionAction);
els.waveTransitionContinueBtn?.addEventListener('click', async () => {
  closeWaveTransitionOverlay();
  await startWaveAction();
});
els.waveTransitionStopBtn?.addEventListener('click', async () => {
  closeWaveTransitionOverlay();
  if (state?.wave_state?.in_progress) await stopExpeditionAction();
  else showToast('Поход завершён у привала.');
});
els.rebirthBtn?.addEventListener('click', rebirth);
els.rebirthContinueBtn?.addEventListener('click', closeRebirthOverlay);
els.rebirthOverlay?.addEventListener('click', (event) => {
  if (event.target === els.rebirthOverlay || event.target.classList.contains('rebirth-backdrop')) closeRebirthOverlay();
});
els.waveTransitionOverlay?.addEventListener('click', (event) => {
  if (event.target === els.waveTransitionOverlay || event.target.classList.contains('wave-transition-backdrop')) closeWaveTransitionOverlay();
});

document.addEventListener('keydown', (event) => {
  if (event.code === 'Space') {
    event.preventDefault();
    tapEnemy();
    return;
  }
  const map = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right' };
  if (map[event.code]) {
    event.preventDefault();
    window.__lastSwipeGesture = null;
    swipeEnemy(map[event.code]);
    return;
  }
  if (event.code === 'KeyH') {
    event.preventDefault();
    holdEnemy(1200);
  }
});

async function boot() {
  try {
    initTelegram();
    await refreshState(false);
    clearInterval(pollTimer);
    pollTimer = setInterval(() => refreshState(true), POLL_INTERVAL_MS);
  } catch (error) {
    console.error('boot_failed', error);
    showToast('Игра не загрузилась. Обнови страницу');
  }
}

window.addEventListener('error', (event) => {
  console.error('page_error', event.error || event.message);
});
window.addEventListener('resize', applyViewportMode);
applyViewportMode();

boot();


/* === MOBILE UX REWORK V3 === */
let mobileScreen = 'fight';

function mobileSections() {
  return {
    fight: [
      document.querySelector('.center-column .battle-panel'),
      document.querySelector('.mobile-stack .shaman-hud.mobile-card.mobile-only')
    ].filter(Boolean),
    shamans: [
      document.querySelector('.mobile-stack .squad-hud.mobile-card')
    ].filter(Boolean),
    meta: [
      document.querySelector('.mobile-stack .mobile-tabs-panel')
    ].filter(Boolean),
  };
}

function ensureMobileNav() {
  if (document.querySelector('.mobile-nav-shell')) return;
  const shell = document.createElement('div');
  shell.className = 'mobile-nav-shell';
  shell.innerHTML = `
    <button type="button" class="mobile-nav-btn active" data-mobile-screen="fight">Бой</button>
    <button type="button" class="mobile-nav-btn" data-mobile-screen="shamans">Шаманы</button>
    <button type="button" class="mobile-nav-btn" data-mobile-screen="meta">Топ-Дары</button>
  `;
  document.body.appendChild(shell);
  shell.querySelectorAll('[data-mobile-screen]').forEach((btn) => {
    btn.addEventListener('click', () => setMobileScreen(btn.dataset.mobileScreen));
  });
}

function setMobileScreen(screen) {
  mobileScreen = screen || 'fight';
  const isMobile = window.innerWidth <= 860;
  const sections = mobileSections();

  Object.entries(sections).forEach(([key, nodes]) => {
    nodes.forEach((node) => {
      node.classList.toggle('mobile-screen-hidden', isMobile && key !== mobileScreen);
    });
  });

  document.querySelectorAll('.mobile-nav-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.mobileScreen === mobileScreen);
  });
}
