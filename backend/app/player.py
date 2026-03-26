from __future__ import annotations

import time
from typing import Any

from .enemies import boss_shadow_active, generate_enemy
from .heroes import hero_level, is_hero_active, pair_has_earth, trophy_power_multiplier

def player_max_hp_value(state: dict[str, Any]) -> float:
    base = 130.0 + max(0, int(state.get("stage", 1)) - 1) * 14.0
    base += max(0, int(state.get("tap_level", 1)) - 1) * 9.0
    base *= 1 + int(state.get("rebirths", 0)) * 0.12 + int(state.get("trophies", 0)) * 0.025
    if is_hero_active(state, "water"):
        level = hero_level(state, "water")
        base *= 1 + level * 0.01 + hero_breakpoint_count(level) * 0.06
    if is_hero_active(state, "earth"):
        level = hero_level(state, "earth")
        base *= 1 + level * 0.012 + hero_breakpoint_count(level) * 0.08
    return round(base, 2)


def player_defense_value(state: dict[str, Any]) -> float:
    defense = 0.05 + int(state.get("rebirths", 0)) * 0.01 + int(state.get("trophies", 0)) * 0.002
    if is_hero_active(state, "earth"):
        level = hero_level(state, "earth")
        defense += level * 0.006 + hero_breakpoint_count(level) * 0.03
    return round(min(defense, 0.72), 4)


def player_regen_value(state: dict[str, Any]) -> float:
    regen = player_max_hp_value(state) * 0.01 + int(state.get("rebirths", 0)) * 0.8
    if is_hero_active(state, "water"):
        level = hero_level(state, "water")
        regen += 2.2 + level * 0.9 + hero_breakpoint_count(level) * 5.5
    return round(regen, 2)


def player_heal_power_value(state: dict[str, Any]) -> float:
    heal = 1.0
    if is_hero_active(state, "water"):
        level = hero_level(state, "water")
        heal += level * 0.03 + hero_breakpoint_count(level) * 0.18
    return round(heal, 2)


def player_max_shield_value(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "earth"):
        return 0.0
    level = hero_level(state, "earth")
    base = player_max_hp_value(state) * 0.18
    base += level * 16.0 + hero_breakpoint_count(level) * 32.0
    return round(base, 2)


def player_shield_regen_value(state: dict[str, Any]) -> float:
    if not is_hero_active(state, "earth"):
        return 0.0
    level = hero_level(state, "earth")
    return round(1.5 + level * 0.45 + hero_breakpoint_count(level) * 2.6, 2)


def sync_player_combat_stats(state: dict[str, Any], refill: bool = False) -> None:
    prev_max_hp = float(state.get("player_max_hp", 0.0) or 0.0)
    prev_max_shield = float(state.get("player_max_shield", 0.0) or 0.0)
    max_hp = player_max_hp_value(state)
    max_shield = player_max_shield_value(state)
    state["player_max_hp"] = max_hp
    state["player_defense"] = player_defense_value(state)
    state["player_regen"] = player_regen_value(state)
    state["player_heal_power"] = player_heal_power_value(state)
    state["player_max_shield"] = max_shield
    state["player_shield_regen"] = player_shield_regen_value(state)
    if refill or float(state.get("player_hp", 0.0)) <= 0:
        state["player_hp"] = max_hp
    elif prev_max_hp > 0:
        ratio = float(state.get("player_hp", 0.0)) / prev_max_hp
        state["player_hp"] = round(min(max_hp, max(1.0, ratio * max_hp)), 2)
    else:
        state["player_hp"] = max_hp
    if max_shield <= 0:
        state["player_shield"] = 0.0
    elif refill or prev_max_shield <= 0:
        state["player_shield"] = round(min(max_shield, float(state.get("player_shield", 0.0)) or max_shield * 0.5), 2)
    else:
        ratio = float(state.get("player_shield", 0.0)) / max(1.0, prev_max_shield)
        state["player_shield"] = round(min(max_shield, max(0.0, ratio * max_shield)), 2)


def apply_heal_to_player(state: dict[str, Any], amount: float, source: str = "regen") -> float:
    heal = max(0.0, float(amount))
    if heal <= 0:
        return 0.0
    before = float(state.get("player_hp", 0.0))
    max_hp = float(state.get("player_max_hp", 0.0))
    state["player_hp"] = round(min(max_hp, before + heal), 2)
    applied = round(float(state["player_hp"]) - before, 2)
    if applied > 0:
        state["player_last_heal_at"] = time.time()
    return applied


def apply_shield_to_player(state: dict[str, Any], amount: float, source: str = "earth") -> float:
    gain = max(0.0, float(amount))
    max_shield = float(state.get("player_max_shield", 0.0))
    if gain <= 0 or max_shield <= 0:
        return 0.0
    before = float(state.get("player_shield", 0.0))
    state["player_shield"] = round(min(max_shield, before + gain), 2)
    applied = round(float(state["player_shield"]) - before, 2)
    if applied > 0:
        state["player_last_shield_at"] = time.time()
    return applied


def mitigated_player_damage(state: dict[str, Any], raw_damage: float) -> float:
    raw = max(0.0, float(raw_damage))
    reduced = raw * (1.0 - float(state.get("player_defense", 0.0)))
    return round(max(0.0, reduced), 2)


def apply_damage_to_player(state: dict[str, Any], damage: float, attack_kind: str = "hit") -> dict[str, Any]:
    incoming = mitigated_player_damage(state, damage)
    shield_before = float(state.get("player_shield", 0.0))
    hp_before = float(state.get("player_hp", 0.0))
    shield_spent = min(shield_before, incoming)
    state["player_shield"] = round(max(0.0, shield_before - shield_spent), 2)
    hp_damage = max(0.0, incoming - shield_spent)
    state["player_hp"] = round(max(0.0, hp_before - hp_damage), 2)
    state["player_last_hit_at"] = time.time()
    return {
        "player_damage_taken": round(hp_damage, 2),
        "player_damage_blocked": round(shield_spent, 2),
        "player_hp": round(float(state.get("player_hp", 0.0)), 2),
        "player_shield": round(float(state.get("player_shield", 0.0)), 2),
        "enemy_attack": round(incoming, 2),
        "enemy_attack_kind": attack_kind,
        "player_defeated": float(state.get("player_hp", 0.0)) <= 0,
        "player_shield_broken": shield_before > 0 and float(state.get("player_shield", 0.0)) <= 0 and shield_spent > 0,
    }


def reset_after_player_defeat(state: dict[str, Any]) -> None:
    state["player_downs"] = int(state.get("player_downs", 0)) + 1
    stage = int(state.get("stage", 1))
    state["enemy"] = generate_enemy(stage)
    sync_player_combat_stats(state, refill=True)
    state["player_shield"] = round(float(state.get("player_max_shield", 0.0)) * 0.4, 2)


def merge_battle_result(base: dict[str, Any] | None, extra: dict[str, Any] | None) -> dict[str, Any] | None:
    if extra is None:
        return base
    if base is None:
        return dict(extra)
    merged = dict(base)
    for key in ("kills", "gold_gained", "armor_damage", "shield_damage", "player_damage_taken", "player_damage_blocked", "player_healed", "player_shielded"):
        merged[key] = round(float(merged.get(key, 0.0)) + float(extra.get(key, 0.0)), 2)
    for key in ("boss_kill", "blocked", "shield_hit", "seal_hit", "armor_broken", "shield_broken", "player_defeated", "player_shield_broken", "sustain_tick"):
        merged[key] = bool(merged.get(key)) or bool(extra.get(key))
    for key in ("blocked_reason", "enemy_phase", "enemy_status", "defeated_enemy_name", "defeated_enemy_type", "next_enemy_type", "enemy_attack_kind"):
        if extra.get(key) not in (None, ""):
            merged[key] = extra.get(key)
    if extra.get("enemy_attack"):
        merged["enemy_attack"] = extra.get("enemy_attack")
    if extra.get("player_hp") is not None:
        merged["player_hp"] = extra.get("player_hp")
    if extra.get("player_shield") is not None:
        merged["player_shield"] = extra.get("player_shield")
    if extra.get("damage"):
        merged["damage"] = round(float(merged.get("damage", 0.0)) + float(extra.get("damage", 0.0)), 2)
    return merged


def process_player_regen(state: dict[str, Any], elapsed: float) -> dict[str, float]:
    healed = apply_heal_to_player(state, float(state.get("player_regen", 0.0)) * elapsed, source="regen")
    shielded = 0.0
    if time.time() - float(state.get("player_last_hit_at", 0.0)) > 1.4:
        shielded = apply_shield_to_player(state, float(state.get("player_shield_regen", 0.0)) * elapsed, source="earth_regen")
    return {"player_healed": healed, "player_shielded": shielded, "sustain_tick": True}


def process_enemy_attacks(state: dict[str, Any], elapsed: float) -> dict[str, Any] | None:
    enemy = state["enemy"]
    interval = max(0.65, float(enemy.get("attack_interval", 2.0)) / max(0.35, float(enemy.get("attack_speed_mult", 1.0))))
    last_attack_at = float(enemy.get("last_attack_at", time.time()))
    now = time.time()
    attacks = int((now - last_attack_at) // interval)
    attacks = max(0, min(attacks, 4))
    if attacks <= 0:
        return None
    result: dict[str, Any] | None = None
    for _ in range(attacks):
        raw = float(enemy.get("attack_damage", 0.0)) * float(enemy.get("attack_damage_mult", 1.0))
        if enemy.get("type") == "boss" and enemy.get("mechanic") == "rage_phase" and float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0))) <= 0.5:
            raw *= 1.22
        if enemy.get("mechanic") == "shadow" and boss_shadow_active(enemy):
            raw *= 1.1
        damage_result = apply_damage_to_player(state, raw, attack_kind=str(enemy.get("attack_kind", "hit")))
        result = merge_battle_result(result, damage_result)
        if damage_result.get("player_defeated"):
            reset_after_player_defeat(state)
            result["player_hp"] = round(float(state.get("player_hp", 0.0)), 2)
            result["player_shield"] = round(float(state.get("player_shield", 0.0)), 2)
            break
    enemy["last_attack_at"] = last_attack_at + attacks * interval if attacks > 0 else now
    return result

