from __future__ import annotations

from typing import Any

from .content import HEROES, HERO_UNLOCK_COST, RITUALS
from .enemies import enemy_phase_name, enemy_status_text
from .heroes import (
    active_hero_ids,
    active_pair_key,
    blessing_level,
    blessing_synergies,
    build_active_heroes,
    crit_chance,
    crit_multiplier,
    gold_multiplier,
    hero_breakpoint_count,
    hero_cost,
    hero_level,
    hero_milestone_cards,
    hero_next_bonus_text,
    hero_passive_text,
    hero_personal_dps,
    is_hero_active,
    ritual_cost,
    ritual_level,
    tap_damage,
    total_blessing_levels,
    total_hero_dps,
    trophy_power_multiplier,
)
from .models import PlayerIdentity
from .progression import blessing_cost, build_achievements, rebirth_reward, rebirth_reward_breakdown, score_value, tap_upgrade_cost, wave_number
from .storage import fetch_leaderboard


BLESSING_DESCRIPTIONS = {
    "fire": "Тап, burn и добивание по раненым целям становятся злее.",
    "water": "Hold, лечение и устойчивость в затяжном бою заметно крепнут.",
    "earth": "Щиты, бронелом и урон по элиткам становятся тяжелее.",
    "air": "Свайпы, темп и длина комбо-окон растут с каждым даром.",
}

BLESSING_NAMES = {
    "fire": "Путь Огня",
    "water": "Путь Воды",
    "earth": "Путь Земли",
    "air": "Путь Ветра",
}


def build_payload(state: dict[str, Any], identity: PlayerIdentity, last_hit: dict[str, Any] | None = None) -> dict[str, Any]:
    enemy = state["enemy"]
    achievements = build_achievements(state)
    current_score = score_value(state, achievements["unlocked"])
    leaderboard = fetch_leaderboard(identity.player_id)
    rebirth_breakdown = rebirth_reward_breakdown(state)

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
                "milestones": hero_milestone_cards(hero["id"], level),
                "owned": level > 0,
                "selected": is_hero_active(state, hero["id"]),
                "unlock_cost": HERO_UNLOCK_COST,
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

    blessing_items = []
    for blessing_id in ("fire", "water", "earth", "air"):
        level = blessing_level(state, blessing_id)
        blessing_items.append(
            {
                "id": blessing_id,
                "name": BLESSING_NAMES[blessing_id],
                "desc": BLESSING_DESCRIPTIONS[blessing_id],
                "level": level,
                "cost": blessing_cost(level),
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
        "wave": int(state.get("wave_index", wave_number(int(state["stage"])))),
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
        "trophies_earned": int(state.get("total_trophies_earned", state.get("trophies", 0))),
        "rebirths": int(state.get("rebirths", 0)),
        "power_bonus": round((trophy_power_multiplier(state) - 1) * 100, 1),
        "rebirth_gain": rebirth_reward(state),
        "rebirth_breakdown": rebirth_breakdown,
        "score": current_score,
        "can_rebirth": rebirth_reward(state) > 0,
        "enemy": {
            "id": enemy["id"],
            "name": enemy["name"],
            "asset": enemy.get("asset"),
            "glyph": enemy.get("glyph", "✦"),
            "type": enemy["type"],
            "flavor": enemy.get("flavor", ""),
            "mechanic": enemy.get("mechanic"),
            "mechanic_name": enemy.get("mechanic_name"),
            "mechanic_desc": enemy.get("mechanic_desc"),
            "phase": enemy_phase_name(state),
            "status": enemy_status_text(state),
            "shield_hits": int(enemy.get("shield_hits", 0)),
            "shield_hits_max": int(enemy.get("shield_hits_max", 0)),
            "shield_hp": round(float(enemy.get("shield_hp", 0.0)), 2),
            "shield_max": round(float(enemy.get("shield_max", 0.0)), 2),
            "seal_hits": int(enemy.get("seal_hits", 0)),
            "seal_hits_max": int(enemy.get("seal_hits_max", 0)),
            "hp": round(enemy["hp"], 2),
            "max_hp": round(enemy["max_hp"], 2),
            "reward": round(enemy["reward"] * gold_multiplier(state), 2),
            "count": int(enemy.get("count", 1)),
            "armor": round(float(enemy.get("armor", 0.0)), 2),
            "armor_max": round(float(enemy.get("armor_max", 0.0)), 2),
            "burn_stacks": int(enemy.get("burn_stacks", 0)),
            "attack_damage": round(float(enemy.get("attack_damage", 0.0)), 2),
            "attack_interval": round(float(enemy.get("attack_interval", 0.0)), 2),
        },
        "high_shaman": {
            "hp": round(float(state.get("player_hp", 0.0)), 2),
            "max_hp": round(float(state.get("player_max_hp", 0.0)), 2),
            "hp_percent": round((float(state.get("player_hp", 0.0)) / max(1.0, float(state.get("player_max_hp", 1.0)))) * 100, 1),
            "shield": round(float(state.get("player_shield", 0.0)), 2),
            "max_shield": round(float(state.get("player_max_shield", 0.0)), 2),
            "shield_percent": round((float(state.get("player_shield", 0.0)) / max(1.0, float(state.get("player_max_shield", 1.0)))) * 100, 1) if float(state.get("player_max_shield", 0.0)) > 0 else 0.0,
            "defense": round(float(state.get("player_defense", 0.0)) * 100, 1),
            "regen": round(float(state.get("player_regen", 0.0)), 2),
            "heal_power": round((float(state.get("player_heal_power", 1.0)) - 1) * 100, 1),
            "downs": int(state.get("player_downs", 0)),
        },
        "heroes": hero_cards,
        "active_heroes": build_active_heroes(state),
        "active_hero_ids": active_hero_ids(state),
        "rituals": ritual_cards,
        "blessings": {
            "items": blessing_items,
            "synergies": blessing_synergies(state),
            "total_levels": total_blessing_levels(state),
        },
        "achievements": achievements,
        "top": {
            "score": current_score,
            "best_score": max(int(state.get("best_score", 0)), current_score),
            "top_runs": list(state.get("top_runs", [])),
            "leaderboard": leaderboard["items"],
            "my_rank": leaderboard["rank"],
        },
        "swipe_state": {
            "history": list(state.get("swipe_history", []))[-4:],
            "pair_key": active_pair_key(state),
        },
        "wave_state": {
            "index": int(state.get("wave_index", wave_number(int(state["stage"])))),
            "progress": int(state.get("wave_progress", 0)),
            "size": int(state.get("wave_size", 0)),
            "in_progress": bool(state.get("wave_in_progress", False)),
            "waiting": bool(state.get("wave_waiting", False)),
            "location": str(state.get("wave_location", "Степь")),
            "hint": str(state.get("wave_hint", "")),
            "recommended_pairs": list(state.get("wave_recommended_pairs", [])),
            "theme_id": str(state.get("wave_theme_id", "")),
        },
        "hold_state": {
            "last_hold_ms": int(state.get("last_hold_ms", 0)),
            "pair_key": active_pair_key(state),
            "water_active": is_hero_active(state, "water"),
            "earth_active": is_hero_active(state, "earth"),
        },
        "last_rebirth_summary": state.get("last_rebirth_summary"),
        "last_hit": last_hit,
    }

