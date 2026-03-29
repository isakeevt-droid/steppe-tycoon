from __future__ import annotations

import math
from typing import Any

from .heroes import tap_damage, total_hero_dps

def wave_number(stage: int) -> int:
    return math.ceil(stage / 10)


def award_gold(state: dict[str, Any], amount: float) -> None:
    wave_bonus = 1.0 + max(0, int(state.get("wave_index", 1)) - 1) * 0.05
    total_amount = amount * wave_bonus
    state["gold"] += total_amount
    state["lifetime_gold"] = float(state.get("lifetime_gold", 0.0)) + total_amount


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
        return float(state.get("total_trophies_earned", state.get("trophies", 0)))
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
        + int(state.get("total_trophies_earned", state.get("trophies", 0))) * 1000
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

def tap_upgrade_cost(state: dict[str, Any]) -> float:
    return 18 * (1.18 ** max(0, state["tap_level"] - 1))




def blessing_cost(level: int) -> int:
    return int(3 + max(0, level) ** 2 + max(0, level) * 2)


def rebirth_reward_breakdown(state: dict[str, Any]) -> dict[str, int]:
    stage = int(state.get("stage", 1))
    bosses = int(state.get("boss_kills", 0))
    wave = wave_number(stage)
    stage_needed = max(0, 25 - stage)
    if stage < 25:
        return {
            "depth": 0,
            "boss": bosses,
            "wave": 0,
            "elite": 0,
            "stage_needed": stage_needed,
            "total": 0,
        }

    depth = max(1, int(((stage - 20) / 10) ** 1.6))
    boss_bonus = bosses
    wave_bonus = max(0, wave - 2)
    elite_bonus = max(0, stage // 15)
    total = max(1, depth + boss_bonus + wave_bonus + elite_bonus)
    best_stage = max(1, int(state.get("best_stage", stage)))
    run_ratio = stage / best_stage
    if run_ratio < 0.6:
        total = max(1, int(total * 0.5))
    elif run_ratio < 0.85:
        total = max(1, int(total * 0.75))

    return {
        "depth": depth,
        "boss": boss_bonus,
        "wave": wave_bonus,
        "elite": elite_bonus,
        "stage_needed": 0,
        "total": total,
    }

def rebirth_reward(state: dict[str, Any]) -> int:
    return int(rebirth_reward_breakdown(state)["total"])

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

