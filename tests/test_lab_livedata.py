import tempfile
import unittest
from pathlib import Path

from lab import livedata


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

    def test_the_portal_page_includes_the_new_routes(self) -> None:
        from lab import dashboard
        template = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        self.assertIn("/*__DRYRUN_LIVE__*/", template)
        self.assertIn("id: 'aovivo'", template)
        self.assertIn("pageDryrunLive", template)


if __name__ == "__main__":
    unittest.main()
