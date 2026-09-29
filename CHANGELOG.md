# Changelog

## 1.0.0 — 2026-09-29

Initial release.

- Full 5-field cron parser: lists, ranges, steps, named months/weekdays, Sunday 0/7, special strings
- Vixie-cron DOM/DOW OR semantics with correct month and length handling (Feb 30 never fires; Feb 29 waits for leap years)
- `explain` with gotcha warnings; `next` with `--why` skip traces and JSON mode
- `quiz` with three tiers, seeded reproducible item sets, and prediction checking (incl. never-fires answers)
- Zero dependencies; Python ≥ 3.10
