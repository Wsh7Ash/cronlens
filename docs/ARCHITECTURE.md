# Architecture

## Overview

```text
parser.py ──Schedule──▶ matcher.py ──fires──▶ cli.py
    │                      ▲
    │                      │
    └──▶ explainer.py      quiz.py ──(uses parser+matcher)──▶ cli.py
```

### parser.py

Five-field parsing into frozen sets of valid values:

- lists (`,`), ranges (`-`), steps (`/`), `*`, named months (`jan`–`dec`,
  full names accepted) and weekdays (`sun`–`sat`)
- DOW normalization: 7 → 0 (Sunday), and a bare `*` DOW yields 0–6 (not 0–7,
  since 7 is an alias, not an extra slot)
- strict validation: out-of-range values, descending ranges, zero steps, and
  impossible day-of-month 0 are all errors
- special strings are translated before splitting (`@daily` → `0 0 * * *`)
- `matches(sched, dt)` implements Vixie cron's day rule: **OR** when both DOM
  and DOW are restricted, **AND** otherwise (with `*` counting as
  unrestricted)

### matcher.py

Fire-time simulation by day-walking: from the next minute boundary after the
reference time, each day is tested against the day rules (month set, then the
DOM/DOW OR/AND rule); matching days emit their (hour, minute) candidates in
sorted order. Day-walking (not minute-walking) makes sparse schedules like
`0 0 29 2 *` cheap while still being exact, and every skipped day can be
explained in a `--why` trace (bounded at 60 entries). A 200-year hard stop
bounds never-firing expressions like `0 0 30 2 *`.

### explainer.py

Field-by-field table plus plain-language "fires:" summary, and gotcha
detection: DOM/DOW OR warnings, February day-30/31 cliffs, long-month-only
slots, and the top-of-every-hour `0 *` pattern. It reads only the parsed
schedule, so warnings can never contradict the matcher.

### quiz.py

Deterministic item generation: `Random(seed*31 + tier)` draws expressions
from tier templates and interesting reference times (now, +1h, +1d, +13d,
+41d jittered). Answers are computed by the real matcher — the quiz and the
simulator cannot disagree. Tier 3 always contains at least one never-fires
item (`59 23 30 2 *`) because recognizing impossibility is the skill. The
grader returns exact-match, off-by-N-minutes, and never/never feedback.

## Design decisions

- **Explain/simulate/quiz as one engine** — the quiz reuses the simulator, so
  "the tool said the answer" is always defensible; there is no second source
  of truth to drift.
- **Stdlib-only, no tz database** — cron semantics are reproduced for naive
  datetimes; DST-aware simulation via `zoneinfo` is scoped as future work and
  documented as a limitation rather than approximated silently.
- **Day-walking over candidate iteration** — a simpler invariant (one day at
  a time, candidates within a day) makes correctness auditable; performance
  is fine for a teaching tool even at 200-year worst cases.
- **Never-firing is a first-class answer** — `0 0 30 2 *` is not an error at
  parse time (cron accepts it); it is explained, simulated as empty, and
  quizzed as "never".
