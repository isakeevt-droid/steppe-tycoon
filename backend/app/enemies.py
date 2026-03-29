from __future__ import annotations

import random
import time
from typing import Any

from .content import BOSSES, ELITES, ENEMIES, STAGE_KILL_TARGETS, WAVE_ARCHETYPES
from .heroes import pair_has_earth


def stage_type(stage: int) -> str:
    if stage % 10 == 0:
        return "boss"
    if stage % 5 == 0:
        return "elite"
    if stage % 3 == 0:
        return "group"
    return "normal"


def wave_theme_for_index(wave_index: int) -> dict[str, Any]:
    if not WAVE_ARCHETYPES:
        raise ValueError("Wave archetypes are empty")
    return WAVE_ARCHETYPES[(max(1, int(wave_index)) - 1) % len(WAVE_ARCHETYPES)]


def wave_size_for_index(wave_index: int) -> int:
    cycle = (max(1, int(wave_index)) - 1) % 6
    return [6, 7, 8, 9, 10, 12][cycle]


def wave_location_text(wave_index: int) -> str:
    return str(wave_theme_for_index(wave_index).get("location", "Степь"))


def wave_hint_text(wave_index: int) -> str:
    theme = wave_theme_for_index(wave_index)
    return str(theme.get("slang") or theme.get("hint") or "Степь шепчет что-то мутное.")


def wave_recommended_pairs(wave_index: int) -> list[str]:
    theme = wave_theme_for_index(wave_index)
    signals = theme.get("signals", [])
    return [str(item) for item in signals if item]




def wave_modifier_for_theme(wave_theme_id: str | None) -> dict[str, Any]:
    if not wave_theme_id:
        return {}
    theme = next((item for item in WAVE_ARCHETYPES if item.get("id") == wave_theme_id), None)
    if not theme:
        return {}
    modifiers = theme.get("modifiers", {})
    return modifiers if isinstance(modifiers, dict) else {}


def late_wave_pair_profile(theme_id: str | None) -> dict[str, Any]:
    profiles: dict[str, dict[str, Any]] = {
        "embers": {"pairs": {"fire_air", "fire_water"}, "sources": {"tap", "burn", "swipe"}, "combo_only": False},
        "ash": {"pairs": {"fire_air", "fire_water", "fire_earth"}, "sources": {"tap", "burn", "swipe"}, "combo_only": False},
        "stone": {"pairs": {"fire_earth", "air_earth", "water_earth"}, "sources": {"swipe", "hold"}, "combo_only": True},
        "iron": {"pairs": {"fire_earth", "air_earth", "water_earth"}, "sources": {"swipe", "hold"}, "combo_only": True},
        "storm": {"pairs": {"fire_air", "air_water", "air_earth"}, "sources": {"swipe"}, "combo_only": True},
        "gale": {"pairs": {"fire_air", "air_water", "air_earth"}, "sources": {"swipe"}, "combo_only": True},
        "dust": {"pairs": {"fire_air", "air_earth"}, "sources": {"swipe", "tap"}, "combo_only": True},
        "tide": {"pairs": {"fire_water", "air_water", "water_earth"}, "sources": {"hold"}, "combo_only": False},
        "reeds": {"pairs": {"air_water", "water_earth"}, "sources": {"hold", "swipe"}, "combo_only": False},
        "mire": {"pairs": {"fire_water", "water_earth"}, "sources": {"hold"}, "combo_only": False},
        "ritual": {"pairs": {"fire_air", "fire_earth", "air_water", "water_earth"}, "sources": {"tap", "swipe", "hold"}, "combo_only": True},
        "shrine": {"pairs": {"fire_earth", "air_earth", "water_earth"}, "sources": {"swipe", "hold"}, "combo_only": True},
        "dusk": {"pairs": {"fire_air", "air_earth"}, "sources": {"tap", "swipe"}, "combo_only": False},
        "howls": {"pairs": {"fire_air", "air_water"}, "sources": {"swipe", "tap"}, "combo_only": False},
        "blacksky": {"pairs": {"fire_water", "air_earth", "fire_air"}, "sources": {"tap", "swipe", "hold"}, "combo_only": True},
    }
    return dict(profiles.get(theme_id or "", {"pairs": set(), "sources": {"tap", "swipe", "hold", "burn", "dps"}, "combo_only": False}))


def late_wave_pair_multiplier(
    state: dict[str, Any],
    enemy: dict[str, Any],
    source: str,
    pair_key: str,
    combo_key: str,
) -> tuple[float, str | None]:
    wave_index = max(1, int(state.get("wave_index", 1)))
    if wave_index <= 10:
        return 1.0, None

    profile = late_wave_pair_profile(str(enemy.get("theme_id") or enemy.get("wave_theme_id") or ""))
    allowed_pairs = {str(item) for item in profile.get("pairs", set()) if item}
    preferred_sources = {str(item) for item in profile.get("sources", set()) if item}
    combo_only = bool(profile.get("combo_only", False))
    pair_ok = pair_key in allowed_pairs
    combo_ready = bool(combo_key) and len(combo_key) >= 2
    source_ok = source in preferred_sources or source in {"burn", "dps"}

    pressure_step = wave_index - 10
    boss_or_elite = enemy.get("type") in {"boss", "elite"}

    if pair_key == "solo":
        return (0.08 if boss_or_elite else 0.15), "pair_mismatch"

    if not pair_ok:
        if enemy.get("type") == "boss":
            return max(0.10, 0.22 - pressure_step * 0.012), "pair_mismatch"
        if enemy.get("type") == "elite":
            return max(0.14, 0.28 - pressure_step * 0.012), "pair_mismatch"
        return max(0.12, 0.45 - pressure_step * 0.02), "pair_mismatch"

    mult = 1.0
    if boss_or_elite:
        mult *= min(1.58, 1.16 + pressure_step * 0.032)
    else:
        mult *= min(1.34, 1.06 + pressure_step * 0.02)

    if source in {"swipe", "hold", "tap"} and not source_ok:
        mult *= 0.52 if boss_or_elite else 0.7
        return mult, "pair_action_mismatch"

    if combo_only and not combo_ready:
        return 0.10, "pair_combo_mismatch"

    if pair_ok:
        mult *= 1.25 + pressure_step * 0.02
    if combo_ready and source == "swipe":
        mult *= 1.18
    if source == "hold" and "hold" in preferred_sources:
        mult *= 1.2
    if source in {"tap", "burn"} and ("tap" in preferred_sources or "burn" in preferred_sources):
        mult *= 1.14
    return mult, None

def enemy_base_hp(stage: int) -> float:
    # Longer fights from the first waves, then a much sharper ramp for build checks.
    wave = max(0, (stage - 1) // 10)
    intra_wave = max(0, (stage - 1) % 10)
    base = 72 * (1.9 ** wave) * (1.19 ** intra_wave)
    if wave >= 10:
        base *= 1.32 ** (wave - 9)
        base *= 1.05 ** intra_wave
    return base


def enemy_reward(stage: int) -> float:
    wave = max(0, (stage - 1) // 10)
    intra_wave = max(0, (stage - 1) % 10)
    return 8 * (1.48 ** wave) * (1.06 ** intra_wave)


def stage_kill_target(stage: int) -> int:
    return int(STAGE_KILL_TARGETS.get(stage_type(stage), 1))


def _pick_template(pool: list[dict[str, Any]], last_enemy_id: str | None = None, allowed_ids: list[str] | None = None) -> dict[str, Any]:
    if not pool:
        raise ValueError("Enemy pool is empty")
    candidates = list(pool)
    if allowed_ids:
        allowed = set(allowed_ids)
        filtered_allowed = [item for item in candidates if item.get("id") in allowed]
        if filtered_allowed:
            candidates = filtered_allowed
    if last_enemy_id and len(candidates) > 1:
        filtered = [item for item in candidates if item.get("id") != last_enemy_id]
        if filtered:
            candidates = filtered
    return random.choice(candidates)


def wave_slot_kind(wave_size: int, wave_slot: int) -> str:
    if wave_slot >= wave_size:
        return random.choice(["elite", "boss"])
    if wave_slot == max(1, wave_size - 1):
        return "elite"
    if wave_slot in {3, 4, 7}:
        return random.choice(["group", "normal"])
    return "normal"


def generate_enemy(
    stage: int,
    last_enemy_id: str | None = None,
    *,
    wave_theme_id: str | None = None,
    forced_kind: str | None = None,
    wave_slot: int | None = None,
    wave_size: int | None = None,
) -> dict[str, Any]:
    kind = forced_kind or stage_type(stage)
    theme = next((item for item in WAVE_ARCHETYPES if item["id"] == wave_theme_id), None) if wave_theme_id else None
    if kind == "boss":
        allowed = theme.get("boss_tags") if theme else None
        template = _pick_template(BOSSES, last_enemy_id=last_enemy_id, allowed_ids=allowed)
    elif kind == "elite":
        allowed = theme.get("elite_tags") if theme else None
        template = _pick_template(ELITES, last_enemy_id=last_enemy_id, allowed_ids=allowed)
    else:
        allowed = theme.get("enemy_tags") if theme else None
        template = _pick_template(ENEMIES, last_enemy_id=last_enemy_id, allowed_ids=allowed)

    base_hp = enemy_base_hp(stage)
    base_reward = enemy_reward(stage)
    modifiers = wave_modifier_for_theme(wave_theme_id)
    wave_pressure = 1.0 + max(0, int((wave_size or 1)) - 5) * 0.05 + max(0, int((wave_slot or 1)) - 1) * 0.015
    hp = base_hp * float(template.get("hp_mult", 1.0)) * float(modifiers.get("enemy_hp_mult", 1.0)) * wave_pressure
    reward = base_reward * float(template.get("reward_mult", 1.0)) * float(modifiers.get("reward_mult", 1.0))
    if kind == "group":
        hp *= 1.85 * float(modifiers.get("group_hp_mult", 1.0))
        reward *= 1.3
    if kind == "elite":
        hp *= 1.42
        reward *= 1.12
    if kind == "boss":
        hp *= 1.18
        reward *= 1.22

    attack_base = 2.8 * (1.082 ** max(0, stage - 1))
    attack_mult = {"normal": 1.0, "group": 0.84, "elite": 1.2, "boss": 1.52}[kind]
    attack_interval = {"normal": 3.05, "group": 2.25, "elite": 2.55, "boss": 2.1}[kind] * float(modifiers.get("enemy_attack_interval_mult", 1.0))
    attack_kind = {"normal": "bite", "group": "pack", "elite": "slam", "boss": "ritual"}[kind]

    group_count = int(modifiers.get("group_count", 4 if kind == "group" else 1)) if kind == "group" else 1
    enemy_name = template["name"] if kind != "group" else f"Стая · {template["name"]}"
    enemy_flavor = template.get("flavor", "") if kind != "group" else f"Идут пачкой. {template.get("flavor", "")}"

    enemy = {
        "id": template["id"],
        "name": enemy_name,
        "asset": template.get("asset"),
        "glyph": template.get("glyph", "✦"),
        "type": kind,
        "flavor": enemy_flavor,
        "mechanic": template.get("mechanic"),
        "mechanic_name": template.get("mechanic_name"),
        "mechanic_desc": template.get("mechanic_desc"),
        "hp": round(hp, 2),
        "max_hp": round(hp, 2),
        "reward": round(reward, 2),
        "count": group_count,
        "wave_theme_id": wave_theme_id or "",
        "theme_modifiers": modifiers,
        "attack_damage": round(attack_base * attack_mult * float(modifiers.get("enemy_attack_mult", 1.0)), 2),
        "attack_interval": attack_interval,
        "attack_kind": attack_kind,
        "wave_slot": int(wave_slot or 1),
        "wave_size": int(wave_size or 1),
        "theme_id": wave_theme_id,
    }
    return ensure_enemy_runtime_fields(enemy, stage)


def boss_shadow_active(enemy: dict[str, Any]) -> bool:
    if enemy.get("mechanic") != "shadow":
        return False
    spawned_at = float(enemy.get("spawned_at", time.time()))
    cycle = (time.time() - spawned_at) % 5.2
    return cycle < 1.9


def ritual_cycle_phase(enemy: dict[str, Any]) -> str:
    hp_ratio = float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0)))
    if hp_ratio > 0.75:
        return "fire"
    if hp_ratio > 0.5:
        return "air"
    if hp_ratio > 0.25:
        return "earth"
    return "water"


def enemy_phase_name(state: dict[str, Any]) -> str | None:
    enemy = state["enemy"]
    if enemy.get("type") != "boss":
        return None
    hp_ratio = float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0)))
    mechanic = enemy.get("mechanic")
    if mechanic == "shadow":
        return "Теневая фаза" if boss_shadow_active(enemy) else "Окно для DPS"
    if mechanic == "shield_hits":
        shield_hp = round(float(enemy.get("shield_hp", 0.0)), 1)
        shield_max = max(1.0, float(enemy.get("shield_max", 1.0)))
        return f"Каменный щит {shield_hp}/{round(shield_max, 1)}" if shield_hp > 0 else "Щит расколот"
    if mechanic == "combo_gate":
        seal_hits = int(enemy.get("seal_hits", 0))
        return f"Печать: {seal_hits} тяжёлых комбо" if seal_hits > 0 else "Печать сломана"
    if mechanic == "rage_phase":
        return "Спокойная фаза" if hp_ratio > 0.5 else "Ярость"
    if mechanic == "swipe_gate":
        return "Буря: нужны свайпы"
    if mechanic == "hold_gate":
        return "Узел: нужен hold"
    if mechanic == "burn_gate":
        return f"Жар на шкуре · огонь {int(enemy.get('burn_stacks', 0))}/6"
    if mechanic == "armor_gate":
        return f"Панцирь {round(float(enemy.get('armor', 0.0)), 1)}"
    if mechanic == "mirror_swipe":
        return "Ломает повтор одного направления"
    if mechanic == "ritual_cycle":
        return f"Фаза ритуала: {ritual_cycle_phase(enemy)}"
    if mechanic == "chain_breaker":
        return "Не любит повторы одного источника"
    return None


def enemy_status_text(state: dict[str, Any]) -> str | None:
    enemy = state["enemy"]
    if enemy.get("type") != "boss":
        return None
    mechanic = enemy.get("mechanic")
    hp_ratio = float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0)))
    if mechanic == "shadow":
        return "Сейчас в тени — тап вскрывает фазу, свайпы и hold почти тонут." if boss_shadow_active(enemy) else "Теневая фаза спала — можно вливать весь урон."
    if mechanic == "shield_hits":
        shield_hp = round(float(enemy.get("shield_hp", 0.0)), 1)
        return f"Каменный щит держится. Его режут свайпы через Землю. Осталось {shield_hp}." if shield_hp > 0 else "Щит разбит, теперь босса можно разваливать любыми связками."
    if mechanic == "combo_gate":
        seal_hits = int(enemy.get("seal_hits", 0))
        return f"Печать держится. Нужны тяжёлые земные DD или длинный RRUU. Осталось {seal_hits}." if seal_hits > 0 else "Печать осыпалась. Теперь можно вливать весь урон."
    if mechanic == "rage_phase":
        return "Сбей до половины HP, чтобы открыть яростную фазу под комбо." if hp_ratio > 0.5 else "Во второй фазе свайпы и hold заходят заметно больнее."
    if mechanic == "swipe_gate":
        return "Тап тонет в буре. Режь её свайпами, а воздушные комбо пробивают сильнее."
    if mechanic == "hold_gate":
        return "Узел слушается только удержания. Водные связки вливают заметно больнее."
    if mechanic == "burn_gate":
        return "Пока цель не горит всерьёз, обычные удары вязнут. Поджигай и раздувай огонь."
    if mechanic == "armor_gate":
        return "Каменный панцирь режет весь входящий урон. Земля и тяжёлые свайпы заходят лучше."
    if mechanic == "mirror_swipe":
        return "Один и тот же свайп подряд тухнет. Меняй направление и держи ритм."
    if mechanic == "ritual_cycle":
        return "Фазы меняются по HP: огонь → воздух → земля → вода. Читай бой, не долби в лоб."
    if mechanic == "chain_breaker":
        return "Повтор tap, swipe или hold штрафуется. Миксуй источники урона."
    return None


def ensure_enemy_runtime_fields(enemy: dict[str, Any], stage: int) -> dict[str, Any]:
    enemy.setdefault("spawned_at", time.time())
    enemy.setdefault("burn_stacks", 0)
    enemy.setdefault("burn_until", 0.0)
    enemy.setdefault("burn_tick_at", 0.0)
    enemy.setdefault("burn_power", 0.0)
    enemy.setdefault("last_attack_at", time.time())
    enemy.setdefault("attack_speed_mult", 1.0)
    enemy.setdefault("attack_damage_mult", 1.0)
    enemy.setdefault("combo_vuln_until", 0.0)
    enemy.setdefault("combo_vuln_mult", 1.0)
    enemy.setdefault("armor_exposed_until", 0.0)
    enemy.setdefault("armor_exposed_mult", 1.0)
    enemy.setdefault("gold_window_until", 0.0)
    enemy.setdefault("gold_window_mult", 1.0)
    enemy.setdefault("slow_until", 0.0)
    enemy.setdefault("slow_mult", 1.0)
    enemy.setdefault("recent_sources", [])
    enemy.setdefault("recent_swipes", [])
    if enemy.get("type") == "boss" and enemy.get("mechanic") == "shield_hits":
        theme_mod = enemy.get("theme_modifiers") or {}
        shield_value = float(enemy.get("shield_max") or (float(enemy.get("max_hp", 1.0)) * 0.28 * float(theme_mod.get("shield_mult", 1.0))))
        enemy.setdefault("shield_max", round(shield_value, 2))
        enemy.setdefault("shield_hp", round(shield_value, 2))
    if enemy.get("type") == "boss" and enemy.get("mechanic") == "combo_gate":
        seal_hits = int(enemy.get("seal_hits_max") or (2 + max(0, stage // 25)))
        enemy.setdefault("seal_hits_max", seal_hits)
        enemy.setdefault("seal_hits", seal_hits)
    if enemy.get("type") in {"elite", "boss"}:
        theme_mod = enemy.get("theme_modifiers") or {}
        base_armor = float(enemy.get("max_hp", 1.0)) * (0.2 if enemy.get("type") == "elite" else 0.26) * float(theme_mod.get("enemy_armor_mult", 1.0))
        enemy.setdefault("armor_max", round(base_armor, 2))
        enemy.setdefault("armor", round(base_armor, 2))
        enemy.setdefault("shatter_until", 0.0)
    return enemy


def damage_after_enemy_mechanics(state: dict[str, Any], damage: float, source: str, consume: bool = True, source_meta: dict[str, Any] | None = None) -> tuple[float, dict[str, Any]]:
    enemy = state["enemy"]
    info = {"blocked": False, "blocked_reason": None, "shield_hit": False, "seal_hit": False}
    final_damage = max(0.0, damage)
    source_meta = source_meta or {}

    mechanic = enemy.get("mechanic")
    hp_ratio = float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0)))
    pair_key = str(source_meta.get("pair_key") or "")
    combo_key = str(source_meta.get("combo_key") or "")
    earth_combo = pair_has_earth(pair_key)
    air_combo = "air" in pair_key
    water_combo = "water" in pair_key
    fire_combo = "fire" in pair_key
    combo_len = len(combo_key)
    theme_mod = enemy.get("theme_modifiers") or {}

    if source == "tap":
        final_damage *= float(theme_mod.get("tap_mult", 1.0))
    elif source == "swipe":
        final_damage *= float(theme_mod.get("swipe_mult", 1.0))
        if combo_len >= 2:
            final_damage *= float(theme_mod.get("combo_mult", 1.0))
    elif source == "hold":
        final_damage *= float(theme_mod.get("hold_mult", 1.0))
    elif source == "burn":
        final_damage *= float(theme_mod.get("burn_mult", 1.0))
    elif source == "dps":
        final_damage *= float(theme_mod.get("dps_mult", 1.0))

    if fire_combo:
        final_damage *= float(theme_mod.get("fire_pair_mult", 1.0))
    if water_combo:
        final_damage *= float(theme_mod.get("water_pair_mult", 1.0))
    if earth_combo:
        final_damage *= float(theme_mod.get("earth_pair_mult", 1.0))
    if air_combo:
        final_damage *= float(theme_mod.get("air_pair_mult", 1.0))
    if pair_key and pair_key != "solo":
        final_damage *= float(theme_mod.get("pair_mult", 1.0))
    if source == "tap" and source_meta.get("crit"):
        final_damage *= float(theme_mod.get("crit_mult", 1.0))

    late_pair_mult, late_pair_reason = late_wave_pair_multiplier(state, enemy, source, pair_key, combo_key)
    final_damage *= late_pair_mult
    if late_pair_reason:
        info["blocked"] = True
        info["blocked_reason"] = late_pair_reason

    if enemy.get("type") != "boss":
        return round(final_damage, 2), info

    if mechanic == "shadow" and boss_shadow_active(enemy):
        if source == "tap":
            final_damage *= 1.2
        elif source == "swipe":
            info["blocked"] = True
            info["blocked_reason"] = "shadow"
            final_damage *= 0.32
        elif source == "hold":
            info["blocked"] = True
            info["blocked_reason"] = "shadow"
            final_damage *= 0.24
        elif source == "dps":
            info["blocked"] = True
            info["blocked_reason"] = "shadow"
            return 0.0, info
        elif source == "burn":
            final_damage *= 0.38

    if mechanic == "shield_hits" and float(enemy.get("shield_hp", 0.0)) > 0:
        heavy_swipe = source == "swipe"
        info["shield_hit"] = True
        info["shield_only"] = True
        if not heavy_swipe:
            info["blocked"] = True
            info["blocked_reason"] = "shield"
        elif not earth_combo:
            info["blocked"] = True
            info["blocked_reason"] = "earth_shield"
        else:
            info["blocked_reason"] = "shield"
        if source == "swipe":
            final_damage *= 1.44 if earth_combo else 0.3
            if combo_len >= 4:
                final_damage *= 1.2
            elif combo_key == "DD":
                final_damage *= 1.15
        elif source == "hold":
            final_damage *= 0.16
        elif source == "dps":
            final_damage *= 0.08
        else:
            final_damage *= 0.12
        return round(final_damage, 2), info

    if mechanic == "combo_gate" and int(enemy.get("seal_hits", 0)) > 0:
        heavy_earth_combo = source == "swipe" and earth_combo and combo_key in {"DD", "RRUU"}
        if heavy_earth_combo:
            if consume:
                seal_before = int(enemy.get("seal_hits", 0))
                seal_drop = 2 if combo_key == "RRUU" else 1
                enemy["seal_hits"] = max(0, seal_before - seal_drop)
                if seal_before > 0 and int(enemy.get("seal_hits", 0)) <= 0:
                    enemy["gold_window_until"] = max(float(enemy.get("gold_window_until", 0.0)), time.time() + 5.0)
                    enemy["gold_window_mult"] = max(float(enemy.get("gold_window_mult", 1.0)), 1.25)
            info["seal_hit"] = True
            final_damage *= 1.34 if combo_key == "RRUU" else 1.24
        else:
            info["blocked"] = True
            info["blocked_reason"] = "combo_gate"
            return 0.0, info

    if mechanic == "rage_phase" and hp_ratio <= 0.5:
        if source == "swipe":
            final_damage *= 1.26 if combo_len >= 2 else 1.14
        elif source == "hold":
            final_damage *= 1.24
        else:
            final_damage *= 1.08
    elif mechanic == "swipe_gate":
        if source != "swipe":
            info["blocked"] = True
            info["blocked_reason"] = "swipe_gate"
            if source == "dps":
                return 0.0, info
            final_damage *= 0.1
        else:
            final_damage *= 1.24
            if air_combo:
                final_damage *= 1.2
            if combo_len >= 4:
                final_damage *= 1.16
            elif combo_len >= 2:
                final_damage *= 1.12
    elif mechanic == "hold_gate":
        if source != "hold":
            info["blocked"] = True
            info["blocked_reason"] = "hold_gate"
            if source == "dps":
                return 0.0, info
            final_damage *= 0.08
        else:
            if consume:
                enemy["armor_exposed_until"] = max(float(enemy.get("armor_exposed_until", 0.0)), time.time() + 3.2)
                enemy["armor_exposed_mult"] = max(float(enemy.get("armor_exposed_mult", 1.0)), 1.28)
            final_damage *= 1.18 * (1.22 if water_combo else 1.0)
    elif mechanic == "burn_gate":
        burn_stacks = int(enemy.get("burn_stacks", 0))
        if source == "burn":
            final_damage *= 1.7
        elif burn_stacks < 2:
            info["blocked"] = True
            info["blocked_reason"] = "burn_gate"
            if source == "dps":
                return 0.0, info
            final_damage *= 0.14
        else:
            final_damage *= 1.14 if fire_combo else 0.94
    elif mechanic == "armor_gate":
        armor_left = float(enemy.get("armor", 0.0))
        if armor_left > 0:
            if source == "swipe":
                final_damage *= 1.26 if earth_combo else 0.45
            elif source == "hold":
                final_damage *= 0.72 if water_combo and earth_combo else 0.38
            elif source == "tap":
                final_damage *= 0.3
            elif source == "dps":
                final_damage *= 0.42
        else:
            final_damage *= 1.15
    elif mechanic == "mirror_swipe":
        if source == "swipe":
            recent_swipes = list(enemy.get("recent_swipes", []))
            direction = str(source_meta.get("direction") or "")
            if recent_swipes and recent_swipes[-1] == direction:
                info["blocked"] = True
                info["blocked_reason"] = "mirror_repeat"
                final_damage *= 0.24
            else:
                final_damage *= 1.22 if air_combo else 1.02
            if consume and direction:
                recent_swipes.append(direction)
                enemy["recent_swipes"] = recent_swipes[-3:]
        else:
            final_damage *= 0.92
    elif mechanic == "ritual_cycle":
        phase = ritual_cycle_phase(enemy)
        if phase == "fire":
            final_damage *= 1.22 if source in {"tap", "burn"} or fire_combo else 0.74
        elif phase == "air":
            final_damage *= 1.22 if source == "swipe" or air_combo else 0.76
        elif phase == "earth":
            final_damage *= 1.24 if earth_combo else 0.72
        elif phase == "water":
            final_damage *= 1.24 if source == "hold" or water_combo else 0.74
    elif mechanic == "chain_breaker":
        recent_sources = list(enemy.get("recent_sources", []))
        repeated = len(recent_sources) >= 1 and recent_sources[-1] == source
        if repeated:
            info["blocked"] = True
            info["blocked_reason"] = "chain_repeat"
            final_damage *= 0.42
        else:
            final_damage *= 1.08
        if consume:
            recent_sources.append(source)
            enemy["recent_sources"] = recent_sources[-3:]

    return round(final_damage, 2), info
