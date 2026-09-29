# Results

## Environment
- OS: Windows 11 (win32, Git Bash)
- Runtime: Python 3.14.3
- Dependency manager: none (stdlib only)

## Validation performed
- install: PASS (no dependencies)
- build: PASS (stdlib-only package)
- unit tests: PASS — 28/28 (`PYTHONPATH=src python -m unittest discover -s tests`)
- integration tests: N/A (CLI exercised in unit tests)
- lint: N/A
- type check: N/A
- demo run: PASS (`PYTHONPATH=src python scripts/demo.py` → `results/demo-session.txt`, `results/quiz-items.json`)

## Commands executed
```shell
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python scripts/demo.py
PYTHONPATH=src python -m cronlens next "0 12 13 * 5" -n 3 --utc 2026-09-29T10:00:00
```

## Observed result
- 28/28 tests pass: parser sets (steps/lists/ranges/names, `10/20` = 10,30,50), Sunday 0-and-7 normalization, bare `*` DOW = 0–6, specials translation, 10 invalid-input rejections, restriction flags, `*/10` stepping from a reference minute, daily rollover, DOM/DOW OR (Fri Oct 2 + Tue Oct 13 both fire for `0 12 13 * 5`), AND when only one side restricted, February 30 never fires, Feb 29 leap-year wait (2028-02-29), year rollover, 31st skipping short months, skip traces, explain warnings (OR reminder, February cliff, clean for simple expressions), quiz determinism, answer validity (fires are future and match the schedule), tier-3 guaranteed never-fires item, grader paths (exact / off-by-+60 / never / unparseable), CLI output and JSON, parse-error exit code 2.
- Demo: explain (workday stepper + two gotcha cases), next with `--why` trace, and a scripted tier-3 quiz (miss-by-an-hour on round 1, perfect afterwards incl. the never-fires item) → 4 artifacts saved.
- Defects caught by tests and fixed before release:
  1. `*/15` style fields raised UnboundLocalError (step-with-star never set the range end).
  2. Bare `*` DOW produced an extra 7 instead of normalized 0–6.
  3. Rewritten matcher dropped the month check from the day rule — February-only schedules would fire in March (caught by `test_never_fires_february_30`).
  4. CLI returned 2 instead of raising SystemExit(2) on parse errors.
  5. `7 in sched.parts[4]` compared an int against a string (TypeError in explainer).
  6. Month abbreviations (`jan`) rejected — only full names were registered.
  7. Windows cp1252 console crashed on ✓/✗; stdout now reconfigures to UTF-8 with replacement.
- One test expectation corrected after verifying with an independent weekday check: Oct 2 2026 is a Friday, so under OR semantics `0 12 13 * 5` fires Oct 2 before Oct 13 (the original test was wrong, not the matcher).

## Generated artifacts
- `results/demo-session.txt` — full demo transcript (explain × 3, next with trace, scripted quiz)
- `results/quiz-items.json` — 18 seeded quiz items across tiers with computed answers

## Known limitations
- Naive datetimes / fixed UTC reference only; DST transitions not simulated
- No `@reboot`, seconds field, or environment modeling
- Quiz is terminal-interactive only
