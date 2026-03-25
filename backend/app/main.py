from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import random
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
DB_PATH = ROOT_DIR / "backend" / "players.db"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

app = FastAPI(title="Steppe Shaman")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
state_lock = threading.Lock()

ENEMIES = [
    {
        "id": "wolf",
        "name": "Лютый Волчара",
        "glyph": "/assets/icons/wolf.svg",
        "base_hp": 16,
        "reward_mult": 1.0,
        "flavor": "Шныряет по степи и лезет под руку.",
    },
    {
        "id": "raven",
        "name": "Чёрный Каркун",
        "glyph": "/assets/icons/raven.svg",
        "base_hp": 14,
        "reward_mult": 1.05,
        "flavor": "Каркает сверху, как будто беду заспавнил.",
    },
    {
        "id": "spirit",
        "name": "Шальной Дух",
        "glyph": "/assets/icons/spirit.svg",
        "base_hp": 18,
        "reward_mult": 1.12,
        "flavor": "Сквозняком залетел и решил качать права.",
    },
    {
        "id": "totem",
        "name": "Дикий Тотем",
        "glyph": "/assets/icons/totem.svg",
        "base_hp": 20,
        "reward_mult": 1.18,
        "flavor": "Старый идол, но вайб у него злой до мурашек.",
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
        "name": "Волк Затмения",
        "asset": "/assets/bosses/boss_wolf.png",
        "hp_mult": 12.0,
        "reward_mult": 10.0,
        "flavor": "Ночной хозяин степи. Если вышел — будет мясо.",
    },
    {
        "id": "boss_idol",
        "name": "Громовой Идол",
        "asset": "/assets/bosses/boss_idol.png",
        "hp_mult": 13.5,
        "reward_mult": 11.5,
        "flavor": "Каменная махина, заряженная молнией по полной.",
    },
    {
        "id": "boss_guard",
        "name": "Страж Кургана",
        "asset": "/assets/bosses/boss_guard.png",
        "hp_mult": 15.0,
        "reward_mult": 13.0,
        "flavor": "Поднялся с кургана и явно не рад гостям.",
    },
    {
        "id": "boss_khan",
        "name": "Костяной Хан",
        "asset": "/assets/bosses/boss_khan.png",
        "hp_mult": 16.5,
        "reward_mult": 14.5,
        "flavor": "Старый хан вернулся и хочет забрать весь лут.",
    },
    {
        "id": "boss_wind",
        "name": "Владычица Ветра",
        "asset": "/assets/bosses/boss_wind.png",
        "hp_mult": 18.0,
        "reward_mult": 16.0,
        "flavor": "С её бурей даже бывалые шаманы приседают.",
    },
    {
        "id": "boss_void",
        "name": "Тень Разлома",
        "asset": "/assets/bosses/boss_void.png",
        "hp_mult": 20.0,
        "reward_mult": 18.0,
        "flavor": "Чистая пустотная жуть, тут без прокаста никак.",
    },
]

HEROES = [
    {
        "id": "fire",
        "name": "Шаман Огня",
        "title": "раздаёт стартовый жар",
        "asset": "/assets/heroes/hero_fire.png",
        "base_cost": 25,
        "base_dps": 4.0,
        "desc": "Разгоняет тап и сам жарит врага, пока степь только просыпается.",
        "growth": 1.18,
    },
    {
        "id": "water",
        "name": "Шаман Воды",
        "title": "фармит и не душнит",
        "asset": "/assets/heroes/hero_water.png",
        "base_cost": 80,
        "base_dps": 8.0,
        "desc": "Льёт ровный урон и подтягивает больше золота в котёл.",
        "growth": 1.18,
    },
    {
        "id": "earth",
        "name": "Шаман Земли",
        "title": "ломает жирных",
        "asset": "/assets/heroes/hero_earth.png",
        "base_cost": 250,
        "base_dps": 16.0,
        "desc": "Когда выходит жирный моб, этот шаман включается по-взрослому.",
        "growth": 1.17,
    },
    {
        "id": "air",
        "name": "Шаман Воздуха",
        "title": "разгоняет всю пачку",
        "asset": "/assets/heroes/hero_air.png",
        "base_cost": 700,
        "base_dps": 12.0,
        "desc": "Поддувает всей пачке, и общий DPS летит вверх как степной ветер.",
        "growth": 1.16,
    },
]

RITUALS = [
    {
        "id": "embers",
        "name": "Ритуал Углей",
        "base_cost": 120,
        "cost_mult": 1.8,
        "desc": "+25% к силе тапа за уровень. Рука станет тяжелее.",
    },
    {
        "id": "tide",
        "name": "Ритуал Прилива",
        "base_cost": 180,
        "cost_mult": 1.85,
        "desc": "+20% к золоту за уровень. Лут капает жирнее.",
    },
    {
        "id": "stone",
        "name": "Ритуал Камня",
        "base_cost": 260,
        "cost_mult": 1.9,
        "desc": "+2% к шансу крита за уровень. Проков будет больше.",
    },
    {
        "id": "storm",
        "name": "Ритуал Бури",
        "base_cost": 420,
        "cost_mult": 1.92,
        "desc": "+25% к DPS за уровень. Вся стая бьёт жёстче.",
    },
]

BREAKPOINTS = (10, 25, 50, 100)


class BuyRequest(BaseModel):
    id: str


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
        "enemy": {},
    }
    state["enemy"] = generate_enemy(state["stage"])
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
            if key in {"enemy", "heroes", "rituals"}:
                continue
            state[key] = data.get(key, state[key])
        state["heroes"].update(data.get("heroes", {}))
        state["rituals"].update(data.get("rituals", {}))
        enemy = data.get("enemy") or generate_enemy(int(state["stage"]))
        if "hp" not in enemy or "max_hp" not in enemy:
            enemy = generate_enemy(int(state["stage"]))
        state["enemy"] = enemy
        state["last_tick"] = float(data.get("last_tick", time.time()))
        if not isinstance(state.get("top_runs"), list):
            state["top_runs"] = []
        return state
    except Exception:
        state = default_state()
        save_state(state)
        return state


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
    return {
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


def hero_level(state: dict[str, Any], hero_id: str) -> int:
    return int(state["heroes"].get(hero_id, 0))


def ritual_level(state: dict[str, Any], ritual_id: str) -> int:
    return int(state["rituals"].get(ritual_id, 0))


def hero_cost(hero_id: str, level: int) -> float:
    hero = next(item for item in HEROES if item["id"] == hero_id)
    return hero["base_cost"] * (1.16 ** level)


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


def hero_personal_dps(hero_id: str, level: int) -> float:
    if level <= 0:
        return 0.0
    hero = next(item for item in HEROES if item["id"] == hero_id)
    dps = hero["base_dps"] * level * (hero["growth"] ** max(0, level - 1))
    dps *= 2 ** hero_breakpoint_count(level)
    return dps


def air_aura_multiplier(state: dict[str, Any]) -> float:
    level = hero_level(state, "air")
    if level <= 0:
        return 1.0
    return 1.0 + level * 0.015 + hero_breakpoint_count(level) * 0.15


def fire_tap_bonus(state: dict[str, Any]) -> float:
    level = hero_level(state, "fire")
    return level * 0.03 + hero_breakpoint_count(level) * 0.20


def water_gold_bonus(state: dict[str, Any]) -> float:
    level = hero_level(state, "water")
    return level * 0.02 + hero_breakpoint_count(level) * 0.10


def earth_boss_bonus(state: dict[str, Any]) -> float:
    level = hero_level(state, "earth")
    return level * 0.03 + hero_breakpoint_count(level) * 0.35


def earth_crit_bonus(state: dict[str, Any]) -> float:
    level = hero_level(state, "earth")
    return level * 0.002 + hero_breakpoint_count(level) * 0.01


def total_hero_dps(state: dict[str, Any]) -> float:
    total = sum(hero_personal_dps(hero["id"], hero_level(state, hero["id"])) for hero in HEROES)
    total *= air_aura_multiplier(state)
    total *= 1 + 0.25 * ritual_level(state, "storm")
    total *= trophy_power_multiplier(state)
    if state["enemy"].get("type") in {"boss", "elite"}:
        total *= 1 + earth_boss_bonus(state)
    return total


def crit_chance(state: dict[str, Any]) -> float:
    chance = 0.05 + earth_crit_bonus(state) + ritual_level(state, "stone") * 0.02
    return min(chance, 0.65)


def crit_multiplier(state: dict[str, Any]) -> float:
    earth = hero_level(state, "earth")
    return 2.0 + earth * 0.02 + int(state.get("trophies", 0)) * 0.01


def tap_damage(state: dict[str, Any]) -> float:
    embers = ritual_level(state, "embers")
    base = 1.0 + (state["tap_level"] - 1) * 1.4
    base *= 1 + fire_tap_bonus(state)
    base *= 1 + embers * 0.25
    base *= trophy_power_multiplier(state)
    if state["enemy"].get("type") in {"boss", "elite"}:
        base *= 1 + earth_boss_bonus(state) * 0.5
    return base


def gold_multiplier(state: dict[str, Any]) -> float:
    tide = ritual_level(state, "tide")
    return 1 + water_gold_bonus(state) + tide * 0.20 + int(state.get("trophies", 0)) * 0.015


def wave_number(stage: int) -> int:
    return math.ceil(stage / 10)


def award_gold(state: dict[str, Any], amount: float) -> None:
    state["gold"] += amount
    state["lifetime_gold"] = float(state.get("lifetime_gold", 0.0)) + amount


def achievement_catalog() -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    entries = [
        ("Разносы", "kills", [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000], "Разнеси {value} врагов за всё время."),
        ("Боссы", "boss_kills", [1, 3, 5, 10, 15, 25, 40, 60, 80, 120, 160, 220], "Урони {value} боссов за всё время."),
        ("Этап", "stage", [5, 10, 15, 20, 30, 40, 50, 75, 100, 125, 150, 200], "Долети до этапа {value}."),
        ("Трофеи", "trophies", [1, 3, 5, 10, 15, 20, 30, 45, 60, 80, 100, 140], "Подними {value} трофеев с перерождений."),
        ("Перероды", "rebirths", [1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 50, 75], "Сделай {value} перерождений."),
        ("Золото", "gold", [100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1_000_000, 5_000_000, 10_000_000, 50_000_000], "Подними {value} золота за всё время."),
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
    score = (
        int(state.get("best_stage", 1)) * 25
        + int(state.get("trophies", 0)) * 1000
        + int(state.get("lifetime_boss_kills", 0)) * 100
        + unlocked * 50
    )
    return int(score)


def update_records(state: dict[str, Any]) -> None:
    stage = int(state["stage"])
    state["best_stage"] = max(int(state.get("best_stage", 1)), stage)
    state["best_wave"] = max(int(state.get("best_wave", 1)), wave_number(stage))
    state["best_tap"] = max(float(state.get("best_tap", 1.0)), tap_damage(state))
    state["best_dps"] = max(float(state.get("best_dps", 0.0)), total_hero_dps(state))
    state["best_score"] = max(int(state.get("best_score", 0)), score_value(state))


def resolve_enemy_death(state: dict[str, Any]) -> None:
    reward = state["enemy"]["reward"] * gold_multiplier(state)
    award_gold(state, reward)
    state["kills"] += 1
    state["lifetime_kills"] = int(state.get("lifetime_kills", 0)) + 1
    if state["enemy"]["type"] == "boss":
        state["boss_kills"] += 1
        state["lifetime_boss_kills"] = int(state.get("lifetime_boss_kills", 0)) + 1
    state["stage"] += 1
    state["enemy"] = generate_enemy(int(state["stage"]))
    update_records(state)


def apply_damage(state: dict[str, Any], damage: float) -> int:
    kills = 0
    remaining = damage
    while remaining > 0:
        hp = state["enemy"]["hp"]
        if remaining >= hp:
            remaining -= hp
            kills += 1
            resolve_enemy_death(state)
        else:
            state["enemy"]["hp"] = round(max(0.0, hp - remaining), 2)
            break
        if kills > 200:
            break
    return kills


def advance_state(state: dict[str, Any]) -> None:
    now = time.time()
    elapsed = max(0.0, now - float(state.get("last_tick", now)))
    state["last_tick"] = now
    dps = total_hero_dps(state)
    if elapsed <= 0 or dps <= 0:
        return
    apply_damage(state, dps * elapsed)


def tap_upgrade_cost(state: dict[str, Any]) -> float:
    return 12 * (1.33 ** max(0, state["tap_level"] - 1))


def rebirth_reward(state: dict[str, Any]) -> int:
    stage = int(state.get("stage", 1))
    bosses = int(state.get("boss_kills", 0))
    return max(0, (stage - 1) // 10 + bosses)


def hero_passive_text(state: dict[str, Any], hero_id: str) -> str:
    level = hero_level(state, hero_id)
    if hero_id == "fire":
        return f"Тап жарит на +{round(fire_tap_bonus(state) * 100, 1)}%"
    if hero_id == "water":
        return f"Лута сверху +{round(water_gold_bonus(state) * 100, 1)}%"
    if hero_id == "earth":
        return f"По жирным целям +{round(earth_boss_bonus(state) * 100, 1)}%"
    if hero_id == "air":
        return f"Пачка бустится на +{round((air_aura_multiplier(state) - 1) * 100, 1)}%"
    return f"Уровень {level}"


def hero_next_bonus_text(hero_id: str, level: int) -> str:
    nxt = next_breakpoint(level)
    if nxt is None:
        return "Все жирные пороги уже забраны"
    bonus = {
        "fire": "x2 к личному DPS и тап лупит больнее",
        "water": "x2 к личному DPS и лута сыпет жирнее",
        "earth": "x2 к личному DPS и жирных ломает крепче",
        "air": "x2 к личному DPS и пачку разгоняет жёстче",
    }[hero_id]
    return f"Следующий порог: {nxt} лвл → {bonus}"


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



class PlayerIdentity(BaseModel):
    player_id: str
    display_name: str
    username: str | None = None
    is_telegram: bool = False


def db_connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                username TEXT,
                is_telegram INTEGER NOT NULL DEFAULT 0,
                state_json TEXT NOT NULL,
                best_score INTEGER NOT NULL DEFAULT 0,
                best_stage INTEGER NOT NULL DEFAULT 1,
                trophies INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def verify_telegram_init_data(init_data: str) -> dict[str, Any] | None:
    if not init_data or not BOT_TOKEN:
        return None
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = pairs.pop("hash", "")
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
        calculated = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return None
        user_raw = pairs.get("user")
        if not user_raw:
            return None
        return json.loads(user_raw)
    except Exception:
        return None


def sanitize_identity(raw_user: dict[str, Any] | None, guest_id: str | None) -> PlayerIdentity:
    if raw_user and raw_user.get("id") is not None:
        first = str(raw_user.get("first_name", "") or "").strip()
        last = str(raw_user.get("last_name", "") or "").strip()
        username = str(raw_user.get("username", "") or "").strip() or None
        display_name = " ".join(part for part in [first, last] if part).strip() or username or f"Игрок {raw_user['id']}"
        return PlayerIdentity(
            player_id=f"tg:{raw_user['id']}",
            display_name=display_name[:64],
            username=username,
            is_telegram=True,
        )
    fallback = (guest_id or "guest-local").strip()[:64] or "guest-local"
    return PlayerIdentity(player_id=f"guest:{fallback}", display_name="Гость степи", username=None, is_telegram=False)


def get_identity(request: Request) -> PlayerIdentity:
    verified_user = verify_telegram_init_data(request.headers.get("X-Telegram-Init-Data", ""))
    if verified_user:
        return sanitize_identity(verified_user, None)
    raw_header = request.headers.get("X-Telegram-User", "")
    raw_user = None
    if raw_header:
        try:
            raw_user = json.loads(raw_header)
        except Exception:
            raw_user = None
    guest_id = request.headers.get("X-Player-Id") or request.query_params.get("player_id")
    return sanitize_identity(raw_user, guest_id)


def load_player_row(player_id: str) -> sqlite3.Row | None:
    with db_connect() as conn:
        return conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()


def load_player_state(identity: PlayerIdentity) -> dict[str, Any]:
    row = load_player_row(identity.player_id)
    if row is None:
        state = default_state()
        save_player_state(identity, state)
        return state
    try:
        data = json.loads(row["state_json"])
        state = default_state()
        for key in state.keys():
            if key in {"enemy", "heroes", "rituals"}:
                continue
            state[key] = data.get(key, state[key])
        state["heroes"].update(data.get("heroes", {}))
        state["rituals"].update(data.get("rituals", {}))
        enemy = data.get("enemy") or generate_enemy(int(state["stage"]))
        if "hp" not in enemy or "max_hp" not in enemy:
            enemy = generate_enemy(int(state["stage"]))
        state["enemy"] = enemy
        state["last_tick"] = float(data.get("last_tick", time.time()))
        if not isinstance(state.get("top_runs"), list):
            state["top_runs"] = []
        return state
    except Exception:
        state = default_state()
        save_player_state(identity, state)
        return state


def save_player_state(identity: PlayerIdentity, state: dict[str, Any]) -> None:
    update_records(state)
    payload = json.dumps(state, ensure_ascii=False)
    now = int(time.time())
    with db_connect() as conn:
        conn.execute(
            """
            INSERT INTO players (player_id, display_name, username, is_telegram, state_json, best_score, best_stage, trophies, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET
                display_name=excluded.display_name,
                username=excluded.username,
                is_telegram=excluded.is_telegram,
                state_json=excluded.state_json,
                best_score=excluded.best_score,
                best_stage=excluded.best_stage,
                trophies=excluded.trophies,
                updated_at=excluded.updated_at
            """,
            (
                identity.player_id,
                identity.display_name,
                identity.username,
                1 if identity.is_telegram else 0,
                payload,
                int(state.get("best_score", 0)),
                int(state.get("best_stage", 1)),
                int(state.get("trophies", 0)),
                now,
            ),
        )
        conn.commit()


def better_players_count(conn: sqlite3.Connection, *, score: int, stage: int, trophies: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM players
        WHERE (best_score > ?)
           OR (best_score = ? AND best_stage > ?)
           OR (best_score = ? AND best_stage = ? AND trophies > ?)
        """,
        (score, score, stage, score, stage, trophies),
    ).fetchone()
    return int(row["c"] if row else 0)


def fetch_leaderboard(player_id: str, limit: int = 20) -> dict[str, Any]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT player_id, display_name, username, best_score, best_stage, trophies
            FROM players
            ORDER BY best_score DESC, best_stage DESC, trophies DESC, updated_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        me = conn.execute(
            "SELECT player_id, display_name, username, best_score, best_stage, trophies FROM players WHERE player_id = ?",
            (player_id,),
        ).fetchone()
        rank = None
        if me is not None:
            rank = better_players_count(
                conn,
                score=int(me["best_score"]),
                stage=int(me["best_stage"]),
                trophies=int(me["trophies"]),
            ) + 1

    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        items.append(
            {
                "rank": index,
                "player_id": row["player_id"],
                "name": row["display_name"],
                "username": row["username"],
                "best_score": int(row["best_score"]),
                "best_stage": int(row["best_stage"]),
                "trophies": int(row["trophies"]),
                "is_me": row["player_id"] == player_id,
            }
        )
    return {"items": items, "rank": rank}


def build_payload(state: dict[str, Any], identity: PlayerIdentity, last_hit: dict[str, Any] | None = None) -> dict[str, Any]:
    enemy = state["enemy"]
    achievements = build_achievements(state)
    current_score = score_value(state, achievements["unlocked"])
    leaderboard = fetch_leaderboard(identity.player_id)

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
                "desc": hero["desc"],
                "level": level,
                "cost": round(cost, 2),
                "dps": round(dps_value, 2),
                "breakpoints": hero_breakpoint_count(level),
                "passive": hero_passive_text(state, hero["id"]),
                "next_bonus": hero_next_bonus_text(hero["id"], level),
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

    return {
        "player": {
            "id": identity.player_id,
            "name": identity.display_name,
            "username": identity.username,
            "is_telegram": identity.is_telegram,
        },
        "gold": round(state["gold"], 2),
        "stage": int(state["stage"]),
        "wave": wave_number(int(state["stage"])),
        "kills": int(state["kills"]),
        "boss_kills": int(state["boss_kills"]),
        "tap_level": int(state["tap_level"]),
        "tap_cost": round(tap_upgrade_cost(state), 2),
        "tap_damage": round(tap_damage(state), 2),
        "dps": round(total_hero_dps(state), 2),
        "crit_chance": round(crit_chance(state) * 100, 1),
        "crit_multiplier": round(crit_multiplier(state), 2),
        "gold_bonus": round((gold_multiplier(state) - 1) * 100, 1),
        "trophies": int(state.get("trophies", 0)),
        "rebirths": int(state.get("rebirths", 0)),
        "power_bonus": round((trophy_power_multiplier(state) - 1) * 100, 1),
        "rebirth_gain": rebirth_reward(state),
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
        },
        "heroes": hero_cards,
        "active_heroes": build_active_heroes(state),
        "rituals": ritual_cards,
        "achievements": achievements,
        "top": {
            "score": current_score,
            "best_score": max(int(state.get("best_score", 0)), current_score),
            "top_runs": list(state.get("top_runs", [])),
            "leaderboard": leaderboard["items"],
            "my_rank": leaderboard["rank"],
        },
        "last_hit": last_hit,
    }


def with_player_state(request: Request) -> tuple[PlayerIdentity, dict[str, Any]]:
    identity = get_identity(request)
    state = load_player_state(identity)
    return identity, state


@app.get("/api/state")
def get_state(request: Request) -> JSONResponse:
    with state_lock:
        identity, state = with_player_state(request)
        advance_state(state)
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.get("/api/leaderboard")
def get_leaderboard(request: Request) -> JSONResponse:
    identity = get_identity(request)
    return JSONResponse(fetch_leaderboard(identity.player_id))


@app.post("/api/tap")
def tap_enemy(request: Request) -> JSONResponse:
    with state_lock:
        identity, state = with_player_state(request)
        advance_state(state)
        damage = tap_damage(state)
        crit = random.random() < crit_chance(state)
        if crit:
            damage *= crit_multiplier(state)
        damage = round(damage, 2)
        apply_damage(state, damage)
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity, {"damage": damage, "crit": crit}))


@app.post("/api/buy-hero")
def buy_hero(request: Request, req: BuyRequest) -> JSONResponse:
    with state_lock:
        identity, state = with_player_state(request)
        advance_state(state)
        if req.id not in state["heroes"]:
            return JSONResponse({"error": "unknown_hero"}, status_code=400)
        cost = hero_cost(req.id, hero_level(state, req.id))
        if state["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        state["gold"] -= cost
        state["heroes"][req.id] += 1
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.post("/api/buy-ritual")
def buy_ritual(request: Request, req: BuyRequest) -> JSONResponse:
    with state_lock:
        identity, state = with_player_state(request)
        advance_state(state)
        if req.id not in state["rituals"]:
            return JSONResponse({"error": "unknown_ritual"}, status_code=400)
        cost = ritual_cost(req.id, ritual_level(state, req.id))
        if state["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        state["gold"] -= cost
        state["rituals"][req.id] += 1
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.post("/api/upgrade-tap")
def upgrade_tap(request: Request) -> JSONResponse:
    with state_lock:
        identity, state = with_player_state(request)
        advance_state(state)
        cost = tap_upgrade_cost(state)
        if state["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        state["gold"] -= cost
        state["tap_level"] += 1
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.post("/api/rebirth")
def rebirth(request: Request) -> JSONResponse:
    with state_lock:
        identity, state = with_player_state(request)
        advance_state(state)
        reward = rebirth_reward(state)
        if reward <= 0:
            return JSONResponse({"error": "rebirth_locked"}, status_code=400)
        achievements = build_achievements(state)
        push_top_run(state, reward, achievements["unlocked"])
        trophies = int(state.get("trophies", 0)) + reward
        rebirths = int(state.get("rebirths", 0)) + 1
        best_stage = max(int(state.get("best_stage", 1)), int(state.get("stage", 1)))
        best_wave = max(int(state.get("best_wave", 1)), wave_number(int(state.get("stage", 1))))
        best_tap = max(float(state.get("best_tap", 1.0)), tap_damage(state))
        best_dps = max(float(state.get("best_dps", 0.0)), total_hero_dps(state))
        best_score = max(int(state.get("best_score", 0)), score_value(state, achievements["unlocked"]))
        lifetime_gold = float(state.get("lifetime_gold", 0.0))
        lifetime_kills = int(state.get("lifetime_kills", 0))
        lifetime_boss_kills = int(state.get("lifetime_boss_kills", 0))
        top_runs = list(state.get("top_runs", []))

        state = default_state()
        state["trophies"] = trophies
        state["rebirths"] = rebirths
        state["best_stage"] = best_stage
        state["best_wave"] = best_wave
        state["best_tap"] = best_tap
        state["best_dps"] = best_dps
        state["best_score"] = best_score
        state["lifetime_gold"] = lifetime_gold
        state["lifetime_kills"] = lifetime_kills
        state["lifetime_boss_kills"] = lifetime_boss_kills
        state["top_runs"] = top_runs

        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True})


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app.js")
def app_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/style.css")
def style_css() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "style.css", media_type="text/css")


init_db()
