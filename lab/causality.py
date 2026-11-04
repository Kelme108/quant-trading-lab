"""Generic, strategy-agnostic anti-lookahead checks.

A signal function `compute(frame) -> DataFrame` is causal when the value at row t depends only on rows <= t. Two
complementary tests, both run on any function, with synthetic or real data:

1. Prefix invariance: compute(frame[:cut]) must equal compute(frame)[:cut] for every cut. A shift(-n), a full-series
   normalisation or an un-windowed max/min changes values near the cut and is caught.
2. Future corruption: overwrite every row from `cut` onward with garbage; the output before `cut` must not change.

These do not replace Freqtrade's lookahead-analysis (which runs the real engine); they make the property testable
without Docker and for pure functions such as regime filters and pattern detectors.
"""

from __future__ import annotations

from typing import Callable, Iterable

import numpy as np
import pandas as pd


def _equal(a: pd.DataFrame, b: pd.DataFrame, tolerance: float) -> pd.Series:
    """Row-wise equality of two aligned frames, NaN == NaN, numeric tolerance."""
    both_nan = a.isna() & b.isna()
    close = pd.DataFrame(
        np.isclose(a.to_numpy(dtype=float), b.to_numpy(dtype=float), rtol=tolerance, atol=tolerance, equal_nan=True),
        index=a.index, columns=a.columns,
    )
    return (close | both_nan).all(axis=1)


def prefix_invariance(compute: Callable[[pd.DataFrame], pd.DataFrame], frame: pd.DataFrame, cuts: Iterable[int],
                      columns: list[str] | None = None, tolerance: float = 1e-9) -> list[str]:
    """Problems found (empty = causal at these cuts)."""
    full = compute(frame.copy())
    columns = columns or list(full.columns)
    problems = []
    for cut in cuts:
        part = compute(frame.iloc[:cut].copy())
        same = _equal(part[columns].astype(float), full[columns].iloc[:cut].astype(float), tolerance)
        if not same.all():
            first = int(np.flatnonzero(~same.to_numpy())[0])
            problems.append(f"cut {cut}: output differs from the full-series output at row {first}")
    return problems


def future_corruption(compute: Callable[[pd.DataFrame], pd.DataFrame], frame: pd.DataFrame, cut: int,
                      columns: list[str] | None = None, garbage: float = 1.0e6, tolerance: float = 1e-9) -> list[str]:
    """Overwrite numeric input columns from row `cut` onward; the output before `cut` must be unchanged."""
    original = compute(frame.copy())
    columns = columns or list(original.columns)
    broken = frame.copy()
    for name in broken.select_dtypes("number").columns:
        broken.iloc[cut:, broken.columns.get_loc(name)] = garbage
    after = compute(broken)
    same = _equal(after[columns].iloc[:cut].astype(float), original[columns].iloc[:cut].astype(float), tolerance)
    if same.all():
        return []
    return [f"output before row {cut} changed when only rows >= {cut} were corrupted (first at row {int(np.flatnonzero(~same.to_numpy())[0])})"]
