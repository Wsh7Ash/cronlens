# Contributing

Thanks for considering a contribution to cronlens.

## Development setup

- Python ≥ 3.10, no third-party packages.

```shell
git clone https://github.com/Wsh7Ash/cronlens.git
cd cronlens
PYTHONPATH=src python -m unittest discover -s tests
```

## Ground rules

- **One source of truth.** Quiz answers must come from the real matcher —
  never hardcode expected fire times in quiz generation.
- Keep the stdlib-only property.
- Semantic changes (parser or matcher) must ship with tests that pin Vixie
  cron behavior, including at least one edge case from the wild (February
  cliffs, DOW 7, OR rule, month lengths).
- Warnings in `explainer.py` must be derivable from the parsed schedule only,
  so explain output can never contradict simulation output.

## Adding a quiz tier (checklist)

1. Add templates to `TIER_TEMPLATES` — every template must parse and either
   fire or be a deliberate never-fires teaching case.
2. Register the tier name in `TIERS`.
3. Add tests: determinism, answer validity, and tier-specific edge cases.
4. Mention the tier in README and USAGE.

## Reporting bugs

Open an issue with the expression, the reference time, and observed vs
expected fire times. Include `--why` output when relevant.
