"""Anchored walk-forward over a family of configurations.

For each fold the configuration with the best TRAIN Sharpe is chosen using data before the test window only, and
its TEST returns are recorded. The concatenated test returns are the honest out-of-sample series of "the procedure
of picking the best configuration": that is what a user of the grid would actually have experienced. Fixed-rule
strategies with no grid have nothing to select; they are evaluated by cycle instead (lab/cycles.py).

Input is a DataFrame of daily returns, one column per configuration, indexed by UTC day.
"""

from __future__ import annotations

import pandas as pd

from lab import stats


def anchored_folds(index: pd.DatetimeIndex, first_test_year: int, last_test_year: int) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    """(train_start, train_end, test_start, test_end) per calendar test year; train = everything before the year."""
    folds = []
    start = index.min()
    for year in range(first_test_year, last_test_year + 1):
        test_start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        test_end = pd.Timestamp(f"{year}-12-31", tz="UTC")
        train_end = test_start - pd.Timedelta(days=1)
        if start >= train_end or index.max() < test_start:
            continue
        folds.append((start, train_end, test_start, min(test_end, index.max())))
    return folds


def walk_forward(returns: pd.DataFrame, folds) -> dict:
    """Pick the best train-Sharpe column per fold; stitch the test returns."""
    pieces, chosen = [], []
    for train_start, train_end, test_start, test_end in folds:
        train = returns.loc[train_start:train_end]
        test = returns.loc[test_start:test_end]
        if len(train) < 30 or test.empty:
            continue
        scores = {column: stats.sharpe(train[column].to_numpy()) for column in returns.columns}
        best = max(scores, key=scores.get)
        pieces.append(test[best])
        chosen.append({"test_start": str(test_start.date()), "chosen": best, "train_sharpe_annualised": stats.annualise(scores[best]),
                       "test_sharpe_annualised": stats.annualise(stats.sharpe(test[best].to_numpy())),
                       "test_return": float((1 + test[best]).prod() - 1)})
    if not pieces:
        return {"folds": [], "oos_returns": pd.Series(dtype=float)}
    oos = pd.concat(pieces)
    return {"folds": chosen, "oos_returns": oos, "oos_sharpe_annualised": stats.annualise(stats.sharpe(oos.to_numpy())),
            "oos_return": float((1 + oos).prod() - 1)}
