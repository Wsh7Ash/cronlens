"""matcher.py — next-fire-time simulation with skip traces.

Strategy: walk days one at a time from the next minute boundary after the
reference time. For each day that matches the schedule's day rules, emit all
(hour, minute) candidates. Day-level walking (not minute-level) keeps sparse
schedules fast, and every skipped day can be explained for the --why trace.
"""

import datetime as dt

MAX_TRACE = 60
MAX_DAYS = 366 * 200  # hard stop (~200 years) for never-firing expressions


def next_fires(sched, after, count=3, want_trace=False):
    """Return (fires, traces): up to `count` fire datetimes strictly after
    `after`, plus (datetime, reason) traces of skipped days when requested."""
    fires = []
    traces = []

    t0 = after.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    day = t0.date()

    for _ in range(MAX_DAYS):
        if _day_matches(sched, day, traces if want_trace else None):
            for hour in sorted(sched.hours):
                for minute in sorted(sched.minutes):
                    cand = dt.datetime.combine(day, dt.time(hour, minute))
                    if cand >= t0:
                        fires.append(cand)
                        if len(fires) >= count:
                            return fires, traces
        day += dt.timedelta(days=1)

    return fires, traces


def _day_matches(sched, date, traces):
    """Day-level match: month first, then Vixie cron's DOM/DOW OR rule."""
    if date.month not in sched.months:
        if traces is not None and len(traces) < MAX_TRACE:
            traces.append((dt.datetime(date.year, date.month, date.day),
                           f"month {date.month} not in {sorted(sched.months)}"))
        return False
    dom_ok = date.day in sched.doms if sched.dom_restricted else True
    dow_ok = ((date.weekday() + 1) % 7) in sched.dows if sched.dow_restricted else True
    if sched.dom_restricted and sched.dow_restricted:
        ok = dom_ok or dow_ok
    else:
        ok = dom_ok and dow_ok
    if not ok and traces is not None:
        reasons = []
        if sched.dom_restricted and not dom_ok:
            reasons.append(f"DOM {date.day} not in {sorted(sched.doms)}")
        if sched.dow_restricted and not dow_ok:
            reasons.append(f"DOW {date.strftime('%a')} not in {sorted(sched.dows)}")
        if sched.months and date.month not in sched.months:
            reasons.append(f"month {date.month} not in {sorted(sched.months)}")
        if len(traces) < MAX_TRACE:
            traces.append((dt.datetime(date.year, date.month, date.day), "; ".join(reasons) or "restricted"))
    return ok
