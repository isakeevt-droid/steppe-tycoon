from __future__ import annotations

import random
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .combat import apply_burn, apply_damage, advance_state, elemental_visual_for_state, hold_damage_value, register_swipe_combo, swipe_damage_value
from .content import ASSETS_DIR, FRONTEND_DIR, HOLD_MAX_MS, HOLD_MIN_MS
from .heroes import active_hero_ids, active_pair_key, base_tap_damage, crit_chance, crit_multiplier, hero_cost, hero_level, is_hero_active, ritual_cost, ritual_level, tap_damage, total_hero_dps
from .models import BuyRequest, HoldRequest, PlayerIdentity, SwipeRequest
from .payloads import build_payload
from .player import apply_heal_to_player, apply_shield_to_player
from .progression import build_achievements, push_top_run, rebirth_reward, tap_upgrade_cost, wave_number
from .storage import fetch_leaderboard, get_identity, get_player_lock, init_db, load_player_state, save_player_state

app = FastAPI(title="Steppe Shaman")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


def with_player_state(request: Request) -> tuple[PlayerIdentity, dict[str, Any]]:
    identity = get_identity(request)
    state = load_player_state(identity)
    return identity, state

@app.get("/api/state")
def get_state(request: Request) -> JSONResponse:
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
        progress = advance_state(state)
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity, progress))


@app.get("/api/leaderboard")
def get_leaderboard(request: Request) -> JSONResponse:
    identity = get_identity(request)
    return JSONResponse(fetch_leaderboard(identity.player_id))


@app.post("/api/tap")
def tap_enemy(request: Request) -> JSONResponse:
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
        advance_state(state)
        raw_damage = base_tap_damage(state)
        crit = random.random() < crit_chance(state)
        if crit:
            raw_damage *= crit_multiplier(state)
        raw_damage = round(raw_damage, 2)
        hit_result = apply_damage(state, raw_damage, source="tap", source_meta={"pair_key": active_pair_key(state)})
        if crit:
            apply_burn(state, raw_damage, "tap")
        hit_result["damage"] = raw_damage
        hit_result["crit"] = crit
        hit_result["source"] = "tap"
        hit_result["combo_visual"] = elemental_visual_for_state(state, "tap")
        hit_result["visual"] = hit_result["combo_visual"]
        hit_result["combo_name"] = "Стихийный удар" if active_hero_ids(state) else "Удар"
        hit_result["combo_effect"] = "Тап бьёт в теме активных шаманов." if active_hero_ids(state) else "Обычный удар верховного шамана."
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity, hit_result))


@app.post("/api/swipe")
def swipe_enemy(request: Request, req: SwipeRequest) -> JSONResponse:
    identity = get_identity(request)
    direction = (req.direction or "").lower().strip()
    if direction not in {"up", "down", "left", "right"}:
        return JSONResponse({"error": "invalid_direction"}, status_code=400)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
        advance_state(state)
        combo_key, history, combo, pair_key = register_swipe_combo(state, direction)
        raw_damage, armor_mult = swipe_damage_value(state, direction, combo)
        hit_result = apply_damage(state, raw_damage, source="swipe", source_meta={"pair_key": pair_key, "combo_key": combo_key, "direction": direction})
        if is_hero_active(state, "fire") and (combo is not None or direction in {"up", "right"}):
            apply_burn(state, raw_damage, "swipe")
        hit_result["damage"] = raw_damage
        hit_result["crit"] = False
        hit_result["source"] = "swipe"
        hit_result["swipe_direction"] = direction
        hit_result["swipe_history"] = history[-4:]
        hit_result["combo_key"] = combo_key
        hit_result["combo_name"] = combo.get("name") if combo else None
        hit_result["combo_effect"] = combo.get("effect") if combo else None
        hit_result["combo_visual"] = combo.get("visual") if combo else elemental_visual_for_state(state, "swipe")
        hit_result["visual"] = hit_result["combo_visual"]
        hit_result["pair_key"] = pair_key
        hit_result["armor_mult"] = armor_mult
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity, hit_result))


@app.post("/api/hold")
def hold_enemy(request: Request, req: HoldRequest) -> JSONResponse:
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
        advance_state(state)
        duration_ms = max(HOLD_MIN_MS, min(HOLD_MAX_MS, int(req.duration_ms)))
        raw_damage, meta = hold_damage_value(state, duration_ms)
        hit_result = apply_damage(state, raw_damage, source="hold", source_meta={"pair_key": meta["pair_key"], "hold_ms": duration_ms})
        if is_hero_active(state, "fire"):
            apply_burn(state, raw_damage, "hold")
        state["last_hold_ms"] = duration_ms
        state["last_hold_at"] = time.time()
        hit_result["damage"] = raw_damage
        hit_result["crit"] = False
        hit_result["source"] = "hold"
        hit_result["hold_ms"] = duration_ms
        hit_result["hold_ticks"] = meta["ticks"]
        hit_result["hold_charge"] = meta["charge"]
        healed = apply_heal_to_player(state, meta.get("heal_amount", 0.0), source="hold")
        shielded = apply_shield_to_player(state, meta.get("shield_amount", 0.0), source="hold")
        hit_result["player_healed"] = round(float(hit_result.get("player_healed", 0.0)) + healed, 2)
        hit_result["player_shielded"] = round(float(hit_result.get("player_shielded", 0.0)) + shielded, 2)
        hit_result["combo_name"] = "Поток" if is_hero_active(state, "water") else "Удержание"
        hit_result["combo_effect"] = meta["effect"]
        hit_result["combo_visual"] = meta["visual"]
        hit_result["hold_visual"] = meta["visual"]
        hit_result["pair_key"] = meta["pair_key"]
        hit_result["heal_amount"] = meta.get("heal_amount", 0.0)
        hit_result["shield_amount"] = meta.get("shield_amount", 0.0)
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity, hit_result))


@app.post("/api/buy-hero")
def buy_hero(request: Request, req: BuyRequest) -> JSONResponse:
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
        advance_state(state)
        if req.id not in state["heroes"]:
            return JSONResponse({"error": "unknown_hero"}, status_code=400)
        cost = hero_cost(req.id, hero_level(state, req.id))
        if state["gold"] < cost:
            return JSONResponse({"error": "not_enough_gold"}, status_code=400)
        state["gold"] -= cost
        state["heroes"][req.id] += 1
        active_ids = active_hero_ids(state)
        if req.id not in active_ids and len(active_ids) < 2:
            state.setdefault("active_heroes", []).append(req.id)
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.post("/api/buy-ritual")
def buy_ritual(request: Request, req: BuyRequest) -> JSONResponse:
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
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


@app.post("/api/toggle-active-hero")
def toggle_active_hero(request: Request, req: BuyRequest) -> JSONResponse:
    identity, state = with_player_state(request)
    with get_player_lock(identity.player_id):
        advance_state(state)
        if req.id not in state["heroes"]:
            return JSONResponse({"error": "unknown_hero"}, status_code=400)
        if hero_level(state, req.id) <= 0:
            return JSONResponse({"error": "hero_not_owned"}, status_code=400)
        active_ids = active_hero_ids(state)
        if req.id in active_ids:
            state["active_heroes"] = [hero_id for hero_id in active_ids if hero_id != req.id]
        else:
            if len(active_ids) >= 2:
                return JSONResponse({"error": "circle_full"}, status_code=400)
            state["active_heroes"] = active_ids + [req.id]
        save_player_state(identity, state)
        return JSONResponse(build_payload(state, identity))


@app.post("/api/upgrade-tap")
def upgrade_tap(request: Request) -> JSONResponse:
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
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
    identity = get_identity(request)
    with get_player_lock(identity.player_id):
        state = load_player_state(identity)
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


@app.get('/favicon.ico')
def favicon() -> JSONResponse:
    return JSONResponse({}, status_code=204)
