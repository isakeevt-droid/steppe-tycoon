from __future__ import annotations

import json
import math
import random
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
SAVE_PATH = ROOT_DIR / "backend" / "save_state.json"

app = FastAPI(title="Steppe Shaman")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
state_lock = threading.Lock()

ENEMIES = [
    {
        "id": "wolf",
        "name": "Лютый Волчара",
        "glyph": "/assets/icons/wolf.svg",
        "reward_mult": 1.0,
        "flavor": "Шныряет по степи и лезет под руку.",
    },
    {
        "id": "raven",
        "name": "Чёрный Каркун",
        "glyph": "/assets/icons/raven.svg",
        "reward_mult": 1.05,
        "flavor": "Каркает сверху, как будто беду заспавнил.",
    },
    {
        "id": "spirit",
        "name": "Шальной Дух",
        "glyph": "/assets/icons/spirit.svg",
        "reward_mult": 1.12,
        "flavor": "Сквозняком залетел и решил качать права.",
    },
    {
        "id": "totem",
        "name": "Дикий Тотем",
        "glyph": "/assets/icons/totem.svg",
        "reward_mult": 1.18,
        "flavor": "Старый идол, но вайб у него злой до мурашек.",
    },
]

ELITES = [
    {
        "id": "elite_wolf",
        "name": "Элитный Волчара",
        "asset": "/assets/elites/elite_wolf.png",
        "hp_mult": 5.2,
        "reward_mult": 4.2,
        "flavor": "Вожак стаи, тут уже без суеты не вывезешь.",
    },
    {
        "id": "elite_spirit",
        "name": "Разломный Дух",
        "asset": "/assets/elites/elite_spirit.png",
        "hp_mult": 5.8,
        "reward_mult": 4.5,
        "flavor": "Туманная жесть с разлома, бьёт жёстко.",
    },
    {
        "id": "elite_totem",
        "name": "Древний Идол",
        "asset": "/assets/elites/elite_totem.png",
        "hp_mult": 6.4,
        "reward_mult": 4.9,
        "flavor": "Резной столб, но характер у него как у рейд-босса.",
    },
    {
        "id": "elite_rift",
        "name": "Разрыв Пустоты",
        "asset": "/assets/elites/elite_rift.png",
        "hp_mult": 6.9,
        "reward_mult": 5.3,
        "flavor": "Степь рядом с ним прям корёжит, будь начеку.",
    },
]

BOSSES = [
    {
        "id": "boss_wolf",
        "name": "Волк Затмения",
        "asset": "/assets/bosses/boss_wolf.png",
        "hp_mult": 12.0,
        "reward_mult": 11.0,
        "mechanic": "burst",
        "mechanic_name": "Таймер",
        "hint": "Убей за 12 сек, иначе он тебя сожрёт.",
        "flavor": "Ночной хозяин степи. Если вышел — будет мясо.",
        "timer": 12.0,
    },
    {
        "id": "boss_idol",
        "name": "Громовой Идол",
        "asset": "/assets/bosses/boss_idol.png",
        "hp_mult": 13.5,
        "reward_mult": 12.0,
        "mechanic": "shield",
        "mechanic_name": "Щит",
        "hint": "Почти не чувствует духов. Бей руками.",
        "flavor": "Каменная махина, заряженная молнией по полной.",
    },
    {
        "id": "boss_guard",
        "name": "Страж Кургана",
        "asset": "/assets/bosses/boss_guard.png",
        "hp_mult": 15.0,
        "reward_mult": 13.0,
        "mechanic": "anti_dps",
        "mechanic_name": "Анти-DPS",
        "hint": "Духи проседают. Тащи критами и тапом.",
        "flavor": "Поднялся с кургана и явно не рад гостям.",
    },
    {
        "id": "boss_wind",
        "name": "Владычица Ветра",
        "asset": "/assets/bosses/boss_wind.png",
        "hp_mult": 17.2,
        "reward_mult": 15.0,
        "mechanic": "anti_crit",
        "mechanic_name": "Анти-крит",
        "hint": "Криты режет в ноль. Дави стабильной силой.",
        "flavor": "С её бурей даже бывалые шаманы приседают.",
    },
    {
        "id": "boss_void",
        "name": "Тень Разлома",
        "asset": "/assets/bosses/boss_void.png",
        "hp_mult": 19.0,
        "reward_mult": 17.0,
        "mechanic": "scaling",
        "mechanic_name": "Разгон",
        "hint": "Чем дольше бой, тем жирнее эта тварь.",
        "flavor": "Чистая пустотная жуть, тут без прокаста никак.",
        "scale_interval": 3.0,
        "scale_mult": 1.25,
    },
]

HEROES = [
    {
        "id": "fire",
        "name": "Шаман Огня",
        "title": "бурст и жар",
        "asset": "/assets/heroes/hero_fire.png",
        "base_cost": 25,
        "base_dps": 4.0,
        "desc": "Качает тап, бурст и крит урон.",
        "growth": 1.15,
        "emoji": "🔥",
    },
    {
        "id": "water",
        "name": "Шаман Воды",
        "title": "фарм и лут",
        "asset": "/assets/heroes/hero_water.png",
        "base_cost": 80,
        "base_dps": 8.0,
        "desc": "Тащит золото и шанс двойной награды.",
        "growth": 1.15,
        "emoji": "🌊",
    },
    {
        "id": "earth",
        "name": "Шаман Земли",
        "title": "антибосс и крит шанс",
        "asset": "/assets/heroes/hero_earth.png",
        "base_cost": 250,
        "base_dps": 16.0,
        "desc": "Ломает боссов и делает криты стабильнее.",
        "growth": 1.145,
        "emoji": "🪨",
    },
    {
        "id": "air",
        "name": "Шаман Воздуха",
        "title": "ускоряет всю пачку",
        "asset": "/assets/heroes/hero_air.png",
        "base_cost": 700,
        "base_dps": 12.0,
        "desc": "Баффает всех и держит темп боя.",
        "growth": 1.14,
        "emoji": "🌪",
    },
]

RITUALS = [
    {
        "id": "embers",
        "name": "Ритуал Углей",
        "base_cost": 120,
        "cost_mult": 1.8,
        "desc": "+25% к силе тапа за уровень.",
    },
    {
        "id": "tide",
        "name": "Ритуал Прилива",
        "base_cost": 180,
        "cost_mult": 1.85,
        "desc": "+20% к золоту за уровень.",
    },
    {
        "id": "stone",
        "name": "Ритуал Камня",
        "base_cost": 260,
        "cost_mult": 1.9,
        "desc": "+2% к шансу крита за уровень.",
    },
    {
        "id": "storm",
        "name": "Ритуал Бури",
        "base_cost": 420,
        "cost_mult": 1.92,
        "desc": "+25% к DPS за уровень.",
    },
]

RITUAL_PATHS = {
    "damage": {
        "name": "Ветка огня",
        "desc": "+18% к тапу и +12% к бурсту.",
    },
    "farm": {
        "name": "Ветка воды",
        "desc": "+22% к золоту и +10% к двойному золоту.",
    },
    "boss": {
        "name": "Ветка земли",
        "desc": "+20% к урону по боссам.",
    },
}

META_UPGRADES = {
    "tap": {"name": "Сила руки", "cost": 1, "desc": "+15% к тапу за уровень."},
    "dps": {"name": "Сила духов", "cost": 1, "desc": "+10% к DPS за уровень."},
    "gold": {"name": "Шаманский барыш", "cost": 1, "desc": "+20% к золоту за уровень."},
    "boss": {"name": "Охота на ханов", "cost": 1, "desc": "+25% к урону по боссам за уровень."},
}

SKILLS = {
    "lightning": {
        "name": "Удар молнии",
        "cooldown": 6.0,
        "desc": "x5 от текущего тапа. Крит тоже может прокнуть.",
    },
    "totem": {
        "name": "Тотем ярости",
        "cooldown": 15.0,
        "duration": 5.0,
        "desc": "+100% к DPS и +50% к тапу на 5 сек.",
    },
    "shield": {
        "name": "Каменный щит",
        "cooldown": 12.0,
        "duration": 3.0,
        "desc": "На 3 сек игнорит механику босса.",
    },
}

BUILD_PRESETS = {
    "crit": ("fire", "air"),
    "farm": ("water", "earth"),
    "boss": ("earth", "fire"),
}

SYNERGY_RULES = [
    {
        "id": "crit",
        "name": "Крит билд ⚡",
        "heroes": ("fire", "air"),
        "threshold": 25,
        "desc": "+50% крит урон и +20% шанс крита.",
    },
    {
        "id": "farm",
        "name": "Фарм билд 💰",
        "heroes": ("water", "earth"),
        "threshold": 25,
        "desc": "+40% золота и +20% к двойному золоту.",
    },
    {
        "id": "boss",
        "name": "Антибосс билд 🐉",
        "heroes": ("earth", "fire"),
        "threshold": 25,
        "desc": "+60% к урону по боссам.",
    },
    {
        "id": "speed",
        "name": "Скоростной билд 🌪",
        "heroes": ("air", "water"),
        "threshold": 25,
        "desc": "+30% к DPS и +20% к золоту.",
    },
]

BOSS_VICTORY_LINES = [
    "РАЗНЕС В ПЫЛЬ 💀",
    "СТЕПЬ ОДОБРЯЕТ ⚡",
    "ХАН УПАЛ 🐺",
    "ДУХ СЛОМАН 🌪",
    "ЭТО БЫЛ РАЗЪЁМ 🔥",
]

BREAKPOINTS = (10, 25, 50)
RESPEC_COOLDOWN = 600.0


class BuyRequest(BaseModel):
    id: str


class SkillRequest(BaseModel):
    id: str


class PathRequest(BaseModel):
    id: str


class MetaRequest(BaseModel):
    id: str


class RespecRequest(BaseModel):
    preset: str | None = None


class BuildBuyRequest(BaseModel):
    hero_id: str


def default_state() -> dict[str, Any]:
    state = {
        "gold": 0.0,
        "stage": 1,
        "kills": 0,
        "boss_kills": 0,
        "last_tick": time.time(),
        "tap_level": 1,
        "heroes": {hero["id"]: 0 for hero in HEROES},
        "rituals": {ritual["id"]: 0 for ritual in RITUALS},
        "ritual_path": "damage",
        "meta_points": 0,
        "meta_upgrades": {key: 0 for key in META_UPGRADES},
        "trophies": 0,
        "rebirths": 0,
        "best_stage": 1,
        "best_wave": 1,
        "best_tap": 1.0,
        "best_dps": 0.0,
        "best_score": 0,
        "lifetime_gold": 0.0,
        "lifetime_kills": 0,
        "lifetime_boss_kills": 0,
        "top_runs": [],
        "hero_gold_spent": 0.0,
        "last_respec_at": 0.0,
        "boss_fail_streak": 0,
        "last_feedback": "",
        "last_boss_message": "",
        "skills": {
            skill_id: {"ready_at": 0.0, "active_until": 0.0}
            for skill_id in SKILLS
        },
        "enemy": {},
    }
    state["enemy"] = generate_enemy(state["stage"])
    reset_enemy_runtime(state)
    return state


def save_state(state: dict[str, Any]) -> None:
    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = SAVE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(SAVE_PATH)


def safe_load_state() -> dict[str, Any]:
    if not SAVE_PATH.exists():
        state = default_state()
        save_state(state)
        return state
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        state = default_state()
        for key in state.keys():
            if key in {"enemy", "heroes", "rituals", "skills", "meta_upgrades"}:
                continue
            state[key] = data.get(key, state[key])
        state["heroes"].update(data.get("heroes", {}))
        state["rituals"].update(data.get("rituals", {}))
        state["meta_upgrades"].update(data.get("meta_upgrades", {}))
        if isinstance(data.get("skills"), dict):
            for skill_id in state["skills"]:
                state["skills"][skill_id].update(data["skills"].get(skill_id, {}))
        enemy = data.get("enemy") or generate_enemy(int(state["stage"]))
        if "hp" not in enemy or "max_hp" not in enemy:
            enemy = generate_enemy(int(state["stage"]))
        state["enemy"] = enemy
        state["last_tick"] = float(data.get("last_tick", time.time()))
        state["ritual_path"] = data.get("ritual_path", "damage") if data.get("ritual_path") in RITUAL_PATHS else "damage"
        if not isinstance(state.get("top_runs"), list):
            state["top_runs"] = []
        reset_enemy_runtime(state)
        return state
    except Exception:
        state = default_state()
        save_state(state)
        return state


def reset_enemy_runtime(state: dict[str, Any]) -> None:
    enemy = state["enemy"]
    now = time.time()
    if enemy.get("type") == "boss":
        if enemy.get("mechanic") == "burst":
            enemy["timer_end"] = now + float(enemy.get("timer", 12.0))
        else:
            enemy["timer_end"] = None
        enemy["next_scale_at"] = now + float(enemy.get("scale_interval", 3.0))
    else:
        enemy["timer_end"] = None
        enemy["next_scale_at"] = None


def stage_type(stage: int) -> str:
    if stage % 10 == 0:
        return "boss"
    if stage % 5 == 0:
        return "elite"
    return "normal"


def enemy_base_hp(stage: int) -> float:
    return 16 * (1.32 ** (stage - 1))


def enemy_reward(stage: int) -> float:
    return 6 * (1.18 ** (stage - 1))


def generate_enemy(stage: int) -> dict[str, Any]:
    kind = stage_type(stage)
    if kind == "boss":
        template = BOSSES[((stage // 10) - 1) % len(BOSSES)]
    elif kind == "elite":
        template = ELITES[((stage // 5) - 1) % len(ELITES)]
    else:
        template = ENEMIES[(stage - 1) % len(ENEMIES)]
    base_hp = enemy_base_hp(stage)
    base_reward = enemy_reward(stage)
    hp = base_hp * float(template.get("hp_mult", 1.0))
    reward = base_reward * float(template.get("reward_mult", 1.0))
    if kind == "boss":
        reward *= 1.3
    enemy = {
        "id": template["id"],
        "name": template["name"],
        "asset": template.get("asset"),
        "glyph": template.get("glyph", "✦"),
        "type": kind,
        "flavor": template.get("flavor", ""),
        "hp": round(hp, 2),
        "max_hp": round(hp, 2),
        "reward": round(reward, 2),
    }
    if kind == "boss":
        enemy["mechanic"] = template.get("mechanic")
        enemy["mechanic_name"] = template.get("mechanic_name")
        enemy["hint"] = template.get("hint")
        if template.get("timer"):
            enemy["timer"] = float(template["timer"])
        if template.get("scale_interval"):
            enemy["scale_interval"] = float(template["scale_interval"])
        if template.get("scale_mult"):
            enemy["scale_mult"] = float(template["scale_mult"])
    return enemy


def hero_level(state: dict[str, Any], hero_id: str) -> int:
    return int(state["heroes"].get(hero_id, 0))


def ritual_level(state: dict[str, Any], ritual_id: str) -> int:
    return int(state["rituals"].get(ritual_id, 0))


def meta_level(state: dict[str, Any], meta_id: str) -> int:
    return int(state["meta_upgrades"].get(meta_id, 0))


def hero_cost(hero_id: str, level: int) -> float:
    hero = next(item for item in HEROES if item["id"] == hero_id)
    return hero["base_cost"] * (1.15 if hero_id in {"fire", "water"} else 1.14 if hero_id == "air" else 1.145) ** level


def ritual_cost(ritual_id: str, level: int) -> float:
    ritual = next(item for item in RITUALS if item["id"] == ritual_id)
    return ritual["base_cost"] * (ritual["cost_mult"] ** level)


def trophy_power_multiplier(state: dict[str, Any]) -> float:
    return 1 + int(state.get("trophies", 0)) * 0.12


def hero_breakpoint_count(level: int) -> int:
    return sum(1 for point in BREAKPOINTS if level >= point)


def next_breakpoint(level: int) -> int | None:
    for point in BREAKPOINTS:
        if level < point:
            return point
    return None


def build_levels(state: dict[str, Any]) -> dict[str, int]:
    return {hero["id"]: hero_level(state, hero["id"]) for hero in HEROES}


def active_synergy_ids(state: dict[str, Any]) -> set[str]:
    levels = build_levels(state)
    active: set[str] = set()
    for rule in SYNERGY_RULES:
        left, right = rule["heroes"]
        if levels[left] >= int(rule["threshold"]) and levels[right] >= int(rule["threshold"]):
            active.add(rule["id"])
    return active


def primary_synergy(state: dict[str, Any]) -> dict[str, Any] | None:
    active = active_synergy_ids(state)
    for rule in SYNERGY_RULES:
        if rule["id"] in active:
            return rule
    return None


def ritual_path_multiplier(state: dict[str, Any], aspect: str) -> float:
    path = state.get("ritual_path", "damage")
    if aspect == "tap" and path == "damage":
        return 1.18
    if aspect == "burst" and path == "damage":
        return 1.12
    if aspect == "gold" and path == "farm":
        return 1.22
    if aspect == "double_gold" and path == "farm":
        return 1.10
    if aspect == "boss" and path == "boss":
        return 1.20
    return 1.0


def skill_active(state: dict[str, Any], skill_id: str) -> bool:
    return float(state["skills"][skill_id].get("active_until", 0.0)) > time.time()


def hero_personal_dps(hero_id: str, level: int) -> float:
    if level <= 0:
        return 0.0
    hero = next(item for item in HEROES if item["id"] == hero_id)
    dps = hero["base_dps"] * level * (hero["growth"] ** max(0, level - 1))
    dps *= 2 ** hero_breakpoint_count(level)
    return dps


def air_aura_multiplier(state: dict[str, Any]) -> float:
    level = hero_level(state, "air")
    return 1.0 + level * 0.015


def fire_tap_bonus(state: dict[str, Any]) -> float:
    return hero_level(state, "fire") * 0.03


def water_gold_bonus(state: dict[str, Any]) -> float:
    return hero_level(state, "water") * 0.02


def earth_boss_bonus(state: dict[str, Any]) -> float:
    return hero_level(state, "earth") * 0.03


def earth_crit_bonus(state: dict[str, Any]) -> float:
    return hero_level(state, "earth") * 0.002


def meta_tap_multiplier(state: dict[str, Any]) -> float:
    return 1 + meta_level(state, "tap") * 0.15


def meta_dps_multiplier(state: dict[str, Any]) -> float:
    return 1 + meta_level(state, "dps") * 0.10


def meta_gold_multiplier(state: dict[str, Any]) -> float:
    return 1 + meta_level(state, "gold") * 0.20


def meta_boss_multiplier(state: dict[str, Any]) -> float:
    return 1 + meta_level(state, "boss") * 0.25


def safety_multiplier(state: dict[str, Any]) -> float:
    return 1 + min(int(state.get("boss_fail_streak", 0)), 3) * 0.2


def boss_damage_multiplier(state: dict[str, Any]) -> float:
    mult = 1.0
    if state["enemy"].get("type") == "boss":
        mult *= 1 + earth_boss_bonus(state)
        mult *= meta_boss_multiplier(state)
        mult *= ritual_path_multiplier(state, "boss")
        if "boss" in active_synergy_ids(state):
            mult *= 1.6
        mult *= safety_multiplier(state)
    return mult


def total_hero_dps(state: dict[str, Any]) -> float:
    total = sum(hero_personal_dps(hero["id"], hero_level(state, hero["id"])) for hero in HEROES)
    total *= air_aura_multiplier(state)
    total *= 1 + 0.25 * ritual_level(state, "storm")
    total *= trophy_power_multiplier(state)
    total *= meta_dps_multiplier(state)
    if "speed" in active_synergy_ids(state):
        total *= 1.3
    if skill_active(state, "totem"):
        total *= 2.0
    return total * boss_damage_multiplier(state)


def crit_chance(state: dict[str, Any]) -> float:
    chance = 0.05 + earth_crit_bonus(state) + ritual_level(state, "stone") * 0.02
    if "crit" in active_synergy_ids(state):
        chance += 0.20
    chance *= enemy_crit_modifier(state)
    return min(chance, 0.65)


def crit_multiplier(state: dict[str, Any]) -> float:
    mult = 2.0 + hero_level(state, "fire") * 0.02 + int(state.get("trophies", 0)) * 0.01
    if "crit" in active_synergy_ids(state):
        mult *= 1.5
    return mult


def tap_damage(state: dict[str, Any]) -> float:
    embers = ritual_level(state, "embers")
    base = 1.0 + (state["tap_level"] - 1) * 1.4
    base *= 1 + fire_tap_bonus(state)
    base *= 1 + embers * 0.25
    base *= trophy_power_multiplier(state)
    base *= meta_tap_multiplier(state)
    base *= ritual_path_multiplier(state, "tap")
    if skill_active(state, "totem"):
        base *= 1.5
    base *= boss_damage_multiplier(state)
    return base


def double_gold_chance(state: dict[str, Any]) -> float:
    chance = hero_level(state, "water") * 0.02 + hero_breakpoint_count(hero_level(state, "water")) * 0.10
    if "farm" in active_synergy_ids(state):
        chance += 0.20
    chance *= ritual_path_multiplier(state, "double_gold")
    return min(chance, 0.60)


def gold_multiplier(state: dict[str, Any]) -> float:
    mult = 1 + water_gold_bonus(state) + ritual_level(state, "tide") * 0.20 + int(state.get("trophies", 0)) * 0.015
    mult *= meta_gold_multiplier(state)
    mult *= ritual_path_multiplier(state, "gold")
    if "farm" in active_synergy_ids(state):
        mult *= 1.4
    if "speed" in active_synergy_ids(state):
        mult *= 1.2
    return mult


def enemy_dps_modifier(state: dict[str, Any]) -> float:
    if skill_active(state, "shield"):
        return 1.0
    mechanic = state["enemy"].get("mechanic")
    if mechanic == "shield":
        return 0.3
    if mechanic == "anti_dps":
        return 0.2
    return 1.0


def enemy_tap_modifier(state: dict[str, Any]) -> float:
    if skill_active(state, "shield"):
        return 1.0
    return 1.0


def enemy_crit_modifier(state: dict[str, Any]) -> float:
    if skill_active(state, "shield"):
        return 1.0
    if state["enemy"].get("mechanic") == "anti_crit":
        return 0.5
    if state["enemy"].get("mechanic") == "anti_dps":
        return 1.15
    return 1.0


def wave_number(stage: int) -> int:
    return math.ceil(stage / 10)


def award_gold(state: dict[str, Any], amount: float) -> dict[str, Any] | None:
    payout = amount
    doubled = random.random() < double_gold_chance(state)
    if doubled:
        payout *= 2
    state["gold"] += payout
    state["lifetime_gold"] = float(state.get("lifetime_gold", 0.0)) + payout
    if doubled:
        return {"type": "double_gold", "text": "x2 золото 💰"}
    return None


def achievement_catalog() -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    entries = [
        ("Разносы", "kills", [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000], "Разнеси {value} врагов за всё время."),
        ("Боссы", "boss_kills", [1, 3, 5, 10, 15, 25, 40, 60, 80, 120, 160, 220], "Урони {value} боссов за всё время."),
        ("Этап", "stage", [5, 10, 15, 20, 30, 40, 50, 75, 100, 125, 150, 200], "Долети до этапа {value}."),
        ("Трофеи", "trophies", [1, 3, 5, 10, 15, 20, 30, 45, 60, 80, 100, 140], "Подними {value} трофеев с перерождений."),
        ("Перероды", "rebirths", [1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 50, 75], "Сделай {value} перерождений."),
        ("Золото", "gold", [100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1_000_000], "Подними {value} золота за всё время."),
    ]
    for prefix, stat, values, desc in entries:
        for value in values:
            catalog.append(
                {
                    "id": f"{stat}_{value}",
                    "name": f"{prefix}: {value}",
                    "stat": stat,
                    "target": value,
                    "desc": desc.format(value=value),
                }
            )
    return catalog


ACHIEVEMENTS = achievement_catalog()


def achievement_progress_value(state: dict[str, Any], stat: str) -> float:
    if stat == "kills":
        return float(state.get("lifetime_kills", 0))
    if stat == "boss_kills":
        return float(state.get("lifetime_boss_kills", 0))
    if stat == "stage":
        return float(state.get("best_stage", state.get("stage", 1)))
    if stat == "trophies":
        return float(state.get("trophies", 0))
    if stat == "rebirths":
        return float(state.get("rebirths", 0))
    if stat == "gold":
        return float(state.get("lifetime_gold", 0.0))
    return 0.0


def build_achievements(state: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    unlocked = 0
    for ach in ACHIEVEMENTS:
        value = achievement_progress_value(state, ach["stat"])
        done = value >= ach["target"]
        if done:
            unlocked += 1
        items.append(
            {
                "id": ach["id"],
                "name": ach["name"],
                "desc": ach["desc"],
                "target": ach["target"],
                "value": round(value, 2),
                "done": done,
            }
        )
    items.sort(key=lambda item: (item["done"], item["value"] / max(1, item["target"])), reverse=True)
    return {"unlocked": unlocked, "total": len(items), "items": items}


def score_value(state: dict[str, Any], achievements_unlocked: int | None = None) -> int:
    unlocked = achievements_unlocked if achievements_unlocked is not None else build_achievements(state)["unlocked"]
    return int(
        int(state.get("best_stage", 1)) * 25
        + int(state.get("trophies", 0)) * 1000
        + int(state.get("lifetime_boss_kills", 0)) * 100
        + unlocked * 50
    )


def update_records(state: dict[str, Any]) -> None:
    stage = int(state["stage"])
    state["best_stage"] = max(int(state.get("best_stage", 1)), stage)
    state["best_wave"] = max(int(state.get("best_wave", 1)), wave_number(stage))
    state["best_tap"] = max(float(state.get("best_tap", 1.0)), tap_damage(state))
    state["best_dps"] = max(float(state.get("best_dps", 0.0)), total_hero_dps(state))
    state["best_score"] = max(int(state.get("best_score", 0)), score_value(state))


def boss_fail_feedback(state: dict[str, Any]) -> str:
    enemy = state["enemy"]
    mechanic = enemy.get("mechanic")
    if mechanic == "burst":
        return "Не хватило burst. Качни 🔥 огонь и прожми молнию." 
    if mechanic == "shield":
        return "Босс режет духов. Нужен тап и 🔥 огонь." 
    if mechanic == "anti_dps":
        return "Авто-DPS задушен. Собирай 🪨 землю + 🔥 огонь." 
    if mechanic == "anti_crit":
        return "Криты режет. Нужен стабильный 🌪 воздух." 
    if mechanic == "scaling":
        return "Бой затянулся. Разгони DPS и тотем ярости." 
    return enemy.get("hint", "Подтяни билд и попробуй ещё раз.")


def reset_current_enemy(state: dict[str, Any], feedback: str = "") -> None:
    state["enemy"] = generate_enemy(int(state["stage"]))
    reset_enemy_runtime(state)
    if feedback:
        state["last_feedback"] = feedback


def resolve_enemy_death(state: dict[str, Any]) -> dict[str, Any] | None:
    reward = state["enemy"]["reward"] * gold_multiplier(state)
    reward_event = award_gold(state, reward)
    boss_kill = state["enemy"]["type"] == "boss"
    state["kills"] += 1
    state["lifetime_kills"] = int(state.get("lifetime_kills", 0)) + 1
    if boss_kill:
        state["boss_kills"] += 1
        state["lifetime_boss_kills"] = int(state.get("lifetime_boss_kills", 0)) + 1
        state["boss_fail_streak"] = 0
        state["last_feedback"] = ""
        state["last_boss_message"] = random.choice(BOSS_VICTORY_LINES)
    state["stage"] += 1
    state["enemy"] = generate_enemy(int(state["stage"]))
    reset_enemy_runtime(state)
    update_records(state)
    return reward_event


def apply_damage(state: dict[str, Any], damage: float) -> tuple[int, dict[str, Any] | None]:
    kills = 0
    event: dict[str, Any] | None = None
    remaining = damage
    while remaining > 0:
        hp = state["enemy"]["hp"]
        if remaining >= hp:
            remaining -= hp
            kills += 1
            event = resolve_enemy_death(state) or event
        else:
            state["enemy"]["hp"] = round(max(0.0, hp - remaining), 2)
            break
        if kills > 200:
            break
    return kills, event


def handle_boss_runtime(state: dict[str, Any], now: float) -> None:
    enemy = state["enemy"]
    if enemy.get("type") != "boss":
        return
    timer_end = enemy.get("timer_end")
    if timer_end and now >= float(timer_end):
        state["boss_fail_streak"] = int(state.get("boss_fail_streak", 0)) + 1
        feedback = boss_fail_feedback(state)
        reset_current_enemy(state, feedback)
        return
    if enemy.get("mechanic") == "scaling":
        next_scale_at = enemy.get("next_scale_at")
        scale_interval = float(enemy.get("scale_interval", 3.0))
        scale_mult = float(enemy.get("scale_mult", 1.25))
        while next_scale_at and now >= float(next_scale_at):
            enemy["max_hp"] = round(enemy["max_hp"] * scale_mult, 2)
            enemy["hp"] = round(enemy["hp"] * scale_mult, 2)
            next_scale_at = float(next_scale_at) + scale_interval
        enemy["next_scale_at"] = next_scale_at


def advance_state(state: dict[str, Any]) -> dict[str, Any] | None:
    now = time.time()
    elapsed = max(0.0, now - float(state.get("last_tick", now)))
    state["last_tick"] = now
    handle_boss_runtime(state, now)
    dps = total_hero_dps(state) * enemy_dps_modifier(state)
    if elapsed <= 0 or dps <= 0:
        return None
    _, event = apply_damage(state, dps * elapsed)
    return event


def tap_upgrade_cost(state: dict[str, Any]) -> float:
    return 12 * (1.33 ** max(0, state["tap_level"] - 1))


def rebirth_reward(state: dict[str, Any]) -> int:
    stage = int(state.get("stage", 1))
    bosses = int(state.get("boss_kills", 0))
    return max(0, (stage - 1) // 10 + bosses)


def respec_refund(state: dict[str, Any]) -> float:
    return float(state.get("hero_gold_spent", 0.0)) * 0.7


def respec_available_in(state: dict[str, Any]) -> float:
    return max(0.0, RESPEC_COOLDOWN - (time.time() - float(state.get("last_respec_at", 0.0))))


def build_status(state: dict[str, Any]) -> dict[str, Any]:
    levels = build_levels(state)
    active_ids = active_synergy_ids(state)
    primary = primary_synergy(state)
    total_tap = tap_damage(state)
    total_dps = total_hero_dps(state)
    farming = (gold_multiplier(state) - 1) * 100
    synergies = []
    for rule in SYNERGY_RULES:
        left, right = rule["heroes"]
        synergies.append(
            {
                "id": rule["id"],
                "name": rule["name"],
                "desc": rule["desc"],
                "active": rule["id"] in active_ids,
                "threshold": rule["threshold"],
                "progress": [levels[left], levels[right]],
                "heroes": [left, right],
            }
        )
    weakness = "Баланс норм"
    enemy = state["enemy"]
    if enemy.get("type") == "boss":
        mechanic = enemy.get("mechanic")
        if mechanic in {"burst", "shield"} and hero_level(state, "fire") < 25:
            weakness = "⚠ мало burst / тапа"
        elif mechanic == "anti_dps" and hero_level(state, "earth") < 25:
            weakness = "⚠ слабый антибосс"
        elif mechanic == "anti_crit" and hero_level(state, "air") < 25:
            weakness = "⚠ низкий стабильный DPS"
        elif mechanic == "scaling" and total_dps < total_tap * 5:
            weakness = "⚠ не хватает темпа DPS"
    return {
        "elements": [
            {"id": hero["id"], "emoji": hero["emoji"], "name": hero["name"], "level": levels[hero["id"]]}
            for hero in HEROES
        ],
        "active_synergy": primary["name"] if primary else "Билд не собран",
        "active_synergy_id": primary["id"] if primary else None,
        "synergies": synergies,
        "strengths": {
            "tap": round(total_tap, 2),
            "dps": round(total_dps, 2),
            "farm": round(farming, 1),
        },
        "weakness": weakness,
    }


def hero_passive_text(state: dict[str, Any], hero_id: str) -> str:
    if hero_id == "fire":
        return f"Тап жарит на +{round(fire_tap_bonus(state) * 100, 1)}%"
    if hero_id == "water":
        return f"Золото +{round(water_gold_bonus(state) * 100, 1)}%"
    if hero_id == "earth":
        return f"По боссам +{round(earth_boss_bonus(state) * 100, 1)}%"
    if hero_id == "air":
        return f"Пачка бустится на +{round((air_aura_multiplier(state) - 1) * 100, 1)}%"
    return ""


def hero_next_bonus_text(hero_id: str, level: int) -> str:
    nxt = next_breakpoint(level)
    if nxt is None:
        return "Все жирные пороги уже забраны"
    bonus = {
        "fire": "x2 к личному DPS и бурсту",
        "water": "x2 к личному DPS и фарму",
        "earth": "x2 к личному DPS и антибоссу",
        "air": "x2 к личному DPS и ускорению пачки",
    }[hero_id]
    return f"Следующий порог: {nxt} лвл → {bonus}"


def hero_build_role(hero_id: str) -> str:
    return {
        "fire": "Тап + крит урон",
        "water": "Золото + x2 награда",
        "earth": "Боссы + крит шанс",
        "air": "Усиление DPS",
    }[hero_id]


def build_active_heroes(state: dict[str, Any]) -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    for hero in HEROES:
        level = hero_level(state, hero["id"])
        if level <= 0:
            continue
        active.append(
            {
                "id": hero["id"],
                "name": hero["name"],
                "title": hero["title"],
                "asset": hero["asset"],
                "level": level,
                "emoji": hero["emoji"],
                "dps": round(hero_personal_dps(hero["id"], level), 2),
                "passive": hero_passive_text(state, hero["id"]),
            }
        )
    return active


def push_top_run(state: dict[str, Any], reward: int, achievements_unlocked: int) -> None:
    run = {
        "rebirth": int(state.get("rebirths", 0)) + 1,
        "score": score_value(state, achievements_unlocked),
        "stage": int(state.get("stage", 1)),
        "trophies": reward,
    }
    top_runs = list(state.get("top_runs", []))
    top_runs.append(run)
    top_runs.sort(key=lambda item: (item["score"], item["stage"], item["trophies"]), reverse=True)
    state["top_runs"] = top_runs[:10]


def build_payload(state: dict[str, Any], last_hit: dict[str, Any] | None = None, flash_event: dict[str, Any] | None = None) -> dict[str, Any]:
    enemy = state["enemy"]
    achievements = build_achievements(state)
    current_score = score_value(state, achievements["unlocked"])

    hero_cards = []
    for hero in HEROES:
        level = hero_level(state, hero["id"])
        cost = hero_cost(hero["id"], level)
        dps_value = hero_personal_dps(hero["id"], level)
        hero_cards.append(
            {
                "id": hero["id"],
                "name": hero["name"],
                "title": hero["title"],
                "asset": hero["asset"],
                "emoji": hero["emoji"],
                "desc": hero["desc"],
                "level": level,
                "cost": round(cost, 2),
                "dps": round(dps_value, 2),
                "breakpoints": hero_breakpoint_count(level),
                "passive": hero_passive_text(state, hero["id"]),
                "next_bonus": hero_next_bonus_text(hero["id"], level),
                "build_role": hero_build_role(hero["id"]),
            }
        )

    ritual_cards = []
    for ritual in RITUALS:
        level = ritual_level(state, ritual["id"])
        ritual_cards.append(
            {
                "id": ritual["id"],
                "name": ritual["name"],
                "desc": ritual["desc"],
                "level": level,
                "cost": round(ritual_cost(ritual["id"], level), 2),
            }
        )

    meta_cards = []
    for meta_id, meta in META_UPGRADES.items():
        meta_cards.append(
            {
                "id": meta_id,
                "name": meta["name"],
                "desc": meta["desc"],
                "level": meta_level(state, meta_id),
                "cost": meta["cost"],
            }
        )

    skills = []
    now = time.time()
    for skill_id, meta in SKILLS.items():
        ready_in = max(0.0, float(state["skills"][skill_id].get("ready_at", 0.0)) - now)
        active_left = max(0.0, float(state["skills"][skill_id].get("active_until", 0.0)) - now)
        skills.append(
            {
                "id": skill_id,
                "name": meta["name"],
                "desc": meta["desc"],
                "ready_in": round(ready_in, 1),
                "active_left": round(active_left, 1),
                "is_ready": ready_in <= 0.0,
            }
        )

    ritual_paths = []
    current_path = state.get("ritual_path", "damage")
    for path_id, path in RITUAL_PATHS.items():
        ritual_paths.append(
            {
                "id": path_id,
                "name": path["name"],
                "desc": path["desc"],
                "active": path_id == current_path,
            }
        )

    feedback = state.get("last_feedback", "")
    if int(state.get("boss_fail_streak", 0)) >= 2 and enemy.get("type") == "boss":
        feedback = boss_fail_feedback(state)

    return {
        "gold": round(state["gold"], 2),
        "stage": int(state["stage"]),
        "wave": wave_number(int(state["stage"])),
        "kills": int(state["kills"]),
        "boss_kills": int(state["boss_kills"]),
        "tap_level": int(state["tap_level"]),
        "tap_cost": round(tap_upgrade_cost(state), 2),
        "tap_damage": round(tap_damage(state) * enemy_tap_modifier(state), 2),
        "dps": round(total_hero_dps(state) * enemy_dps_modifier(state), 2),
        "crit_chance": round(crit_chance(state) * 100, 1),
        "crit_multiplier": round(crit_multiplier(state), 2),
        "gold_bonus": round((gold_multiplier(state) - 1) * 100, 1),
        "double_gold_chance": round(double_gold_chance(state) * 100, 1),
        "trophies": int(state.get("trophies", 0)),
        "rebirths": int(state.get("rebirths", 0)),
        "power_bonus": round((trophy_power_multiplier(state) - 1) * 100, 1),
        "rebirth_gain": rebirth_reward(state),
        "meta_points": int(state.get("meta_points", 0)),
        "score": current_score,
        "enemy": {
            "id": enemy["id"],
            "name": enemy["name"],
            "asset": enemy.get("asset"),
            "glyph": enemy.get("glyph", "✦"),
            "type": enemy["type"],
            "flavor": enemy.get("flavor", ""),
            "hp": round(enemy["hp"], 2),
            "max_hp": round(enemy["max_hp"], 2),
            "reward": round(enemy["reward"] * gold_multiplier(state), 2),
            "mechanic": enemy.get("mechanic"),
            "mechanic_name": enemy.get("mechanic_name"),
            "hint": enemy.get("hint", ""),
            "timer_left": round(max(0.0, float(enemy.get("timer_end") or 0.0) - time.time()), 1) if enemy.get("timer_end") else None,
        },
        "heroes": hero_cards,
        "active_heroes": build_active_heroes(state),
        "rituals": ritual_cards,
        "ritual_paths": ritual_paths,
        "meta_upgrades": meta_cards,
        "build": build_status(state),
        "skills": skills,
        "achievements": achievements,
        "top": {
            "score": current_score,
            "best_score": max(int(state.get("best_score", 0)), current_score),
            "top_runs": list(state.get("top_runs", [])),
        },
        "respec": {
            "refund": round(respec_refund(state), 2),
            "cooldown_left": round(respec_available_in(state), 1),
        },
        "feedback": feedback,
        "last_boss_message": state.get("last_boss_message", ""),
        "last_hit": last_hit,
        "flash_event": flash_event,
    }


STATE = safe_load_state()


@app.get("/api/state")
def get_state() -> JSONResponse:
    with state_lock:
        flash_event = advance_state(STATE)
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event=flash_event))


@app.post("/api/tap")
def tap_enemy() -> JSONResponse:
    with state_lock:
        flash_event = advance_state(STATE)
        damage = tap_damage(STATE) * enemy_tap_modifier(STATE)
        crit = random.random() < crit_chance(STATE)
        if crit:
            damage *= crit_multiplier(STATE)
        damage = round(damage, 2)
        _, tap_event = apply_damage(STATE, damage)
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, {"damage": damage, "crit": crit}, tap_event or flash_event))


@app.post("/api/skill")
def use_skill(req: SkillRequest) -> JSONResponse:
    with state_lock:
        flash_event = advance_state(STATE)
        if req.id not in SKILLS:
            return JSONResponse({"error": "unknown_skill"}, status_code=400)
        now = time.time()
        skill_state = STATE["skills"][req.id]
        if float(skill_state.get("ready_at", 0.0)) > now:
            return JSONResponse({"error": "skill_cooldown"}, status_code=400)
        skill = SKILLS[req.id]
        skill_state["ready_at"] = now + float(skill["cooldown"])
        event = flash_event
        if req.id == "lightning":
            damage = tap_damage(STATE) * 5 * ritual_path_multiplier(STATE, "burst") * enemy_tap_modifier(STATE)
            crit = random.random() < crit_chance(STATE)
            if crit:
                damage *= crit_multiplier(STATE)
            damage = round(damage, 2)
            _, event = apply_damage(STATE, damage)
            payload = build_payload(STATE, {"damage": damage, "crit": crit, "label": "Молния"}, event)
        else:
            skill_state["active_until"] = now + float(skill["duration"])
            payload = build_payload(STATE, flash_event={"type": "skill", "text": skill["name"]})
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(payload)


@app.post("/api/buy-hero")
def buy_hero(req: BuyRequest) -> JSONResponse:
    with state_lock:
        flash_event = advance_state(STATE)
        if req.id not in STATE["heroes"]:
            return JSONResponse({"error": "unknown_hero"}, status_code=400)
        cost = hero_cost(req.id, hero_level(STATE, req.id))
        if STATE["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        STATE["gold"] -= cost
        STATE["heroes"][req.id] += 1
        STATE["hero_gold_spent"] = float(STATE.get("hero_gold_spent", 0.0)) + cost
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event=flash_event))


@app.post("/api/buy-build-hero")
def buy_build_hero(req: BuildBuyRequest) -> JSONResponse:
    return buy_hero(BuyRequest(id=req.hero_id))


@app.post("/api/buy-ritual")
def buy_ritual(req: BuyRequest) -> JSONResponse:
    with state_lock:
        flash_event = advance_state(STATE)
        if req.id not in STATE["rituals"]:
            return JSONResponse({"error": "unknown_ritual"}, status_code=400)
        cost = ritual_cost(req.id, ritual_level(STATE, req.id))
        if STATE["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        STATE["gold"] -= cost
        STATE["rituals"][req.id] += 1
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event=flash_event))


@app.post("/api/set-ritual-path")
def set_ritual_path(req: PathRequest) -> JSONResponse:
    with state_lock:
        advance_state(STATE)
        if req.id not in RITUAL_PATHS:
            return JSONResponse({"error": "unknown_path"}, status_code=400)
        STATE["ritual_path"] = req.id
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event={"type": "path", "text": RITUAL_PATHS[req.id]["name"]}))


@app.post("/api/meta-upgrade")
def buy_meta_upgrade(req: MetaRequest) -> JSONResponse:
    with state_lock:
        advance_state(STATE)
        if req.id not in META_UPGRADES:
            return JSONResponse({"error": "unknown_meta"}, status_code=400)
        cost = int(META_UPGRADES[req.id]["cost"])
        if int(STATE.get("meta_points", 0)) < cost:
            return JSONResponse({"error": "not_enough_meta"}, status_code=400)
        STATE["meta_points"] -= cost
        STATE["meta_upgrades"][req.id] += 1
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event={"type": "meta", "text": META_UPGRADES[req.id]["name"]}))


@app.post("/api/upgrade-tap")
def upgrade_tap() -> JSONResponse:
    with state_lock:
        flash_event = advance_state(STATE)
        cost = tap_upgrade_cost(STATE)
        if STATE["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        STATE["gold"] -= cost
        STATE["tap_level"] += 1
        update_records(STATE)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event=flash_event))


def apply_preset(state: dict[str, Any], preset: str | None) -> None:
    if not preset or preset not in BUILD_PRESETS:
        return
    left, right = BUILD_PRESETS[preset]
    while True:
        left_cost = hero_cost(left, hero_level(state, left))
        right_cost = hero_cost(right, hero_level(state, right))
        target = left if left_cost <= right_cost else right
        target_cost = left_cost if target == left else right_cost
        if state["gold"] < target_cost:
            break
        state["gold"] -= target_cost
        state["heroes"][target] += 1
        state["hero_gold_spent"] = float(state.get("hero_gold_spent", 0.0)) + target_cost


@app.post("/api/respec")
def respec_build(req: RespecRequest) -> JSONResponse:
    with state_lock:
        advance_state(STATE)
        cooldown_left = respec_available_in(STATE)
        if cooldown_left > 0:
            return JSONResponse({"error": "respec_cooldown"}, status_code=400)
        refund = respec_refund(STATE)
        if refund <= 0:
            return JSONResponse({"error": "respec_empty"}, status_code=400)
        STATE["gold"] += refund
        STATE["heroes"] = {hero["id"]: 0 for hero in HEROES}
        STATE["hero_gold_spent"] = 0.0
        STATE["last_respec_at"] = time.time()
        apply_preset(STATE, req.preset)
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event={"type": "respec", "text": "Билд пересобран"}))


@app.post("/api/rebirth")
def rebirth() -> JSONResponse:
    with state_lock:
        advance_state(STATE)
        reward = rebirth_reward(STATE)
        if reward <= 0:
            return JSONResponse({"error": "rebirth_locked"}, status_code=400)
        achievements = build_achievements(STATE)
        push_top_run(STATE, reward, achievements["unlocked"])
        trophies = int(STATE.get("trophies", 0)) + reward
        rebirths = int(STATE.get("rebirths", 0)) + 1
        meta_points = int(STATE.get("meta_points", 0)) + reward
        best_stage = max(int(STATE.get("best_stage", 1)), int(STATE.get("stage", 1)))
        best_wave = max(int(STATE.get("best_wave", 1)), wave_number(int(STATE.get("stage", 1))))
        best_tap = max(float(STATE.get("best_tap", 1.0)), tap_damage(STATE))
        best_dps = max(float(STATE.get("best_dps", 0.0)), total_hero_dps(STATE))
        best_score = max(int(STATE.get("best_score", 0)), score_value(STATE, achievements["unlocked"]))
        lifetime_gold = float(STATE.get("lifetime_gold", 0.0))
        lifetime_kills = int(STATE.get("lifetime_kills", 0))
        lifetime_boss_kills = int(STATE.get("lifetime_boss_kills", 0))
        top_runs = list(STATE.get("top_runs", []))
        current_meta = dict(STATE.get("meta_upgrades", {}))

        STATE.clear()
        STATE.update(default_state())
        STATE["trophies"] = trophies
        STATE["meta_points"] = meta_points
        STATE["meta_upgrades"].update(current_meta)
        STATE["rebirths"] = rebirths
        STATE["best_stage"] = best_stage
        STATE["best_wave"] = best_wave
        STATE["best_tap"] = best_tap
        STATE["best_dps"] = best_dps
        STATE["best_score"] = best_score
        STATE["lifetime_gold"] = lifetime_gold
        STATE["lifetime_kills"] = lifetime_kills
        STATE["lifetime_boss_kills"] = lifetime_boss_kills
        STATE["top_runs"] = top_runs
        save_state(STATE)
        return JSONResponse(build_payload(STATE, flash_event={"type": "rebirth", "text": "Степь приняла новый забег"}))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app.js")
def app_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/style.css")
def style_css() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "style.css", media_type="text/css")
