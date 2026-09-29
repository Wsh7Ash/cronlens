"""cli.py — cronlens command-line interface."""

import argparse
import datetime as dt
import json
import sys

from .explainer import explain, humanize_sets
from .matcher import next_fires
from .parser import CronParseError, parse
from .quiz import TIERS, check_answer, make_quiz


def _parse_ref(s):
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid datetime '{s}' (use ISO format, e.g. 2026-09-29T10:00:00)")


def cmd_explain(args):
    try:
        sched = parse(args.expr)
    except CronParseError as e:
        print(f"cronlens: {e}", file=sys.stderr)
        raise SystemExit(2)
    lines, warnings = explain(sched)
    print("\n".join(lines))
    for w in warnings:
        print(f"warning: {w}")
    if args.json:
        print(json.dumps(humanize_sets(sched), indent=2))
    return 0


def cmd_next(args):
    try:
        sched = parse(args.expr)
    except CronParseError as e:
        print(f"cronlens: {e}", file=sys.stderr)
        raise SystemExit(2)
    after = args.utc if args.utc else dt.datetime.now()
    fires, traces = next_fires(sched, after, count=args.n, want_trace=args.why)

    if args.json:
        payload = {
            "expr": sched.original,
            "after": after.isoformat(),
            "fires": [f.isoformat() for f in fires],
        }
        if args.why:
            payload["skipped"] = [{"at": t.isoformat(), "reason": r} for t, r in traces]
        print(json.dumps(payload, indent=2))
        return 0

    if args.why:
        print("skipped candidates (first 10):")
        for t, reason in traces[:10]:
            print(f"  {t:%Y-%m-%d}  {reason}")
        print("")
    print(f"next {len(fires)} fire time(s) after {after:%Y-%m-%d %H:%M}:")
    for f in fires:
        print(f"  {f:%Y-%m-%d %H:%M}  ({f:%A})")
    if not fires:
        print("  (none found — this expression may never fire; try `explain`)")
    return 0


def cmd_quiz(args):
    items = make_quiz(tier=args.tier, rounds=args.rounds, seed=args.seed)
    print(f"cronlens quiz — tier {args.tier} ({TIERS[args.tier]}), {args.rounds} rounds")
    score = 0
    for i, item in enumerate(items, 1):
        print(f"\nround {i}/{args.rounds} — predict the next fire time AFTER {item['after']:%Y-%m-%d %H:%M}")
        print(f"expression: {item['expr']}")
        raw = input("your guess (YYYY-MM-DD HH:MM, or 'never'): ").strip()
        guess = None
        if raw.lower() not in ("never", "none", ""):
            try:
                guess = dt.datetime.fromisoformat(raw.replace("T", " "))
            except ValueError:
                guess = raw  # unparseable; check_answer explains
        elif raw == "":
            print("  (empty — type 'never' if it never fires, or a datetime)")
        if isinstance(guess, str):
            ok, note = False, f"could not parse '{guess}'; answer is " + (
                f"{item['answer']:%Y-%m-%d %H:%M}" if item["answer"] else "NEVER (correct answer was 'never')"
            )
        else:
            ok, note = check_answer(item, guess)
        if ok:
            score += 1
            print(f"  ✓ {note}")
        else:
            print(f"  ✗ {note}")
    print(f"\nscore: {score}/{args.rounds}")
    if score == args.rounds:
        print("perfect — try the next tier")
    elif score >= args.rounds * 2 // 3:
        print("solid — same tier with a new seed, or step up")
    else:
        print("keep going: run `explain` on each miss, then retry this tier")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="cronlens", description="Learn cron: explain, simulate, quiz")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("explain", help="field-by-field breakdown + gotcha warnings")
    ex.add_argument("expr")
    ex.add_argument("--json", action="store_true")
    ex.set_defaults(func=cmd_explain)

    nx = sub.add_parser("next", help="simulate the next fire times")
    nx.add_argument("expr")
    nx.add_argument("-n", type=int, default=3)
    nx.add_argument("--utc", type=_parse_ref, default=None, help="reference datetime (ISO)")
    nx.add_argument("--why", action="store_true", help="show skipped candidates")
    nx.add_argument("--json", action="store_true")
    nx.set_defaults(func=cmd_next)

    qz = sub.add_parser("quiz", help="predict-the-fire-time practice")
    qz.add_argument("--tier", type=int, choices=sorted(TIERS), default=1)
    qz.add_argument("--rounds", type=int, default=5)
    qz.add_argument("--seed", type=int, default=0)
    qz.set_defaults(func=cmd_quiz)

    return ap


def main(argv=None):
    # Windows consoles often default to cp1252; keep glyphs printable
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
