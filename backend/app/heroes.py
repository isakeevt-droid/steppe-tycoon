from __future__ import annotations

import math
from typing import Any

from .content import BREAKPOINTS, HEROES, HERO_MILESTONES, HERO_UNLOCK_COST, HOLD_MAX_MS, HOLD_MIN_MS, RITUALS

def hero_level(state: dict[str, Any], hero_id: str) -> int:
    return int(state["heroes"].get(hero_id, 0))


def ritual_level(state: dict[str, Any], ritual_id: str) -> int:
    return int(state["rituals"].get(ritual_id, 0))


def hero_cost(hero_id: str, level: int) -> float:
    hero = next(item for item in HEROES if item["id"] == hero_id)
    if level <= 0:
        return float(HERO_UNLOCK_COST)
    return hero["base_cost"] * (float(hero.get("growth", 1.16)) ** max(0, level - 1))


def ritual_cost(ritual_id: str, level: int) -> float:
    ritual = next(item for item in RITUALS if item["id"] == ritual_id)
    return ritual["base_cost"] * (ritual["cost_mult"] ** level)


def trophy_power_multiplier(state: dict[str, Any]) -> float:
    return 1 + int(state.get("trophies", 0)) * 0.12


def hero_breakpoint_count(level: int) -> int:
    return hero_milestone_bonus_count(level)


def next_breakpoint(level: int) -> int | None:
    for point in BREAKPOINTS:
        if level < point:
            return point
    return None


def milestone_unlocked(level: int, point: int) -> bool:
    return level >= point


def hero_milestone_bonus_count(level: int) -> int:
    return sum(1 for point in BREAKPOINTS if level >= point)


def hero_milestone_cards(hero_id: str, level: int) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for point in BREAKPOINTS:
        cards.append(
            {
                "point": point,
                "label": HERO_MILESTONES[hero_id][point],
                "unlocked": milestone_unlocked(level, point),
            }
        )
    return cards


def hero_personal_dps(hero_id: str, level: int) -> float:
    if level <= 0:
        return 0.0
    hero = next(item for item in HEROES if item["id"] == hero_id)
    dps = hero["base_dps"] * level * (hero["growth"] ** max(0, level - 1))
    dps *= 2 ** hero_milestone_bonus_count(level)
    return dps


def active_hero_ids(state: dict[str, Any]) -> list[str]:
    active = state.get("active_heroes", [])
    if not isinstance(active, list):
        return []
    valid_ids = {hero["id"] for hero in HEROES}
    return [hero_id for hero_id in active if hero_id in valid_ids]


def is_hero_active(state: dict[str, Any], hero_id: str) -> bool:
    return hero_id in active_hero_ids(state)


def air_aura_multiplier(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "air"):
        return 1.0
    level = hero_level(state, "air")
    if level <= 0:
        return 1.0
    return 1.0 + level * 0.015 + hero_breakpoint_count(level) * 0.15


def fire_tap_bonus(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "fire"):
        return 0.0
    level = hero_level(state, "fire")
    return level * 0.03 + hero_breakpoint_count(level) * 0.20


def water_gold_bonus(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "water"):
        return 0.0
    level = hero_level(state, "water")
    return level * 0.02 + hero_breakpoint_count(level) * 0.10


def earth_boss_bonus(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "earth"):
        return 0.0
    level = hero_level(state, "earth")
    return level * 0.03 + hero_breakpoint_count(level) * 0.35


def earth_crit_bonus(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "earth"):
        return 0.0
    level = hero_level(state, "earth")
    return level * 0.002 + hero_breakpoint_count(level) * 0.01


def fire_bonus_crit_chance(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "fire"):
        return 0.0
    level = hero_level(state, "fire")
    return 0.015 * hero_breakpoint_count(level) + level * 0.001


def fire_bonus_crit_multiplier(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "fire"):
        return 0.0
    level = hero_level(state, "fire")
    return level * 0.01 + hero_breakpoint_count(level) * 0.12


def earth_armor_break_multiplier(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "earth"):
        return 1.0
    level = hero_level(state, "earth")
    return 1.0 + level * 0.02 + hero_breakpoint_count(level) * 0.22


def water_hold_multiplier(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "water"):
        return 1.0
    level = hero_level(state, "water")
    return 1.0 + level * 0.03 + hero_breakpoint_count(level) * 0.24


def total_hero_dps(state: dict[str, Any]) -> float:
    from .enemies import damage_after_enemy_mechanics

    total = sum(hero_personal_dps(hero["id"], hero_level(state, hero["id"])) for hero in HEROES if is_hero_active(state, hero["id"]))
    total *= air_aura_multiplier(state)
    total *= 1 + 0.25 * ritual_level(state, "storm")
    total *= trophy_power_multiplier(state)
    if state["enemy"].get("type") in {"boss", "elite"}:
        total *= 1 + earth_boss_bonus(state)
    preview_damage, info = damage_after_enemy_mechanics(state, total, "dps", consume=False)
    if info.get("blocked"):
        return 0.0
    return preview_damage


def base_tap_damage(state: dict[str, Any]) -> float:
    embers = ritual_level(state, "embers")
    base = 1.0 + (state["tap_level"] - 1) * 1.4
    base *= 1 + fire_tap_bonus(state)
    base *= 1 + embers * 0.25
    base *= trophy_power_multiplier(state)
    if state["enemy"].get("type") in {"boss", "elite"}:
        base *= 1 + earth_boss_bonus(state) * 0.5
    return round(base, 2)


def crit_chance(state: dict[str, Any]) -> float:
    if state["enemy"].get("type") == "boss" and state["enemy"].get("mechanic") == "anti_crit":
        return 0.0
    chance = 0.05 + earth_crit_bonus(state) + fire_bonus_crit_chance(state) + ritual_level(state, "stone") * 0.02
    return min(chance, 0.65)


def crit_multiplier(state: dict[str, Any]) -> float:
    earth = hero_level(state, "earth") if is_hero_active(state, "earth") else 0
    return 2.0 + earth * 0.02 + fire_bonus_crit_multiplier(state) + int(state.get("trophies", 0)) * 0.01


def tap_damage(state: dict[str, Any]) -> float:
    from .enemies import damage_after_enemy_mechanics

    base = base_tap_damage(state)
    preview_damage, info = damage_after_enemy_mechanics(state, base, "tap", consume=False, source_meta={"pair_key": active_pair_key(state)})
    if info.get("blocked"):
        return 0.0
    return preview_damage


def gold_multiplier(state: dict[str, Any]) -> float:
    tide = ritual_level(state, "tide")
    return 1 + water_gold_bonus(state) + tide * 0.20 + int(state.get("trophies", 0)) * 0.015

def fmt_stat(value: float) -> str:
    value = float(value)
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    if value >= 100:
        return str(int(round(value)))
    return f"{value:.1f}"


def hero_passive_text(state: dict[str, Any], hero_id: str) -> str:
    from .player import player_defense_value, player_heal_power_value, player_max_shield_value, player_regen_value

    level = hero_level(state, hero_id)
    milestone_count = hero_breakpoint_count(level)
    if hero_id == "fire":
        return f"Крит шанс +{round(fire_bonus_crit_chance(state) * 100, 1)}%, сила крита +{round((crit_multiplier(state) - 2.0) * 100, 1)}%"
    if hero_id == "water":
        return f"Hold x{round(water_hold_multiplier(state), 2)}, хил +{round((player_heal_power_value(state) - 1) * 100, 1)}%, реген {fmt_stat(player_regen_value(state))}/с"
    if hero_id == "earth":
        return f"Ломает щиты x{round(earth_armor_break_multiplier(state), 2)}, защита +{round(player_defense_value(state) * 100, 1)}%, щит {fmt_stat(player_max_shield_value(state))}"
    if hero_id == "air":
        return f"Свайпы и пачка бустятся на {round((air_aura_multiplier(state) - 1) * 100, 1)}%, порогов {milestone_count}"
    return f"Уровень {level}"


def hero_next_bonus_text(hero_id: str, level: int) -> str:
    nxt = next_breakpoint(level)
    if nxt is None:
        return "Все milestones открыты: шаман уже в эндгейме."
    return f"Следующий milestone: {nxt} лвл → {HERO_MILESTONES[hero_id][nxt]}"


def active_pair_key(state: dict[str, Any]) -> str:
    active = set(active_hero_ids(state))
    pair_map = {
        frozenset({"fire", "air"}): "fire_air",
        frozenset({"fire", "water"}): "fire_water",
        frozenset({"fire", "earth"}): "fire_earth",
        frozenset({"air", "water"}): "air_water",
        frozenset({"air", "earth"}): "air_earth",
        frozenset({"water", "earth"}): "water_earth",
    }
    return pair_map.get(frozenset(active), "solo")


def pair_has_earth(pair_key: str) -> bool:
    return pair_key in {"fire_earth", "air_earth", "water_earth"}

def build_active_heroes(state: dict[str, Any]) -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    active_ids = active_hero_ids(state)
    hero_map = {hero["id"]: hero for hero in HEROES}
    for slot_index in range(2):
        hero_id = active_ids[slot_index] if slot_index < len(active_ids) else None
        if not hero_id:
            active.append({"slot": slot_index + 1, "empty": True})
            continue
        hero = hero_map[hero_id]
        level = hero_level(state, hero_id)
        active.append(
            {
                "slot": slot_index + 1,
                "empty": False,
                "id": hero_id,
                "name": hero["name"],
                "title": hero["title"],
                "asset": hero["asset"],
                "level": level,
                "dps": round(hero_personal_dps(hero_id, level), 2),
                "passive": hero_passive_text(state, hero_id),
            }
        )
    return active

