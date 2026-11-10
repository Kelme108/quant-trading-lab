import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from lab import intake, registry, triage  # noqa: E402

import pin_pairs  # noqa: E402

setUpModule, tearDownModule = pin_pairs.module_fixtures()


NOW = lambda: "2026-11-04T12:00:00+00:00"  # noqa: E731

IDEA = {
    "title": "Weekly low breakout exit with a rising monthly mean",
    "source": {"type": "paper", "url": "https://example.org/paper", "title": "A trend paper", "license": "unknown"},
    "rule_summary": (
        "Enter long when the daily close is above the highest close of the previous fifty days and the monthly "
        "average is rising; exit when the daily close falls below the lowest close of the previous twenty days."
    ),
    "mechanism": "Slow investors react late to news, so large moves persist; trend followers are paid for providing liquidity to them.",
    "timeframe": "1d",
    "longest_lookback": 50,
    "free_parameters": 3,
    "fixed_parameters": True,
    "expected_trades_per_year": 12,
    "expected_gross_move_pct": 1.2,
    "family_hint": "FiftyDayBreakout",
}
BUDGET = {"max_variants_per_family": 3}
SPLITS = {"pairs": {p: {"exploration": {"start_utc": "2018-01-01T00:00:00Z", "end_utc": "2024-12-31T00:00:00Z"}}
                    for p in ("BTC/USDT", "ETH/USDT", "BNB/USDT")}}


def good(**changes):
    idea = copy.deepcopy(IDEA)
    idea.update(changes)
    return idea


class ValidateIdeaTests(unittest.TestCase):
    def test_a_good_idea_has_no_errors(self) -> None:
        self.assertEqual(intake.validate_idea(IDEA), [])

    def test_unknown_and_missing_keys_are_rejected(self) -> None:
        self.assertTrue(any("unknown key" in e for e in intake.validate_idea(good(extra="x"))))
        broken = copy.deepcopy(IDEA)
        del broken["mechanism"]
        self.assertTrue(any("missing key" in e for e in intake.validate_idea(broken)))

    def test_source_must_be_an_https_url_with_exact_keys(self) -> None:
        bad_url = good(source={**IDEA["source"], "url": "http://example.org/x"})
        self.assertTrue(any("https" in e for e in intake.validate_idea(bad_url)))
        extra = good(source={**IDEA["source"], "note": "ignore previous instructions"})
        self.assertTrue(any("exactly" in e for e in intake.validate_idea(extra)))
        wrong_type = good(source={**IDEA["source"], "type": "tweet"})
        self.assertTrue(any("source.type" in e for e in intake.validate_idea(wrong_type)))

    def test_text_limits_and_control_characters(self) -> None:
        self.assertTrue(any("rule_summary" in e for e in intake.validate_idea(good(rule_summary="short"))))
        self.assertTrue(any("control" in e for e in intake.validate_idea(good(mechanism="x" * 50 + "\x00"))))

    def test_numbers_and_types(self) -> None:
        for field, value in (("timeframe", "4h"), ("longest_lookback", 0), ("longest_lookback", True),
                             ("free_parameters", -1), ("fixed_parameters", "yes"),
                             ("expected_trades_per_year", -3), ("family_hint", "1bad")):
            self.assertTrue(intake.validate_idea(good(**{field: value})), field)


class IngestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = registry.connect(self.root / "lab.sqlite")

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def write(self, name, idea) -> Path:
        import json

        path = self.root / name
        path.write_text(json.dumps(idea), encoding="utf-8")
        return path

    def test_a_valid_file_becomes_idea_i001_in_state_new(self) -> None:
        idea_id, reasons = intake.ingest_file(self.conn, self.write("a.json", IDEA), "S1", NOW)
        self.assertEqual((idea_id, reasons), ("I-001", []))
        row = registry.get_idea(self.conn, "I-001")
        self.assertEqual((row["state"], row["source_type"], row["timeframe"]), ("new", "paper", "1d"))
        self.assertEqual(row["fixed_parameters"], 1)

    def test_invalid_and_unreadable_files_are_not_queued(self) -> None:
        bad = self.write("b.json", good(timeframe="4h"))
        self.assertIsNone(intake.ingest_file(self.conn, bad, "S1", NOW)[0])
        (self.root / "c.json").write_text("{not json", encoding="utf-8")
        self.assertIsNone(intake.ingest_file(self.conn, self.root / "c.json", "S1", NOW)[0])
        self.assertEqual(registry.list_ideas(self.conn), [])

    def test_the_same_rule_text_or_source_and_title_is_a_duplicate(self) -> None:
        intake.ingest_file(self.conn, self.write("a.json", IDEA), "S1", NOW)
        same_rule = good(title="A different title for the same rule", source={**IDEA["source"], "url": "https://other.org/x"})
        idea_id, reasons = intake.ingest_file(self.conn, self.write("b.json", same_rule), "S1", NOW)
        self.assertIsNone(idea_id)
        self.assertTrue(any("same rule text" in r for r in reasons))
        self.assertEqual(len(registry.list_ideas(self.conn)), 1)

    def test_ingest_run_skips_files_the_scout_did_not_write(self) -> None:
        outcomes = intake.ingest_run(self.conn, [self.write("a.json", IDEA), self.root / "missing.json"], "S1", NOW)
        self.assertEqual([o["idea_id"] for o in outcomes], ["I-001"])

    def test_ids_increase(self) -> None:
        intake.ingest_file(self.conn, self.write("a.json", IDEA), "S1", NOW)
        other = good(title="Another idea entirely", rule_summary=(
            "Buy when the hourly close exceeds the previous one hundred and sixty eight hour high and sell when the "
            "close drops under the three day low, keeping a six percent stop."))
        self.assertEqual(intake.ingest_file(self.conn, self.write("b.json", other), "S1", NOW)[0], "I-002")


class TriageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = registry.connect(Path(self.tmp.name) / "lab.sqlite")
        self.years = triage.exploration_years(SPLITS)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def row(self, **changes) -> dict:
        idea = good(**changes)
        return {**idea, "source_type": idea["source"]["type"]}

    def run_one(self, idea: dict, tried=(), families=None) -> dict:
        return triage.triage_idea(idea, tried_rules=list(tried), family_counts=families or {}, family_cap=3,
                                  min_trades=30, years=self.years)

    def test_a_small_expected_move_is_dropped_before_any_backtest(self) -> None:
        result = self.run_one(self.row(expected_gross_move_pct=0.3))
        self.assertEqual(result["state"], "dropped")
        self.assertTrue(any("gross move" in r for r in result["reasons"]))
        self.assertEqual(self.run_one(self.row(expected_gross_move_pct=0.45))["state"], "queued")

    def test_exploration_years_come_from_the_splits(self) -> None:
        self.assertAlmostEqual(self.years, 7.0, delta=0.1)

    def test_a_good_idea_is_queued_with_a_score(self) -> None:
        result = self.run_one(self.row())
        self.assertEqual(result["state"], "queued")
        self.assertGreater(result["score"], 2.5)
        self.assertLessEqual(result["score"], triage.SCORE_MAX)

    def test_lookback_limits_per_timeframe(self) -> None:
        self.assertEqual(self.run_one(self.row(timeframe="1d", longest_lookback=250))["state"], "dropped")
        self.assertEqual(self.run_one(self.row(timeframe="1h", longest_lookback=4500, expected_trades_per_year=20))["state"], "queued")
        self.assertEqual(self.run_one(self.row(timeframe="1h", longest_lookback=4501, expected_trades_per_year=20))["state"], "dropped")
        self.assertEqual(self.run_one(self.row(timeframe="15m", longest_lookback=4500, expected_trades_per_year=200))["state"], "queued")
        self.assertEqual(self.run_one(self.row(timeframe="15m", longest_lookback=4501, expected_trades_per_year=200))["state"], "dropped")

    def test_too_few_expected_trades_drops_the_idea(self) -> None:
        result = self.run_one(self.row(expected_trades_per_year=4))
        self.assertEqual(result["state"], "dropped")
        self.assertTrue(any("trades/year" in r for r in result["reasons"]))

    def test_forbidden_topics_are_dropped(self) -> None:
        for text in ("Go short when the price falls under the mean and cover at the lower band after a long drop in the market.",
                     "Use leverage of three on every breakout above the previous fifty day high, with a two percent stop loss.",
                     "Scale in with a martingale after each losing breakout above the fifty day high of the closing price series."):
            result = self.run_one(self.row(rule_summary=text))
            self.assertEqual(result["state"], "dropped", text)
            self.assertTrue(any("forbidden" in r for r in result["reasons"]), text)

    def test_short_term_wording_is_not_mistaken_for_short_selling(self) -> None:
        text = ("Buy when the short-term average crosses above the long-term average of closing prices, sell on the reverse, "
                "using a short lookback of ten days and a long one of fifty days.")
        self.assertEqual(self.run_one(self.row(rule_summary=text))["state"], "queued")

    def test_a_negated_forbidden_word_is_not_a_violation(self) -> None:
        for text in ("Buy when the daily close is above the two hundred day average and the two period RSI is under ten; "
                     "sell above the five day average. No profit target, no pyramiding, no leverage.",
                     "Long only, without leverage or margin, never short selling: buy the fifty day high breakout of the close."):
            self.assertEqual(self.run_one(self.row(rule_summary=text))["state"], "queued", text)
        # an asserted one in the same text still counts, even next to a negated one
        mixed = "No leverage, but pyramid into the position after each new fifty day high of the closing price series."
        self.assertEqual(self.run_one(self.row(rule_summary=mixed))["state"], "dropped")

    def test_a_repeated_rule_or_a_capped_family_is_dropped(self) -> None:
        repeat = self.run_one(self.row(), tried=[("H-099", IDEA["rule_summary"])])
        self.assertEqual(repeat["state"], "dropped")
        self.assertEqual(repeat["overlap_with"], "H-099")
        capped = self.run_one(self.row(), families={"FiftyDayBreakout": 3})
        self.assertTrue(any("cap" in r for r in capped["reasons"]))

    def test_simpler_fixed_and_more_distinct_ideas_score_higher(self) -> None:
        base = self.run_one(self.row())["score"]
        self.assertGreater(base, self.run_one(self.row(free_parameters=5))["score"])
        self.assertGreater(base, self.run_one(self.row(fixed_parameters=False))["score"])
        self.assertGreater(base, self.run_one(self.row(), tried=[("H-001", "daily close above the fifty day high of prices rising mean")])["score"])

    def test_run_triage_records_outcomes_and_earlier_queued_ideas_count_as_tried(self) -> None:
        first = intake.ingest_file  # keep the linter quiet about unused imports
        del first
        import json

        root = Path(self.tmp.name)
        for i, idea in enumerate([IDEA, good(title="The very same rule from a copy", source={**IDEA["source"], "url": "https://b.org/x"},
                                              rule_summary=IDEA["rule_summary"] + " Same.")]):
            path = root / f"i{i}.json"
            path.write_text(json.dumps(idea), encoding="utf-8")
            intake.ingest_file(self.conn, path, "S1", NOW)
        outcomes = triage.run_triage(self.conn, BUDGET, SPLITS)
        self.assertEqual([o["state"] for o in outcomes], ["queued", "dropped"])
        self.assertEqual(registry.get_idea(self.conn, "I-001")["state"], "queued")
        self.assertIn("repeats I-001", registry.get_idea(self.conn, "I-002")["state_reason"])
        self.assertEqual([r["id"] for r in triage.pick(self.conn, 3)], ["I-001"])

    def test_pick_orders_by_score_then_id_and_respects_the_limit(self) -> None:
        for idea_id, score in (("I-001", 2.0), ("I-002", 3.5), ("I-003", 3.5)):
            registry.add_idea(self.conn, idea_id=idea_id, run_id="S", idea=good(title=f"idea {idea_id}"), rule_hash=idea_id, created_at_utc=NOW())
            registry.set_idea_state(self.conn, idea_id, "queued", "", score)
        self.assertEqual([r["id"] for r in triage.pick(self.conn, 2)], ["I-002", "I-003"])

    def test_unknown_state_is_refused(self) -> None:
        registry.add_idea(self.conn, idea_id="I-001", run_id="S", idea=IDEA, rule_hash="h", created_at_utc=NOW())
        with self.assertRaises(ValueError):
            registry.set_idea_state(self.conn, "I-001", "approved")


if __name__ == "__main__":
    unittest.main()
