#!/usr/bin/env python3
"""FSRS-6 Spaced Repetition Engine for /review skill.

Pure Python CLI — only uses stdlib (math, json, sys, datetime, os, tempfile).
CC calls this via Bash; all state persisted in a JSON file.

Usage:
    python3 fsrs_engine.py <state_file> <command> [args]

Commands:
    due              --limit N              Up to N due cards, sorted by urgency
    record           --id ID --rating 1-4   Record review result
    register         --id ID --title T --content C   Register one card
    bulk_register                           Register cards from stdin JSON
    record_session                          Record session summary from stdin JSON
    stats                                   Print statistics
"""

import json
import math
import os
import sys
import tempfile
from datetime import datetime, date, timedelta

# ── FSRS-6 Default Parameters (w[0]..w[20]) ─────────────────────
# Source: open-spaced-repetition/py-fsrs official defaults

DEFAULT_W = [
    0.2172,   # w0:  S₀(Again) — initial stability after Again
    1.2931,   # w1:  S₀(Hard)
    2.3065,   # w2:  S₀(Good)
    8.2956,   # w3:  S₀(Easy)
    6.4133,   # w4:  D₀ base — initial difficulty center
    0.8334,   # w5:  D₀ grade scaling
    3.0194,   # w6:  difficulty delta coefficient
    0.001,    # w7:  mean reversion weight
    1.8722,   # w8:  SInc base (used as exp(w[8]))
    0.1666,   # w9:  difficulty exponent on SInc
    0.796,    # w10: stability decay exponent on SInc
    1.4835,   # w11: retrievability exponent on SInc / SFail base
    0.0614,   # w12: difficulty exponent on SFail
    0.2629,   # w13: stability exponent on SFail
    1.6483,   # w14: retrievability exponent on SFail
    0.6014,   # w15: hard penalty
    1.8729,   # w16: easy bonus
    0.5425,   # w17: short-term stability parameter
    0.0912,   # w18: short-term grade factor
    0.0658,   # w19: short-term decay
    0.1542,   # w20: forgetting curve decay exponent
]

DEFAULT_TARGET_RETENTION = 0.9
DEFAULT_MAX_INTERVAL = 365


# ── Core FSRS-6 Math ──────────────────────────────────────────────

def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _factor(w20):
    """Derive factor from w[20] so that R(S, S) = 0.9.

    factor = 0.9^(-1/w20) - 1
    """
    if w20 <= 0:
        return 19.0 / 81.0  # fallback to FSRS-5
    return math.pow(0.9, -1.0 / w20) - 1.0


def init_difficulty(w, rating):
    """D₀(G) = w[4] - exp(w[5] * (G - 1)) + 1, clamped [1, 10]."""
    return clamp(w[4] - math.exp(w[5] * (rating - 1)) + 1, 1.0, 10.0)


def init_stability(w, rating):
    """S₀(G) = w[G-1] for G in {1,2,3,4}."""
    return max(w[rating - 1], 0.01)


def retrievability(t_days, stability, w20):
    """FSRS-6 power-law forgetting curve.

    R(t, S) = (1 + factor * t / S)^(-w20)
    """
    if stability <= 0:
        return 0.0
    factor = _factor(w20)
    return math.pow(1.0 + factor * t_days / stability, -w20)


def next_interval(stability, w20, target_r, max_iv):
    """Invert forgetting curve for t.

    I = S / factor * (R^(-1/w20) - 1)
    """
    if target_r <= 0 or target_r >= 1:
        return 1
    factor = _factor(w20)
    iv = stability / factor * (math.pow(target_r, -1.0 / w20) - 1.0)
    return clamp(round(iv), 1, max_iv)


def next_difficulty(w, d, rating):
    """Mean-reverting difficulty update with linear damping.

    delta_D = -w[6] * (G - 3)
    D'  = D + delta_D * (10 - D) / 9
    D'' = w[7] * D₀(4) + (1 - w[7]) * D'
    """
    d0_easy = init_difficulty(w, 4)
    delta_d = -w[6] * (rating - 3)
    d_prime = d + delta_d * (10.0 - d) / 9.0
    return clamp(w[7] * d0_easy + (1 - w[7]) * d_prime, 1.0, 10.0)


def next_stability_success(w, d, s, r, rating):
    """Stability after successful review (rating >= 2).

    S' = S * (e^w[8] * (11-D)^w[9] * S^(-w[10])
              * (e^(w[11]*(1-R)) - 1) * penalty * bonus + 1)
    """
    hard_penalty = w[15] if rating == 2 else 1.0
    easy_bonus = w[16] if rating == 4 else 1.0

    s_inc = (
        math.exp(w[8])
        * math.pow(11 - d, w[9])
        * math.pow(s, -w[10])
        * (math.exp(w[11] * (1 - r)) - 1)
        * hard_penalty
        * easy_bonus
    )
    return max(s * (s_inc + 1), 0.01)


def next_stability_forget(w, d, s, r):
    """Stability after forgetting (rating == 1).

    S' = w[11] * D^(-w[12]) * ((S+1)^w[13] - 1) * e^(w[14]*(1-R))
    """
    new_s = (
        w[11]
        * math.pow(d, -w[12])
        * (math.pow(s + 1, w[13]) - 1)
        * math.exp(w[14] * (1 - r))
    )
    return clamp(new_s, 0.01, s)  # never exceed previous stability


# ── State File I/O ────────────────────────────────────────────────

def empty_state():
    return {
        "version": 1,
        "params": {
            "w": list(DEFAULT_W),
            "target_retention": DEFAULT_TARGET_RETENTION,
            "max_interval_days": DEFAULT_MAX_INTERVAL,
        },
        "cards": {},
        "scan_history": {
            "last_scan": None,
            "known_card_ids": [],
        },
        "session_history": [],
    }


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return empty_state()


def save_state(path, state):
    """Atomic write: write to temp file then rename."""
    abs_path = os.path.abspath(path)
    dir_ = os.path.dirname(abs_path)
    os.makedirs(dir_, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, abs_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── Commands ──────────────────────────────────────────────────────

def cmd_due(state, limit):
    """Return up to `limit` due cards sorted by urgency (lowest R first)."""
    today = date.today().isoformat()
    w = state["params"]["w"]
    w20 = w[20] if len(w) > 20 else 0.5
    due_cards = []

    for cid, card in state["cards"].items():
        # New cards are always "due"
        if card["state"] == "new":
            due_cards.append({
                "id": cid,
                "title": card["title"],
                "state": card["state"],
                "retrievability": 0.0,
                "due_date": card["due_date"],
                "reps": card["reps"],
                "stability": card["stability"],
                "difficulty": card["difficulty"],
                "overdue_days": 0,
            })
            continue

        # Check if due
        if card["due_date"] > today:
            continue

        # Compute current retrievability
        if card["last_review"]:
            elapsed = (date.today() - date.fromisoformat(card["last_review"])).days
        else:
            elapsed = 0
        r = retrievability(elapsed, card["stability"], w20)

        overdue = (date.today() - date.fromisoformat(card["due_date"])).days

        due_cards.append({
            "id": cid,
            "title": card["title"],
            "state": card["state"],
            "retrievability": round(r, 4),
            "due_date": card["due_date"],
            "reps": card["reps"],
            "stability": round(card["stability"], 2),
            "difficulty": round(card["difficulty"], 2),
            "overdue_days": overdue,
        })

    # Sort: learning (reinforcement) > review (scheduled) > new (unseen)
    # Within each group, sort by retrievability ascending (most urgent first)
    state_priority = {"learning": 0, "review": 1, "new": 2}
    due_cards.sort(key=lambda c: (state_priority.get(c["state"], 2), c["retrievability"]))
    return due_cards[:limit]


def cmd_record(state, card_id, rating):
    """Record a review result and update FSRS state."""
    if card_id not in state["cards"]:
        return {"error": f"Card not found: {card_id}"}

    card = state["cards"][card_id]
    w = state["params"]["w"]
    w20 = w[20] if len(w) > 20 else 0.5
    target_r = state["params"]["target_retention"]
    max_iv = state["params"]["max_interval_days"]
    today_str = date.today().isoformat()

    # Compute elapsed days
    if card["last_review"]:
        elapsed = (date.today() - date.fromisoformat(card["last_review"])).days
    else:
        elapsed = 0

    # Current retrievability
    r = retrievability(elapsed, card["stability"], w20) if card["stability"] > 0 else 0.0

    # Save pre-update values for log and stability calc
    d_before = card["difficulty"]
    s_before = card["stability"]

    if card["state"] == "new":
        # First review: initialize
        card["difficulty"] = init_difficulty(w, rating)
        card["stability"] = init_stability(w, rating)
        card["state"] = "learning" if rating == 1 else "review"
    else:
        # Compute new difficulty (but use d_before for stability calc)
        new_d = next_difficulty(w, d_before, rating)

        # Update stability using PRE-UPDATE difficulty
        if rating == 1:
            card["stability"] = next_stability_forget(w, d_before, s_before, r)
            card["lapses"] += 1
            card["state"] = "learning"
        else:
            card["stability"] = next_stability_success(
                w, d_before, s_before, r, rating
            )
            card["state"] = "review"

        # Now apply the new difficulty
        card["difficulty"] = new_d

    # Compute next interval and due date
    iv = next_interval(card["stability"], w20, target_r, max_iv)
    card["due_date"] = (date.today() + timedelta(days=iv)).isoformat()
    card["last_review"] = today_str
    card["reps"] += 1

    # Append to review log
    log_entry = {
        "date": today_str,
        "rating": rating,
        "elapsed_days": elapsed,
        "retrievability": round(r, 4),
        "stability_before": round(s_before, 4),
        "stability_after": round(card["stability"], 4),
        "difficulty_before": round(d_before, 4),
        "difficulty_after": round(card["difficulty"], 4),
        "interval": iv,
    }
    card["review_log"].append(log_entry)

    rating_labels = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
    return {
        "id": card_id,
        "title": card["title"],
        "rating": rating_labels[rating],
        "interval_days": iv,
        "due_date": card["due_date"],
        "stability": round(card["stability"], 2),
        "difficulty": round(card["difficulty"], 2),
        "retrievability": round(r, 4),
    }


def cmd_register(state, card_id, title, content):
    """Register a single new card."""
    if card_id in state["cards"]:
        return {"status": "exists", "id": card_id, "title": state["cards"][card_id]["title"]}

    # Ensure title and content are strings
    if not isinstance(title, str):
        title = str(title) if title else ""
    if not isinstance(content, str):
        content = str(content) if content else ""

    # Truncate content to first 500 chars for snippet
    snippet = content[:500] if len(content) > 500 else content

    state["cards"][card_id] = {
        "title": title,
        "content_snippet": snippet,
        "state": "new",
        "difficulty": 0.0,
        "stability": 0.0,
        "due_date": date.today().isoformat(),
        "last_review": None,
        "reps": 0,
        "lapses": 0,
        "review_log": [],
    }

    # Track in scan history
    if card_id not in state["scan_history"]["known_card_ids"]:
        state["scan_history"]["known_card_ids"].append(card_id)

    return {"status": "registered", "id": card_id, "title": title}


def cmd_bulk_register(state, cards_data):
    """Register multiple cards. Input: list of {id, title, content}."""
    results = []
    skipped = 0
    for card in cards_data:
        cid = card.get("id")
        if not cid:
            skipped += 1
            continue
        title = card.get("title", "")
        content = card.get("content", "")
        r = cmd_register(state, cid, title, content)
        results.append(r)

    state["scan_history"]["last_scan"] = datetime.now().isoformat()
    new_count = sum(1 for r in results if r["status"] == "registered")
    existing_count = sum(1 for r in results if r["status"] == "exists")

    return {
        "total": len(results),
        "new": new_count,
        "existing": existing_count,
        "skipped": skipped,
        "cards": results,
    }


def cmd_record_session(state, session_data):
    """Record a review session summary."""
    state["session_history"].append(session_data)
    return {
        "status": "ok",
        "total_sessions": len(state["session_history"]),
    }


def cmd_stats(state):
    """Output statistics about the card pool."""
    cards = state["cards"]
    total = len(cards)
    w = state["params"]["w"]
    w20 = w[20] if len(w) > 20 else 0.5

    if total == 0:
        return {
            "total_cards": 0,
            "by_state": {},
            "due_today": 0,
            "next_due": None,
            "avg_difficulty": 0,
            "avg_stability": 0,
            "total_reviews": 0,
            "known_card_ids": state["scan_history"]["known_card_ids"],
            "last_scan": state["scan_history"]["last_scan"],
        }

    today = date.today().isoformat()

    by_state = {}
    due_today = 0
    difficulties = []
    stabilities = []
    total_reviews = 0
    next_due_date = None

    for cid, card in cards.items():
        s = card["state"]
        by_state[s] = by_state.get(s, 0) + 1

        if card["due_date"] <= today:
            due_today += 1

        if card["state"] != "new":
            difficulties.append(card["difficulty"])
            stabilities.append(card["stability"])

        total_reviews += card["reps"]

        # Track next due date (for non-due cards)
        if card["due_date"] > today:
            if next_due_date is None or card["due_date"] < next_due_date:
                next_due_date = card["due_date"]

    # Rating distribution from all review logs
    rating_dist = {1: 0, 2: 0, 3: 0, 4: 0}
    for card in cards.values():
        for log in card["review_log"]:
            r = log["rating"]
            if r in rating_dist:
                rating_dist[r] += 1

    sessions = state.get("session_history", [])

    return {
        "total_cards": total,
        "by_state": by_state,
        "due_today": due_today,
        "next_due": next_due_date,
        "avg_difficulty": round(sum(difficulties) / len(difficulties), 2) if difficulties else 0,
        "avg_stability": round(sum(stabilities) / len(stabilities), 2) if stabilities else 0,
        "total_reviews": total_reviews,
        "rating_distribution": {"Again": rating_dist[1], "Hard": rating_dist[2], "Good": rating_dist[3], "Easy": rating_dist[4]},
        "total_sessions": len(sessions),
        "known_card_ids": state["scan_history"]["known_card_ids"],
        "last_scan": state["scan_history"]["last_scan"],
    }


# ── CLI Entry Point ───────────────────────────────────────────────

def parse_args(args):
    """Simple arg parser: --key value pairs."""
    parsed = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                parsed[key] = args[i + 1]
                i += 2
            else:
                parsed[key] = True
                i += 1
        else:
            i += 1
    return parsed


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: fsrs_engine.py <state_file> <command> [args]"}))
        sys.exit(1)

    state_file = os.path.expanduser(sys.argv[1])
    command = sys.argv[2]
    extra = sys.argv[3:]

    state = load_state(state_file)
    result = None
    save = False

    if command == "due":
        opts = parse_args(extra)
        limit = int(opts.get("limit", 10))
        result = cmd_due(state, limit)

    elif command == "record":
        opts = parse_args(extra)
        card_id = opts.get("id")
        rating = int(opts.get("rating", 3))
        if not card_id:
            result = {"error": "Missing --id"}
        elif rating not in (1, 2, 3, 4):
            result = {"error": f"Invalid rating: {rating}. Must be 1-4."}
        else:
            result = cmd_record(state, card_id, rating)
            save = True

    elif command == "register":
        opts = parse_args(extra)
        card_id = opts.get("id")
        title = opts.get("title", "")
        content = opts.get("content", "")
        if not card_id:
            result = {"error": "Missing --id"}
        else:
            result = cmd_register(state, card_id, title, content)
            save = True

    elif command == "bulk_register":
        raw = sys.stdin.read()
        try:
            cards_data = json.loads(raw)
        except json.JSONDecodeError as e:
            result = {"error": f"Invalid JSON on stdin: {e}"}
            print(json.dumps(result))
            sys.exit(1)
        result = cmd_bulk_register(state, cards_data)
        save = True

    elif command == "record_session":
        raw = sys.stdin.read()
        try:
            session_data = json.loads(raw)
        except json.JSONDecodeError as e:
            result = {"error": f"Invalid JSON on stdin: {e}"}
            print(json.dumps(result))
            sys.exit(1)
        result = cmd_record_session(state, session_data)
        save = True

    elif command == "stats":
        result = cmd_stats(state)

    else:
        result = {"error": f"Unknown command: {command}"}

    if save:
        save_state(state_file, state)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
