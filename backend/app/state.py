from __future__ import annotations

import time
from typing import Any

from .content import HEROES, RITUALS
from .enemies import generate_enemy
from .player import sync_player_combat_stats

def default_state() -> dict[str, Any]:
    state = {
        "gold": 0.0,
        "stage": 1,
        "kills": 0,
        "boss_kills": 0,
        "last_tick": time.time(),
        "tap_level": 1,
        "heroes": {hero["id"]: 0 for hero in HEROES},
        "active_heroes": [],
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
        "swipe_history": [],
        "last_swipe_at": 0.0,
        "last_hold_ms": 0,
        "last_hold_at": 0.0,
        "player_hp": 0.0,
        "player_max_hp": 0.0,
        "player_defense": 0.0,
        "player_regen": 0.0,
        "player_heal_power": 0.0,
        "player_shield": 0.0,
        "player_max_shield": 0.0,
        "player_shield_regen": 0.0,
        "player_last_hit_at": 0.0,
        "player_last_heal_at": 0.0,
        "player_last_shield_at": 0.0,
        "player_downs": 0,
    }
    state["enemy"] = generate_enemy(state["stage"])
    sync_player_combat_stats(state, refill=True)
    return state

