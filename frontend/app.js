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
const rebirthGainEl = document.getElementById('rebirth-gain');
const rebirthCountEl = document.getElementById('rebirth-count');
const topBestScoreEl = document.getElementById('top-best-score');
const achievementsSummaryEl = document.getElementById('achievements-summary');
const achievementsListEl = document.getElementById('achievements-list');
const activeHeroesListEl = document.getElementById('active-heroes-list');
const heroesListEl = document.getElementById('heroes-list');
const ritualsListEl = document.getElementById('rituals-list');
const synergiesListEl = document.getElementById('synergies-list');
const ritualPathsEl = document.getElementById('ritual-paths');
const metaUpgradesListEl = document.getElementById('meta-upgrades-list');
const metaPointsEl = document.getElementById('meta-points');
const buildElementsEl = document.getElementById('build-elements');
const buildActiveSynergyEl = document.getElementById('build-active-synergy');
const buildWeaknessEl = document.getElementById('build-weakness');
const buildStrengthsEl = document.getElementById('build-strengths');
const toastEl = document.getElementById('toast');
const hitFloatEl = document.getElementById('hit-float');
const flashBannerEl = document.getElementById('flash-banner');
const skillsGridEl = document.getElementById('skills-grid');
const respecRefundEl = document.getElementById('respec-refund');
const respecCooldownEl = document.getElementById('respec-cooldown');
const respecBtnEl = document.getElementById('respec-btn');
const presetButtons = document.querySelectorAll('.preset-btn');
const rebirthBtnEl = document.getElementById('rebirth-btn');
const bossInfoEl = document.getElementById('boss-info');
const bossMechanicEl = document.getElementById('boss-mechanic');
const bossHintEl = document.getElementById('boss-hint');
const bossTimerEl = document.getElementById('boss-timer');
const bossTimerCardEl = document.getElementById('boss-timer-card');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-section');

let state = null;
let loading = false;
let toastTimer = null;
let flashTimer = null;

function fmt(value) {
  const n = Number(value || 0);
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  if (Math.abs(n) >= 100) return String(Math.round(n));
  if (Number.isInteger(n)) return String(n);
  return n.toFixed(2);
}

function fmtSeconds(value) {
  const n = Math.max(0, Number(value || 0));
  if (n <= 0) return 'готов';
  if (n < 10) return `${n.toFixed(1)}с`;
  return `${Math.ceil(n)}с`;
}

function showToast(text) {
  if (!text) return;
  toastEl.textContent = text;
  toastEl.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.add('hidden'), 1900);
}

function showFlash(text) {
  if (!text) return;
  flashBannerEl.textContent = text;
  flashBannerEl.classList.remove('hidden');
  flashBannerEl.classList.remove('pop');
  void flashBannerEl.offsetWidth;
  flashBannerEl.classList.add('pop');
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => flashBannerEl.classList.add('hidden'), 1000);
}

async function request(path, method = 'GET', body = null) {
  const options = { method, headers: {} };
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
  const label = lastHit.label ? `${lastHit.label} ` : (lastHit.crit ? 'Крит ' : '-');
  hitFloatEl.textContent = `${label}${fmt(lastHit.damage)}`;
  hitFloatEl.className = `hit-float ${lastHit.crit ? 'crit' : ''}`;
  void hitFloatEl.offsetWidth;
  hitFloatEl.classList.remove('hidden');
  setTimeout(() => hitFloatEl.classList.add('hidden'), lastHit.crit ? 620 : 460);
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

  setTimeout(() => spark.remove(), 280);
  setTimeout(() => ring.remove(), 380);
  setTimeout(() => enemyWrapEl.classList.remove('hit'), 180);
}

function renderBuild(build) {
  buildElementsEl.innerHTML = build.elements.map((item) => `
    <div class="element-chip">
      <span>${item.emoji}</span>
      <strong>${item.level}</strong>
    </div>
  `).join('');

  buildActiveSynergyEl.textContent = build.active_synergy;
  buildWeaknessEl.textContent = build.weakness;
  buildStrengthsEl.innerHTML = `
    <div class="mini-card compact"><span>Tap</span><strong>${fmt(build.strengths.tap)}</strong></div>
    <div class="mini-card compact"><span>DPS</span><strong>${fmt(build.strengths.dps)}</strong></div>
    <div class="mini-card compact"><span>Фарм</span><strong>${build.strengths.farm}%</strong></div>
  `;

  synergiesListEl.innerHTML = build.synergies.map((synergy) => `
    <div class="ritual-row ${synergy.active ? 'active-synergy' : ''}">
      <div>
        <div class="card-title">${synergy.name}</div>
        <div class="card-desc">${synergy.desc}</div>
        <div class="card-stats">
          <span class="chip">${synergy.heroes[0]} ${synergy.progress[0]}/${synergy.threshold}</span>
          <span class="chip">${synergy.heroes[1]} ${synergy.progress[1]}/${synergy.threshold}</span>
        </div>
      </div>
      <div class="card-actions">
        <div class="cost">${synergy.active ? 'Активна' : 'Не собрана'}</div>
      </div>
    </div>
  `).join('');
}

function renderActiveHeroes(activeHeroes) {
  if (!activeHeroes || activeHeroes.length === 0) {
    activeHeroesListEl.innerHTML = `
      <div class="ritual-row"><div><div class="card-title">Пока пусто</div><div class="card-desc">Как только наймёшь первого шамана, он появится здесь.</div></div></div>
    `;
    return;
  }

  activeHeroesListEl.innerHTML = activeHeroes.map((hero) => `
    <div class="card-row">
      <img src="${hero.asset}" alt="${hero.name}">
      <div class="card-info">
        <div class="card-title">${hero.emoji} ${hero.name}</div>
        <div class="card-sub">${hero.title}</div>
        <div class="card-stats">
          <span class="chip">Уровень ${hero.level}</span>
          <span class="chip">Личный DPS ${fmt(hero.dps)}</span>
        </div>
        <div class="card-stats card-stats-secondary"><span class="chip">${hero.passive}</span></div>
      </div>
    </div>
  `).join('');
}

function renderHeroes(heroes) {
  heroesListEl.innerHTML = heroes.map((hero) => `
    <div class="card-row">
      <img src="${hero.asset}" alt="${hero.name}">
      <div class="card-info">
        <div class="card-title">${hero.emoji} ${hero.name}</div>
        <div class="card-sub">${hero.title}</div>
        <div class="card-desc">${hero.desc}</div>
        <div class="card-stats">
          <span class="chip">Уровень ${hero.level}</span>
          <span class="chip">Личный DPS ${fmt(hero.dps)}</span>
          <span class="chip">${hero.build_role}</span>
        </div>
        <div class="card-stats card-stats-secondary"><span class="chip">${hero.passive}</span></div>
        <div class="card-next">${hero.next_bonus}</div>
      </div>
      <div class="card-actions">
        <div class="cost">${fmt(hero.cost)} золота</div>
        <button class="action-btn" data-hero-id="${hero.id}">Усилить</button>
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
        handleError(error.message, 'Не вышло подтянуть шамана');
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
        handleError(error.message, 'Ритуал не прокнулся');
      } finally {
        loading = false;
      }
    });
  });
}

function renderRitualPaths(paths) {
  ritualPathsEl.innerHTML = paths.map((path) => `
    <div class="ritual-row ${path.active ? 'active-synergy' : ''}">
      <div>
        <div class="card-title">${path.name}</div>
        <div class="card-desc">${path.desc}</div>
      </div>
      <div class="card-actions">
        <button class="action-btn" data-path-id="${path.id}">${path.active ? 'Выбрано' : 'Взять'}</button>
      </div>
    </div>
  `).join('');

  ritualPathsEl.querySelectorAll('[data-path-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        const next = await request('/set-ritual-path', 'POST', { id: btn.dataset.pathId });
        setState(next);
      } catch (error) {
        handleError(error.message, 'Ветка не сменилась');
      } finally {
        loading = false;
      }
    });
  });
}

function renderMeta(metaUpgrades, metaPoints) {
  metaPointsEl.textContent = fmt(metaPoints);
  metaUpgradesListEl.innerHTML = metaUpgrades.map((item) => `
    <div class="ritual-row slim-row">
      <div>
        <div class="card-title">${item.name}</div>
        <div class="card-desc">${item.desc}</div>
        <div class="card-stats"><span class="chip">Уровень ${item.level}</span></div>
      </div>
      <div class="card-actions">
        <div class="cost">Цена ${item.cost}</div>
        <button class="action-btn" data-meta-id="${item.id}">Усилить</button>
      </div>
    </div>
  `).join('');

  metaUpgradesListEl.querySelectorAll('[data-meta-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        const next = await request('/meta-upgrade', 'POST', { id: btn.dataset.metaId });
        setState(next);
      } catch (error) {
        handleError(error.message, 'Очков меты маловато');
      } finally {
        loading = false;
      }
    });
  });
}

function renderSkills(skills) {
  skillsGridEl.innerHTML = skills.map((skill) => `
    <button class="skill-btn ${skill.active_left > 0 ? 'active' : ''}" data-skill-id="${skill.id}" ${skill.is_ready ? '' : 'disabled'}>
      <strong>${skill.name}</strong>
      <span>${skill.desc}</span>
      <em>${skill.active_left > 0 ? `активно ${fmtSeconds(skill.active_left)}` : skill.is_ready ? 'готово' : `кд ${fmtSeconds(skill.ready_in)}`}</em>
    </button>
  `).join('');

  skillsGridEl.querySelectorAll('[data-skill-id]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (loading) return;
      try {
        loading = true;
        const next = await request('/skill', 'POST', { id: btn.dataset.skillId });
        setState(next);
      } catch (error) {
        handleError(error.message, 'Скилл не прожался');
      } finally {
        loading = false;
      }
    });
  });
}

function renderTop(top) {
  topBestScoreEl.textContent = fmt(top.best_score);
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

function handleFlashEvent(event) {
  if (!event || !event.text) return;
  showFlash(event.text);
}

function setState(next) {
  state = next;
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
    enemyGlyphEl.innerHTML = state.enemy.glyph ? `<img src="${state.enemy.glyph}" alt="${state.enemy.name}" class="enemy-icon">` : '✦';
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

  bossInfoEl.classList.toggle('hidden', state.enemy.type !== 'boss');
  bossMechanicEl.textContent = state.enemy.mechanic_name || '—';
  bossHintEl.textContent = state.enemy.hint || '—';
  bossTimerCardEl.classList.toggle('hidden', state.enemy.timer_left == null);
  bossTimerEl.textContent = state.enemy.timer_left == null ? '—' : fmtSeconds(state.enemy.timer_left);

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
  respecRefundEl.textContent = fmt(state.respec.refund);
  respecCooldownEl.textContent = fmtSeconds(state.respec.cooldown_left);
  respecBtnEl.disabled = state.respec.cooldown_left > 0 || state.respec.refund <= 0;
  presetButtons.forEach((btn) => {
    btn.disabled = state.respec.cooldown_left > 0 || state.respec.refund <= 0;
  });

  renderBuild(state.build);
  renderActiveHeroes(state.active_heroes);
  renderHeroes(state.heroes);
  renderRituals(state.rituals);
  renderRitualPaths(state.ritual_paths);
  renderMeta(state.meta_upgrades, state.meta_points);
  renderSkills(state.skills);
  renderTop(state.top);
  renderAchievements(state.achievements);
  renderHit(state.last_hit);
  handleFlashEvent(state.flash_event);

  if (state.feedback) showToast(state.feedback);
  if (state.last_boss_message) showFlash(state.last_boss_message);
}

function handleError(code, fallback) {
  const map = {
    not_enough_gold: 'Золота маловато',
    skill_cooldown: 'Скилл ещё в КД',
    rebirth_locked: 'Пока рано в перерод',
    not_enough_meta: 'Очков меты не хватает',
    respec_cooldown: 'Перестройка ещё на КД',
    respec_empty: 'Сбрасывать пока нечего',
  };
  showToast(map[code] || fallback);
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
  if (event) playHitEffect(event);
  if (loading) return;
  try {
    loading = true;
    const next = await request('/tap', 'POST');
    setState(next);
  } catch (error) {
    handleError(error.message, 'Тап не дошёл');
  } finally {
    loading = false;
  }
}

enemyWrapEl.addEventListener('click', tapEnemy);

tapUpgradeBtnEl.addEventListener('click', async () => {
  if (loading) return;
  try {
    loading = true;
    const next = await request('/upgrade-tap', 'POST');
    setState(next);
  } catch (error) {
    handleError(error.message, 'Удар не усилился');
  } finally {
    loading = false;
  }
});

rebirthBtnEl.addEventListener('click', async () => {
  if (loading) return;
  try {
    loading = true;
    const next = await request('/rebirth', 'POST');
    setState(next);
  } catch (error) {
    handleError(error.message, 'Перерод не открылся');
  } finally {
    loading = false;
  }
});

respecBtnEl.addEventListener('click', async () => {
  if (loading) return;
  try {
    loading = true;
    const next = await request('/respec', 'POST', {});
    setState(next);
  } catch (error) {
    handleError(error.message, 'Пересборка не сработала');
  } finally {
    loading = false;
  }
});

presetButtons.forEach((btn) => {
  btn.addEventListener('click', async () => {
    if (loading) return;
    try {
      loading = true;
      const next = await request('/respec', 'POST', { preset: btn.dataset.preset });
      setState(next);
    } catch (error) {
      handleError(error.message, 'Пресет не встал');
    } finally {
      loading = false;
    }
  });
});

setInterval(() => refreshState(true), 1200);
refreshState();
