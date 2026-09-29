"""explainer.py — human-readable breakdown and gotcha detection."""

import calendar

from .parser import FIELD_NAMES, FIELD_RANGES

DOW_LABEL = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
MONTH_LABEL = {i: name for i, name in enumerate(calendar.month_name) if name}
FIELD_DESC = {
    "minute": "minutes past the hour",
    "hour": "hours of the day",
    "day-of-month": "days of the month",
    "month": "months of the year",
    "day-of-week": "days of the week (0 and 7 = Sunday)",
}


def _describe(token, name):
    lo, hi = FIELD_RANGES[name]
    if token == "*":
        return f"every {'minute' if name == 'minute' else name.split('-')[-1]}"
    if token.startswith("*/"):
        return f"every {token[2:]} {'minutes' if name == 'minute' else name.split('-')[-1]} (stepped)"
    if "/" in token and not token.startswith("*/"):
        base, step = token.split("/", 1)
        return f"starting at {base}, every {step} (stepped)"
    if "-" in token:
        a, b = token.split("-", 1)
        return f"range: {a} through {b}"
    return "single value" if "," not in token else "list of values"


def _expand(token, name):
    """Short expansion of a token for the fires summary."""
    if token.startswith("*/"):
        return f"every {token[2:]} {name.split('-')[-1]}s"
    if "," in token:
        return "several selected values"
    return _describe(token, name)


def explain(sched):
    """Return (lines, warnings) for a parsed schedule."""
    lines = []
    warnings = []

    lines.append("field         value       meaning")
    lines.append("----          -----       -------")
    for i, name in enumerate(FIELD_NAMES):
        token = sched.parts[i]
        lines.append(f"{name:<13} {token:<11} {_describe(token, name)}")

    # ---- gotchas ----
    if sched.dom_restricted and sched.dow_restricted:
        warnings.append(
            "both day-of-month and day-of-week are restricted — cron fires when EITHER matches (OR), not both"
        )

    doms = sorted(sched.doms)
    if sched.dom_restricted and doms:
        max_dom = max(doms)
        impossible = [d for d in doms if d > 29]
        if impossible:
            warnings.append(
                f"day-of-month {max_dom}: most months have fewer days — this slot only fires in months long enough"
            )
        if 30 in sched.doms or 31 in sched.doms:
            if 2 in sched.months:
                warnings.append(
                    "February combined with day 30/31: February never has 30 or 31 days — those slots never fire"
                )

    if sched.dow_restricted and "7" in sched.parts[4]:
        lines.append("note: DOW 7 is accepted and means Sunday (same as 0)")

    if sched.parts[0] == "0" and sched.parts[1] in ("*", "*/1"):
        warnings.append("minute 0 with every hour: this fires at the top of every hour — was an interval intended?")

    # plain-language fires summary
    m = _expand(sched.parts[0], "minute")
    h = _expand(sched.parts[1], "hour")
    lines.append("")
    lines.append(f"fires: {m}, {h}, " + _expand(sched.parts[2], "day-of-month") + ", "
                 + _expand(sched.parts[3], "month") + ", " + _expand(sched.parts[4], "day-of-week"))
    if sched.dom_restricted and sched.dow_restricted:
        lines.append("(day match rule: DOM OR DOW — see warning)")
    return lines, warnings


def humanize_sets(sched):
    """Pretty-print the parsed value sets (used by --json and verbose)."""
    def fmt_dow(vals):
        return [f"{v}={DOW_LABEL[v][:3]}" for v in sorted(vals)]

    def fmt_month(vals):
        return [f"{v}={MONTH_LABEL[v][:3]}" for v in sorted(vals)]

    return {
        "minutes": sorted(sched.minutes),
        "hours": sorted(sched.hours),
        "days-of-month": sorted(sched.doms),
        "months": fmt_month(sched.months),
        "days-of-week": fmt_dow(sched.dows),
    }
