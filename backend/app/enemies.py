from __future__ import annotations

import random
import time
from typing import Any

from .content import BOSSES, ELITES, ENEMIES
from .heroes import active_pair_key, is_hero_active, pair_has_earth

def stage_type(stage: int) -> str:
    if stage % 10 == 0:
        return "boss"
    if stage % 5 == 0:
        return "elite"
    if stage % 3 == 0:
        return "group"
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
    if kind == "group":
        hp *= 1.65
        reward *= 1.28
    if kind == "boss":
        reward *= 1.3

    attack_base = 3.8 * (1.16 ** max(0, stage - 1))
    attack_mult = {"normal": 1.0, "group": 0.72, "elite": 1.6, "boss": 2.35}[kind]
    attack_interval = {"normal": 2.6, "group": 1.85, "elite": 2.15, "boss": 1.7}[kind]
    attack_kind = {"normal": "bite", "group": "pack", "elite": "slam", "boss": "ritual"}[kind]

    enemy = {
        "id": template["id"],
        "name": template["name"],
        "asset": template.get("asset"),
        "glyph": template.get("glyph", "✦"),
        "type": kind,
        "flavor": template.get("flavor", ""),
        "mechanic": template.get("mechanic"),
        "mechanic_name": template.get("mechanic_name"),
        "mechanic_desc": template.get("mechanic_desc"),
        "hp": round(hp, 2),
        "max_hp": round(hp, 2),
        "reward": round(reward, 2),
        "count": 4 if kind == "group" else 1,
        "attack_damage": round(attack_base * attack_mult, 2),
        "attack_interval": attack_interval,
        "attack_kind": attack_kind,
    }
    return ensure_enemy_runtime_fields(enemy, stage)


def boss_shadow_active(enemy: dict[str, Any]) -> bool:
    if enemy.get("mechanic") != "shadow":
        return False
    spawned_at = float(enemy.get("spawned_at", time.time()))
    cycle = (time.time() - spawned_at) % 4.8
    return cycle < 1.8


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
    return None


def enemy_status_text(state: dict[str, Any]) -> str | None:
    enemy = state["enemy"]
    if enemy.get("type") != "boss":
        return None
    mechanic = enemy.get("mechanic")
    hp_ratio = float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0)))
    if mechanic == "shadow":
        return "Сейчас в тени — бей тапом." if boss_shadow_active(enemy) else "Теневая фаза спала — можно вливать DPS."
    if mechanic == "shield_hits":
        shield_hp = round(float(enemy.get("shield_hp", 0.0)), 1)
        return f"Каменный щит держится. Земные связки ломают его нормально, без Земли идёт крошка. Осталось {shield_hp}." if shield_hp > 0 else "Щит разбит, теперь босса можно разваливать любыми связками."
    if mechanic == "combo_gate":
        seal_hits = int(enemy.get("seal_hits", 0))
        return f"Печать держится. Нужны тяжёлые свайпы вниз через земные связки. Осталось {seal_hits}." if seal_hits > 0 else "Печать осыпалась. Теперь можно вливать весь урон."
    if mechanic == "rage_phase":
        return "Сбей до половины HP, чтобы открыть яростную фазу." if hp_ratio > 0.5 else "Во второй фазе получает больше урона."
    if mechanic == "swipe_gate":
        return "Тап тонет в буре. Режь её свайпами, а воздушные комбо пробивают сильнее."
    if mechanic == "hold_gate":
        return "Узел слушается только удержания и водных связок."
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
    if enemy.get("type") == "boss" and enemy.get("mechanic") == "shield_hits":
        shield_value = float(enemy.get("shield_max") or (float(enemy.get("max_hp", 1.0)) * 0.42))
        enemy.setdefault("shield_max", round(shield_value, 2))
        enemy.setdefault("shield_hp", round(shield_value, 2))
    if enemy.get("type") == "boss" and enemy.get("mechanic") == "combo_gate":
        seal_hits = int(enemy.get("seal_hits_max") or (3 + max(0, stage // 20)))
        enemy.setdefault("seal_hits_max", seal_hits)
        enemy.setdefault("seal_hits", seal_hits)
    if enemy.get("type") in {"elite", "boss"}:
        base_armor = float(enemy.get("max_hp", 1.0)) * (0.22 if enemy.get("type") == "elite" else 0.34)
        enemy.setdefault("armor_max", round(base_armor, 2))
        enemy.setdefault("armor", round(base_armor, 2))
        enemy.setdefault("shatter_until", 0.0)
    return enemy


def damage_after_enemy_mechanics(state: dict[str, Any], damage: float, source: str, consume: bool = True, source_meta: dict[str, Any] | None = None) -> tuple[float, dict[str, Any]]:
    enemy = state["enemy"]
    info = {"blocked": False, "blocked_reason": None, "shield_hit": False, "seal_hit": False}
    final_damage = max(0.0, damage)
    source_meta = source_meta or {}

    if enemy.get("type") != "boss":
        return final_damage, info

    mechanic = enemy.get("mechanic")
    hp_ratio = float(enemy.get("hp", 0.0)) / max(1.0, float(enemy.get("max_hp", 1.0)))

    if mechanic == "shadow" and source == "dps" and boss_shadow_active(enemy):
        info["blocked"] = True
        info["blocked_reason"] = "shadow"
        return 0.0, info

    if mechanic == "shield_hits" and float(enemy.get("shield_hp", 0.0)) > 0:
        pair_key = str(source_meta.get("pair_key") or "")
        earth_combo = pair_has_earth(pair_key)
        info["shield_hit"] = True
        info["shield_only"] = True
        info["earth_combo"] = earth_combo
        info["blocked_reason"] = "shield" if earth_combo else "earth_shield"
        if not earth_combo:
            info["blocked"] = True
        if source == "burn":
            final_damage *= 0.08
        elif source == "dps":
            final_damage *= 0.32 if earth_combo else 0.08
        elif source in {"tap", "swipe", "hold"}:
            final_damage *= 1.0 if earth_combo else 0.14
        else:
            final_damage *= 0.12
        return round(final_damage, 2), info

    if mechanic == "combo_gate" and int(enemy.get("seal_hits", 0)) > 0:
        combo_key = str(source_meta.get("combo_key") or "")
        pair_key = str(source_meta.get("pair_key") or "")
        allowed = source == "swipe" and combo_key == "DD" and pair_key in {"fire_earth", "air_earth", "water_earth"}
        if allowed:
            if consume:
                enemy["seal_hits"] = max(0, int(enemy.get("seal_hits", 0)) - 1)
            info["seal_hit"] = True
            final_damage *= 1.35
        else:
            info["blocked"] = True
            info["blocked_reason"] = "combo_gate"
            return 0.0, info

    if mechanic == "rage_phase" and hp_ratio <= 0.5:
        final_damage *= 1.35
    elif mechanic == "swipe_gate":
        pair_key = str(source_meta.get("pair_key") or "")
        if source != "swipe":
            info["blocked"] = True
            info["blocked_reason"] = "swipe_gate"
            return 0.0, info
        if pair_key in {"fire_air", "air_water", "air_earth"}:
            final_damage *= 1.28
        elif pair_key == "solo" or "air" in pair_key:
            final_damage *= 1.12
    elif mechanic == "hold_gate":
        pair_key = str(source_meta.get("pair_key") or "")
        if source == "hold":
            final_damage *= 1.22
        elif source == "swipe" and pair_key in {"air_water", "fire_water", "water_earth"}:
            final_damage *= 1.08
        else:
            info["blocked"] = True
            info["blocked_reason"] = "hold_gate"
            return 0.0, info

    return round(final_damage, 2), info

