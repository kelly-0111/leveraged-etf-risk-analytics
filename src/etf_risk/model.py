"""Reference (sequential, single-path) daily-reset leveraged return model.

Model, assumptions and breach rule: docs/spec.md, section 3. With r_t the
underlying simple daily return, L the daily target leverage and V_(t-1) the
start-of-day NAV:

    V_t               = V_(t-1) * (1 + L * r_t)
    exposure_before_t = L * V_(t-1) * (1 + r_t)    # end of day, before reset
    exposure_target_t = L * V_t                    # after reset
    rebalance_t       = exposure_target_t - exposure_before_t
                      = L * (L - 1) * V_(t-1) * r_t

Positive rebalance = add exposure, negative = cut exposure. This is a
model-implied amount, not observed trading. Fees, financing, flows and
execution are ignored, so this is not a forecast of any real ETF's NAV.

When 1 + L * r_t <= 0 the model breaks (NAV would hit zero or go negative):
the day is marked STATUS_BREACH and normal NAV updates stop.

The Spark pipeline calls simulate_path() for each path, so Python and Spark
use the same model rules.

AI contribution: drafted with Claude Code (Opus 5.5); the breach branch in
simulate_path() was written by the project author. Verified with the
hand-calculated cases in tests/test_model.py.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

STATUS_OK = "ok"
STATUS_BREACH = "breach"

PATH_COLUMNS = [
    "day", "daily_return", "nav_start", "nav",
    "exposure_before", "exposure_target", "rebalance", "status",
]


def simulate_path(daily_returns: Sequence[float], leverage: float, initial_nav: float = 100.0) -> pd.DataFrame:
    """Run the model over one ordered return path.

    `daily_returns[i]` is the return of day i + 1. The caller must order it and
    remove the first-row null return beforehand; NaN input is rejected.

    Returns one row per simulated day (PATH_COLUMNS + running_peak, drawdown).
    """
    returns = np.asarray(daily_returns, dtype=float)
    _check_inputs(returns, leverage, initial_nav)

    rows: list[dict] = []
    nav = initial_nav
    for day, r in enumerate(returns, start=1):
        growth = 1.0 + leverage * r
        if growth <= 0.0:
            # Model breach: NAV would be <= 0, so the model has no valid value.
            # Record the day with NaN NAV / target / rebalance and stop; later
            # days are not output, so a breached path is shorter than its input.
            rows.append({
                "day": day,
                "daily_return": r,
                "nav_start": nav,
                "nav": np.nan,
                "exposure_before": leverage * nav * (1.0 + r),
                "exposure_target": np.nan,
                "rebalance": np.nan,
                "status": STATUS_BREACH,
            })
            break

        nav_start = nav
        nav = nav_start * growth
        exposure_before = leverage * nav_start * (1.0 + r)
        exposure_target = leverage * nav
        rows.append({
            "day": day,
            "daily_return": r,
            "nav_start": nav_start,
            "nav": nav,
            "exposure_before": exposure_before,
            "exposure_target": exposure_target,
            "rebalance": exposure_target - exposure_before,
            "status": STATUS_OK,
        })

    path = pd.DataFrame(rows, columns=PATH_COLUMNS)
    return _add_drawdown(path, initial_nav)


def summarize_path(path: pd.DataFrame, initial_nav: float = 100.0) -> dict:
    """Path-level metrics. Return metrics are NaN for breached paths; callers
    should report breached paths separately, not drop them."""
    ok = path[path["status"] == STATUS_OK]
    breach_days = path.loc[path["status"] == STATUS_BREACH, "day"]
    breached = not breach_days.empty

    final_nav = float("nan") if breached or ok.empty else float(ok["nav"].iloc[-1])
    abs_rebalance = ok["rebalance"].abs().to_numpy()
    return {
        "days_ok": len(ok),
        "breached": breached,
        "breach_day": int(breach_days.min()) if breached else None,
        "final_nav": final_nav,
        "total_return": final_nav / initial_nav - 1.0,
        # Over pre-breach days; the initial NAV counts as a peak candidate.
        "max_drawdown": float(np.max(ok["drawdown"].to_numpy(), initial=0.0)),
        "total_abs_rebalance": float(abs_rebalance.sum()),
        "max_abs_rebalance": float(np.max(abs_rebalance, initial=0.0)),
    }


def _add_drawdown(path: pd.DataFrame, initial_nav: float) -> pd.DataFrame:
    navs = np.concatenate([[initial_nav], path["nav"].to_numpy(dtype=float)])
    # fmax ignores NaN, so a NaN NAV (if used for a breach row) does not wipe out the peak.
    peaks = np.fmax.accumulate(navs)[1:]
    path["running_peak"] = peaks
    path["drawdown"] = 1.0 - path["nav"].to_numpy(dtype=float) / peaks
    return path


def _check_inputs(returns: np.ndarray, leverage: float, initial_nav: float) -> None:
    if returns.ndim != 1:
        raise ValueError("daily_returns must be one-dimensional")
    if not np.isfinite(returns).all():
        raise ValueError("daily_returns contains NaN or infinite values")
    if (returns < -1.0).any():
        raise ValueError("daily_returns contains a return below -100%")
    if not (np.isfinite(leverage) and leverage > 0):
        raise ValueError("leverage must be finite and > 0 (no inverse leverage in v1)")
    if not (np.isfinite(initial_nav) and initial_nav > 0):
        raise ValueError("initial_nav must be finite and > 0")
