"""Hand-calculated checks for the reference model (implementation plan §4.2).

Each case's expected numbers are worked out in its comment so they can be
re-derived by hand. AI contribution: drafted with Claude Code (Opus 5.5);
the arithmetic in each comment should be re-checked by the project author.
"""
import math

import numpy as np
import pytest

from etf_risk.model import STATUS_BREACH, STATUS_OK, simulate_path, summarize_path

approx = lambda x: pytest.approx(x, rel=1e-12, abs=1e-12)  # noqa: E731


def test_zero_returns_keep_nav_flat():
    path = simulate_path([0.0, 0.0, 0.0], leverage=2.0)
    assert path["nav"].tolist() == [100.0, 100.0, 100.0]
    assert path["rebalance"].tolist() == [0.0, 0.0, 0.0]
    assert summarize_path(path)["max_drawdown"] == 0.0


def test_single_up_day():
    # V1 = 100 * (1 + 2*0.10) = 120
    # before = 2 * 100 * 1.10 = 220; target = 2 * 120 = 240; rebalance = +20
    row = simulate_path([0.10], leverage=2.0).iloc[0]
    assert row["nav"] == approx(120.0)
    assert row["exposure_before"] == approx(220.0)
    assert row["exposure_target"] == approx(240.0)
    assert row["rebalance"] == approx(20.0)


def test_single_down_day():
    # V1 = 100 * (1 - 0.20) = 80; before = 2*100*0.9 = 180; target = 160; rebalance = -20
    path = simulate_path([-0.10], leverage=2.0)
    row = path.iloc[0]
    assert row["nav"] == approx(80.0)
    assert row["rebalance"] == approx(-20.0)
    assert summarize_path(path)["max_drawdown"] == approx(0.20)


def test_two_up_days_compound_above_twice_the_underlying():
    # 2x: 100 -> 120 -> 144 (+44%); underlying: 100 -> 110 -> 121 (+21%); 2 * 21% = 42%
    # day-2 rebalance = L(L-1) * V1 * r = 2 * 1 * 120 * 0.1 = 24
    two_x = simulate_path([0.10, 0.10], leverage=2.0)
    one_x = simulate_path([0.10, 0.10], leverage=1.0)
    assert two_x["nav"].tolist() == [approx(120.0), approx(144.0)]
    assert one_x["nav"].iloc[-1] == approx(121.0)
    assert two_x["rebalance"].iloc[1] == approx(24.0)
    assert summarize_path(two_x)["total_return"] == approx(0.44)


def test_round_trip_underlying_loses_value_at_2x():
    # Underlying: +10%, then -1/11 -> 100 * 1.1 * 10/11 = 100 (flat).
    # 2x: 100 -> 120 -> 120 * (1 - 2/11) = 1080/11 ~= 98.1818
    # day-2 rebalance = 2 * 1 * 120 * (-1/11) = -240/11; max drawdown = 1 - (1080/11)/120 = 2/11
    returns = [0.10, -1.0 / 11.0]
    two_x = simulate_path(returns, leverage=2.0)
    one_x = simulate_path(returns, leverage=1.0)
    assert one_x["nav"].iloc[-1] == approx(100.0)
    assert two_x["nav"].iloc[-1] == approx(1080.0 / 11.0)
    assert two_x["rebalance"].iloc[1] == approx(-240.0 / 11.0)
    assert summarize_path(two_x)["max_drawdown"] == approx(2.0 / 11.0)


def test_unleveraged_path_never_rebalances():
    rng = np.random.default_rng(0)
    path = simulate_path(rng.normal(0, 0.03, 50), leverage=1.0)
    assert (path["rebalance"] == 0.0).all()


@pytest.mark.parametrize("leverage", [1.5, 2.0, 3.0])
def test_rebalance_matches_closed_form(leverage):
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.03, 100)
    path = simulate_path(r, leverage)
    closed_form = leverage * (leverage - 1.0) * path["nav_start"] * path["daily_return"]
    np.testing.assert_allclose(path["rebalance"], closed_form, rtol=1e-9, atol=1e-9)


def test_drawdown_counts_initial_nav_as_a_peak():
    # Falls from day 1, so the only peak is the initial 100: 100 -> 90 -> 81 at 1x
    path = simulate_path([-0.10, -0.10], leverage=1.0)
    assert path["running_peak"].tolist() == [100.0, 100.0]
    assert summarize_path(path)["max_drawdown"] == approx(0.19)


# --- model breach: these need the TODO in model.simulate_path ---------------

def test_breach_stops_the_path():
    # Day 2: 1 + 2 * (-0.6) = -0.2 <= 0 -> breach on day 2
    path = simulate_path([0.10, -0.60, 0.05], leverage=2.0)
    s = summarize_path(path)
    assert s["breached"] is True
    assert s["breach_day"] == 2
    assert s["days_ok"] == 1
    assert math.isnan(s["final_nav"])
    assert not (path["nav"] < 0).any()
    assert (path.loc[path["day"] > 2, "status"] != STATUS_OK).all()


def test_exact_minus_50_percent_at_2x_is_a_breach():
    # 1 + 2 * (-0.5) = 0 -> NAV would be exactly 0; the boundary rule is "<= 0"
    path = simulate_path([-0.50], leverage=2.0)
    assert path.loc[path["day"] == 1, "status"].item() == STATUS_BREACH


# --- invalid inputs are errors, not breaches --------------------------------

@pytest.mark.parametrize("returns", [[0.01, float("nan")], [float("inf")], [-1.5]])
def test_invalid_returns_raise(returns):
    with pytest.raises(ValueError):
        simulate_path(returns, leverage=2.0)


@pytest.mark.parametrize("leverage", [0.0, -2.0, float("nan")])
def test_invalid_leverage_raises(leverage):
    with pytest.raises(ValueError):
        simulate_path([0.01], leverage=leverage)
