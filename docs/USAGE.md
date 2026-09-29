# Usage

## Three commands

```shell
PYTHONPATH=src python -m cronlens explain "<expr>"     # what does this mean?
PYTHONPATH=src python -m cronlens next "<expr>" -n 5   # when will it fire?
PYTHONPATH=src python -m cronlens quiz --tier 2        # can you predict it?
```

## explain

Field-by-field breakdown, expansion of lists/ranges/steps, special strings,
plus gotcha warnings:

- DOM + DOW both restricted → **OR** reminder
- February with day 30/31 → never fires
- day 29–31 → only fires in long-enough months
- `0 * * * *` → "did you mean an interval?"

`--json` appends the parsed value sets as JSON.

## next

```shell
PYTHONPATH=src python -m cronlens next "*/10 * * * *" -n 4 \
    --utc 2026-12-31T23:55:00 --why
```

- `-n N` fire times (default 3)
- `--utc ISO` reference moment (default: now)
- `--why` first 10 skipped days with reasons
- `--json` machine-readable (`fires` + optional `skipped`)

Note the deliberate cron semantics you can observe here: `0 12 13 * 5` fires
on the 13th **or** on Fridays (OR rule), `0 0 31 * *` skips 30-day months,
and `0 0 29 2 *` waits for leap years.

## quiz

```shell
PYTHONPATH=src python -m cronlens quiz --tier 3 --rounds 8 --seed 123
```

- **tier 1 starter** — steps and fixed times
- **tier 2 tricky** — ranges, lists, month rollovers
- **tier 3 hostile** — DOM/DOW OR, February cliffs, guaranteed never-fires item

Type your guess as `YYYY-MM-DD HH:MM` (or `never`). Feedback is exact-match,
off-by-N-minutes, or an explanation. `--seed` makes a quiz reproducible —
useful for classrooms: same seed, same questions, comparable scores.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 2 | usage/parse error |

## Studying with cronlens — a suggested loop

1. `explain` the expressions already in your crontab; read every warning.
2. For each, `next` it with `--why` and verify the skips make sense.
3. `quiz --tier 1 --rounds 10 --seed 1`; target 9/10 before tier 2.
4. In tier 3, when you miss, run `explain` on the miss before retrying.
