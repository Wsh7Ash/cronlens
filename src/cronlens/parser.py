"""parser.py — cron expression parsing into structured, validated sets.

Supports the classic five fields with lists (`,`), ranges (`-`), steps (`/`),
named months and weekdays, `*`, and the special strings
@hourly/@daily/@weekly/@monthly/@yearly/@midnight/@noon.

Semantics follow Vixie cron: minute (0-59), hour (0-23), day-of-month (1-31),
month (1-12), day-of-week (0-7 with 0 and 7 both Sunday).
"""

import calendar
from dataclasses import dataclass

FIELD_NAMES = ("minute", "hour", "day-of-month", "month", "day-of-week")
FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day-of-month": (1, 31),
    "month": (1, 12),
    "day-of-week": (0, 7),
}
MONTH_NAMES = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTH_NAMES.update({name.lower()[:3]: i for i, name in enumerate(calendar.month_name) if name})
DOW_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}

SPECIALS = {
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@noon": "0 12 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
}


class CronParseError(ValueError):
    pass


@dataclass
class Schedule:
    original: str
    minutes: frozenset
    hours: frozenset
    doms: frozenset
    months: frozenset
    dows: frozenset          # normalized to 0-6 (Sunday=0)
    dom_restricted: bool     # DOM field was not '*'
    dow_restricted: bool     # DOW field was not '*'
    parts: list              # raw field tokens for the explainer


def _parse_field(token, name):
    """Parse one field into a sorted list of ints (DOW normalized 0-6)."""
    lo, hi = FIELD_RANGES[name]
    values = set()

    def norm(v, is_dow):
        if is_dow and v == 7:
            return 0
        if v < lo or v > hi:
            raise CronParseError(f"{name} value {v} out of range [{lo},{hi}]")
        return v

    for part in token.split(","):
        part = part.strip()
        if not part:
            raise CronParseError(f"empty list item in {name}")

        step = 1
        body = part
        if "/" in part:
            body, step_s = part.split("/", 1)
            try:
                step = int(step_s)
            except ValueError:
                raise CronParseError(f"{name} step '{step_s}' is not a number")
            if step < 1:
                raise CronParseError(f"{name} step must be >= 1")

        def resolve_word(word):
            w = word.lower()
            if name == "month" and w in MONTH_NAMES:
                return MONTH_NAMES[w]
            if name == "day-of-week" and w in DOW_NAMES:
                return DOW_NAMES[w]
            try:
                return int(word)
            except ValueError:
                raise CronParseError(f"{name} value '{word}' is not a number or name")

        if body == "*":
            if "/" in part:
                start = lo
                end = 7 if name == "day-of-week" else hi
            else:
                # bare '*' for day-of-week covers 0-6 (7 is a alias of 0, not an extra slot)
                top = 7 if name == "day-of-week" else hi
                values.update(range(lo, top) if name == "day-of-week" else range(lo, top + 1))
                continue
        elif "-" in body:
            a_s, b_s = body.split("-", 1)
            a, b = resolve_word(a_s), resolve_word(b_s)
            a, b = norm(a, name == "day-of-week"), norm(b, name == "day-of-week")
            if a > b:
                raise CronParseError(f"{name} range {a}-{b} is descending (wrapping ranges not supported)")
            start, end = a, b
        else:
            v = resolve_word(body)
            v = norm(v, name == "day-of-week")
            if "/" in part:
                start, end = v, (7 if name == "day-of-week" else hi)
            else:
                values.add(v)
                continue

        is_dow = name == "day-of-week"
        v = start
        while v <= end:
            values.add(norm(v, is_dow))
            v += step

    return sorted(values)


def parse(expr):
    """Parse a cron expression or special string into a Schedule."""
    if not isinstance(expr, str) or not expr.strip():
        raise CronParseError("empty expression")
    expr = expr.strip()
    if expr.lower() in SPECIALS:
        expr = SPECIALS[expr.lower()]
    fields = expr.split()
    if len(fields) != 5:
        raise CronParseError(f"expected 5 fields, got {len(fields)}: '{expr}'")

    minutes = _parse_field(fields[0], "minute")
    hours = _parse_field(fields[1], "hour")
    doms = _parse_field(fields[2], "day-of-month")
    months = _parse_field(fields[3], "month")
    dows = _parse_field(fields[4], "day-of-week")

    return Schedule(
        original=expr,
        minutes=frozenset(minutes),
        hours=frozenset(hours),
        doms=frozenset(doms),
        months=frozenset(months),
        dows=frozenset(dows),
        dom_restricted=fields[2] != "*",
        dow_restricted=fields[4] != "*",
        parts=list(fields),
    )


def matches(sched, dt):
    """Does naive datetime dt fire under sched (Vixie DOM/DOW OR rule)?"""
    if dt.minute not in sched.minutes:
        return False
    if dt.hour not in sched.hours:
        return False
    if dt.month not in sched.months:
        return False
    dom_ok = dt.day in sched.doms if sched.dom_restricted else True
    dow_ok = ((dt.weekday() + 1) % 7) in sched.dows if sched.dow_restricted else True
    if sched.dom_restricted and sched.dow_restricted:
        return dom_ok or dow_ok
    return dom_ok and dow_ok
