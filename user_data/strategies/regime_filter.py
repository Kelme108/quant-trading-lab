"""Causal regime filter on DAILY candles (pure functions, no state, no I/O).

Input is the daily close series (one row per CLOSED day, the day's own close). Strategies compute the flags on the
daily dataframe in populate_indicators and merge them into the 1h frame with merge_informative_pair, which exposes a
day only after it has closed. Every value at day t uses days <= t only (trailing windows, no centering, no
full-series statistics).

Ex-ante values: window=30, ratio=1.5, sma_days=200. At most three numeric parameters.
Warm-up on the daily frame: 365 + window + 1 days for vol_regime, sma_days for trend_regime. Strategies using
vol_regime therefore set startup_candle_count >= 400 (it applies to every timeframe loaded).
"""

import numpy as np
import pandas as pd

MEDIAN_DAYS = 365

# Step 1.4 ablation (research/regime-filter-ablation.md): vol_regime did not meet the pre-registered benefit
# criterion, so it is available but OFF unless a strategy asks for it explicitly.
VOL_REGIME_ON_BY_DEFAULT = False


def vol_regime(close_1d: pd.Series, window: int = 30, ratio: float = 1.5) -> pd.Series:
    """True when realised volatility is <= ratio x its own trailing 365-day median.

    Realised volatility = standard deviation of daily log returns over `window` days. False while undefined.
    """
    log_return = np.log(close_1d.astype(float)).diff()
    vol = log_return.rolling(window).std()
    median = vol.rolling(MEDIAN_DAYS).median()
    return (vol <= ratio * median).fillna(False)


def trend_regime(close_1d: pd.Series, sma_days: int = 200) -> pd.Series:
    """True when the closed daily close is above its trailing SMA(sma_days). False while undefined."""
    sma = close_1d.astype(float).rolling(sma_days).mean()
    return (close_1d > sma).fillna(False)


def regime_on(close_1d: pd.Series, window: int = 30, ratio: float = 1.5, sma_days: int = 200,
              use_vol: bool = VOL_REGIME_ON_BY_DEFAULT, use_trend: bool = True) -> pd.Series:
    """AND of the enabled regimes (vol off by default, see VOL_REGIME_ON_BY_DEFAULT). Both disabled = neutral (True)."""
    on = pd.Series(True, index=close_1d.index)
    if use_vol:
        on &= vol_regime(close_1d, window, ratio)
    if use_trend:
        on &= trend_regime(close_1d, sma_days)
    return on
