from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import threading
import time
from typing import Any
from urllib.parse import parse_qsl

from fastapi import Request

from .content import BOT_TOKEN, DB_PATH, HEROES
from .enemies import generate_enemy
from .models import PlayerIdentity
from .player import sync_player_combat_stats
from .progression import update_records
from .state import default_state

player_locks_guard = threading.Lock()
player_locks: dict[str, threading.Lock] = {}

def get_player_lock(player_id: str) -> threading.Lock:
    with player_locks_guard:
        lock = player_locks.get(player_id)
        if lock is None:
            lock = threading.Lock()
            player_locks[player_id] = lock
        return lock


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
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_players_best_rank ON players(best_score DESC, best_stage DESC, trophies DESC, updated_at ASC)"
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


def merge_state(data: dict[str, Any]) -> dict[str, Any]:
    state = default_state()
    for key in state.keys():
        if key in {"enemy", "heroes", "rituals", "active_heroes"}:
            continue
        state[key] = data.get(key, state[key])
    state["heroes"].update(data.get("heroes", {}))
    active_heroes = data.get("active_heroes", [])
    if not isinstance(active_heroes, list):
        active_heroes = []
    valid_ids = {hero["id"] for hero in HEROES}
    normalized_active = []
    for hero_id in active_heroes:
        if hero_id in valid_ids and hero_id not in normalized_active and int(state["heroes"].get(hero_id, 0)) > 0:
            normalized_active.append(hero_id)
        if len(normalized_active) >= 2:
            break
    if not normalized_active:
        for hero in HEROES:
            if int(state["heroes"].get(hero["id"], 0)) > 0:
                normalized_active.append(hero["id"])
                if len(normalized_active) >= 2:
                    break
    state["active_heroes"] = normalized_active
    state["rituals"].update(data.get("rituals", {}))
    enemy = data.get("enemy") or generate_enemy(int(state["stage"]))
    if "hp" not in enemy or "max_hp" not in enemy:
        enemy = generate_enemy(int(state["stage"]))
    state["enemy"] = enemy
    state["last_tick"] = float(data.get("last_tick", time.time()))
    if not isinstance(state.get("top_runs"), list):
        state["top_runs"] = []
    swipe_history = data.get("swipe_history", [])
    if not isinstance(swipe_history, list):
        swipe_history = []
    valid_swipes = {"up", "down", "left", "right"}
    state["swipe_history"] = [item for item in swipe_history if item in valid_swipes][-6:]
    state["last_swipe_at"] = float(data.get("last_swipe_at", 0.0))
    state["last_hold_ms"] = int(data.get("last_hold_ms", 0))
    state["last_hold_at"] = float(data.get("last_hold_at", 0.0))
    state["player_hp"] = float(data.get("player_hp", state.get("player_hp", 0.0)))
    state["player_shield"] = float(data.get("player_shield", state.get("player_shield", 0.0)))
    state["player_last_hit_at"] = float(data.get("player_last_hit_at", 0.0))
    state["player_last_heal_at"] = float(data.get("player_last_heal_at", 0.0))
    state["player_last_shield_at"] = float(data.get("player_last_shield_at", 0.0))
    state["player_downs"] = int(data.get("player_downs", 0))
    sync_player_combat_stats(state)
    return state


def load_player_state(identity: PlayerIdentity) -> dict[str, Any]:
    row = load_player_row(identity.player_id)
    if row is None:
        state = default_state()
        save_player_state(identity, state)
        return state
    try:
        data = json.loads(row["state_json"])
        return merge_state(data)
    except Exception:
        state = default_state()
        save_player_state(identity, state)
        return state


def save_player_state(identity: PlayerIdentity, state: dict[str, Any]) -> None:
    sync_player_combat_stats(state)
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

