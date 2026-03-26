from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
DB_PATH = ROOT_DIR / "backend" / "players.db"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

MAX_OFFLINE_PROGRESS_SECONDS = 8.0
MAX_KILLS_PER_TICK = 100
HERO_UNLOCK_COST = 120

ENEMIES = [
    {
        "id": "wolf",
        "name": "Степной Волчара",
        "glyph": "/assets/enemies/wolf.svg",
        "base_hp": 16,
        "reward_mult": 1.0,
        "flavor": "Шныряет рядом. Даёшь по клыкам и дальше по фарму.",
    },
    {
        "id": "raven",
        "name": "Чёрный Каркун",
        "glyph": "/assets/enemies/raven.svg",
        "base_hp": 14,
        "reward_mult": 1.05,
        "flavor": "Орёт над головой и бесит с первого кадра.",
    },
    {
        "id": "spirit",
        "name": "Левый Дух",
        "glyph": "/assets/enemies/spirit.svg",
        "base_hp": 18,
        "reward_mult": 1.12,
        "flavor": "Вылез не по делу. Сдувай его без церемоний.",
    },
    {
        "id": "totem",
        "name": "Кривой Тотем",
        "glyph": "/assets/enemies/totem.svg",
        "base_hp": 20,
        "reward_mult": 1.18,
        "flavor": "Стоит криво, бьёт больно. Нормальная степная жесть.",
    },
]

ELITES = [
    {
        "id": "elite_wolf",
        "name": "Элитный Волчара",
        "asset": "/assets/elites/elite_wolf.png",
        "hp_mult": 5.5,
        "reward_mult": 4.0,
        "flavor": "Вожак стаи, тут уже без суеты не вывезешь.",
    },
    {
        "id": "elite_spirit",
        "name": "Разломный Дух",
        "asset": "/assets/elites/elite_spirit.png",
        "hp_mult": 6.0,
        "reward_mult": 4.4,
        "flavor": "Туманная жесть с разлома, бьёт жёстко.",
    },
    {
        "id": "elite_totem",
        "name": "Древний Идол",
        "asset": "/assets/elites/elite_totem.png",
        "hp_mult": 6.6,
        "reward_mult": 4.8,
        "flavor": "Резной столб, но характер у него как у рейд-босса.",
    },
    {
        "id": "elite_rift",
        "name": "Разрыв Пустоты",
        "asset": "/assets/elites/elite_rift.png",
        "hp_mult": 7.1,
        "reward_mult": 5.2,
        "flavor": "Степь рядом с ним прям корёжит, будь начеку.",
    },
]

BOSSES = [
    {
        "id": "boss_wolf",
        "name": "Затменный Волчара",
        "asset": "/assets/bosses/boss_wolf.png",
        "hp_mult": 12.0,
        "reward_mult": 10.0,
        "flavor": "Ночной хозяин степи. Если вышел — будет мясо.",
        "mechanic": "shadow",
        "mechanic_name": "Теневая фаза",
        "mechanic_desc": "Ушёл в тень — дави тапом. DPS мимо кассы.",
    },
    {
        "id": "boss_idol",
        "name": "Грозовой Идол",
        "asset": "/assets/bosses/boss_idol.png",
        "hp_mult": 13.5,
        "reward_mult": 11.5,
        "flavor": "Каменная махина, заряженная молнией по полной.",
        "mechanic": "shield_hits",
        "mechanic_name": "Щит",
        "mechanic_desc": "Сначала ломай щит серией тапов. Потом уже наваливай.",
    },
    {
        "id": "boss_guard",
        "name": "Курганный Дед",
        "asset": "/assets/bosses/boss_guard.png",
        "hp_mult": 15.0,
        "reward_mult": 13.0,
        "flavor": "Поднялся с кургана и явно не рад гостям.",
        "mechanic": "combo_gate",
        "mechanic_name": "Печать",
        "mechanic_desc": "Печать снимается тяжёлым свайпом вниз через Землю.",
    },
    {
        "id": "boss_khan",
        "name": "Костяной Хан",
        "asset": "/assets/bosses/boss_khan.png",
        "hp_mult": 16.5,
        "reward_mult": 14.5,
        "flavor": "Старый хан вернулся и хочет забрать весь лут.",
        "mechanic": "rage_phase",
        "mechanic_name": "Ярость",
        "mechanic_desc": "Во второй фазе окно на разнос. Не отпускай темп.",
    },
    {
        "id": "boss_wind",
        "name": "Хозяйка Бури",
        "asset": "/assets/bosses/boss_wind.png",
        "hp_mult": 18.0,
        "reward_mult": 16.0,
        "flavor": "С её бурей даже бывалые шаманы приседают.",
        "mechanic": "swipe_gate",
        "mechanic_name": "Буря",
        "mechanic_desc": "Тап тут ватный. Вскрывай босса свайпами.",
    },
    {
        "id": "boss_void",
        "name": "Разломная Теневая фаза",
        "asset": "/assets/bosses/boss_void.png",
        "hp_mult": 20.0,
        "reward_mult": 18.0,
        "flavor": "Чистая пустотная жуть, тут без прокаста никак.",
        "mechanic": "hold_gate",
        "mechanic_name": "Узел",
        "mechanic_desc": "Зажимай hold. Вода тут заходит лучше всего.",
    },
]

HEROES = [
    {
        "id": "fire",
        "name": "Шаман Огня",
        "title": "жарит с руки",
        "asset": "/assets/heroes/hero_fire.png",
        "base_cost": 25,
        "base_dps": 4.0,
        "desc": "Усиливает тап, поджигает и держит темп.",
        "growth": 1.18,
    },
    {
        "id": "water",
        "name": "Шаман Воды",
        "title": "льёт и фармит",
        "asset": "/assets/heroes/hero_water.png",
        "base_cost": 80,
        "base_dps": 8.0,
        "desc": "Усиливает hold, помогает по луту и не проседает.",
        "growth": 1.18,
    },
    {
        "id": "earth",
        "name": "Шаман Земли",
        "title": "ломает жир",
        "asset": "/assets/heroes/hero_earth.png",
        "base_cost": 250,
        "base_dps": 16.0,
        "desc": "Лучший по бронированным и тяжёлым целям.",
        "growth": 1.17,
    },
    {
        "id": "air",
        "name": "Шаман Воздуха",
        "title": "разгоняет темп",
        "asset": "/assets/heroes/hero_air.png",
        "base_cost": 700,
        "base_dps": 12.0,
        "desc": "Качает свайпы и делает бой быстрее.",
        "growth": 1.16,
    },
]

RITUALS = [
    {
        "id": "embers",
        "name": "Ритуал Углей",
        "base_cost": 120,
        "cost_mult": 1.8,
        "desc": "+25% к тапу за уровень. Рука станет злее.",
    },
    {
        "id": "tide",
        "name": "Ритуал Прилива",
        "base_cost": 180,
        "cost_mult": 1.85,
        "desc": "+20% к золоту. Фарм идёт жирнее.",
    },
    {
        "id": "stone",
        "name": "Ритуал Камня",
        "base_cost": 260,
        "cost_mult": 1.9,
        "desc": "+2% к криту. Проки пойдут чаще.",
    },
    {
        "id": "storm",
        "name": "Ритуал Бури",
        "base_cost": 420,
        "cost_mult": 1.92,
        "desc": "+25% к DPS. Весь круг бьёт жёстче.",
    },
]

BREAKPOINTS = (10, 25, 50, 100)
HOLD_MIN_MS = 240
HOLD_MAX_MS = 2200
HOLD_BASE_TICKS = 4

HERO_MILESTONES = {
    "fire": {
        10: "Криты поджигают цель.",
        25: "Горение тикает сильнее.",
        50: "Тап и свайп получают доп. шанс крита.",
        100: "Поджог разгоняет весь огонь до inferno.",
    },
    "water": {
        10: "Удержание тапа начинает канал воды.",
        25: "Отпускание даёт всплеск урона.",
        50: "Удержание льёт по группе сильнее.",
        100: "Долгий канал даёт штормовой релиз.",
    },
    "earth": {
        10: "Тапы и тяжёлые приёмы сильнее крошат броню.",
        25: "Элитки и боссы получают больше урона.",
        50: "После пробоя брони цель мягче для дожима.",
        100: "Земля даёт тяжёлый shatter-эффект.",
    },
    "air": {
        10: "Свайпы бьют сильнее.",
        25: "Комбо собираются стабильнее.",
        50: "Скоростные жесты усиливаются цепью.",
        100: "Длинные рисунки получают overdrive.",
    },
}
