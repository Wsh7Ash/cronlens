# cronlens

**Learn cron by doing: explain any expression, simulate its next fire times, and pass quizzes that ask you to predict them.**

## The problem

Cron is learned by copy-paste. Five fields, lists, ranges, steps, `*/n`, named weekdays, three day-of-month/day-of-week fields that interact by *OR*, and expressions like `0 0 30 2 *` that are valid-looking and **never fire**. Most people discover these rules through a missed backup.

`cronlens` turns cron from folklore into feedback: it explains expressions field by field, warns about classic mistakes, simulates the next fire times from any reference moment, and quizzes you until you can predict them yourself.

## Key features

- **`explain`** — field-by-field breakdown, expansion of lists/ranges/steps, special-string translation, and gotcha warnings (never-firing dates, DOM/DOW OR semantics, minute-0 confusion)
- **`next`** — the next N fire times after a reference time, with an optional `--why` trace showing skipped candidates and why
- **`quiz`** — interactive practice with three tiers (starter → tricky → hostile); you predict the next fire time, it checks you; deterministic via `--seed`
- **Correct semantics** — Vixie-cron DOM/DOW OR behavior, Sunday as 0 and 7, named months/weekdays, February edge cases
- **Zero dependencies** — Python stdlib only; no system crontab is ever touched

## Terminal example

```text
$ python -m cronlens explain "*/15 9-17 * * mon-fri"

field         value       meaning
minute        */15        every 15 minutes (0, 15, 30, 45)
hour          9-17        range: 9 through 17
day-of-month  *           every day
month         *           every month
day-of-week   mon-fri     range: Monday through Friday

fires: at :00 :15 :30 :45 of every hour from 09:00 to 17:45, Mon–Fri
note:  hour range 9-17 includes 17:45 — the last slot of the workday

$ python -m cronlens next "0 12 13 * 5" -n 3 --utc 2026-09-29T10:00:00

warning: both DOM (13) and DOW (Friday) are restricted — cron ORs them
next fire times (UTC):
  2026-10-13 12:00  (13th of month)
  2026-10-16 12:00  (Friday)
  2026-11-13 12:00  (13th of month)

$ python -m cronlens quiz --tier 2 --rounds 3 --seed 7

predict the next fire time after 2026-09-29 10:00 (UTC)
expression: 30 4 1 * *
your guess (YYYY-MM-DD HH:MM): 2026-10-01 04:30
✓ correct — first of month, 04:30
```

*(Format shown for illustration; exact quiz items come from the seeded generator.)*

## Architecture summary

- `src/cronlens/parser.py` — expression → structured schedule; validation and normalization
- `src/cronlens/matcher.py` — fire-time simulation with candidate stepping and skip reasons
- `src/cronlens/explainer.py` — human-readable breakdown + gotcha detection
- `src/cronlens/quiz.py` — seeded expression generator, tiers, prediction checking, streaks
- `src/cronlens/cli.py` — command wiring and JSON output

## Requirements

- Python ≥ 3.10, no third-party packages

## Installation

```shell
git clone https://github.com/Wsh7Ash/cronlens.git
cd cronlens
```

## Quick start

```shell
PYTHONPATH=src python -m cronlens explain "*/15 9-17 * * mon-fri"
PYTHONPATH=src python -m cronlens next "0 12 13 * 5" -n 3
PYTHONPATH=src python -m cronlens quiz --tier 1 --rounds 5
```

## Usage examples

```shell
# Why does my job never run?
PYTHONPATH=src python -m cronlens explain "0 0 30 2 *"

# Next runs after a specific moment, with skip reasons
PYTHONPATH=src python -m cronlens next "*/10 * * * *" -n 4 --utc 2026-12-31T23:55:00 --why

# Special strings work
PYTHONPATH=src python -m cronlens next "@weekly" -n 2

# Machine-readable
PYTHONPATH=src python -m cronlens next "@daily" -n 3 --json

# Harder quiz tier, deterministic set
PYTHONPATH=src python -m cronlens quiz --tier 3 --rounds 8 --seed 123
```

## Configuration

| Flag | Meaning |
|---|---|
| `explain <expr>` | field-by-field breakdown + warnings |
| `next <expr>` | simulate fire times |
| `-n N` | number of fire times (default 3) |
| `--utc ISO` | reference datetime (default: now) |
| `--why` | show skipped candidates and reasons |
| `--json` | JSON output for `next` |
| `quiz` | interactive practice mode |
| `--tier N` | 1 starter · 2 tricky · 3 hostile (default 1) |
| `--rounds N` | quiz length (default 5) |
| `--seed S` | deterministic quiz set |

Exit codes: `0` success (quiz: completed) · `2` usage/parse error.

## Testing instructions

```shell
PYTHONPATH=src python -m unittest discover -s tests
```

## Project structure

```text
cronlens/
├─ src/cronlens/    parser.py, matcher.py, explainer.py, quiz.py, cli.py
├─ tests/           parser/matcher/quiz/CLI tests
├─ scripts/demo.py — produces results/ artifacts
├─ results/         demo output
├─ docs/            ARCHITECTURE.md, USAGE.md, PROJECT_SPEC.md
└─ .github/workflows/ci.yml
```

## Limitations

- No time zone database: reference times are naive or fixed-offset UTC; DST transitions are not simulated (cron itself runs in local time of the host)
- No `@reboot`, no seconds field, no user-crontab environment modeling
- Quiz input is terminal-interactive; there is no GUI

## Roadmap

- `--tz` with zoneinfo for DST-aware simulation
- `crontab file` linting mode
- Spaced-repetition quiz history

## Security notes

Pure computation over strings and datetimes. It never reads or modifies the system crontab, spawns no processes, and touches no network.

## License

MIT
