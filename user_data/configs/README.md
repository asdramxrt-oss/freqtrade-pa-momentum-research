# Configurations

One frozen configuration per experiment, named `<EXPERIMENT_ID>.json`.

| File | Experiment | Strategy | Notes |
|------|-----------|----------|-------|
| `EXP-001.json` | Turtle raw baseline | `DonchianTurtleBaseline` | 10 pairs, 4h, fee 0.05%, static pairlist |

## Conventions

- `recursive_strategy_search` must be `true`: strategies live in per-family
  subfolders, and freqtrade only walks subfolders when this is enabled.
- `stake_amount` must not be `"unlimited"`, because the strategies implement
  `custom_stake_amount` for risk-based sizing.
- `stake_amount` is a cap, not a target: risk-based sizing returns the smaller of
  its computed stake and this value.
- `pairlists` must be present; `StaticPairList` is used so the traded universe is
  an explicit, reviewable list rather than a dynamic filter.
- `dry_run` is always `true` and the API server is disabled. Research
  configurations must not be able to place a real order.
- Credentials are empty in committed configs. If an exchange ever needs
  authentication for data download, use environment variables or a git-ignored
  private config overlay.

## Adding a configuration

Copy `EXP-001.json`, change `strategy`, `pair_whitelist` and risk settings, and
commit it together with the matching
`research/experiment_specs/<EXPERIMENT_ID>.md` **before** running anything.
A configuration without a specification is not a valid experiment.
