"""b3/freqtrade_adapter.py and b3/ftshim: a Freqtrade strategy file runs unchanged in the B3 engine. Synthetic data."""

import json
import textwrap
from datetime import date

import numpy as np
import pandas as pd
import pytest

from b3 import freqtrade_adapter as fa
from b3.backtest import BacktestConfig, run
from tests.b3.test_b3_lane import weekdays, write_win
from b3 import b3_data
from b3.calendar import SessionRules

fa.ensure_imports()
from freqtrade.strategy import merge_informative_pair  # noqa: E402  (the shim)

STRATEGY = textwrap.dedent('''
    from datetime import timedelta
    import pandas as pd
    from pandas import DataFrame
    from freqtrade.strategy import IStrategy, informative
    from freqtrade.persistence import Trade


    class ToyHourly_T1(IStrategy):
        timeframe = "15m"
        stoploss = -0.01
        startup_candle_count = 8
        use_custom_stoploss = True
        minimal_roi = {"0": 100.0}

        @property
        def protections(self):
            return [{"method": "CooldownPeriod", "stop_duration_candles": 4}]

        @informative("1h")
        def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
            dataframe["mean4"] = dataframe["close"].rolling(4).mean()
            return dataframe

        def populate_indicators(self, dataframe, metadata):
            dataframe["up"] = dataframe["close"] > dataframe["close"].shift(1)
            return dataframe

        def populate_entry_trend(self, dataframe, metadata):
            dataframe.loc[dataframe["up"] & dataframe["mean4_1h"].notna(), ["enter_long", "enter_tag"]] = (1, "toy_up")
            return dataframe

        def populate_exit_trend(self, dataframe, metadata):
            dataframe.loc[~dataframe["up"], ["exit_long", "exit_tag"]] = (1, "toy_down")
            return dataframe

        def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, after_fill=False, **kw):
            return -0.002 if current_profit > 0.001 else None

        def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side,
                                **kw):
            return all(t.open_date_utc.date() != current_time.date() or not t.is_open
                       for t in Trade.get_trades_proxy(pair=pair))
''')


@pytest.fixture
def toy(tmp_path):
    path = tmp_path / "ToyHourly_T1.py"
    path.write_text(STRATEGY, encoding="utf-8")
    return path


def test_shim_merge_equals_the_exact_join_rule_on_24_hour_data():
    base = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=48, freq="15min", tz="UTC"),
                         "close": np.arange(48.0)})
    inf = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=12, freq="1h", tz="UTC"),
                        "close": np.arange(12.0) * 10})
    out = merge_informative_pair(base, inf.copy(), "15m", "1h", ffill=True)
    # Freqtrade: the 1h candle of HH:00 joins the 15m candle of HH:45 (date + 60 - 15) and is forward-filled
    expected = inf.assign(date_merge=inf["date"] + pd.Timedelta(minutes=45))
    exact = base.merge(expected.rename(columns={"close": "close_1h", "date": "date_1h"}), left_on="date",
                       right_on="date_merge", how="left").ffill()
    assert list(out["close_1h"].fillna(-1)) == list(exact["close_1h"].fillna(-1))
    assert out["close_1h"].iloc[2] != out["close_1h"].iloc[2] and out["close_1h"].iloc[3] == 0.0   # NaN, then 0


def test_portability_excludes_other_pairs(tmp_path):
    p = tmp_path / "X.py"
    p.write_text('class X(IStrategy):\n    def informative_pairs(self):\n        return [("BTC/USDT", "1h")]\n')
    assert fa.portability("X", p)["portable"] is False
    real = fa.strategy_files()
    assert len(real) >= 130
    port = [fa.portability(n, f) for n, f in real.items()]
    assert sum(x["portable"] for x in port) >= 120
    assert not next(x for x in port if x["strategy"] == "RelativeStrengthRatioRotation_H047_v1")["portable"]


def test_a_freqtrade_strategy_runs_on_win_flat_before_the_close(tmp_path, toy):
    days = weekdays(date(2025, 3, 3), 12)
    write_win(tmp_path, days)
    bars = b3_data.load_b3_bars("WIN", "5m", tmp_path).assign(adj_offset=0.0)
    rule_cls = fa.make_rule("ToyHourly_T1", toy).on("WIN")
    cal = b3_data.history_calendar("WIN", bars, rule_cls.rules)
    s = rule_cls(cal)
    assert s.name == "C-ToyHourly_T1" and s.price_series == "back_adjusted" and s.timeframe_min == 5
    res = run(bars, s, s.market.cost("base"), BacktestConfig(allow_short=False))
    tr = res.trades_frame()
    assert len(tr) > 5 and res.positions_held_overnight == 0
    assert set(tr["exit_reason"]) <= {"toy_down", "stop_loss", "end_of_day_flatten", "end_of_data"}
    assert "toy_down" in set(tr["exit_reason"])
    # entries only on strategy-candle closes: fills at :00, :15, :30, :45
    minutes = pd.to_datetime(tr["entry_time"]).dt.minute
    assert set(minutes) <= {0, 15, 30, 45}
    # cooldown of 4 candles = 60 minutes after each close
    t = tr.sort_values("entry_time")
    gaps = (pd.to_datetime(t["entry_time"]).iloc[1:].to_numpy() - pd.to_datetime(t["exit_time"]).iloc[:-1].to_numpy())
    same_day = pd.to_datetime(t["entry_time"]).dt.date.iloc[1:].to_numpy() == pd.to_datetime(t["exit_time"]).dt.date.iloc[:-1].to_numpy()
    assert all(g >= np.timedelta64(60, "m") for g, d in zip(gaps, same_day) if d)
    # every stop is on the WIN grid
    assert all(abs(x / 5 - round(x / 5)) < 1e-9 for x in tr["stop_price"])
    assert s.hash == rule_cls(cal).hash and len(s.hash) == 12


def test_the_runner_reads_a_ported_strategy_in_the_b3_lane(tmp_path, toy, monkeypatch, lane):
    import b3.proxy_research as pr
    cls = fa.make_rule("ToyHourly_T1", toy)
    monkeypatch.setitem(pr.RULES, "C-ToyHourly_T1", cls)
    out = pr.evaluate("C-ToyHourly_T1", "WIN", "exploration", data_dir=lane, family="crypto-screen")
    assert out["price_series"] == "back_adjusted" and out["scenarios"]["base"]["trades"] > 0
    assert pr.ledger_rows(pr.B3_LEDGER)[-1]["family"] == "crypto-screen"


from tests.b3.test_b3_lane import lane  # noqa: E402,F401  (fixture)
