import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from lab import forward, livedata  # noqa: E402


class LiveDataTests(unittest.TestCase):
    def setUp(self) -> None:
        livedata._cache.clear()
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name)
        (self.root / "research" / "forward").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_clean_turns_infinity_and_nan_into_null(self) -> None:
        out = livedata.clean({"a": float("inf"), "b": [float("nan"), 1.5], "c": {"d": float("-inf")}})
        self.assertEqual(out, {"a": None, "b": [None, 1.5], "c": {"d": None}})

    def test_the_chart_carries_candles_and_the_last_price(self) -> None:
        candles = [[1000, 1.0, 2.0, 0.5, 1.5, 10.0], [4600, 1.5, 2.5, 1.0, 2.0, 12.0]]
        payload = livedata.live_chart("BTC/USDT", "1h", self.root, fetch=lambda pair, tf: candles)
        self.assertEqual(payload["source"], "binance")
        self.assertEqual(payload["last_price"], 2.0)
        self.assertEqual(payload["bots"], [])
        self.assertEqual(payload["step"], 3600)

    def test_without_network_it_falls_back_to_the_local_file_and_says_so(self) -> None:
        def broken(pair, tf):
            raise OSError("offline")
        payload = livedata.live_chart("ETH/USDT", "15m", self.root, fetch=broken)
        self.assertIn("disco", payload["source"])
        self.assertEqual(payload["candles"], [])
        self.assertIsNone(payload["last_price"])

    def test_unknown_pairs_and_timeframes_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            livedata.live_chart("EVIL/USDT", "1h", self.root, fetch=lambda p, t: [])
        with self.assertRaises(ValueError):
            livedata.live_chart("BTC/USDT", "5m", self.root, fetch=lambda p, t: [])

    def test_unrealised_result_uses_the_current_price(self) -> None:
        self.assertAlmostEqual(livedata._unrealised({"open_rate": 100.0}, 101.5), 1.5)
        self.assertIsNone(livedata._unrealised({"open_rate": 100.0}, None))

    def test_prices_fail_quietly(self) -> None:
        def broken(pair):
            raise OSError("offline")
        self.assertEqual(livedata.last_prices(self.root, fetch=broken), {})

    def multi_pair_bot(self) -> None:
        sys.path.insert(0, str(Path(__file__).parent))
        from test_lab_dryrun import multi_pair_root
        from test_lab_forward import CLOSED, OPEN, make_database
        multi_pair_root(self.root, ["ETH/USDT", "SOL/USDT"])
        make_database(self.root / forward.multi_database_path("H-105"), [
            {**CLOSED, "id": 1, "pair": "ETH/USDT"},
            {**CLOSED, "id": 2, "pair": "SOL/USDT", "close_profit": -0.01, "close_profit_abs": -2.5},
            {**OPEN, "id": 3, "pair": "SOL/USDT"},
        ], [])
        (self.root / "research" / "forward" / "H-105-freeze.json").write_text(json.dumps({
            "hypothesis": "H-105", "frozen_at_utc": "2026-11-10T00:00:00+00:00", "strategy": {"class": "X_H105_v1"},
            "layout": forward.MULTI_PAIR, "databases": {p: forward.pair_selector(forward.multi_database_path("H-105"), p)
                                                         for p in ("ETH/USDT", "SOL/USDT")}}), encoding="utf-8")

    def test_a_multi_pair_bot_shows_per_pair_data_in_the_same_shape(self) -> None:
        self.multi_pair_bot()
        state = livedata.bots_state(self.root, prices={"SOL/USDT": 101.0})
        bot = state["bots"][0]
        self.assertNotIn("error", bot)
        self.assertEqual(set(bot), {"id", "strategy", "frozen_at", "verdict", "reasons", "pooled", "wallet", "pairs", "open",
                                    "closed", "need_trades", "need_days"})
        self.assertEqual(bot["wallet"], 2000.0)
        self.assertEqual(set(bot["pairs"]), {"ETH/USDT", "SOL/USDT"})
        self.assertEqual((bot["pairs"]["ETH/USDT"]["trades"], bot["pairs"]["ETH/USDT"]["open"]), (1, 0))
        self.assertEqual((bot["pairs"]["SOL/USDT"]["trades"], bot["pairs"]["SOL/USDT"]["open"]), (1, 1))
        self.assertEqual([t["pair"] for t in bot["open"]], ["SOL/USDT"])
        self.assertAlmostEqual(bot["open"][0]["unrealised_pct"], 1.0)
        self.assertEqual(sorted(t["pair"] for t in bot["closed"]), ["ETH/USDT", "SOL/USDT"])

        chart = livedata.live_chart("SOL/USDT", "1h", self.root, fetch=lambda pair, tf: [[1000, 1, 2, 0.5, 1.5, 10]])
        self.assertEqual(chart["pairs"], ["ETH/USDT", "SOL/USDT"])
        self.assertEqual([b["id"] for b in chart["bots"]], ["H-105"])
        self.assertEqual(len(chart["bots"][0]["trades"]), 2)          # only SOL's two trades, not ETH's
        self.assertEqual(sorted(m["is_open"] for m in chart["bots"][0]["trades"]), [False, True])
        other = livedata.live_chart("BTC/USDT", "1h", self.root, fetch=lambda pair, tf: [])
        self.assertEqual(other["bots"], [])                            # the bot does not trade BTC

    def test_readers_that_only_know_the_freeze_databases_still_see_each_pair_alone(self) -> None:
        from lab import dashboard
        self.multi_pair_bot()
        card = dashboard._dryrun(self.root)[0]
        self.assertEqual(card["pairs"]["ETH/USDT"]["trades"], 1)
        self.assertEqual((card["pairs"]["SOL/USDT"]["trades"], card["pairs"]["SOL/USDT"]["open"]), (2, 1))

    def test_the_portal_page_includes_the_new_routes(self) -> None:
        from lab import dashboard
        template = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        self.assertIn("/*__DRYRUN_LIVE__*/", template)
        self.assertIn("id: 'aovivo'", template)
        self.assertIn("pageDryrunLive", template)


if __name__ == "__main__":
    unittest.main()
