# Git ↔ Notion map

Notion is the research control plane; Git is the source of truth for code, tests,
configs, specifications, results and decisions. This file is the bridge: it maps
each experiment ID to its Notion record and its repository artifacts, so a result
can be traced in both directions.

Workspace: `asdramxrt's Space`
Top-level page: **AI Trading Research** —
https://app.notion.com/p/3dd017d63ac781328070fd7e660b7cbd

Programme page: **Freqtrade PA Momentum Research** —
https://app.notion.com/p/3dd017d63ac7818f8ef0d08a855c826a

Experiments database: **Experiments** —
https://app.notion.com/p/1a91654b27394de48575b6d8b5b117db

> Deliberately separate from the pre-existing `🤖 AI Trading Bot Engineering`
> control centre, which governs a different (earlier) project. Research records
> are kept isolated so one programme's evidence cannot be confused with
> another's.

## Section pages

| Section | Notion |
|---------|--------|
| 00 — Project Control | https://app.notion.com/p/3dd017d63ac78174801cefa1b118cf82 |
| 01 — Research Charter | https://app.notion.com/p/3dd017d63ac78140b2bfda21c00be26a |
| 02 — Strategy Specifications | https://app.notion.com/p/3dd017d63ac7817cad3ade3e7344c9a7 |
| 03 — Experiments | https://app.notion.com/p/3dd017d63ac781289f9edeeb0b78a81d |
| 04 — Results | https://app.notion.com/p/3dd017d63ac7816aae57c931e5f52f24 |
| 05 — Walk Forward | https://app.notion.com/p/3dd017d63ac78131b7dad0905f76ee47 |
| 06 — Decisions / Rejected Ideas | https://app.notion.com/p/3dd017d63ac781469ba9d8376f508f77 |
| 07 — Production Readiness | https://app.notion.com/p/3dd017d63ac7819e967ac6c104f6a008 |
| 08 — Architecture | https://app.notion.com/p/3dd017d63ac781cc8ca1c1e64f1fac1d |

## Experiment records

| ID | Notion | Branch | Spec | Result | Status |
|----|--------|--------|------|--------|--------|
| EXP-001 | https://app.notion.com/p/3dd017d63ac7815d9a4ce01b206bf95c | `research/turtle-baseline` | `research/experiment_specs/EXP-001.md` | `research/experiment_results/EXP-001.md` + `.json` | FAIL |
| EXP-002 | https://app.notion.com/p/3dd017d63ac781aab9d6f98bbf828732 | `research/turtle-costs` | `research/experiment_specs/EXP-002.md` | `research/experiment_results/EXP-002.md` + `.json` + `.raw.json` | FAIL |
| EXP-003 | https://app.notion.com/p/3dd017d63ac78101b610feddc1529963 | `research/pullback-continuation` | `research/experiment_specs/EXP-003.md` | `research/experiment_results/EXP-003.md` + `.json` + `.raw.json` (+ `.geometry.json`, `.complementarity.json`) | MIXED |
| EXP-004 | https://app.notion.com/p/3dd017d63ac781199c41c8ea668e358d | `research/frozen-pullback-oos` | `research/experiment_specs/EXP-004.md` | `research/experiment_results/EXP-004.md` + `.json` + `.raw.json` (+ `.regression.json`) | FAILS FRESH OOS |
| EXP-005 | https://app.notion.com/p/3dd017d63ac781d6a113d58b5e80e34d | not created | not written | not written | PLANNED |
| EXP-006 | https://app.notion.com/p/3dd017d63ac781ccb4aef958c0c7ed30 | not created | not written | not written | PLANNED |
| EXP-007 | https://app.notion.com/p/3dd017d63ac78145aa22fb20a03bbee5 | not created | not written | not written | PLANNED |
| EXP-008 | https://app.notion.com/p/3dd017d63ac7814cb8efd69c98e258c4 | not created | not written | not written | PLANNED |
| EXP-009 | https://app.notion.com/p/3dd017d63ac7811ea4eac1664deb8435 | not created | not written | not written | PLANNED |
| EXP-010 | https://app.notion.com/p/3dd017d63ac781aab692e7e5d6c0df1c | not created | not written | not written | PLANNED |
| EXP-011 | https://app.notion.com/p/3dd017d63ac7812d99aefcaab254e457 | not created | not written | not written | PLANNED |
| EXP-012 | https://app.notion.com/p/3dd017d63ac78134be3cf6c49bcd58c2 | not created | not written | not written | PLANNED |
| EXP-013 | https://app.notion.com/p/3dd017d63ac781d59007fdac9e4eee5b | not created | not written | not written | PLANNED |
| EXP-014 | https://app.notion.com/p/3dd017d63ac78198a003eb831cfcfcc3 | not created | not written | not written | PLANNED |
| EXP-015 | https://app.notion.com/p/3dd017d63ac781b6afbae2b73119c7ac | not created | not written | not written | PLANNED |

## Phase 2 diagnostics

| Artifact | Path |
|----------|------|
| Specification | `research/experiment_specs/PHASE2_DIAGNOSTIC.md` |
| Report | `research/experiment_results/PHASE2_DIAGNOSTIC.md` |
| Machine-readable | `PHASE2_data_quality.json`, `PHASE2_market_regimes.json`, `PHASE2_turtle_followthrough.json`, `PHASE2_pullback_geometry.json`, `PHASE2_trade_diagnostics.json`, `PHASE2_statistics.json`, `PHASE2_lineage.json` |
| Scripts | `user_data/scripts/diagnostics/` |
| Branch | `research/diagnostic-generalization` |

Diagnostic only. No strategy change and no strategy verdict.

## Update procedure after each experiment

1. Write `research/experiment_specs/<ID>.md` and `user_data/configs/<ID>.json`,
   commit them **before** running.
2. Run the experiment.
3. Write `research/experiment_results/<ID>.md` and `<ID>.json`.
4. Add an entry to `research/decisions/DECISION_LOG.md`.
5. Add the row/links to the table above in the same commit.
6. Update the matching Notion row: status, metrics, OOS, robustness, decision,
   GitHub branch and commit SHA.
