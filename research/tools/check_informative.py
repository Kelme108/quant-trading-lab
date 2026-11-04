"""Run INSIDE the Freqtrade container: prove merge_informative_pair of 1d candles into 1h is causal.

  docker run --rm --entrypoint python -v <repo>/user_data:/freqtrade/user_data -v <repo>/research/tools:/chk:ro \
      freqtradeorg/freqtrade:2026.9 /chk/check_informative.py

Checks (BTC/USDT, real data):
 1. The daily value shown on a 1h row dated t is the candle of day floor(t+1h)-1 day. Freqtrade makes the daily candle
    visible on the 1h row dated 23:00, whose close time (00:00 UTC) is the daily close; orders execute at the next open.
 2. Corrupting every daily candle from a cut-off date onward leaves all merged rows before that date unchanged.
"""
import sys

import pandas as pd
from freqtrade.strategy import merge_informative_pair

base = "/freqtrade/user_data/data/binance/BTC_USDT-"
h = pd.read_feather(base + "1h.feather")
d = pd.read_feather(base + "1d.feather")
for frame in (h, d):
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
h = h[h["date"] >= "2022-01-01"].reset_index(drop=True)
d = d.reset_index(drop=True)


def merged(daily):
    return merge_informative_pair(h.copy(), daily.copy(), "1h", "1d", ffill=True)


m = merged(d)
expected_day = (m["date"] + pd.Timedelta(hours=1)).dt.floor("D") - pd.Timedelta(days=1)
lookup = d.set_index("date")["close"]
expected = expected_day.map(lookup)
valid = m["close_1d"].notna()
bad1 = int(((m.loc[valid, "close_1d"] - expected[valid]).abs() > 1e-9).sum())
print(f"check 1: rows compared {int(valid.sum())}, mismatches {bad1}")

cut = pd.Timestamp("2023-06-01", tz="UTC")
d2 = d.copy()
future = d2["date"] >= cut
d2.loc[future, ["open", "high", "low", "close", "volume"]] = 123456.0
m2 = merged(d2)
before = m["date"] < cut
bad2 = int((~((m.loc[before, "close_1d"].fillna(-1) == m2.loc[before, "close_1d"].fillna(-1)))).sum())
print(f"check 2: rows before cut-off {int(before.sum())}, changed by future corruption {bad2}")
sys.exit(1 if (bad1 or bad2) else 0)
