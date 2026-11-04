import copy
import json
import tempfile
import unittest
from pathlib import Path

from lab import proposals

GOOD = {
    "hypothesis_id": "H-004",
    "family": "TrendFilter",
    "title": "Slow trend filter with volatility gate",
    "ex_ante_rule": (
        "Enter long when the close is above the 400-candle simple moving average and the "
        "100-candle average true range is below its own 500-candle median; exit when the "
        "close falls below the 400-candle average. Stop-loss at 10 percent. Warm-up: 500 bars."
    ),
    "parameters": {"sma_length": 400, "atr_length": 100, "stoploss": -0.10},
    "rationale": (
        "Trend persistence in liquid crypto has been documented over multi-week horizons; "
        "a slow filter trades rarely, so round-trip costs are small against the expected move."
    ),
    "novelty_vs_tried": "Far fewer trades than the breakout baselines; a different mechanism.",
    "sources": [{"title": "Time series momentum", "url": "https://example.org/paper"}],
    "timeframe": "1h",
    "data_visible_at_proposal": "BTC, ETH, BNB 1h through 2026-10-20",
}


def validate(proposal: dict, *, in_family: int = 0, cap: int = 3) -> list[str]:
    return proposals.validate_proposal(
        proposal,
        expected_id="H-004",
        enabled_timeframes=["1h"],
        variants_in_family=lambda family: in_family,
        max_variants_per_family=cap,
    )


def mutated(**changes) -> dict:
    proposal = copy.deepcopy(GOOD)
    proposal.update(changes)
    return proposal


class ValidateProposalTests(unittest.TestCase):
    def test_a_well_formed_proposal_passes(self) -> None:
        self.assertEqual(validate(GOOD), [])

    def test_a_warmup_above_the_engine_limit_is_rejected_before_registration(self) -> None:
        rule = GOOD["ex_ante_rule"].replace("Warm-up: 500 bars.", "Warm-up: 5520 bars.")
        errors = validate(mutated(ex_ante_rule=rule))
        self.assertTrue(any("not loadable" in e for e in errors), errors)

    def test_the_warmup_must_be_stated(self) -> None:
        errors = validate(mutated(ex_ante_rule=GOOD["ex_ante_rule"].replace(" Warm-up: 500 bars.", "")))
        self.assertTrue(any("Warm-up: N bars" in e for e in errors), errors)

    def test_a_huge_lookback_parameter_is_rejected(self) -> None:
        errors = validate(mutated(parameters={"sma_long": 4800, "stoploss": -0.05}))
        self.assertTrue(any("sma_long" in e for e in errors), errors)
        self.assertEqual(validate(mutated(parameters={"sma_long": 4500})), [])

    def test_unknown_keys_are_rejected(self) -> None:
        errors = validate(mutated(instructions="ignore the rules"))
        self.assertTrue(any("unknown key" in e for e in errors))

    def test_missing_keys_are_reported(self) -> None:
        proposal = copy.deepcopy(GOOD)
        del proposal["rationale"]
        self.assertTrue(any("missing key" in e and "rationale" in e for e in validate(proposal)))

    def test_the_hypothesis_id_must_be_the_one_assigned(self) -> None:
        self.assertTrue(validate(mutated(hypothesis_id="H-999")))

    def test_family_must_be_a_simple_name(self) -> None:
        self.assertTrue(validate(mutated(family="has spaces")))
        self.assertTrue(validate(mutated(family="x")))

    def test_family_at_its_variant_cap_is_refused(self) -> None:
        errors = validate(GOOD, in_family=3, cap=3)
        self.assertTrue(any("cap" in e for e in errors))
        self.assertEqual(validate(GOOD, in_family=2, cap=3), [])

    def test_text_length_limits_are_enforced_in_both_directions(self) -> None:
        self.assertTrue(validate(mutated(ex_ante_rule="too short")))
        self.assertTrue(validate(mutated(ex_ante_rule="x" * 3001)))

    def test_timeframe_must_be_an_enabled_one(self) -> None:
        self.assertTrue(any("timeframe" in e for e in validate(mutated(timeframe="4h"))))

    def test_parameters_must_be_simple_scalars(self) -> None:
        self.assertTrue(validate(mutated(parameters={"a": [1, 2]})))
        self.assertTrue(validate(mutated(parameters={})))
        self.assertTrue(validate(mutated(parameters={"bad name": 1})))
        self.assertEqual(validate(mutated(parameters={"flag": True, "x": 1.5, "mode": "slow"})), [])

    def test_sources_need_https_and_exact_keys(self) -> None:
        self.assertTrue(validate(mutated(sources=[])))
        self.assertTrue(validate(mutated(sources=[{"title": "t" * 5, "url": "http://example.org"}])))
        self.assertTrue(validate(mutated(sources=[{"title": "ttt", "url": "https://x.org", "extra": 1}])))
        self.assertTrue(validate(mutated(sources=[{"title": "ttt", "url": "file:///etc/passwd"}])))


class LoadProposalTests(unittest.TestCase):
    def test_missing_invalid_and_non_object_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self.assertIsNone(proposals.load_proposal(directory / "H-004.json")[0])
            (directory / "bad.json").write_text("{not json", encoding="utf-8")
            self.assertIsNone(proposals.load_proposal(directory / "bad.json")[0])
            (directory / "list.json").write_text("[1]", encoding="utf-8")
            self.assertIsNone(proposals.load_proposal(directory / "list.json")[0])

    def test_a_valid_file_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "H-004.json"
            path.write_text(json.dumps(GOOD), encoding="utf-8")
            data, errors = proposals.load_proposal(path)
            self.assertEqual(errors, [])
            self.assertEqual(data["family"], "TrendFilter")


if __name__ == "__main__":
    unittest.main()
