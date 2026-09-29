"""quiz.py — deterministic cron-reading practice.

Three tiers of generated expressions, each with a reference time chosen to
make the interesting edge case visible (month rollovers, DOM/DOW OR, February
cliffs). The learner predicts the next fire time; the checker compares
datetimes and explains the answer.
"""

import datetime as dt
import random

from .matcher import next_fires
from .parser import parse

TIERS = {
    1: "starter — steps and fixed times",
    2: "tricky — ranges, lists, month rollovers",
    3: "hostile — DOM/DOW OR, February cliffs, rare slots",
}

# (expr template, reference-time chooser)
TIER_TEMPLATES = {
    1: [
        "*/10 * * * *",
        "0 * * * *",
        "30 4 * * *",
        "15 8 * * 1-5",
        "0 22 * * *",
        "*/30 * * * *",
        "0 9 * * 1",
    ],
    2: [
        "0 9-17/2 * * *",
        "0 0 1,15 * *",
        "30 6 1 * mon",
        "0 12 * jan,dec 1-5",
        "15 */4 * * *",
        "0 0 * * 0",
        "5 4 * 2 *",
    ],
    3: [
        "0 12 13 * 5",
        "0 0 29 2 *",
        "0 0 31 * *",
        "0 3 1 1 mon",
        "59 23 30 2 *",
        "0 0 * 2 1",
        "0 9 1 * 0",
    ],
}


def _reference(seed_rng, tier):
    """A deterministic, interesting reference moment."""
    base = dt.datetime(2026, 9, 29, 10, 7)
    offsets = [0, 3600, 86400, 86400 * 13, 86400 * 41]
    return base + dt.timedelta(seconds=seed_rng.choice(offsets) + seed_rng.randint(0, 59))


def make_quiz(tier=1, rounds=5, seed=0):
    """Return a list of quiz items: dicts with expr, after, answer."""
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier}")
    rng = random.Random(seed * 31 + tier)
    templates = TIER_TEMPLATES[tier]
    items = []
    for i in range(rounds):
        expr = rng.choice(templates)
        after = _reference(rng, tier)
        sched = parse(expr)
        fires, _ = next_fires(sched, after, count=1)
        if not fires:
            # never-fires expressions are teaching moments in tier 3
            items.append({"expr": expr, "after": after, "answer": None})
        else:
            items.append({"expr": expr, "after": after, "answer": fires[0]})
    if tier == 3 and rounds >= 3 and not any(i["answer"] is None for i in items):
        # guarantee the never-fires teaching moment in every tier-3 quiz
        items[0] = {"expr": "59 23 30 2 *", "after": _reference(rng, tier), "answer": None}
    return items


def check_answer(item, guess):
    """Grade a guess (datetime or None) against an item. Returns (ok, note)."""
    answer = item["answer"]
    if answer is None:
        ok = guess is None or str(guess).strip().lower() in ("never", "none")
        return ok, "this expression can never fire (see `explain` for why)"
    if guess is None:
        return False, f"actually fires at {answer:%Y-%m-%d %H:%M}"
    if not hasattr(guess, "year"):
        return False, f"could not parse your datetime; answer is {answer:%Y-%m-%d %H:%M}"
    if guess.replace(tzinfo=None) == answer:
        return True, "exact match"
    delta = (guess.replace(tzinfo=None) - answer).total_seconds() / 60
    return False, f"off by {delta:+.0f} minutes — answer is {answer:%Y-%m-%d %H:%M}"
