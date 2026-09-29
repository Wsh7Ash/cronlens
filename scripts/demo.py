#!/usr/bin/env python3
"""demo.py — produces cronlens demo artifacts in results/:
explain output, next-fire simulation with skip trace, and a scripted quiz."""

import io
import json
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cronlens.cli import cmd_explain, cmd_next  # noqa: E402
from cronlens.parser import parse  # noqa: E402
from cronlens.explainer import explain  # noqa: E402
from cronlens.quiz import make_quiz, check_answer  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

out = []


def section(title):
    out.append("")
    out.append("=" * 72)
    out.append(title)
    out.append("=" * 72)


def cli_run(fn, args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = fn(args)
    return buf.getvalue(), code


def main():
    section("1) explain — a normal expression")
    text, _ = cli_run(cmd_explain, _ns(["explain", "*/15 9-17 * * mon-fri"]))
    out.append(text.rstrip())

    section("2) explain — gotchas detected")
    for expr in ("0 0 30 2 *", "0 12 13 * 5"):
        text, _ = cli_run(cmd_explain, _ns(["explain", expr]))
        out.append(f"$ cronlens explain \"{expr}\"")
        out.append(text.rstrip())

    section("3) next — simulation with skip trace")
    text, _ = cli_run(cmd_next, _ns(["next", "0 0 13 * *", "-n", "2",
                                     "--utc", "2026-09-29T10:00:00", "--why"]))
    out.append(text.rstrip())

    section("4) quiz — scripted tier-3 round (learner answers shown)")
    items = make_quiz(tier=3, rounds=4, seed=7)
    # scripted learner: misses round 1 by an hour, gets the rest right
    # (a 'never' answer is given whenever the expression cannot fire)
    score = 0
    for i, item in enumerate(items, 1):
        out.append(f"round {i} — predict next fire AFTER {item['after']:%Y-%m-%d %H:%M}")
        out.append(f"expression: {item['expr']}")
        if item["answer"] is None:
            guess, shown = "never", "never"
        elif i == 1:
            import datetime as dt
            guess = item["answer"] + dt.timedelta(hours=1)
            shown = f"{guess:%Y-%m-%d %H:%M}"
        else:
            guess, shown = item["answer"], f"{item['answer']:%Y-%m-%d %H:%M}"
        out.append(f"your guess: {shown}")
        ok, note = check_answer(item, guess)
        score += 1 if ok else 0
        out.append(f"  {'✓' if ok else '✗'} {note}")
    out.append(f"score: {score}/{len(items)}")

    with open(os.path.join(RESULTS, "demo-session.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))

    # machine-readable artifact
    payload = []
    for tier in (1, 2, 3):
        for item in make_quiz(tier=tier, rounds=6, seed=7):
            payload.append({
                "tier": tier,
                "expr": item["expr"],
                "after": item["after"].isoformat(),
                "answer": item["answer"].isoformat() if item["answer"] else None,
            })
    with open(os.path.join(RESULTS, "quiz-items.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("saved results/demo-session.txt and results/quiz-items.json")


def _ns(argv):
    """Build the argparse namespace the CLI funcs expect, bypassing main()."""
    from cronlens.cli import build_parser
    return build_parser().parse_args(argv)


if __name__ == "__main__":
    main()
