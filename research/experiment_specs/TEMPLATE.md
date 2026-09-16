# Experiment specification — TEMPLATE

Copy to `research/experiment_specs/EXP-0NN.md`, fill every field, and commit it
**before** running the experiment. A specification committed after the run is not
a specification.

| Field | Value |
|-------|-------|
| **Experiment ID** | EXP-0NN |
| **Title** | |
| **Strategy** | |
| **Branch** | `research/<topic>` |
| **Config** | `user_data/configs/EXP-0NN.json` |
| **Depends on** | EXP-0MM (state the decision that allowed this experiment) |
| **Status** | PLANNED |

## 1. Objective

What question does this experiment answer? One question per experiment.

## 2. Hypothesis under test

Falsifiable statement, plus a pointer to the hypothesis document in
`research/hypotheses/`.

## 3. Frozen implementation

Exact entry, exact exit, stop, sizing, direction, and anything else needed to
reproduce the run. Ambiguity here becomes an overfitting opportunity later.

## 4. Fixed parameters

Every parameter, with its value, recorded before any run. State explicitly which
parameters are *not* tunable in this experiment.

## 5. Dataset

Universe, period(s), data source, and any deviation from
`research/preregistration/experiment_protocol.md` with a reason.

## 6. Cost scenarios

Fee levels to be tested. Default: 0.05% base, 0.10% mid, 0.20% stress.

## 7. Runs to perform

Enumerate them. Fix the number of OOS evaluations in advance.

## 8. Success criteria

Charter criteria A1–A8 plus any experiment-specific criterion. Any additional
criterion must be stated here, before the run.

## 9. Out of scope

What this experiment must not do — usually the thing that would make the result
uninterpretable.

## 10. Expected failure modes

Copied from the hypothesis document, so a failure is diagnosed rather than
discovered.
