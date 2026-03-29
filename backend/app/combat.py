from __future__ import annotations

import time
from typing import Any

from .content import HOLD_BASE_TICKS, HOLD_MAX_MS, HOLD_MIN_MS, MAX_KILLS_PER_TICK, MAX_OFFLINE_PROGRESS_SECONDS
from .enemies import (
    boss_shadow_active,
    damage_after_enemy_mechanics,
    enemy_phase_name,
    enemy_status_text,
    generate_enemy,
    stage_kill_target,
    wave_hint_text,
    wave_location_text,
    wave_recommended_pairs,
    wave_size_for_index,
    wave_theme_for_index,
    wave_slot_kind,
)
from .heroes import (
    active_hero_ids,
    active_pair_key,
    base_tap_damage,
    earth_armor_break_multiplier,
    gold_multiplier,
    hero_breakpoint_count,
    hero_level,
    is_hero_active,
    total_hero_dps,
    water_hold_multiplier,
)
from .player import (
    apply_damage_to_player,
    apply_heal_to_player,
    apply_shield_to_player,
    player_heal_power_value,
    player_max_hp_value,
    player_max_shield_value,
    reset_after_player_defeat,
    sync_player_combat_stats,
)
from .progression import award_gold, update_records


def refresh_enemy_temporary_effects(state: dict[str, Any]) -> None:
    enemy = state["enemy"]
    now = time.time()
    if float(enemy.get("slow_until", 0.0)) > now:
        enemy["attack_speed_mult"] = float(enemy.get("slow_mult", 1.0))
    else:
        enemy["attack_speed_mult"] = 1.0
        enemy["slow_until"] = 0.0
        enemy["slow_mult"] = 1.0
    if float(enemy.get("combo_vuln_until", 0.0)) <= now:
        enemy["combo_vuln_until"] = 0.0
        enemy["combo_vuln_mult"] = 1.0
    if float(enemy.get("armor_exposed_until", 0.0)) <= now:
        enemy["armor_exposed_until"] = 0.0
        enemy["armor_exposed_mult"] = 1.0
    if float(enemy.get("gold_window_until", 0.0)) <= now:
        enemy["gold_window_until"] = 0.0
        enemy["gold_window_mult"] = 1.0


def can_fight(state: dict[str, Any]) -> bool:
    return bool(state.get("wave_in_progress")) and not bool(state.get("wave_waiting"))


def prepare_next_wave_preview(state: dict[str, Any]) -> None:
    wave_index = max(1, int(state.get("wave_index", 1)))
    theme = wave_theme_for_index(wave_index)
    state["wave_theme_id"] = theme["id"]
    state["wave_location"] = wave_location_text(wave_index)
    state["wave_hint"] = wave_hint_text(wave_index)
    state["wave_recommended_pairs"] = wave_recommended_pairs(wave_index)
    preview_size = wave_size_for_index(wave_index)
    preview_enemy = generate_enemy(
        int(state.get("stage", 1)),
        state.get("last_enemy_id"),
        wave_theme_id=theme["id"],
        forced_kind=wave_slot_kind(preview_size, 1),
        wave_slot=1,
        wave_size=preview_size,
    )
    state["enemy"] = preview_enemy
    state["last_enemy_id"] = preview_enemy.get("id")


def start_wave(state: dict[str, Any]) -> dict[str, Any]:
    if can_fight(state):
        return {"wave_started": False, "wave_locked": True}
    wave_index = max(1, int(state.get("wave_index", 1)))
    wave_size = wave_size_for_index(wave_index)
    theme = wave_theme_for_index(wave_index)
    state["wave_size"] = wave_size
    state["wave_progress"] = 0
    state["wave_in_progress"] = True
    state["wave_waiting"] = False
    state["swipe_history"] = []
    state["wave_theme_id"] = theme["id"]
    state["wave_location"] = wave_location_text(wave_index)
    state["wave_hint"] = wave_hint_text(wave_index)
    state["wave_recommended_pairs"] = wave_recommended_pairs(wave_index)
    first_enemy = generate_enemy(
        int(state.get("stage", 1)),
        state.get("last_enemy_id"),
        wave_theme_id=theme["id"],
        forced_kind=wave_slot_kind(wave_size, 1),
        wave_slot=1,
        wave_size=wave_size,
    )
    state["enemy"] = first_enemy
    state["last_enemy_id"] = first_enemy.get("id")
    return {"wave_started": True, "wave_locked": False, "wave_size": wave_size}


def stop_expedition(state: dict[str, Any]) -> dict[str, Any]:
    was_active = bool(state.get("wave_in_progress")) and not bool(state.get("wave_waiting"))
    stopped_wave = max(1, int(state.get("wave_index", 1)))
    cleared = int(state.get("wave_progress", 0))
    state["wave_in_progress"] = False
    state["wave_waiting"] = True
    state["wave_progress"] = 0
    state["wave_size"] = 0
    state["swipe_history"] = []
    prepare_next_wave_preview(state)
    update_records(state)
    return {
        "expedition_stopped": True,
        "stopped_wave": stopped_wave,
        "stopped_progress": cleared,
        "stopped_mid_wave": was_active,
    }


def apply_swipe_combo_effect(state: dict[str, Any], combo_key: str, combo: dict[str, Any] | None, pair_key: str) -> dict[str, Any]:
    enemy = state["enemy"]
    refresh_enemy_temporary_effects(state)
    if not combo or not combo_key:
        return {"combo_proc": False, "combo_proc_text": ""}

    now = time.time()
    vuln_until = 0.0
    vuln_mult = 1.0
    proc_text = ""

    if combo_key == "RR":
        vuln_until = now + 1.8
        vuln_mult = 1.06
        proc_text = "Рывок расшатал цель. Короткое окно на добивание."
    elif combo_key == "UU":
        vuln_until = now + 2.0
        vuln_mult = 1.08
        proc_text = "Подброс вскрыл стойку. Следующий прокаст залетает сочнее."
    elif combo_key == "LL":
        enemy["slow_until"] = max(float(enemy.get("slow_until", 0.0)), now + 2.8)
        enemy["slow_mult"] = min(float(enemy.get("slow_mult", 1.0)), 0.76)
        proc_text = "Боковой срез сбил темп врага. Он бьёт медленнее."
    elif combo_key == "DD":
        vuln_until = now + 2.2
        vuln_mult = 1.1
        enemy["shatter_until"] = max(float(enemy.get("shatter_until", 0.0)), now + 2.4)
        proc_text = "Тяжёлый удар вниз раскалывает стойку и крошит броню."
    elif combo_key == "RRUU":
        vuln_until = now + 3.2
        vuln_mult = 1.14
        enemy["slow_until"] = max(float(enemy.get("slow_until", 0.0)), now + 2.2)
        enemy["slow_mult"] = min(float(enemy.get("slow_mult", 1.0)), 0.82)
        enemy["shatter_until"] = max(float(enemy.get("shatter_until", 0.0)), now + 3.0)
        proc_text = "Длинная связка вскрыла цель по полной. Есть окно на жёсткий разнос."

    if "air" in pair_key and combo_key in {"RR", "RRUU"}:
        enemy["slow_until"] = max(float(enemy.get("slow_until", 0.0)), now + 3.1)
        enemy["slow_mult"] = min(float(enemy.get("slow_mult", 1.0)), 0.72)
    if "earth" in pair_key and combo_key in {"DD", "RRUU"}:
        enemy["shatter_until"] = max(float(enemy.get("shatter_until", 0.0)), now + 3.6)
    if "water" in pair_key and combo_key in {"LL", "RRUU"}:
        vuln_until = max(vuln_until, now + 2.8)
        vuln_mult = max(vuln_mult, 1.14)
    if "fire" in pair_key and combo_key in {"UU", "RRUU"}:
        vuln_until = max(vuln_until, now + 2.4)
        vuln_mult = max(vuln_mult, 1.16)

    if vuln_until > now:
        enemy["combo_vuln_until"] = max(float(enemy.get("combo_vuln_until", 0.0)), vuln_until)
        enemy["combo_vuln_mult"] = max(float(enemy.get("combo_vuln_mult", 1.0)), vuln_mult)

    refresh_enemy_temporary_effects(state)
    return {"combo_proc": True, "combo_proc_text": proc_text}


def apply_burn(state: dict[str, Any], source_damage: float, source: str) -> None:
    if not is_hero_active(state, "fire"):
        return
    enemy = state["enemy"]
    level = hero_level(state, "fire")
    milestone_count = hero_breakpoint_count(level)
    if source == "tap" and milestone_count < 1:
        return
    if source == "swipe" and milestone_count < 2:
        return
    if source == "hold" and "water" not in active_hero_ids(state):
        return
    stacks = 1
    if source == "swipe" and milestone_count >= 2:
        stacks += 1
    if milestone_count >= 4:
        stacks += 1
    enemy["burn_stacks"] = min(6, int(enemy.get("burn_stacks", 0)) + stacks)
    base_power = source_damage * (0.045 + milestone_count * 0.016)
    if active_pair_key(state) == "fire_water":
        base_power *= 1.18
    elif active_pair_key(state) == "fire_air":
        base_power *= 1.12
    elif active_pair_key(state) == "fire_earth":
        base_power *= 1.1
    enemy["burn_power"] = max(float(enemy.get("burn_power", 0.0)), round(base_power, 2))
    enemy["burn_until"] = time.time() + 4.0 + milestone_count * 0.45
    enemy["burn_tick_at"] = min(float(enemy.get("burn_tick_at", 0.0)) or time.time(), time.time() + 0.55)


def process_enemy_burn(state: dict[str, Any]) -> dict[str, Any] | None:
    enemy = state["enemy"]
    if float(enemy.get("burn_until", 0.0)) <= time.time() or int(enemy.get("burn_stacks", 0)) <= 0:
        enemy["burn_stacks"] = 0
        enemy["burn_power"] = 0.0
        return None
    now = time.time()
    next_tick = float(enemy.get("burn_tick_at", 0.0) or now)
    if now < next_tick:
        return None
    pair_key = active_pair_key(state)
    stacks = int(enemy.get("burn_stacks", 0))
    damage = float(enemy.get("burn_power", 0.0)) * (0.55 + stacks * 0.18)
    if pair_key == "fire_air" and enemy.get("type") == "group":
        damage *= 1.14
    if pair_key == "fire_earth" and enemy.get("type") in {"elite", "boss"}:
        damage *= 1.1
    enemy["burn_tick_at"] = now + 0.7
    hit = apply_damage(state, round(damage, 2), source="burn")
    hit["source"] = "burn"
    hit["damage"] = round(damage, 2)
    hit["burn_tick"] = True
    return hit


def resolve_enemy_death(state: dict[str, Any]) -> dict[str, Any]:
    defeated_enemy = dict(state["enemy"])
    current_stage = int(state.get("stage", 1))
    reward = defeated_enemy["reward"] * gold_multiplier(state)
    if float(defeated_enemy.get("gold_window_until", 0.0)) > time.time():
        reward *= max(1.0, float(defeated_enemy.get("gold_window_mult", 1.0)))
    award_gold(state, reward)
    state["kills"] += 1
    state["lifetime_kills"] = int(state.get("lifetime_kills", 0)) + 1
    boss_kill = defeated_enemy["type"] == "boss"
    if boss_kill:
        state["boss_kills"] += 1
        state["lifetime_boss_kills"] = int(state.get("lifetime_boss_kills", 0)) + 1

    stage_target = stage_kill_target(current_stage)
    stage_progress = int(state.get("stage_progress", 0)) + 1
    state["stage_progress"] = stage_progress
    if stage_progress >= stage_target:
        state["stage"] = current_stage + 1
        state["stage_progress"] = 0

    state["wave_progress"] = int(state.get("wave_progress", 0)) + 1
    wave_size = max(1, int(state.get("wave_size", 1) or 1))
    wave_completed = int(state.get("wave_progress", 0)) >= wave_size

    state["last_enemy_id"] = defeated_enemy.get("id")
    next_enemy_type = None
    if wave_completed:
        state["wave_in_progress"] = False
        state["wave_waiting"] = True
        state["wave_index"] = max(1, int(state.get("wave_index", 1))) + 1
        state["wave_size"] = 0
        prepare_next_wave_preview(state)
        next_enemy_type = state["enemy"]["type"]
    else:
        next_slot = int(state.get("wave_progress", 0)) + 1
        next_kind = wave_slot_kind(wave_size, next_slot)
        theme_id = str(state.get("wave_theme_id") or wave_theme_for_index(int(state.get("wave_index", 1)))["id"])
        next_enemy = generate_enemy(
            int(state["stage"]),
            state.get("last_enemy_id"),
            wave_theme_id=theme_id,
            forced_kind=next_kind,
            wave_slot=next_slot,
            wave_size=wave_size,
        )
        state["enemy"] = next_enemy
        state["last_enemy_id"] = next_enemy.get("id")
        next_enemy_type = next_enemy["type"]

    update_records(state)
    return {
        "enemy_id": defeated_enemy["id"],
        "enemy_name": defeated_enemy["name"],
        "enemy_type": defeated_enemy["type"],
        "reward": round(reward, 2),
        "boss_kill": boss_kill,
        "next_stage": int(state["stage"]),
        "next_enemy_type": next_enemy_type,
        "stage_cleared": stage_progress >= stage_target,
        "stage_progress": int(state.get("stage_progress", 0)),
        "stage_target": stage_kill_target(int(state.get("stage", 1))),
        "wave_completed": wave_completed,
        "wave_progress": int(state.get("wave_progress", 0)),
        "wave_size": wave_size,
    }


def apply_damage(state: dict[str, Any], damage: float, source: str = "tap", source_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    refresh_enemy_temporary_effects(state)
    result = {
        "kills": 0,
        "gold_gained": 0.0,
        "boss_kill": False,
        "defeated_enemy_name": None,
        "defeated_enemy_type": None,
        "next_enemy_type": state["enemy"].get("type"),
        "blocked": False,
        "blocked_reason": None,
        "shield_hit": False,
        "seal_hit": False,
        "enemy_phase": enemy_phase_name(state),
        "enemy_status": enemy_status_text(state),
        "armor_damage": 0.0,
        "armor_broken": False,
        "shield_damage": 0.0,
        "shield_broken": False,
        "player_damage_taken": 0.0,
        "player_damage_blocked": 0.0,
        "player_healed": 0.0,
        "player_shielded": 0.0,
        "player_defeated": False,
        "player_shield_broken": False,
    }
    if not can_fight(state):
        result["blocked"] = True
        result["blocked_reason"] = "wave_paused"
        return result

    remaining = max(0.0, damage)
    while remaining > 0 and result["kills"] < MAX_KILLS_PER_TICK:
        adjusted_damage, mechanic_info = damage_after_enemy_mechanics(state, remaining, source, source_meta=source_meta)
        result["blocked"] = result["blocked"] or mechanic_info.get("blocked", False)
        if mechanic_info.get("blocked_reason"):
            result["blocked_reason"] = mechanic_info["blocked_reason"]
        result["shield_hit"] = result["shield_hit"] or mechanic_info.get("shield_hit", False)
        result["seal_hit"] = result["seal_hit"] or mechanic_info.get("seal_hit", False)
        if adjusted_damage <= 0:
            break

        enemy = state["enemy"]
        if mechanic_info.get("shield_only"):
            shield_before = float(enemy.get("shield_hp", 0.0))
            absorbed = min(shield_before, adjusted_damage)
            enemy["shield_hp"] = round(max(0.0, shield_before - absorbed), 2)
            result["shield_damage"] = round(result.get("shield_damage", 0.0) + absorbed, 2)
            if shield_before > 0 and float(enemy.get("shield_hp", 0.0)) <= 0:
                result["shield_broken"] = True
                if enemy.get("mechanic") == "shield_hits":
                    enemy["combo_vuln_until"] = max(float(enemy.get("combo_vuln_until", 0.0)), time.time() + 2.5)
                    enemy["combo_vuln_mult"] = max(float(enemy.get("combo_vuln_mult", 1.0)), 1.35)
            result["enemy_phase"] = enemy_phase_name(state)
            result["enemy_status"] = enemy_status_text(state)
            break

        if enemy.get("type") in {"elite", "boss"} and float(enemy.get("armor", 0.0)) > 0:
            armor_damage = adjusted_damage * (0.24 if source == "dps" else 0.52)
            if source in {"tap", "swipe", "hold"}:
                armor_damage *= earth_armor_break_multiplier(state)
            if float(enemy.get("armor_exposed_until", 0.0)) > time.time():
                armor_damage *= max(1.0, float(enemy.get("armor_exposed_mult", 1.0)))
            if source == "hold" and is_hero_active(state, "water"):
                armor_damage *= 0.82
            if source == "burn":
                armor_damage *= 0.2
            armor_before = float(enemy.get("armor", 0.0))
            enemy["armor"] = round(max(0.0, armor_before - armor_damage), 2)
            result["armor_damage"] = round(result["armor_damage"] + armor_damage, 2)
            if armor_before > 0 and enemy["armor"] <= 0:
                result["armor_broken"] = True
                enemy["shatter_until"] = time.time() + 5.0
            adjusted_damage *= 0.64 if armor_before > 0 else 1.0

        if float(enemy.get("shatter_until", 0.0)) > time.time():
            adjusted_damage *= 1.16
        if float(enemy.get("combo_vuln_until", 0.0)) > time.time():
            adjusted_damage *= max(1.0, float(enemy.get("combo_vuln_mult", 1.0)))
        if float(enemy.get("armor_exposed_until", 0.0)) > time.time() and source in {"tap", "swipe", "hold"}:
            adjusted_damage *= max(1.0, float(enemy.get("armor_exposed_mult", 1.0)))

        hp = float(enemy["hp"])
        if adjusted_damage >= hp:
            remaining = max(0.0, remaining - hp)
            death_info = resolve_enemy_death(state)
            result["kills"] += 1
            result["gold_gained"] = round(result["gold_gained"] + death_info["reward"], 2)
            result["boss_kill"] = result["boss_kill"] or death_info["boss_kill"]
            result["defeated_enemy_name"] = death_info["enemy_name"]
            result["defeated_enemy_type"] = death_info["enemy_type"]
            result["next_enemy_type"] = death_info["next_enemy_type"]
            result["wave_completed"] = death_info.get("wave_completed", False)
            result["wave_progress"] = death_info.get("wave_progress")
            result["wave_size"] = death_info.get("wave_size")
            result["enemy_phase"] = enemy_phase_name(state)
            result["enemy_status"] = enemy_status_text(state)
            continue

        enemy["hp"] = round(max(0.0, hp - adjusted_damage), 2)
        result["enemy_phase"] = enemy_phase_name(state)
        result["enemy_status"] = enemy_status_text(state)
        break
    return result


def advance_state(state: dict[str, Any]) -> dict[str, Any] | None:
    now = time.time()
    elapsed = max(0.0, now - float(state.get("last_tick", now)))
    elapsed = min(elapsed, MAX_OFFLINE_PROGRESS_SECONDS)
    state["last_tick"] = now
    sync_player_combat_stats(state)
    refresh_enemy_temporary_effects(state)
    result = None

    if elapsed > 0:
        sustain = process_player_regen(state, elapsed)
        if sustain.get("player_healed") or sustain.get("player_shielded"):
            result = merge_battle_result(result, sustain)

    if not can_fight(state):
        return result

    dps = total_hero_dps(state)
    if elapsed > 0 and dps > 0:
        result = merge_battle_result(result, apply_damage(state, dps * elapsed, source="dps", source_meta={"pair_key": active_pair_key(state)}))

    burn_result = process_enemy_burn(state)
    if burn_result:
        result = merge_battle_result(result, burn_result)

    incoming = process_enemy_attacks(state, elapsed)
    if incoming:
        result = merge_battle_result(result, incoming)
    return result


def merge_battle_result(base: dict[str, Any] | None, extra: dict[str, Any] | None) -> dict[str, Any] | None:
    if extra is None:
        return base
    if base is None:
        return dict(extra)
    merged = dict(base)
    for key in ("kills", "gold_gained", "armor_damage", "shield_damage", "player_damage_taken", "player_damage_blocked", "player_healed", "player_shielded"):
        merged[key] = round(float(merged.get(key, 0.0)) + float(extra.get(key, 0.0)), 2)
    for key in ("boss_kill", "blocked", "shield_hit", "seal_hit", "armor_broken", "shield_broken", "player_defeated", "player_shield_broken", "sustain_tick", "wave_completed"):
        merged[key] = bool(merged.get(key)) or bool(extra.get(key))
    for key in ("blocked_reason", "enemy_phase", "enemy_status", "defeated_enemy_name", "defeated_enemy_type", "next_enemy_type", "enemy_attack_kind"):
        if extra.get(key) not in (None, ""):
            merged[key] = extra.get(key)
    for key in ("wave_progress", "wave_size"):
        if extra.get(key) is not None:
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
    interval = max(0.7, float(enemy.get("attack_interval", 2.0)) / max(0.35, float(enemy.get("attack_speed_mult", 1.0))))
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
            raw *= 1.14
        if enemy.get("mechanic") == "shadow" and boss_shadow_active(enemy):
            raw *= 1.06
        damage_result = apply_damage_to_player(state, raw, attack_kind=str(enemy.get("attack_kind", "hit")))
        result = merge_battle_result(result, damage_result)
        if damage_result.get("player_defeated"):
            reset_after_player_defeat(state)
            result["player_hp"] = round(float(state.get("player_hp", 0.0)), 2)
            result["player_shield"] = round(float(state.get("player_shield", 0.0)), 2)
            break
    enemy["last_attack_at"] = last_attack_at + attacks * interval if attacks > 0 else now
    return result


def elemental_visual_for_state(state: dict[str, Any], source: str = "tap") -> str | None:
    pair_key = active_pair_key(state)
    pair_visuals = {
        "fire_air": "fx-fire-wind",
        "fire_water": "fx-steam",
        "fire_earth": "fx-lava",
        "air_water": "fx-storm",
        "air_earth": "fx-sand",
        "water_earth": "fx-mud",
    }
    if pair_key in pair_visuals:
        return pair_visuals[pair_key]
    active = set(active_hero_ids(state))
    if "fire" in active:
        return "fx-fire"
    if "water" in active:
        return "fx-water"
    if "earth" in active:
        return "fx-earth"
    if "air" in active:
        return "fx-wind"
    return None if source == "swipe" else "fx-arcane"


def swipe_direction_multiplier(direction: str) -> float:
    return {"up": 1.0, "down": 1.22, "left": 0.92, "right": 1.08}.get(direction, 1.0)


def swipe_combo_payload(pair_key: str, combo_key: str) -> dict[str, Any] | None:
    combo_map = {
        "solo": {
            "RR": {"name": "Рывок", "damage_mult": 1.18, "effect": "Точный добивающий рывок.", "visual": "fx-wind"},
            "UU": {"name": "Подброс", "damage_mult": 1.16, "effect": "Враг ловит вертикальный импульс.", "visual": "fx-arcane"},
            "LL": {"name": "Срез", "damage_mult": 1.14, "effect": "Режущий боковой удар.", "visual": "fx-shadow"},
            "DD": {"name": "Дробление", "damage_mult": 1.24, "effect": "Тяжёлый удар вниз.", "visual": "fx-earth"},
            "RRUU": {"name": "Степной наскок", "damage_mult": 1.38, "effect": "Комбо разгоняет общий урон.", "visual": "fx-wind"},
        },
        "fire_air": {
            "RR": {"name": "Искровой рывок", "damage_mult": 1.34, "effect": "Свайп разрезает цель огненным ветром.", "visual": "fx-fire-wind"},
            "UU": {"name": "Пламенный подъём", "damage_mult": 1.32, "effect": "Поджигает и подбрасывает урон вверх.", "visual": "fx-fire-wind"},
            "RRUU": {"name": "Огненное торнадо", "damage_mult": 1.72, "effect": "Две тяги вправо и две вверх поднимают огненное торнадо вокруг цели.", "visual": "fx-fire-wind"},
            "DD": {"name": "Жаровой обвал", "damage_mult": 1.48, "effect": "Тяжёлый удар вниз взрывает искры вокруг цели.", "visual": "fx-fire"},
        },
        "fire_water": {
            "RR": {"name": "Паровой разгон", "damage_mult": 1.28, "effect": "Густой пар ускоряет следующую атаку.", "visual": "fx-steam"},
            "UU": {"name": "Кипящий столб", "damage_mult": 1.3, "effect": "Столб пара прожигает цель по вертикали.", "visual": "fx-steam"},
            "RRUU": {"name": "Паровой взрыв", "damage_mult": 1.66, "effect": "Комбо срывает крупный взрыв пара.", "visual": "fx-steam"},
            "DD": {"name": "Обвар", "damage_mult": 1.42, "effect": "Плотный горячий удар вниз.", "visual": "fx-fire"},
        },
        "fire_earth": {
            "RR": {"name": "Лавовый надлом", "damage_mult": 1.22, "armor_mult": 1.2, "effect": "Жар проходит через трещины брони.", "visual": "fx-lava"},
            "DD": {"name": "Лавовый раскол", "damage_mult": 1.62, "armor_mult": 1.75, "effect": "Ломает защиту элит и боссов быстрее.", "visual": "fx-lava"},
            "RRUU": {"name": "Вспышка магмы", "damage_mult": 1.58, "armor_mult": 1.45, "effect": "Магма рвёт броню и здоровье одним пакетом.", "visual": "fx-lava"},
        },
        "air_water": {
            "RR": {"name": "Косой шквал", "damage_mult": 1.3, "effect": "Водяной ветер режет цель на скорости.", "visual": "fx-storm"},
            "UU": {"name": "Штормовой подъём", "damage_mult": 1.34, "effect": "Поднимает волну урона вверх.", "visual": "fx-storm"},
            "LL": {"name": "Обратное течение", "damage_mult": 1.28, "effect": "Свайп влево сбивает ритм врага.", "visual": "fx-water"},
            "RRUU": {"name": "Грозовой фронт", "damage_mult": 1.68, "effect": "Четырёхходовый рисунок вызывает штормовой прокаст.", "visual": "fx-storm"},
        },
        "air_earth": {
            "RR": {"name": "Песчаный разгон", "damage_mult": 1.26, "armor_mult": 1.2, "effect": "Песок срезает защитный слой.", "visual": "fx-sand"},
            "DD": {"name": "Обвал", "damage_mult": 1.56, "armor_mult": 1.8, "effect": "Лучшее тяжёлое комбо по броне.", "visual": "fx-sand"},
            "LL": {"name": "Песчаный сдвиг", "damage_mult": 1.24, "effect": "Сносит устойчивость врага в сторону.", "visual": "fx-sand"},
            "RRUU": {"name": "Песчаная буря", "damage_mult": 1.64, "armor_mult": 1.5, "effect": "Вихрь песка быстро крошит элиту.", "visual": "fx-sand"},
        },
        "water_earth": {
            "RR": {"name": "Глиняный натиск", "damage_mult": 1.2, "effect": "Липкий удар давит цель по линии.", "visual": "fx-mud"},
            "LL": {"name": "Топь", "damage_mult": 1.22, "effect": "Тягучий резкий срыв темпа.", "visual": "fx-mud"},
            "DD": {"name": "Грязевой молот", "damage_mult": 1.48, "armor_mult": 1.45, "effect": "Хорошо вскрывает тяжёлые цели.", "visual": "fx-mud"},
            "RRUU": {"name": "Болотный прилив", "damage_mult": 1.6, "effect": "Сильная волна вязкого давления.", "visual": "fx-mud"},
        },
    }
    pair_combos = combo_map.get(pair_key, combo_map["solo"])
    return pair_combos.get(combo_key) or combo_map["solo"].get(combo_key)


def swipe_damage_value(state: dict[str, Any], direction: str, combo: dict[str, Any] | None) -> tuple[float, float]:
    damage = base_tap_damage(state) * 0.92
    damage *= swipe_direction_multiplier(direction)
    active = set(active_hero_ids(state))
    pair_key = active_pair_key(state)
    wave_index = max(1, int(state.get("wave_index", 1)))
    if "air" in active:
        level = hero_level(state, "air")
        damage *= 1 + level * 0.022 + hero_breakpoint_count(level) * 0.2
    if "water" in active:
        level = hero_level(state, "water")
        damage *= 1 + level * 0.014 + hero_breakpoint_count(level) * 0.1
    if combo:
        damage *= float(combo.get("damage_mult", 1.0))
    if wave_index > 10 and "air" in pair_key:
        damage *= 1.25
    armor_mult = float(combo.get("armor_mult", 1.0)) if combo else 1.0
    if state["enemy"].get("type") in {"elite", "boss"} and ("earth" in active or armor_mult > 1.0):
        level = hero_level(state, "earth") if "earth" in active else 0
        damage *= 1 + level * 0.018 + hero_breakpoint_count(level) * 0.12
        damage *= armor_mult
    if wave_index > 10 and "earth" in pair_key:
        damage *= 1.2
    return round(damage, 2), armor_mult


def register_swipe_combo(state: dict[str, Any], direction: str) -> tuple[str, list[str], dict[str, Any] | None, str]:
    history = list(state.get("swipe_history", []))
    history.append(direction)
    history = history[-6:]
    state["swipe_history"] = history
    state["last_swipe_at"] = time.time()
    tail = ''.join(item[0].upper() for item in history[-4:])
    pair_key = active_pair_key(state)
    for size in (4, 2):
        key = tail[-size:]
        combo = swipe_combo_payload(pair_key, key)
        if combo:
            return key, history, combo, pair_key
    return '', history, None, pair_key


def hold_damage_value(state: dict[str, Any], duration_ms: int) -> tuple[float, dict[str, Any]]:
    duration_ms = max(HOLD_MIN_MS, min(HOLD_MAX_MS, int(duration_ms)))
    charge = duration_ms / HOLD_MAX_MS
    base = base_tap_damage(state) * (0.58 + charge * 1.28)
    ticks = HOLD_BASE_TICKS + int(charge * 4)
    pair_key = active_pair_key(state)
    wave_index = max(1, int(state.get("wave_index", 1)))
    extra = 1.0
    effect = "Пустой канал без стихии."
    visual = "fx-water"
    heal_amount = 0.0
    shield_amount = 0.0
    if is_hero_active(state, "water"):
        extra *= water_hold_multiplier(state)
        heal_amount += (player_max_hp_value(state) * (0.015 + charge * 0.035)) * player_heal_power_value(state)
        effect = "Вода разгоняет удержание тапа, лечит верховного шамана и выливает поток урона."
    if is_hero_active(state, "earth"):
        shield_amount += player_max_shield_value(state) * (0.096 + charge * 0.176)
    if pair_key == "fire_water":
        extra *= 1.12
        heal_amount *= 1.12
        effect = "Паровой канал: отпускание даёт горячий всплеск и подлечивает шамана."
        visual = "fx-steam"
    elif pair_key == "air_water":
        extra *= 1.12
        heal_amount *= 1.16
        effect = "Штормовой канал: ветер режет поток по группе и ускоряет отхил."
        visual = "fx-storm"
    elif pair_key == "water_earth":
        extra *= 1.14
        heal_amount *= 1.12
        shield_amount *= 1.3
        effect = "Грязевой нажим: поток давит броню, лечит и набрасывает щит верховному шаману."
        visual = "fx-mud"
    elif pair_key == "fire_air":
        extra *= 1.08
        visual = "fx-fire-wind"
    if state["enemy"].get("type") == "group":
        extra *= 1.08
    if state["enemy"].get("type") in {"elite", "boss"} and is_hero_active(state, "earth"):
        extra *= 1.06
    if wave_index > 10 and "water" in pair_key:
        extra *= 1.35
    if wave_index > 10 and "earth" in pair_key:
        extra *= 1.2
    return round(base * extra, 2), {
        "ticks": ticks,
        "charge": round(charge, 2),
        "effect": effect,
        "visual": visual,
        "pair_key": pair_key,
        "heal_amount": round(heal_amount, 2),
        "shield_amount": round(shield_amount, 2),
    }
