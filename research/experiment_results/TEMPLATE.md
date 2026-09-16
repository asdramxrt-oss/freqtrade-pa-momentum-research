# Experiment result — TEMPLATE

Copy to `research/experiment_results/EXP-0NN.md`. Also emit the machine-readable
companion `EXP-0NN.json` so that the record can be linked from Notion to the
exact commit and configuration.

| Field | Value |
|-------|-------|
| **Experiment ID** | EXP-0NN |
| **Status** | COMPLETED → PASS / FAIL / REJECTED |
| **Branch** | |
| **Commit** | |
| **Run date** | |

## 1. Environment

Framework version, CCXT version, Python, pandas, numpy. An unrecorded
environment makes a result unreproducible.

## 2. Exact commands

Paste the commands verbatim, including timeranges and fee overrides.

## 3. Results — full sample

Net return, CAGR, profit factor, trades, win rate, expectancy, average/median
trade, exposure, turnover, fees paid, Sharpe, Sortino, SQN, per-trade p-value,
max drawdown (trade-based and wallet-based).

## 4. Results — out-of-sample

Same metrics, plus the number of OOS evaluations used for this version.

## 5. Results — cost sensitivity

Table across fee scenarios.

## 6. Results — per year

Table: trades, return, profit factor, drawdown.

## 7. Results — per pair

Table: trades, return, profit factor. Flag any pair that dominates the result.

## 8. Acceptance criteria evaluation

One row per criterion, with the measured value and PASS/FAIL. Never summarise as
"mostly passed".

## 9. Limitations

Everything that could make this result wrong or non-generalisable. Include the
ones that are inconvenient.

## 10. Decision

The factual decision, the consequences for the programme, and the next
experiment ID. Cross-reference the decision record in
`research/decisions/DECISION_LOG.md`.
