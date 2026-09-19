"""Unit tests for the DEC-007 diagnostic walk-forward harness.

These tests exercise the pure harness logic only. They do **not** run a
backtest and do not require freqtrade, so they run in CI.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.research

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = PROJECT_ROOT / "research" / "walk_forward" / "run_walk_forward.py"
CONFIG_PATH = PROJECT_ROOT / "research" / "walk_forward" / "walk_forward_config.json"


def _load_harness():
    """
    Load the harness module by path.

    :return: Imported module object.
    """
    spec = importlib.util.spec_from_file_location("run_walk_forward", HARNESS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wf = _load_harness()


def _sample_result(*, funding: float = 0.0) -> dict:
    """
    Build a minimal freqtrade-shaped result for summarise().

    :param funding: Funding PnL to attach to the winning trade.
    :return: Result dictionary.
    """
    trades = [
        {
            "amount": 1.0,
            "open_rate": 100.0,
            "close_rate": 110.0,
            "fee_open": 0.0005,
            "fee_close": 0.0005,
            "profit_abs": 10.0,
            "trade_duration": 60,
            "is_short": False,
            "min_rate": 99.0,
            "max_rate": 111.0,
            "funding_fees": funding,
        },
        {
            "amount": 1.0,
            "open_rate": 100.0,
            "close_rate": 95.0,
            "fee_open": 0.0005,
            "fee_close": 0.0005,
            "profit_abs": -5.0,
            "trade_duration": 30,
            "is_short": False,
            "min_rate": 94.0,
            "max_rate": 101.0,
            "funding_fees": 0.0,
        },
    ]
    strategy = {
        "total_trades": 2,
        "starting_balance": 1000.0,
        "final_balance": 1005.0,
        "profit_total_abs": 5.0,
        "profit_total": 0.005,
        "cagr": 0.01,
        "profit_factor": 2.0,
        "expectancy": 2.5,
        "expectancy_ratio": 0.5,
        "profit_mean": 0.0025,
        "profit_median": 0.0025,
        "sharpe": 1.0,
        "sortino": 1.2,
        "sqn": 0.5,
        "p_value": 0.3,
        "winrate": 0.5,
        "wins": 1,
        "losses": 1,
        "draws": 0,
        "max_relative_drawdown": 0.02,
        "wallet_stats": {"max_relative_drawdown": 0.03},
        "holding_avg_s": 100.0,
        "market_change": 0.01,
        "backtest_days": 10.0,
        "trades": trades,
        "results_per_pair": [{"key": "TOTAL", "trades": 2, "profit_total": 0.005}],
    }
    return {"strategy": {"Sample": strategy}}


class TestWindows:
    """The frozen window scheme must be honoured exactly."""

    def test_resolve_windows_matches_config(self) -> None:
        config = wf.load_config(CONFIG_PATH)
        windows = wf.resolve_windows(config)

        assert len(windows) == len(config["windows"]) == 4
        assert [w["id"] for w in windows] == ["W1", "W2", "W3", "W4"]
        anchor = config["methodology"]["is_anchor"]
        assert all(w["is_start"] == anchor for w in windows)

    def test_is_end_equals_oos_start_and_timeranges(self) -> None:
        windows = wf.resolve_windows(wf.load_config(CONFIG_PATH))
        for window in windows:
            assert window["is_end"] == window["oos_start"]
            assert window["is_timerange"] == f"{window['is_start']}-{window['is_end']}"
            assert window["oos_timerange"] == f"{window['oos_start']}-{window['oos_end']}"

    def test_non_pristine_labels(self) -> None:
        windows = {w["id"]: w for w in wf.resolve_windows(wf.load_config(CONFIG_PATH))}
        assert windows["W1"]["non_pristine"] is False
        assert windows["W2"]["non_pristine"] is False
        assert windows["W3"]["non_pristine"] is True
        assert windows["W4"]["non_pristine"] is True

    def test_anchor_mismatch_raises(self) -> None:
        config = wf.load_config(CONFIG_PATH)
        config["windows"][0]["is_start"] = "20180101"

        with pytest.raises(ValueError):
            wf.resolve_windows(config)


class TestCommandAndSummary:
    """Command construction and metric extraction."""

    def test_build_command_is_backtesting_not_search(self) -> None:
        config = wf.load_config(CONFIG_PATH)
        window = wf.resolve_windows(config)[0]
        arm = config["arms"]["long_vol"]
        command = wf.build_command(arm, window["oos_timerange"], config, Path("strategies"))

        assert command[:3] == [wf.sys.executable, "-m", "freqtrade"]
        assert "backtesting" in command
        assert "TurtleFuturesLong" in command
        assert window["oos_timerange"] in command
        for forbidden in ("hyperopt", "optimize", "--spaces", "--epochs"):
            assert forbidden not in command

    def test_summarise_extracts_metrics_and_funding(self) -> None:
        summary = wf.summarise(_sample_result(funding=-1.25))

        for key in wf.METRIC_KEYS:
            assert key in summary
        assert summary["trades"] == 2
        assert summary["profit_factor"] == pytest.approx(2.0)
        assert summary["funding_fees_applied_usdt"] == pytest.approx(-1.25)


class TestStabilityAndDecay:
    """Stability and decay summaries."""

    def _oos(self, returns: list[float], pfs: list[float]) -> list[dict]:
        return [
            {"net_profit_pct": r, "profit_factor": p} for r, p in zip(returns, pfs, strict=True)
        ]

    def test_compute_stability_mixed(self) -> None:
        result = wf.compute_stability(self._oos([5.0, 3.0, -4.0, 8.0], [1.2, 1.1, 0.8, 1.5]))

        assert result["windows"] == 4
        assert result["positive_windows"] == 3
        assert result["positive_fraction"] == pytest.approx(0.75)
        assert result["sign_consistent"] is False
        assert result["pf_min"] == pytest.approx(0.8)
        assert result["pf_max"] == pytest.approx(1.5)

    def test_compute_stability_all_positive(self) -> None:
        result = wf.compute_stability(self._oos([1.0, 2.0], [1.1, 1.2]))

        assert result["sign_consistent"] is True
        assert result["positive_fraction"] == pytest.approx(1.0)

    def test_compute_decay_ratios(self) -> None:
        records = [
            {
                "window": "W1",
                "is_metrics": {"expectancy": 2.0, "net_profit_pct": 10.0},
                "oos_metrics": {"expectancy": 1.0, "net_profit_pct": 4.0},
            },
            {
                "window": "W2",
                "is_metrics": {"expectancy": 4.0, "net_profit_pct": 8.0},
                "oos_metrics": {"expectancy": -1.0, "net_profit_pct": -2.0},
            },
        ]
        decay = wf.compute_decay(records)

        assert decay["per_window"][0]["oos_over_is_expectancy"] == pytest.approx(0.5)
        assert decay["per_window"][1]["oos_over_is_expectancy"] == pytest.approx(-0.25)
        assert decay["mean_oos_over_is_expectancy"] == pytest.approx(0.125)


class TestReproducibility:
    """Pass comparison ignores nothing but must catch metric drift."""

    def test_identical_passes_pass(self) -> None:
        pass1 = {"a|W1|oos|pass1": {"metrics": {"trades": 1, "profit_factor": 1.1}}}
        pass2 = {"a|W1|oos|pass2": {"metrics": {"trades": 1, "profit_factor": 1.1}}}

        wf.assert_reproducible(pass1, pass2)

    def test_metric_mismatch_raises(self) -> None:
        pass1 = {"a|W1|oos|pass1": {"metrics": {"trades": 1, "profit_factor": 1.1}}}
        pass2 = {"a|W1|oos|pass2": {"metrics": {"trades": 1, "profit_factor": 1.2}}}

        with pytest.raises(AssertionError):
            wf.assert_reproducible(pass1, pass2)


class TestConfigFrozen:
    """The config must not contain any search space."""

    def test_no_parameter_search_keys(self) -> None:
        config = wf.load_config(CONFIG_PATH)

        assert config["methodology"]["parameter_selection"] == "NONE"
        serialised = str(config)
        for forbidden in ("candidates", "param_grid", "search_space", "hyperopt"):
            assert forbidden not in serialised

    def test_arms_are_the_authorised_engines(self) -> None:
        config = wf.load_config(CONFIG_PATH)

        assert set(config["arms"]) == {"long_vol", "long_raw", "carry"}
        assert config["arms"]["long_vol"]["strategy"] == "TurtleFuturesLong"
        assert config["arms"]["long_raw"]["strategy"] == "TurtleFuturesLongRaw"
        assert config["arms"]["carry"]["strategy"] == "FundingCarry"


class TestProductionGuard:
    """Production strategy subtrees must remain untouched."""

    def test_production_subtrees_have_no_diff(self) -> None:
        try:
            completed = subprocess.run(
                ["git", "diff", "--numstat", "--", "user_data/strategies"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            pytest.skip("git is not available")
        if completed.returncode != 0:
            pytest.skip("git diff is unavailable in this checkout")

        assert completed.stdout.strip() == ""
