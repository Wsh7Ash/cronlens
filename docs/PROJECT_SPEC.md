# PROJECT_SPEC — cronlens

- **Name:** cronlens
- **Category:** learner-tool
- **Target user:** developers and sysadmin juniors who write cron expressions by copying from the internet and never quite understand the fields
- **Problem:** Cron syntax has five fields, three special strings, four step/range/list operators, and a mental model most people get subtly wrong (day-of-month vs day-of-week OR semantics, February edge cases, DST-timeless UTC assumptions). Copy-paste scheduling leads to jobs firing at the wrong times and nobody noticing.
- **Solution:** `cronlens` is a stdlib-only Python CLI with three modes: `explain` (human-readable field-by-field breakdown with common-mistake warnings), `next` (simulate the next N fire times from a reference time, showing how the matcher works), and `quiz` (interactive practice: predict the next fire time of a generated expression; progress gates unlock harder tiers). A deterministic expression generator produces valid-but-tricky expressions (steps, ranges, weekday OR semantics, month boundaries).
- **Core workflow:** `python -m cronlens explain "<expr>"`; `python -m cronlens next "<expr>" -n 5`; `python -m cronlens quiz --tier 1 --rounds 10`
- **Must-have features:** full 5-field parser with lists/ranges/steps/names (`mon`, `jan`), `@reboot`-era specials limited to `@hourly/@daily/@weekly/@monthly/@yearly/@midnight/@noon`; next-fire simulation (correct DOM/DOW OR semantics); explain output with gotcha detection (e.g. `0 0 30 2 *` never fires; `* * 0 * *` warns about OR semantics); quiz with deterministic seeded expressions and prediction checking; JSON mode for `next`
- **Nice-to-have:** `--utc` fixed timezone note; streak scoring in quiz; `--why` trace of skipped candidates
- **Stack:** Python ≥ 3.10, stdlib only (datetime, calendar, argparse, json, random)
- **Test strategy:** unittest on parser round-trips, matcher semantics (incl. Feb 30 never-fires, DOW 7=0, DOM/DOW OR), specials equivalence, next-fire correctness vs brute force, quiz logic, CLI e2e
- **Demo/result strategy:** `scripts/demo.py` runs explain + next + a scripted quiz transcript → `results/`
- **Safety considerations:** pure computation; no system crontab is read or modified
- **Definition of done:** tests pass, demo artifacts produced, README commands verified
