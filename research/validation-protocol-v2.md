# Reproducible validation protocol v2

## Frozen scope

- Spot only; long only; no margin, leverage, futures, or short.
- BTC/USDT and 1h until a separate universe protocol is approved.
- Closed candles only; a signal at candle close is executed no earlier than the next candle.
- No private exchange credentials and no live trading.
- `SmaTrendBaseline` is immutable and is never optimized retrospectively.

## Required experiment order

1. Validate the dataset and save its SHA-256.
2. Record the hypothesis in `research/hypothesis-ledger.md`.
3. Record the exact runtime, image, configuration, command, and hashes in a manifest.
4. Run the normal backtest and export trades.
5. Run `lookahead-analysis` and save its separate output.
6. Run `recursive-analysis` and save its separate output.
7. Run the same experiment under declared cost scenarios.
8. Compare with cash, buy-and-hold, and approved simple benchmarks.
9. Report all subperiods and all tested variants.
10. Keep the final test period locked until every preceding decision is frozen.

## Cost scenarios

The fee and slippage values are experiment inputs, not claims about historical execution.
Every result must state fee per side, spread assumption, slippage per side, order type,
price source, timeout, and whether partial fills are modeled.

Minimum scenarios:

- optimistic: fee 0.10% per side, 0 bps slippage, 0 bps additional spread;
- base: fee 0.10% per side, 5 bps slippage per side, 5 bps spread;
- conservative: fee 0.10% per side, 10--20 bps slippage per side, 10 bps spread;
- stress: fee at least 0.10% per side, 25--50 bps slippage per side, 25 bps spread.

These are sensitivity scenarios. They must not be presented as measured Binance costs.

**Amendment, 2026-11-06 (owner, Luiz Kelme).** To make day-trade rules viable: the fee is 0.075% per side in every scenario (Binance spot fee paid in BNB; a real account must hold BNB for fees), slippage and spread unchanged; the 25% drawdown ceiling applies to optimistic, base and conservative, and the stress drawdown is reported. Decisions made before this date used the 0.10% fee and the stress drawdown gate.

## Approval and rejection

A strategy is not approved by positive return alone. It must have causal signals,
reproducible data, no detected lookahead, stable startup behavior, enough observations
for the stated question, explicit costs, benchmark comparison, and no dependence on a
single period or trade. With one or very few trades, report `inconclusive`.

## Commands

Run from WSL with Docker available:

```bash
python3 research/validate_ohlcv.py user_data/data/binance/BTC_USDT-1h.feather
python3 -m unittest discover -s tests -v

docker compose config --quiet
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

The exact backtest, lookahead, and recursive commands must be copied into the manifest.
Do not use `stable` image tags or overwrite prior result artifacts.
