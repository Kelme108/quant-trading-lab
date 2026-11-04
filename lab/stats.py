"""Statistics that discount the number of configurations tried.

References (formulas implemented from the papers; no third-party code):
- Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio", Journal of Portfolio Management.
- Bailey, Borwein, Lopez de Prado & Zhu (2015), "The Probability of Backtest Overfitting", Journal of Computational Finance.

Everything works on PER-PERIOD (here daily) return series. Sharpe ratios are per period unless annualised
explicitly with `annualise`. These are diagnostics, not proofs: they assume the N configurations counted are all the
ones that were tried (the registry counts them), and returns that are roughly independent across periods.
"""

from __future__ import annotations

import itertools
import math
from statistics import NormalDist

import numpy as np

EULER_GAMMA = 0.5772156649015329
_NORMAL = NormalDist()


def sharpe(returns, *, ddof: int = 1) -> float:
    """Per-period Sharpe ratio (mean / std, zero risk-free). 0.0 for a constant or too-short series."""
    r = np.asarray(returns, dtype=float)
    if r.size < 2:
        return 0.0
    std = r.std(ddof=ddof)
    return float(r.mean() / std) if std > 0 else 0.0


def annualise(per_period_sharpe: float, periods_per_year: float = 365.0) -> float:
    return per_period_sharpe * math.sqrt(periods_per_year)


def _moments(returns) -> tuple[float, float]:
    """(skewness, kurtosis) with kurtosis NOT in excess form (normal = 3)."""
    r = np.asarray(returns, dtype=float)
    std = r.std(ddof=0)
    if std == 0:
        return 0.0, 3.0
    z = (r - r.mean()) / std
    return float((z**3).mean()), float((z**4).mean())


def probabilistic_sharpe(returns, benchmark_sharpe: float = 0.0) -> float:
    """PSR: probability that the true per-period Sharpe exceeds `benchmark_sharpe`, given the observed Sharpe,
    sample length, skewness and kurtosis (Bailey & Lopez de Prado 2012/2014)."""
    r = np.asarray(returns, dtype=float)
    n = r.size
    if n < 3:
        return float("nan")
    observed = sharpe(r)
    skew, kurt = _moments(r)
    denominator = 1.0 - skew * observed + (kurt - 1.0) / 4.0 * observed**2
    if denominator <= 0:
        return float("nan")
    return _NORMAL.cdf((observed - benchmark_sharpe) * math.sqrt(n - 1) / math.sqrt(denominator))


def expected_max_sharpe(n_trials: int, variance_of_trial_sharpes: float) -> float:
    """SR0: the Sharpe the best of `n_trials` unskilled configurations is expected to show by chance.

    SR0 = sqrt(V) * ((1 - g) * Phi^-1(1 - 1/N) + g * Phi^-1(1 - 1/(N e))), g = Euler-Mascheroni. N = 1 gives 0."""
    if n_trials <= 1 or variance_of_trial_sharpes <= 0:
        return 0.0
    return math.sqrt(variance_of_trial_sharpes) * (
        (1.0 - EULER_GAMMA) * _NORMAL.inv_cdf(1.0 - 1.0 / n_trials)
        + EULER_GAMMA * _NORMAL.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    )


def deflated_sharpe(returns, n_trials: int, variance_of_trial_sharpes: float) -> dict:
    """DSR: PSR evaluated at the expected maximum Sharpe of `n_trials` configurations.

    `variance_of_trial_sharpes` is the cross-sectional variance of the per-period Sharpe ratios of ALL tried
    configurations (use `trial_sharpe_variance`). A DSR below 0.95 means the result is not distinguishable from the
    best of N lucky draws at the usual confidence level."""
    sr0 = expected_max_sharpe(n_trials, variance_of_trial_sharpes)
    return {
        "sharpe_per_period": sharpe(returns),
        "sharpe_annualised": annualise(sharpe(returns)),
        "n_trials": n_trials,
        "sr0_per_period": sr0,
        "psr_vs_zero": probabilistic_sharpe(returns, 0.0),
        "dsr": probabilistic_sharpe(returns, sr0),
    }


def trial_sharpe_variance(returns_by_config) -> float:
    """Variance across configurations of their per-period Sharpe ratios (ddof=1)."""
    values = [sharpe(r) for r in returns_by_config]
    return float(np.var(values, ddof=1)) if len(values) > 1 else 0.0


def pbo_cscv(matrix, n_slices: int = 16) -> dict:
    """Probability of Backtest Overfitting by combinatorially symmetric cross-validation.

    `matrix` has shape (T periods, N configurations). Rows are cut into `n_slices` contiguous slices; for every way
    of choosing half of them as in-sample, the best in-sample configuration (by Sharpe) is ranked out-of-sample.
    PBO = share of splits where that configuration ends up at or below the OOS median (logit of its relative rank
    <= 0). Also returns the mean OOS Sharpe of the in-sample winner and the distribution of logits.
    """
    m = np.asarray(matrix, dtype=float)
    t, n = m.shape
    if n < 2:
        raise ValueError("PBO needs at least two configurations")
    if n_slices % 2 or n_slices < 4 or t < n_slices * 2:
        raise ValueError("n_slices must be even, >= 4, and the series at least 2 observations per slice")
    edges = np.linspace(0, t, n_slices + 1).astype(int)
    count = np.array([edges[i + 1] - edges[i] for i in range(n_slices)], dtype=float)
    total = np.stack([m[edges[i]:edges[i + 1]].sum(axis=0) for i in range(n_slices)])
    squares = np.stack([(m[edges[i]:edges[i + 1]] ** 2).sum(axis=0) for i in range(n_slices)])

    def sharpe_of(indices):
        idx = list(indices)
        k = count[idx].sum()
        s1, s2 = total[idx].sum(axis=0), squares[idx].sum(axis=0)
        mean = s1 / k
        var = np.maximum((s2 - k * mean**2) / (k - 1), 0.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(var > 0, mean / np.sqrt(var), 0.0)

    logits, oos_of_winner = [], []
    all_slices = set(range(n_slices))
    for in_sample in itertools.combinations(range(n_slices), n_slices // 2):
        out_sample = sorted(all_slices - set(in_sample))
        winner = int(np.argmax(sharpe_of(in_sample)))
        oos = sharpe_of(out_sample)
        rank = int((oos < oos[winner]).sum()) + 1  # 1 = worst
        relative = rank / (n + 1)
        logits.append(math.log(relative / (1.0 - relative)))
        oos_of_winner.append(float(oos[winner]))
    logits_arr = np.array(logits)
    return {
        "pbo": float((logits_arr <= 0).mean()),
        "n_splits": int(logits_arr.size),
        "n_configs": n,
        "n_slices": n_slices,
        "mean_oos_sharpe_of_is_winner": float(np.mean(oos_of_winner)),
        "median_logit": float(np.median(logits_arr)),
    }


def block_bootstrap_ci(values, statistic, *, block: int = 5, n_resamples: int = 4000, seed: int = 1,
                       level: float = 0.95) -> dict:
    """Moving-block bootstrap confidence interval of `statistic(sample)` for a 1-D series (seeded, reproducible).

    Intended for per-trade or per-day returns; `block` keeps short-range dependence. With fewer than ~100
    observations the interval is wide by design and the result carries `low_sample=True`."""
    x = np.asarray(values, dtype=float)
    n = x.size
    if n < 2:
        return {"estimate": float("nan"), "low": float("nan"), "high": float("nan"), "n": n, "low_sample": True}
    block = max(1, min(block, n))
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n / block)
    starts = rng.integers(0, n - block + 1, size=(n_resamples, n_blocks))
    offsets = np.arange(block)
    samples = x[(starts[:, :, None] + offsets[None, None, :]).reshape(n_resamples, -1)[:, :n]]
    stats = np.array([statistic(row) for row in samples])
    alpha = (1.0 - level) / 2.0
    return {
        "estimate": float(statistic(x)),
        "low": float(np.quantile(stats, alpha)),
        "high": float(np.quantile(stats, 1.0 - alpha)),
        "n": int(n),
        "low_sample": bool(n < 100),
    }
